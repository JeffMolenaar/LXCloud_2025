#!/bin/bash
# Setup Code-Server with Extensions on Ubuntu
# Run this script on your Ubuntu server via SSH

set -e

echo "=== LXCloud Code-Server Extension Setup ==="
echo

# Configuration
CODE_SERVER_PORT=8081
INSTALL_DIR="/home/lxcloud"
SERVICE_USER="lxcloud"

echo "1. Stopping code-server if running..."
sudo systemctl stop code-server@$SERVICE_USER || echo "   Service not running"

echo "2. Setting up code-server configuration..."
mkdir -p $INSTALL_DIR/.config/code-server
cat > $INSTALL_DIR/.config/code-server/config.yaml << 'EOF'
bind-addr: 0.0.0.0:8081
auth: password
password: LXCloud
cert: false
EOF

chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/.config/code-server

echo "3. Installing extensions via curl (Open VSX Registry)..."

# Create extensions directory
mkdir -p $INSTALL_DIR/.local/share/code-server/extensions

# Python extension
echo "   Installing Python extension..."
curl -L "https://open-vsx.org/api/ms-python/python/linux-x64/latest/file" -o python-extension.vsix
code-server --install-extension python-extension.vsix || echo "   Python extension install failed"
rm -f python-extension.vsix

# GitHub Copilot (if available)
echo "   Checking for GitHub Copilot..."
curl -L "https://open-vsx.org/api/github/copilot/linux-x64/latest/file" -o copilot.vsix 2>/dev/null || echo "   Copilot not available in Open VSX"
if [ -f copilot.vsix ]; then
    code-server --install-extension copilot.vsix
    rm -f copilot.vsix
fi

# Alternative extensions for development
echo "   Installing development extensions..."

# Pylance (Python Language Server)
curl -L "https://open-vsx.org/api/ms-python/pylance/linux-x64/latest/file" -o pylance.vsix 2>/dev/null || echo "   Pylance not available"
if [ -f pylance.vsix ]; then
    code-server --install-extension pylance.vsix
    rm -f pylance.vsix
fi

# Git extension
curl -L "https://open-vsx.org/api/vscode/git/latest/file" -o git.vsix 2>/dev/null || echo "   Git extension not available"
if [ -f git.vsix ]; then
    code-server --install-extension git.vsix
    rm -f git.vsix
fi

# HTML/CSS/JS support
curl -L "https://open-vsx.org/api/vscode/html-language-features/latest/file" -o html.vsix 2>/dev/null || echo "   HTML extension not available"
if [ -f html.vsix ]; then
    code-server --install-extension html.vsix
    rm -f html.vsix
fi

echo "4. Setting up systemd service..."
sudo tee /etc/systemd/system/code-server@.service > /dev/null << 'EOF'
[Unit]
Description=code-server
After=network.target

[Service]
Type=exec
ExecStart=/usr/bin/code-server --config /home/%i/.config/code-server/config.yaml /home/lxcloud/LXCloud
Restart=always
RestartSec=10
User=%i
Group=%i
Environment=PATH=/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

echo "5. Starting code-server service..."
sudo systemctl daemon-reload
sudo systemctl enable code-server@$SERVICE_USER
sudo systemctl start code-server@$SERVICE_USER

echo "6. Opening firewall port..."
sudo ufw allow $CODE_SERVER_PORT/tcp || echo "   UFW not installed or configured"

echo "7. Verifying installation..."
sleep 5
if sudo systemctl is-active --quiet code-server@$SERVICE_USER; then
    echo "   ✅ code-server is running"
else
    echo "   ❌ code-server failed to start"
    sudo systemctl status code-server@$SERVICE_USER
fi

echo
echo "=== Code-Server Setup Complete ==="
echo
echo "Access your code-server at:"
echo "   http://YOUR_SERVER_IP:8081"
echo "   Password: LXCloud"
echo
echo "Workspace location: /home/lxcloud/LXCloud"
echo
echo "To check status: sudo systemctl status code-server@lxcloud"
echo "To view logs: sudo journalctl -u code-server@lxcloud -f"
echo