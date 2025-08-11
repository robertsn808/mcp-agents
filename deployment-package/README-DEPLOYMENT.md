# MCP Property Search Agent - EC2 Deployment Guide

## 🚀 Quick Deployment Instructions

### Prerequisites
- EC2 instance running Ubuntu 20.04+ with SSH access
- SSH key file (amazon.pem) with proper permissions
- Security group allowing inbound traffic on ports 22, 80, and 8000

### Step 1: Copy Files to EC2

From your local machine, run these commands:

```bash
# Navigate to the deployment package directory
cd /mnt/c/Users/rober/Documents/Work/mcp-agents-repo/deployment-package

# Copy all files to EC2 instance
scp -i ~/amazon.pem -r * ubuntu@ec2-3-93-198-58.compute-1.amazonaws.com:~/mcp-agent/

# Alternative: Create tar and copy
tar -czf mcp-deployment.tar.gz *
scp -i ~/amazon.pem mcp-deployment.tar.gz ubuntu@ec2-3-93-198-58.compute-1.amazonaws.com:~/
```

### Step 2: Connect to EC2 and Deploy

```bash
# SSH into your EC2 instance
ssh -i ~/amazon.pem ubuntu@ec2-3-93-198-58.compute-1.amazonaws.com

# If you used tar method, extract files
tar -xzf mcp-deployment.tar.gz
mkdir -p mcp-agent
mv * mcp-agent/ 2>/dev/null || true
cd mcp-agent

# Run the deployment script
chmod +x deploy-to-ec2.sh
./deploy-to-ec2.sh
```

### Step 3: Configure Environment

```bash
# Edit environment file with your API keys
nano .env

# Add your actual API keys:
# ANTHROPIC_API_KEY=your_anthropic_key_here
# GITHUB_TOKEN=your_github_token_here
```

### Step 4: Start Services

```bash
# Start the MCP agent service
sudo systemctl start mcp-agent

# Enable auto-start on boot
sudo systemctl enable mcp-agent

# Check service status
sudo systemctl status mcp-agent
```

### Step 5: Test Deployment

```bash
# Test the deployment
./test-deployment.sh

# Or manually test endpoints
curl http://localhost:8000/
curl http://localhost:8000/property/search/status
```

## 🌐 Access Your MCP Agent

Once deployed, your MCP agent will be available at:

- **Public URL**: `http://ec2-3-93-198-58.compute-1.amazonaws.com:8000`
- **Local URL**: `http://localhost:8000` (from EC2 instance)

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/status` | GET | Service status and recent activity |
| `/property/search/seller` | POST | Trigger seller market analysis |
| `/property/search/buyer` | POST | Trigger buyer property search |
| `/property/search/status` | GET | Property search agent status |
| `/webhook/github` | POST | GitHub webhook receiver |

## 🔧 Managing the Service

### Service Commands
```bash
# Start service
sudo systemctl start mcp-agent

# Stop service
sudo systemctl stop mcp-agent

# Restart service
sudo systemctl restart mcp-agent

# View service status
sudo systemctl status mcp-agent

# View live logs
sudo journalctl -u mcp-agent -f

# View recent logs
sudo journalctl -u mcp-agent --since "1 hour ago"
```

### Configuration Updates
```bash
# After modifying .env or Python files
sudo systemctl restart mcp-agent

# Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart mcp-agent
```

## 🔒 Security Configuration

### Firewall Settings
The deployment script configures UFW firewall with these rules:
- Port 22: SSH access
- Port 80: HTTP (nginx proxy)
- Port 8000: Direct MCP agent access

### SSL/HTTPS Setup (Optional)
```bash
# Install certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

## 📈 Monitoring and Logs

### Log Locations
- **Service logs**: `sudo journalctl -u mcp-agent`
- **Application logs**: `~/mcp-agent/logs/` (if configured)
- **Nginx logs**: `/var/log/nginx/`

### Health Monitoring
```bash
# Create a simple health check script
cat > ~/health-check.sh << 'EOF'
#!/bin/bash
if curl -f -s http://localhost:8000/ > /dev/null; then
    echo "$(date): MCP Agent is healthy"
else
    echo "$(date): MCP Agent is down - restarting..."
    sudo systemctl restart mcp-agent
fi
EOF

chmod +x ~/health-check.sh

# Add to crontab for regular health checks
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/health-check.sh >> /home/ubuntu/health.log") | crontab -
```

## 🔄 Updates and Maintenance

### Updating the MCP Agent
```bash
# Pull latest changes from GitHub
cd ~/mcp-agent
git pull origin trunk  # or download new files

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart mcp-agent
```

### Backup Configuration
```bash
# Backup important configuration
tar -czf mcp-backup-$(date +%Y%m%d).tar.gz .env logs/ uploads/

# Store backup safely
aws s3 cp mcp-backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u mcp-agent -n 50

# Check if port is available
sudo netstat -tlnp | grep 8000

# Verify Python virtual environment
source venv/bin/activate
python webhook_server.py  # Test manually
```

#### 2. API Key Issues
```bash
# Verify environment variables are loaded
sudo systemctl show mcp-agent --property=Environment

# Test API keys manually
source venv/bin/activate
python -c "import os; print(f'Anthropic: {bool(os.getenv(\"ANTHROPIC_API_KEY\"))}')"
```

#### 3. Network Connectivity
```bash
# Test external connectivity
curl -I https://api.anthropic.com
curl -I https://www.zillow.com

# Check security group settings in AWS console
# Ensure ports 80, 8000, and 22 are open
```

#### 4. Memory/Performance Issues
```bash
# Check system resources
htop
free -h
df -h

# Adjust service if needed
sudo systemctl edit mcp-agent
# Add:
# [Service]
# MemoryLimit=1G
# CPUQuota=50%
```

### Getting Help

1. **Check logs first**: `sudo journalctl -u mcp-agent -f`
2. **Test endpoints manually**: `curl -v http://localhost:8000/`
3. **Verify configuration**: Check `.env` file has correct API keys
4. **Resource monitoring**: Use `htop` to check CPU/memory usage
5. **Network issues**: Verify security group and firewall settings

## 📞 Support

For issues with the MCP agent:
1. Check the deployment logs
2. Verify all environment variables are set correctly
3. Test network connectivity to external APIs
4. Review AWS security group settings
5. Monitor system resources and logs

## 🔗 Integration with Seller App

Once your MCP agent is running on EC2, update your seller application's configuration:

```properties
# In your seller app's application.properties
mcp.agent.base-url=http://ec2-3-93-198-58.compute-1.amazonaws.com:8000
```

Then follow the seller integration guide to complete the setup.