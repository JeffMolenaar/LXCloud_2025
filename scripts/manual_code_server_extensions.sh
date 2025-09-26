# Code-Server Extension Installation - Manual Method
# Copy these commands to your SSH session

echo "=== Manual Extension Installation for Code-Server ==="

# Method 1: Check what's available
echo "1. Check available extensions in code-server:"
code-server --list-extensions

# Method 2: Try installing with exact names from code-server marketplace
echo "2. Try alternative extension names:"

# These might work (try one by one):
code-server --install-extension Python
code-server --install-extension python
code-server --install-extension YAML
code-server --install-extension yaml
code-server --install-extension JSON
code-server --install-extension json

# Method 3: Check code-server version and capabilities
echo "3. Check code-server info:"
code-server --version
code-server --help

# Method 4: Manual extension directory setup
echo "4. Create extension directory manually:"
mkdir -p ~/.local/share/code-server/extensions
ls -la ~/.local/share/code-server/extensions/

# Method 2: Direct download approach
echo "Method 2: Direct download from marketplace"
echo

# Python Extension
echo "Installing Python extension via direct download..."
cd /tmp
wget -O python.vsix "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/ms-python/vsextensions/python/2023.20.0/vspackage"
if [ -f python.vsix ]; then
    code-server --install-extension python.vsix --extensions-dir $EXTENSIONS_DIR
    echo "   ✅ Python extension installed"
else
    echo "   ❌ Python extension download failed"
fi

# Cleanup
rm -f *.vsix

echo "3. Alternative: Install via VS Code marketplace mirror..."
echo
echo "# Use Open VSX Registry (code-server compatible)"
echo "code-server --install-extension ms-python.python --marketplace-url https://open-vsx.org/vscode/gallery"
echo

echo "4. Verify installed extensions..."
code-server --list-extensions --extensions-dir $EXTENSIONS_DIR

echo
echo "=== Manual Installation Complete ==="
echo "If extensions still don't work, use the VS Code web interface:"
echo "   1. Open http://YOUR_SERVER_IP:8081"
echo "   2. Go to Extensions tab (Ctrl+Shift+X)"
echo "   3. Search and install extensions directly in the web interface"