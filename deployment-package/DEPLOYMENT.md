# MCP Agents Deployment Guide

## 🚀 Deploy to Render

### Method 1: Automatic (Recommended)

1. Fork this repository to your GitHub account
2. Connect your GitHub account to Render
3. Create a new Web Service from GitHub
4. Select this repository
5. Render will automatically use the `render.yaml` blueprint

### Method 2: Manual Setup

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure build settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python webhook_server.py`

### Environment Variables

Set these in your Render dashboard:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Your Anthropic API key |
| `GITHUB_TOKEN` | ✅ | GitHub Personal Access Token |
| `GITHUB_WEBHOOK_SECRET` | ⭕ | Optional webhook verification |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `PORT` | ⭕ | Port (defaults to 8000) |
| `HOST` | ⭕ | Host (defaults to 0.0.0.0) |

### Database Setup

1. Create a PostgreSQL database on Render
2. Connect to your database and run the `init.sql` script
3. Add the database URL to your environment variables

## 🐳 Deploy with Docker

### Local Development

```bash
# Build the image
docker build -t mcp-agents .

# Run with environment file
docker run --env-file .env -p 8000:8000 mcp-agents
```

### Production Deployment

```bash
# Build and push to registry
docker build -t your-registry/mcp-agents .
docker push your-registry/mcp-agents

# Deploy to your preferred platform
# (AWS ECS, Google Cloud Run, etc.)
```

## ☁️ Other Cloud Platforms

### Railway

1. Connect your GitHub repository to Railway
2. Set environment variables
3. Railway will auto-deploy using the Dockerfile

### Heroku

```bash
# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set ANTHROPIC_API_KEY=your_key
heroku config:set GITHUB_TOKEN=your_token

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Deploy
git push heroku main
```

### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/your-project/mcp-agents

# Deploy to Cloud Run
gcloud run deploy mcp-agents \
  --image gcr.io/your-project/mcp-agents \
  --platform managed \
  --region us-central1 \
  --set-env-vars ANTHROPIC_API_KEY=your_key
```

## 📡 GitHub Webhook Setup

After deployment, configure your GitHub repositories:

1. Go to **Repository Settings → Webhooks**
2. Click **Add webhook**
3. Set **Payload URL** to: `https://your-deployment-url.com/webhook/github`
4. Set **Content type** to: `application/json`
5. Select events: **Push** and **Pull requests**
6. Add your webhook secret if configured
7. Click **Add webhook**

## 🧪 Testing Your Deployment

```bash
# Health check
curl https://your-deployment-url.com/

# Manual test
curl -X POST https://your-deployment-url.com/webhook/manual \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "push",
    "repository": {"full_name": "youruser/yourrepo"},
    "commits": [{"modified": ["src/app.py"], "message": "Test"}]
  }'

# Check status
curl https://your-deployment-url.com/status
```

## 📊 Monitoring

- **Logs**: Check your platform's log viewer
- **Database**: Monitor agent runs and actions tables
- **Health**: Use `/` endpoint for health checks
- **Status**: Use `/status` endpoint for recent activity

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify `DATABASE_URL` is correct
   - Ensure database allows external connections
   - Check if `init.sql` was run

2. **GitHub Webhook 401 Error**
   - Verify webhook secret matches `GITHUB_WEBHOOK_SECRET`
   - Check GitHub token permissions

3. **Anthropic API Errors**
   - Verify `ANTHROPIC_API_KEY` is valid
   - Check API rate limits

### Getting Help

- Check application logs for detailed error messages
- Verify all environment variables are set
- Test with manual webhook endpoint first
- Ensure database schema is properly initialized