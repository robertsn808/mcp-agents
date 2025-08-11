#!/usr/bin/env python3
"""
Webhook Server for AI Development Team
Receives GitHub webhooks and routes them to appropriate AI agents
"""

import asyncio
import json
import logging
from typing import Dict, Any
import os
import hashlib
import hmac
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from ai_dev_team import AIDevTeam
from property_search_agent import PropertySearchAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Development Team", description="AI agents for GitHub automation")

# Initialize AI team
ai_team = AIDevTeam()

# Initialize property search agent
property_agent = PropertySearchAgent()

# GitHub webhook secret for signature verification
WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', '')

def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify GitHub webhook signature"""
    if not WEBHOOK_SECRET:
        logger.warning("No webhook secret configured - skipping signature verification")
        return True
    
    if not signature_header:
        return False
    
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)

async def process_github_event(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process GitHub event with appropriate AI agent"""
    try:
        if event_type == 'push':
            # Skip if it's a branch deletion
            if payload.get('deleted'):
                return {'status': 'skipped', 'reason': 'Branch deletion event'}
            
            # Skip if no commits
            if not payload.get('commits'):
                return {'status': 'skipped', 'reason': 'No commits in push'}
            
            # Skip if commits are from AI agents (avoid loops)
            commits = payload.get('commits', [])
            if any('Co-authored-by: AI' in commit.get('message', '') for commit in commits):
                return {'status': 'skipped', 'reason': 'AI-generated commits detected'}
            
            result = await ai_team.handle_push_event(payload)
            return {'status': 'success', 'data': result}
        
        elif event_type == 'pull_request':
            action = payload.get('action')
            
            # Only process opened PRs
            if action != 'opened':
                return {'status': 'skipped', 'reason': f'PR action "{action}" not relevant'}
            
            # Skip if PR is from AI agents (avoid loops)
            pr = payload.get('pull_request', {})
            if pr.get('head', {}).get('ref', '').startswith('ai/'):
                return {'status': 'skipped', 'reason': 'AI-generated PR detected'}
            
            result = await ai_team.handle_pr_event(payload)
            return {'status': 'success', 'data': result}
        
        elif event_type == 'issues':
            action = payload.get('action')
            
            if action == 'opened':
                # Could handle issue analysis here
                return {'status': 'skipped', 'reason': 'Issue handling not implemented yet'}
        
        else:
            return {'status': 'skipped', 'reason': f'Event type "{event_type}" not supported'}
    
    except Exception as e:
        logger.error(f"Error processing {event_type} event: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Development Team",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/status")
async def get_status():
    """Get service status and recent activity"""
    try:
        # Get recent runs from database
        conn = await ai_team.connect_db()
        
        recent_runs = await conn.fetch('''
            SELECT run_id, trigger_type, role, status, created_at
            FROM agent_runs
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        
        # Get stats
        stats = await conn.fetchrow('''
            SELECT 
                COUNT(*) as total_runs,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_runs,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_runs
            FROM agent_runs
            WHERE created_at > NOW() - INTERVAL '24 hours'
        ''')
        
        await conn.close()
        
        return {
            "status": "operational",
            "recent_runs": [dict(run) for run in recent_runs],
            "stats_24h": dict(stats) if stats else {}
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {"status": "error", "error": str(e)}

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events"""
    try:
        # Get headers
        event_type = request.headers.get('x-github-event')
        signature = request.headers.get('x-hub-signature-256')
        delivery_id = request.headers.get('x-github-delivery')
        
        # Get payload
        payload_body = await request.body()
        
        # Verify signature
        if not verify_signature(payload_body, signature):
            logger.warning(f"Invalid signature for delivery {delivery_id}")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse payload
        try:
            payload = json.loads(payload_body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        logger.info(f"Received {event_type} event (delivery: {delivery_id}) for repo: {payload.get('repository', {}).get('full_name', 'unknown')}")
        
        # Process event in background
        background_tasks.add_task(process_github_event, event_type, payload)
        
        # Return immediate response to GitHub
        return JSONResponse(
            content={
                "status": "accepted",
                "event_type": event_type,
                "delivery_id": delivery_id,
                "message": "Event queued for processing"
            },
            status_code=202
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/webhook/manual")
async def manual_trigger(request: Request):
    """Manual trigger for testing"""
    payload = await request.json()
    event_type = payload.get('event_type', 'push')
    
    logger.info(f"Manual trigger for {event_type} event")
    
    result = await process_github_event(event_type, payload)
    return result

@app.get("/runs/{run_id}")
async def get_run_details(run_id: str):
    """Get details of a specific run"""
    try:
        conn = await ai_team.connect_db()
        
        # Get run details
        run = await conn.fetchrow('''
            SELECT * FROM agent_runs WHERE run_id = $1
        ''', run_id)
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Get associated actions
        actions = await conn.fetch('''
            SELECT * FROM agent_actions WHERE run_id = $1 ORDER BY created_at
        ''', run_id)
        
        await conn.close()
        
        return {
            "run": dict(run),
            "actions": [dict(action) for action in actions]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting run details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/property/search/buyer")
async def search_properties_for_buyer(background_tasks: BackgroundTasks):
    """Search properties based on buyer criteria from realconnect.online/buyer"""
    try:
        logger.info("Starting property search for buyer criteria")
        background_tasks.add_task(run_buyer_property_search)
        
        return JSONResponse(
            content={
                "status": "accepted",
                "message": "Buyer property search started",
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=202
        )
    except Exception as e:
        logger.error(f"Error starting buyer property search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/property/search/seller")
async def search_properties_for_seller(background_tasks: BackgroundTasks):
    """Search properties based on seller criteria from realconnect.online/seller"""
    try:
        logger.info("Starting property search for seller criteria")
        background_tasks.add_task(run_seller_property_search)
        
        return JSONResponse(
            content={
                "status": "accepted",
                "message": "Seller property search started",
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=202
        )
    except Exception as e:
        logger.error(f"Error starting seller property search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/property/search/status")
async def get_property_search_status():
    """Get status of property search operations"""
    try:
        # This would typically check a job queue or database
        # For now, return a simple status
        return {
            "status": "operational",
            "message": "Property search agent ready",
            "timestamp": datetime.utcnow().isoformat(),
            "available_sources": ["zillow", "realtor"]
        }
    except Exception as e:
        logger.error(f"Error getting property search status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_buyer_property_search():
    """Background task to run buyer property search"""
    try:
        result = await property_agent.run_buyer_search()
        logger.info(f"Buyer property search completed: {result.get('search_result', {}).get('total_found', 0)} properties found")
        # Here you could store results in database, send to webhook, etc.
        return result
    except Exception as e:
        logger.error(f"Error in buyer property search: {str(e)}")

async def run_seller_property_search():
    """Background task to run seller property search"""
    try:
        result = await property_agent.run_seller_search()
        logger.info(f"Seller property search completed: {result.get('search_result', {}).get('total_found', 0)} properties found")
        # Here you could store results in database, send to webhook, etc.
        return result
    except Exception as e:
        logger.error(f"Error in seller property search: {str(e)}")

if __name__ == "__main__":
    # Load environment variables
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting AI Development Team webhook server on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "webhook_server:app",
        host=host,
        port=port,
        reload=False,  # Set to True for development
        log_level="info"
    )