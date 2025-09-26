#!/bin/bash
# Setup Remote Development Access for Copilot
# This enables live debugging and testing capabilities

echo "=== Setting up Copilot Remote Development Access ==="

SERVER_IP=$(hostname -I | awk '{print $1}')
SERVICE_USER="lxcloud"
CODE_SERVER_PORT="8081"

echo "1. Verifying code-server is running..."
if sudo systemctl is-active --quiet code-server@$SERVICE_USER; then
    echo "   ✅ Code-server is running"
else
    echo "   ❌ Code-server not running, starting..."
    sudo systemctl start code-server@$SERVICE_USER
    sleep 3
fi

echo "2. Setting up remote development workspace..."
WORKSPACE_DIR="/home/$SERVICE_USER/LXCloud"
cd "$WORKSPACE_DIR" || exit 1

# Create .vscode workspace settings for optimal remote development
mkdir -p .vscode

echo "3. Creating VS Code workspace configuration..."
cat > .vscode/settings.json << 'EOF'
{
    "python.pythonPath": "./venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000,
    "terminal.integrated.defaultProfile.linux": "bash",
    "terminal.integrated.cwd": "${workspaceFolder}",
    "git.enableSmartCommit": true,
    "git.confirmSync": false,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "."
    ]
}
EOF

echo "4. Creating launch configuration for debugging..."
cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask App",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/run.py",
            "env": {
                "FLASK_ENV": "development",
                "FLASK_DEBUG": "1"
            },
            "args": [],
            "jinja": true,
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        }
    ]
}
EOF

echo "5. Creating tasks for common operations..."
cat > .vscode/tasks.json << 'EOF'
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start LXCloud Server",
            "type": "shell",
            "command": "python3",
            "args": ["run.py"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "problemMatcher": []
        },
        {
            "label": "Install Requirements",
            "type": "shell",
            "command": "pip",
            "args": ["install", "-r", "requirements.txt"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "python",
            "args": ["-m", "pytest", "-v"],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Check Services",
            "type": "shell",
            "command": "sudo",
            "args": ["systemctl", "status", "lxcloud", "nginx", "mosquitto"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        }
    ]
}
EOF

echo "6. Setting up live development helpers..."

# Create a development status script
cat > dev_status.py << 'EOF'
#!/usr/bin/env python3
"""
Live development status checker for LXCloud
Run this to check system status for remote debugging
"""
import subprocess
import json
from datetime import datetime

def check_system_status():
    status = {
        'timestamp': datetime.now().isoformat(),
        'services': {},
        'python_env': {},
        'database': {},
        'network': {}
    }
    
    # Check services
    services = ['lxcloud', 'nginx', 'mosquitto', 'code-server@lxcloud']
    for service in services:
        try:
            result = subprocess.run(['sudo', 'systemctl', 'is-active', service], 
                                  capture_output=True, text=True)
            status['services'][service] = result.stdout.strip()
        except:
            status['services'][service] = 'unknown'
    
    # Check Python environment
    try:
        import flask
        status['python_env']['flask_version'] = flask.__version__
    except:
        status['python_env']['flask_version'] = 'not_installed'
    
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        status['python_env']['python_version'] = result.stdout.strip()
    except:
        status['python_env']['python_version'] = 'unknown'
    
    # Check database connectivity
    try:
        from app import create_app
        app = create_app()
        status['database']['connection'] = 'ok'
    except Exception as e:
        status['database']['connection'] = f'error: {str(e)}'
    
    return status

if __name__ == "__main__":
    status = check_system_status()
    print(json.dumps(status, indent=2))
EOF

chmod +x dev_status.py

echo "7. Creating live debugging helpers..."

# Create a quick test runner
cat > quick_test.py << 'EOF'
#!/usr/bin/env python3
"""
Quick test runner for live debugging
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports"""
    try:
        from app import create_app
        print("✅ Flask app import: OK")
        
        from app.models import User, Controller
        print("✅ Models import: OK")
        
        from app.routes import auth_bp, dashboard_bp, admin_bp
        print("✅ Routes import: OK")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test Flask app creation"""
    try:
        from app import create_app
        app = create_app()
        print("✅ App creation: OK")
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

if __name__ == "__main__":
    print("=== Live Debug Test ===")
    test_imports()
    test_app_creation()
    print("=== Test Complete ===")
EOF

chmod +x quick_test.py

echo "8. Setting up file permissions for remote access..."
sudo chown -R $SERVICE_USER:$SERVICE_USER "$WORKSPACE_DIR"
sudo chmod -R 755 "$WORKSPACE_DIR"

echo "9. Creating remote access information file..."
cat > remote_access_info.txt << EOF
=== LXCloud Remote Development Access ===

Code-Server Access:
URL: http://$SERVER_IP:$CODE_SERVER_PORT
Password: LXCloud
Workspace: $WORKSPACE_DIR

Development Tools Available:
- Integrated Terminal
- Python Debugger (F5 to start)
- Git Integration
- File Explorer
- Extensions: Python, YAML, etc.

Quick Commands in Terminal:
./dev_status.py        - Check system status
./quick_test.py        - Run quick tests
python3 run.py         - Start Flask dev server
sudo systemctl status lxcloud - Check service

Remote Development Features:
✅ Live file editing
✅ Integrated debugging
✅ Terminal access
✅ Git operations
✅ Service management
✅ Real-time testing

For Copilot Access:
The assistant can now help with live debugging by:
1. Analyzing real-time system status
2. Making direct code changes
3. Running tests immediately
4. Checking service logs
5. Database operations
6. Configuration updates

Next Steps:
1. Open http://$SERVER_IP:$CODE_SERVER_PORT in browser
2. Enter workspace: $WORKSPACE_DIR  
3. Open integrated terminal
4. Run: ./dev_status.py to verify setup
5. Start live development!

EOF

echo "10. Final verification..."
echo "   Code-server status:"
sudo systemctl status code-server@$SERVICE_USER --no-pager -l | head -5

echo "   Workspace permissions:"
ls -la "$WORKSPACE_DIR/.vscode/"

echo
echo "=== Remote Development Setup Complete! ==="
echo
echo "🚀 Access your live development environment:"
echo "   URL: http://$SERVER_IP:$CODE_SERVER_PORT"
echo "   Password: LXCloud"
echo "   Workspace: $WORKSPACE_DIR"
echo
echo "🔧 Development tools ready:"
echo "   - VS Code with extensions"
echo "   - Integrated terminal"  
echo "   - Python debugger"
echo "   - Git integration"
echo "   - Live file editing"
echo
echo "📊 Status check: Run './dev_status.py' in terminal"
echo "🧪 Quick test: Run './quick_test.py' in terminal"
echo
echo "The assistant can now provide live debugging assistance!"
