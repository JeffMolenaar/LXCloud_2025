#!/bin/bash
# Verify Remote Development Setup
# Check if everything is ready for live Copilot assistance

echo "=== Verifying Remote Development Setup ==="

SERVER_IP=$(hostname -I | awk '{print $1}')
CODE_SERVER_PORT="8081"
SERVICE_USER="lxcloud"
WORKSPACE="/home/$SERVICE_USER/LXCloud"

echo "1. System Information:"
echo "   Server IP: $SERVER_IP"
echo "   Code-server Port: $CODE_SERVER_PORT"
echo "   Service User: $SERVICE_USER"
echo "   Workspace: $WORKSPACE"
echo

echo "2. Service Status Check:"
services=("code-server@lxcloud" "lxcloud" "nginx" "mosquitto")
for service in "${services[@]}"; do
    if sudo systemctl is-active --quiet "$service"; then
        echo "   ✅ $service: RUNNING"
    else
        echo "   ❌ $service: NOT RUNNING"
    fi
done
echo

echo "3. Network Accessibility:"
echo "   Code-server URL: http://$SERVER_IP:$CODE_SERVER_PORT"
if curl -s --connect-timeout 5 "http://localhost:$CODE_SERVER_PORT" >/dev/null; then
    echo "   ✅ Code-server is accessible"
else
    echo "   ⚠️  Code-server may not be accessible (check firewall)"
fi
echo

echo "4. Workspace Structure:"
if [ -d "$WORKSPACE" ]; then
    echo "   ✅ Workspace directory exists"
    echo "   Files in workspace:"
    ls -la "$WORKSPACE" | head -10
    
    if [ -d "$WORKSPACE/.vscode" ]; then
        echo "   ✅ VS Code configuration exists"
        ls -la "$WORKSPACE/.vscode/"
    else
        echo "   ⚠️  VS Code configuration missing"
    fi
else
    echo "   ❌ Workspace directory not found"
fi
echo

echo "5. Development Tools:"
if [ -f "$WORKSPACE/dev_status.py" ]; then
    echo "   ✅ Development status tool available"
else
    echo "   ⚠️  Development status tool missing"
fi

if [ -f "$WORKSPACE/quick_test.py" ]; then
    echo "   ✅ Quick test tool available"
else
    echo "   ⚠️  Quick test tool missing"
fi
echo

echo "6. Python Environment:"
cd "$WORKSPACE" || exit 1
if [ -f "venv/bin/activate" ]; then
    echo "   ✅ Virtual environment exists"
    source venv/bin/activate
    python3 --version
    echo "   Flask version: $(python3 -c 'import flask; print(flask.__version__)' 2>/dev/null || echo 'Not installed')"
    deactivate
else
    echo "   ⚠️  Virtual environment not found"
    echo "   System Python: $(python3 --version)"
fi
echo

echo "7. Database Connectivity:"
cd "$WORKSPACE"
if python3 -c "from app import create_app; app = create_app(); print('Database connection: OK')" 2>/dev/null; then
    echo "   ✅ Database connection working"
else
    echo "   ⚠️  Database connection issues"
fi
echo

echo "8. File Permissions:"
WORKSPACE_OWNER=$(stat -c '%U:%G' "$WORKSPACE")
echo "   Workspace owner: $WORKSPACE_OWNER"
if [ "$WORKSPACE_OWNER" = "$SERVICE_USER:$SERVICE_USER" ]; then
    echo "   ✅ Correct file ownership"
else
    echo "   ⚠️  File ownership may need fixing"
fi
echo

echo "9. Firewall Status:"
if command -v ufw >/dev/null 2>&1; then
    ufw_status=$(sudo ufw status | grep "$CODE_SERVER_PORT")
    if [ -n "$ufw_status" ]; then
        echo "   ✅ Firewall allows code-server port"
        echo "   Rule: $ufw_status"
    else
        echo "   ⚠️  Firewall rule for code-server port not found"
    fi
else
    echo "   ℹ️  UFW not installed (firewall status unknown)"
fi
echo

echo "10. Remote Access Instructions:"
echo "   🌐 Open browser: http://$SERVER_IP:$CODE_SERVER_PORT"
echo "   🔑 Password: LXCloud"
echo "   📁 Open workspace: $WORKSPACE"
echo "   🔧 Open terminal in VS Code"
echo "   🧪 Run: ./dev_status.py"
echo "   ⚡ Run: ./quick_test.py"
echo

echo "=== Verification Complete ==="
echo
echo "🚀 If all items show ✅, remote development is ready!"
echo "⚠️  If items show ⚠️ or ❌, run setup script again"
echo
echo "For live assistance, the remote environment provides:"
echo "   - Real-time code editing"
echo "   - Integrated terminal access"
echo "   - Python debugging capabilities"
echo "   - Service management"
echo "   - Database operations"
echo "   - Log file access"
echo "   - Git operations"
echo
echo "The assistant can now help with live debugging and testing!"