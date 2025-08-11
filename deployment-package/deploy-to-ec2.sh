#!/bin/bash

# MCP Property Search Agent - EC2 Deployment Script
# Run this script on your EC2 instance after copying files

echo "🚀 Deploying MCP Property Search Agent on EC2"
echo "=============================================="

# Update system packages
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python and required packages
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git curl

# Install Node.js (for potential frontend needs)
echo "📋 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p logs
mkdir -p uploads

# Set up environment variables
echo "⚙️ Setting up environment configuration..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# MCP Property Search Agent Configuration
PORT=8000
HOST=0.0.0.0

# Database (optional - comment out if not using)
# DATABASE_URL=postgresql://user:password@localhost:5432/mcp_agents

# API Keys (set these with your actual keys)
# ANTHROPIC_API_KEY=your_anthropic_key_here
# GITHUB_TOKEN=your_github_token_here

# Webhook Secret (optional)
# GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Real Estate APIs (optional)
# ZILLOW_API_KEY=your_zillow_key_here
# REALTOR_API_KEY=your_realtor_key_here
EOF
    echo "Created .env file. Please edit it with your API keys."
fi

# Set up systemd service
echo "🔧 Setting up systemd service..."
sudo tee /etc/systemd/system/mcp-agent.service > /dev/null << EOF
[Unit]
Description=MCP Property Search Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python webhook_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable mcp-agent
echo "Service created. Start with: sudo systemctl start mcp-agent"

# Set up nginx reverse proxy (optional)
if command -v nginx &> /dev/null; then
    echo "🌐 Configuring nginx reverse proxy..."
    sudo tee /etc/nginx/sites-available/mcp-agent > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/mcp-agent /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    echo "Nginx configured to proxy port 80 to 8000"
fi

# Set up firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 8000/tcp # MCP Agent
sudo ufw --force enable

# Create test script
cat > test-deployment.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing MCP Agent deployment..."

# Test health endpoint
echo "Testing health endpoint..."
curl -f http://localhost:8000/ || echo "❌ Health check failed"

# Test property search status
echo "Testing property search status..."
curl -f http://localhost:8000/property/search/status || echo "❌ Property search status failed"

echo "✅ Deployment test completed"
EOF
chmod +x test-deployment.sh

echo ""
echo "🎉 Deployment Setup Complete!"
echo "=============================="
echo ""
echo "📋 Next Steps:"
echo "1. Edit .env file with your API keys:"
echo "   nano .env"
echo ""
echo "2. Start the MCP agent service:"
echo "   sudo systemctl start mcp-agent"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status mcp-agent"
echo ""
echo "4. Test the deployment:"
echo "   ./test-deployment.sh"
echo ""
echo "5. View logs:"
echo "   sudo journalctl -u mcp-agent -f"
echo ""
echo "🌐 Your MCP agent will be available at:"
echo "   http://$(curl -s ifconfig.me):8000"
echo "   http://localhost:8000 (local)"
echo ""
echo "📊 API Endpoints:"
echo "   GET  / - Health check"
echo "   GET  /status - Service status"
echo "   POST /property/search/seller - Seller market analysis"
echo "   POST /property/search/buyer - Buyer property search"
echo "   GET  /property/search/status - Search status"
echo ""
echo "🔧 Useful Commands:"
echo "   sudo systemctl start mcp-agent    # Start service"
echo "   sudo systemctl stop mcp-agent     # Stop service"
echo "   sudo systemctl restart mcp-agent  # Restart service"
echo "   sudo journalctl -u mcp-agent -f   # View logs"
echo "   curl http://localhost:8000/       # Test health"