#!/bin/bash

# MCP Property Search Agent - Copy to EC2 Script
# Run this from your local machine

EC2_HOST="ubuntu@ec2-3-93-198-58.compute-1.amazonaws.com"
SSH_KEY="/home/i0vvny0u/amazon.pem"

echo "🚀 Copying MCP Property Search Agent to EC2"
echo "============================================"

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found at $SSH_KEY"
    echo "Please update the SSH_KEY variable in this script"
    exit 1
fi

# Create remote directory
echo "📁 Creating remote directory..."
ssh -i "$SSH_KEY" "$EC2_HOST" "mkdir -p ~/mcp-agent"

# Copy core Python files
echo "🐍 Copying core Python files..."
scp -i "$SSH_KEY" deployment-package/property_search_agent.py "$EC2_HOST":~/mcp-agent/
scp -i "$SSH_KEY" deployment-package/webhook_server.py "$EC2_HOST":~/mcp-agent/
scp -i "$SSH_KEY" deployment-package/ai_dev_team.py "$EC2_HOST":~/mcp-agent/
scp -i "$SSH_KEY" deployment-package/requirements.txt "$EC2_HOST":~/mcp-agent/

# Copy configuration and setup files
echo "⚙️ Copying configuration files..."
scp -i "$SSH_KEY" deployment-package/init.sql "$EC2_HOST":~/mcp-agent/
scp -i "$SSH_KEY" deployment-package/render.yaml "$EC2_HOST":~/mcp-agent/
scp -i "$SSH_KEY" deployment-package/setup.sh "$EC2_HOST":~/mcp-agent/
scp -i "$SSH_KEY" deployment-package/deploy-to-ec2.sh "$EC2_HOST":~/mcp-agent/

# Copy documentation
echo "📚 Copying documentation..."
scp -i "$SSH_KEY" deployment-package/README.md "$EC2_HOST":~/mcp-agent/
scp -i "$SSH_KEY" deployment-package/DEPLOYMENT.md "$EC2_HOST":~/mcp-agent/
scp -i "$SSH_KEY" deployment-package/README-DEPLOYMENT.md "$EC2_HOST":~/mcp-agent/

# Copy seller integration package
echo "🏢 Copying seller integration files..."
scp -i "$SSH_KEY" -r deployment-package/seller-integration "$EC2_HOST":~/mcp-agent/

# Make scripts executable
echo "🔧 Setting permissions..."
ssh -i "$SSH_KEY" "$EC2_HOST" "chmod +x ~/mcp-agent/*.sh"

echo ""
echo "✅ Copy completed successfully!"
echo "================================"
echo ""
echo "📋 Next Steps:"
echo "1. SSH into your EC2 instance:"
echo "   ssh -i $SSH_KEY $EC2_HOST"
echo ""
echo "2. Navigate to the MCP agent directory:"
echo "   cd ~/mcp-agent"
echo ""
echo "3. Run the deployment script:"
echo "   ./deploy-to-ec2.sh"
echo ""
echo "4. Configure your API keys:"
echo "   nano .env"
echo ""
echo "5. Start the service:"
echo "   sudo systemctl start mcp-agent"
echo ""
echo "🌐 Your MCP agent will be available at:"
echo "   http://ec2-3-93-198-58.compute-1.amazonaws.com:8000"
echo ""
echo "🔧 To check deployment status:"
echo "   ssh -i $SSH_KEY $EC2_HOST 'sudo systemctl status mcp-agent'"
