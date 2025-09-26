#!/bin/bash
# Quick Fix for Code-Server Extensions
# Simplified approach that actually works

echo "=== Quick Code-Server Extension Fix ==="

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "Code-server is running but CLI extensions don't work."
echo "This is normal - code-server has limited CLI extension support."
echo
echo "✅ WORKING SOLUTION:"
echo
echo "1. Open your browser"
echo "2. Go to: http://$SERVER_IP:8081"
echo "3. Enter password: LXCloud"
echo "4. Click Extensions icon (四square grid) in left sidebar"
echo "5. Search and install:"
echo "   - Python"
echo "   - YAML Language Support" 
echo "   - Any other extensions you need"
echo
echo "Most extensions install fine via the web interface!"
echo
echo "Current code-server status:"
sudo systemctl status code-server@lxcloud --no-pager -l

echo
echo "If you need to restart code-server:"
echo "sudo systemctl restart code-server@lxcloud"
echo
echo "To check logs:"
echo "sudo journalctl -u code-server@lxcloud -f"

# Check if extensions directory exists
EXTENSIONS_DIR="/home/lxcloud/.local/share/code-server/extensions"
if [ -d "$EXTENSIONS_DIR" ]; then
    echo
    echo "Extensions directory exists:"
    ls -la "$EXTENSIONS_DIR" 2>/dev/null || echo "Directory empty"
else
    echo
    echo "Creating extensions directory:"
    mkdir -p "$EXTENSIONS_DIR"
    chown lxcloud:lxcloud "$EXTENSIONS_DIR"
    echo "Directory created: $EXTENSIONS_DIR"
fi

echo
echo "=== Next Steps ==="
echo "1. Access web interface: http://$SERVER_IP:8081"
echo "2. Install extensions via web UI"  
echo "3. Open LXCloud project: /home/lxcloud/LXCloud"
echo "4. Start developing with full IDE features!"
