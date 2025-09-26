#!/bin/bash
# Working Code-Server Extension Setup
# This script uses methods that actually work with code-server

echo "=== Code-Server Extension Fix (Working Methods) ==="
echo

# Stop code-server first
echo "1. Stopping code-server..."
sudo systemctl stop code-server@lxcloud

echo "2. Installing extensions via web interface setup..."

# Create a simple extension list file
cat > /tmp/extensions_to_install.txt << 'EOF'
# Extensions available in code-server registry:
# Use the web interface to install these

1. Python support:
   - Search for "Python" in web interface
   - Install "Python" extension if available
   - Or install "Pylance" for Python language server

2. YAML support:
   - Search for "YAML" in web interface
   - Install "YAML" extension

3. JSON support:
   - Usually built-in, no installation needed

4. Git support:
   - Usually built-in with code-server

5. HTML/CSS/JS:
   - Usually built-in with code-server

Manual installation via web interface is recommended.
EOF

echo "3. Starting code-server with proper workspace..."
sudo systemctl start code-server@lxcloud

echo "4. Waiting for service to start..."
sleep 5

echo "5. Checking if service is running..."
if sudo systemctl is-active --quiet code-server@lxcloud; then
    echo "   ✅ Code-server is running on port 8081"
else
    echo "   ❌ Code-server failed to start"
    echo "   Checking logs:"
    sudo journalctl -u code-server@lxcloud --no-pager -l
fi

echo
echo "=== Extension Installation Instructions ==="
echo
echo "Since CLI extension installation doesn't work, use the web interface:"
echo
echo "1. Open browser: http://$(hostname -I | awk '{print $1}'):8081"
echo "2. Enter password: LXCloud"
echo "3. Click Extensions icon (📦) on left sidebar"
echo "4. Search and install:"
echo "   - Python (for .py files)"
echo "   - YAML (for .yml/.yaml files)"  
echo "   - Any other extensions you need"
echo
echo "Alternative: Check what extensions are already available:"
code-server --list-extensions || echo "No extensions currently installed"

echo
echo "=== Troubleshooting ==="
echo "If code-server won't start:"
echo "sudo journalctl -u code-server@lxcloud -f"
echo
echo "To restart code-server:"
echo "sudo systemctl restart code-server@lxcloud"
echo
echo "Current status:"
sudo systemctl status code-server@lxcloud --no-pager