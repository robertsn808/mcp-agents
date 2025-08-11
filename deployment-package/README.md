# MCP AI Development Team

A sophisticated AI development team built with Model Context Protocol (MCP) for GitHub automation. Deploy anywhere with Docker or cloud platforms like Render.

## 🚀 Features

- **Multi-Role AI Agents**: 5 specialized roles (Backend, Frontend, QA, DevOps, Security)
- **Smart Role Selection**: Automatically chooses appropriate expertise based on file changes
- **GitHub Integration**: Webhooks for push events, PR analysis, and automated improvements
- **PostgreSQL Logging**: Complete audit trail of all AI actions
- **Cloud-Ready**: Deploy to Render, Railway, or any cloud platform

## 🏗️ Architecture

```
GitHub Events → Webhook Server → AI Agent → GitHub Actions
                     ↓
              PostgreSQL Database Logging
```

## 🤖 AI Roles

- **Backend Engineer**: Code review, performance, security analysis
- **Frontend Engineer**: UI/UX, accessibility, component architecture
- **QA Engineer**: Test plans, edge cases, quality assurance
- **DevOps Engineer**: Infrastructure, CI/CD, deployment optimization
- **Security Engineer**: Vulnerability analysis, secure coding practices

## 🔧 Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_key_here
GITHUB_TOKEN=your_github_token_here

# Optional
GITHUB_WEBHOOK_SECRET=optional_webhook_secret
DATABASE_URL=postgresql://user:pass@host:port/db
PORT=8000
HOST=0.0.0.0
```

## 🚀 Deployment

### Render (Recommended)

1. Fork this repository
2. Connect to Render
3. Set environment variables
4. Deploy as Web Service

### Docker

```bash
# Build and run locally
docker build -t mcp-agents .
docker run -p 8000:8000 --env-file .env mcp-agents
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your_key"
export GITHUB_TOKEN="your_token"

# Run the server
python webhook_server.py
```

## 📡 API Endpoints

- **GET /** - Health check
- **POST /webhook/github** - GitHub webhook receiver
- **GET /status** - Service status and recent activity
- **POST /webhook/manual** - Manual testing endpoint
- **GET /runs/{run_id}** - Detailed run information

## 🔧 GitHub Webhook Setup

1. Go to your repository **Settings → Webhooks**
2. Add webhook with:
   - **URL**: `https://your-deployment-url.com/webhook/github`
   - **Content type**: `application/json`
   - **Events**: Push, Pull requests
   - **Secret**: Your webhook secret (optional)

## 🗄️ Database Schema

The system requires PostgreSQL with these tables:
- `agent_runs` - Track AI executions
- `agent_actions` - Log GitHub actions
- `agent_memory` - Store context and preferences

See `init.sql` for complete schema.

## 🧪 Testing

```bash
# Health check
curl https://your-deployment-url.com/

# Manual test
curl -X POST https://your-deployment-url.com/webhook/manual \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "push",
    "repository": {"full_name": "youruser/yourrepo"},
    "commits": [{"modified": ["src/app.py"], "message": "Fix bug"}]
  }'
```

## 📊 Monitoring

View recent activity and stats:
```bash
curl https://your-deployment-url.com/status
```

## 🔮 Future Enhancements

- Real MCP integration with official GitHub MCP server
- Vector memory for code context and learning
- Multi-repository analysis
- Slack/Discord notifications
- Human approval workflows

## 📝 License

MIT License - see LICENSE file for details