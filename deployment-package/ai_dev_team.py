#!/usr/bin/env python3
"""
AI Development Team - MCP-based AI agents for GitHub automation
"""

import asyncio
import json
import ast
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import uuid

from anthropic import AsyncAnthropic
import asyncpg
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubEvent(BaseModel):
    event_type: str
    repository: str
    ref: Optional[str] = None
    commits: Optional[List[Dict]] = None
    pull_request: Optional[Dict] = None
    files_changed: Optional[List[str]] = None

class AgentResult(BaseModel):
    role: str
    analysis: str
    actions: List[Dict]
    success: bool
    error: Optional[str] = None

class AIDevTeam:
    """AI Development Team with multiple specialized roles"""
    
    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.db_url = os.getenv('DATABASE_URL', '')
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        # Role-specific system prompts
        self.roles = {
            'backend': {
                'prompt': '''You are an expert Backend Engineer AI agent. Your role is to:
- Review server-side code changes for quality, performance, and security
- Suggest specific improvements with code examples
- Generate comprehensive unit and integration tests
- Ensure proper error handling and validation
- Follow REST/GraphQL best practices
- Focus on scalability and maintainability

When analyzing code, provide:
1. Brief analysis of changes
2. Specific improvement suggestions with code examples
3. Security considerations
4. Test recommendations
5. Performance implications

Output format: JSON with analysis, improvements, tests, and actions.''',
                'temperature': 0.1,
                'file_patterns': ['.py', '.js', '.ts', '.java', '.go', '.php', '.rb', '.cs']
            },
            
            'frontend': {
                'prompt': '''You are an expert Frontend Engineer AI agent. Your role is to:
- Review client-side code for UI/UX best practices
- Ensure responsive design and accessibility
- Optimize for performance and user experience
- Maintain consistent component architecture
- Follow modern React/Vue/Angular patterns
- Ensure cross-browser compatibility

When analyzing code, provide:
1. UI/UX analysis
2. Accessibility improvements
3. Performance optimizations
4. Component structure suggestions
5. CSS/styling recommendations

Output format: JSON with analysis, improvements, and actions.''',
                'temperature': 0.1,
                'file_patterns': ['.jsx', '.tsx', '.vue', '.css', '.scss', '.html']
            },
            
            'qa': {
                'prompt': '''You are an expert QA Engineer AI agent. Your role is to:
- Analyze code changes for potential bugs and edge cases
- Generate comprehensive test plans and test cases
- Identify integration points and failure scenarios
- Ensure proper test coverage
- Focus on user workflows and error handling
- Suggest automated testing strategies

When analyzing code, provide:
1. Risk assessment of changes
2. Detailed test plan with scenarios
3. Edge cases and error conditions
4. Test automation suggestions
5. Quality recommendations

Output format: JSON with analysis, test_plan, test_cases, and actions.''',
                'temperature': 0.2,
                'file_patterns': ['*']  # QA reviews all file types
            },
            
            'devops': {
                'prompt': '''You are an expert DevOps Engineer AI agent. Your role is to:
- Review infrastructure and deployment configurations
- Ensure CI/CD pipeline efficiency and security
- Optimize containerization and orchestration
- Monitor performance and reliability
- Implement proper monitoring and alerting
- Focus on scalability and automation

When analyzing code, provide:
1. Infrastructure analysis
2. Deployment improvements
3. Security configurations
4. Monitoring recommendations
5. Automation opportunities

Output format: JSON with analysis, improvements, and actions.''',
                'temperature': 0.1,
                'file_patterns': ['.yml', '.yaml', 'Dockerfile', '.tf', '.json']
            },
            
            'security': {
                'prompt': '''You are an expert Security Engineer AI agent. Your role is to:
- Identify security vulnerabilities and risks
- Ensure secure coding practices
- Review authentication and authorization
- Check for data protection compliance
- Analyze dependency security
- Suggest security improvements

When analyzing code, provide:
1. Security risk assessment
2. Vulnerability identification
3. Secure coding recommendations
4. Compliance considerations
5. Mitigation strategies

Output format: JSON with analysis, vulnerabilities, recommendations, and actions.''',
                'temperature': 0.1,
                'file_patterns': ['*']  # Security reviews all file types
            }
        }
    
    async def connect_db(self):
        """Connect to PostgreSQL database"""
        if not self.db_url:
            raise RuntimeError("DATABASE_URL is not set; database connectivity is disabled")
        return await asyncpg.connect(self.db_url)

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Remove common Markdown code fences from a string."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(cleaned.splitlines()[1:])
        if cleaned.endswith("```"):
            cleaned = "\n".join(cleaned.splitlines()[:-1])
        return cleaned.strip()

    @staticmethod
    def _try_load_json_lenient(text: str) -> Any:
        """Attempt to parse JSON by extracting a JSON block and fixing common issues.
        Strategy:
        - Prefer ```json fenced blocks if present
        - Strip markdown fences
        - Remove // and /* */ comments
        - Remove trailing commas repeatedly
        - Normalize smart quotes
        - Try json.loads; on failure, try ast.literal_eval after mapping true/false/null
        """
        raw = text.strip()
        # Prefer fenced json block
        fence_match = re.search(r"```json\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
        if fence_match:
            candidate = fence_match.group(1)
        else:
            candidate = AIDevTeam._strip_code_fences(raw)
        # Extract the first top-level object to ignore prose before/after
        start_index = candidate.find('{')
        end_index = candidate.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            candidate = candidate[start_index:end_index + 1]
        # Remove line and block comments
        candidate = re.sub(r"//.*?$", "", candidate, flags=re.MULTILINE)
        candidate = re.sub(r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/", "", candidate, flags=re.DOTALL)
        # Remove trailing commas repeatedly until stable
        while True:
            new_candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
            if new_candidate == candidate:
                break
            candidate = new_candidate
        # Normalize smart quotes
        candidate = candidate.replace('\u201c', '"').replace('\u201d', '"').replace('\u2019', "'")
        # First try strict JSON
        try:
            return json.loads(candidate)
        except Exception:
            pass
        # Fallback: attempt Python literal eval after mapping JSON constants
        py_like = re.sub(r"\btrue\b", "True", candidate, flags=re.IGNORECASE)
        py_like = re.sub(r"\bfalse\b", "False", py_like, flags=re.IGNORECASE)
        py_like = re.sub(r"\bnull\b", "None", py_like, flags=re.IGNORECASE)
        try:
            return ast.literal_eval(py_like)
        except Exception:
            # Re-raise the original strict error for clearer logging if both fail
            return json.loads(candidate)
    
    async def determine_role(self, event: GitHubEvent) -> str:
        """Determine the appropriate AI role based on the event and files changed"""
        if not event.files_changed:
            return 'backend'  # Default role
        
        # Count files matching each role's patterns
        role_scores = {}
        for role, config in self.roles.items():
            score = 0
            for file in event.files_changed:
                for pattern in config['file_patterns']:
                    if pattern == '*' or file.endswith(pattern):
                        score += 1
            role_scores[role] = score
        
        # Return role with highest score
        return max(role_scores.items(), key=lambda x: x[1])[0]
    
    async def get_github_files(self, repo: str, files: List[str], ref: str = 'main') -> Dict[str, str]:
        """Get file contents from GitHub (simulated - would use actual MCP GitHub tools)"""
        # In a real implementation, this would use MCP GitHub tools
        # For now, return simulated file contents
        file_contents = {}
        for file in files[:5]:  # Limit to 5 files to avoid token limits
            file_contents[file] = f"// Contents of {file}\n// This would be the actual file content from GitHub\n"
        return file_contents
    
    async def analyze_with_role(self, role: str, event: GitHubEvent, file_contents: Dict[str, str]) -> AgentResult:
        """Analyze the event using the specified role's expertise"""
        role_config = self.roles[role]
        
        # Prepare context for the AI
        context = {
            'event_type': event.event_type,
            'repository': event.repository,
            'files_changed': event.files_changed,
            'file_contents': file_contents,
            'commits': event.commits[:3] if event.commits else [],  # Limit to recent commits
        }
        
        messages = [
            {'role': 'user', 'content': f'''{role_config['prompt']}

Please analyze the following code changes and provide recommendations:

Context: {json.dumps(context, indent=2)}

Please provide your analysis in the following JSON format (a single top-level JSON object):
{{
    "analysis": "Brief analysis of the changes",
    "improvements": [
        {{
            "file": "path/to/file",
            "issue": "Description of issue",
            "suggestion": "Specific improvement suggestion",
            "code_example": "Example code if applicable"
        }}
    ],
    "actions": [
        {{
            "type": "create_branch|create_file|create_pr|add_comment",
            "parameters": {{"branch_name": "ai/improvements", "file_path": "...", "content": "..."}}
        }}
    ],
    "priority": "low|medium|high",
    "confidence": 0.95
}}

Return only valid JSON. Do not include any prose, markdown, or code fences. If unsure, still return syntactically valid JSON matching the schema above.'''}
        ]
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=messages,
                temperature=role_config['temperature'],
                max_tokens=2000
            )
            
            content = response.content[0].text
            try:
                result_data = json.loads(content)
            except json.JSONDecodeError:
                result_data = self._try_load_json_lenient(content)
            
            return AgentResult(
                role=role,
                analysis=result_data.get('analysis', ''),
                actions=result_data.get('actions', []),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in {role} analysis: {str(e)}")
            return AgentResult(
                role=role,
                analysis=f"Error in analysis: {str(e)}",
                actions=[],
                success=False,
                error=str(e)
            )
    
    async def execute_github_actions(self, actions: List[Dict], repo: str) -> List[Dict]:
        """Execute GitHub actions via MCP (simulated)"""
        results = []
        
        for action in actions:
            action_type = action.get('type')
            params = action.get('parameters', {})
            
            try:
                if action_type == 'create_branch':
                    # Simulate branch creation
                    result = {
                        'action': action_type,
                        'success': True,
                        'url': f"https://github.com/{repo}/tree/{params.get('branch_name')}",
                        'message': f"Created branch {params.get('branch_name')}"
                    }
                
                elif action_type == 'create_file':
                    # Simulate file creation
                    result = {
                        'action': action_type,
                        'success': True,
                        'url': f"https://github.com/{repo}/blob/main/{params.get('file_path')}",
                        'message': f"Created file {params.get('file_path')}"
                    }
                
                elif action_type == 'create_pr':
                    # Simulate PR creation
                    result = {
                        'action': action_type,
                        'success': True,
                        'url': f"https://github.com/{repo}/pull/123",  # Simulated PR number
                        'message': f"Created PR: {params.get('title')}"
                    }
                
                elif action_type == 'add_comment':
                    # Simulate comment addition
                    result = {
                        'action': action_type,
                        'success': True,
                        'url': f"https://github.com/{repo}/issues/{params.get('issue_number')}#comment",
                        'message': f"Added comment to issue/PR {params.get('issue_number')}"
                    }
                
                else:
                    result = {
                        'action': action_type,
                        'success': False,
                        'error': f"Unknown action type: {action_type}"
                    }
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'action': action_type,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    async def log_run(self, run_id: str, event: GitHubEvent, role: str, result: AgentResult, action_results: List[Dict]):
        """Log the agent run to database"""
        try:
            if not self.db_url:
                logger.info("Skipping database logging because DATABASE_URL is not set")
                return
            conn = await self.connect_db()
            
            # Insert run record
            await conn.execute('''
                INSERT INTO agent_runs (run_id, trigger_type, trigger_data, role, status, result)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', run_id, event.event_type, json.dumps(event.dict()), role, 
                'completed' if result.success else 'failed', json.dumps(result.dict()))
            
            # Insert action records
            for action_result in action_results:
                await conn.execute('''
                    INSERT INTO agent_actions (run_id, action_type, resource, success)
                    VALUES ($1, $2, $3, $4)
                ''', run_id, action_result.get('action'), action_result.get('url'), action_result.get('success'))
            
            await conn.close()
            logger.info(f"Logged run {run_id} to database")
            
        except Exception as e:
            logger.error(f"Error logging run to database: {str(e)}")
    
    async def handle_push_event(self, payload: Dict) -> Dict:
        """Handle GitHub push event"""
        run_id = str(uuid.uuid4())
        
        # Parse the event
        event = GitHubEvent(
            event_type='push',
            repository=payload.get('repository', {}).get('full_name', ''),
            ref=payload.get('ref', ''),
            commits=payload.get('commits', []),
            files_changed=self.extract_changed_files(payload.get('commits', []))
        )
        
        logger.info(f"Handling push event {run_id} for {event.repository}")
        
        # Determine appropriate role
        role = await self.determine_role(event)
        logger.info(f"Selected role: {role}")
        
        # Get file contents
        file_contents = await self.get_github_files(event.repository, event.files_changed or [])
        
        # Analyze with selected role
        result = await self.analyze_with_role(role, event, file_contents)
        
        # Execute actions
        action_results = []
        if result.success and result.actions:
            action_results = await self.execute_github_actions(result.actions, event.repository)
        
        # Log to database
        await self.log_run(run_id, event, role, result, action_results)
        
        return {
            'run_id': run_id,
            'role': role,
            'success': result.success,
            'analysis': result.analysis,
            'actions_executed': len(action_results),
            'action_results': action_results
        }
    
    async def handle_pr_event(self, payload: Dict) -> Dict:
        """Handle GitHub pull request event"""
        run_id = str(uuid.uuid4())
        
        pr_data = payload.get('pull_request', {})
        event = GitHubEvent(
            event_type='pull_request',
            repository=payload.get('repository', {}).get('full_name', ''),
            pull_request=pr_data,
            files_changed=[]  # Would get from PR files API
        )
        
        logger.info(f"Handling PR event {run_id} for {event.repository}")
        
        # Always use QA role for PR analysis
        role = 'qa'
        
        # Get PR file contents (simulated)
        file_contents = await self.get_github_files(event.repository, event.files_changed or [])
        
        # Analyze with QA role
        result = await self.analyze_with_role(role, event, file_contents)
        
        # Execute actions (typically adding comments)
        action_results = []
        if result.success and result.actions:
            action_results = await self.execute_github_actions(result.actions, event.repository)
        
        # Log to database
        await self.log_run(run_id, event, role, result, action_results)
        
        return {
            'run_id': run_id,
            'role': role,
            'success': result.success,
            'analysis': result.analysis,
            'actions_executed': len(action_results),
            'action_results': action_results
        }
    
    def extract_changed_files(self, commits: List[Dict]) -> List[str]:
        """Extract changed files from commits"""
        files = set()
        for commit in commits:
            if 'added' in commit:
                files.update(commit['added'])
            if 'modified' in commit:
                files.update(commit['modified'])
        return list(files)

# Example usage
async def main():
    """Test the AI dev team"""
    team = AIDevTeam()
    
    # Simulate a push event
    test_payload = {
        'repository': {'full_name': 'user/test-repo'},
        'ref': 'refs/heads/main',
        'commits': [
            {
                'id': 'abc123',
                'message': 'Add new API endpoint',
                'modified': ['src/api/users.py', 'tests/test_users.py'],
                'added': ['src/models/user_profile.py']
            }
        ]
    }
    
    result = await team.handle_push_event(test_payload)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())