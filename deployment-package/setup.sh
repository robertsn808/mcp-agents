#!/bin/bash

# MCP Agents Repository Setup Script

set -e

echo "🤖 Setting up MCP AI Development Team Repository..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Initialize git repository if not already initialized
if [ ! -d .git ]; then
    echo "📂 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: MCP AI Development Team

✨ Features:
- Multi-role AI agents (Backend, Frontend, QA, DevOps, Security)
- Smart role selection based on file changes
- GitHub webhook integration
- PostgreSQL logging and audit trail
- Cloud-ready deployment (Render, Docker, etc.)

🚀 Ready for deployment!"
else
    echo "📂 Git repository already initialized"
fi

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual API keys!"
else
    echo "🔧 .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Create GitHub repository: gh repo create mcp-agents --public --source=."
echo "3. Push to GitHub: git remote add origin https://github.com/YOURUSERNAME/mcp-agents.git && git push -u origin main"
echo "4. Deploy to Render or your preferred platform"
echo "5. Configure GitHub webhooks with your deployment URL"
echo ""
echo "📖 See DEPLOYMENT.md for detailed deployment instructions"
echo "🔗 Repository will be available at: https://github.com/YOURUSERNAME/mcp-agents"