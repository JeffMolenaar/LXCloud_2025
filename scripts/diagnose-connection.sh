#!/bin/bash

# LXCloud Connection Diagnostics Script
# Helps diagnose login and connection issues

echo "🔍 LXCloud Connection Diagnostics"
echo "=================================="
echo ""

# Check if server is running
echo "1. Checking if LXCloud server is running..."
if curl -s http://localhost:3000/api/health >/dev/null 2>&1; then
    echo "✅ Server is running on port 3000"
    
    # Get server status
    SERVER_STATUS=$(curl -s http://localhost:3000/api/health)
    echo "   Server status: $SERVER_STATUS"
else
    echo "❌ Server is not responding on port 3000"
    echo "   Try starting with: npm start or ./scripts/start-lxcloud.sh"
fi

echo ""

# Check login page accessibility
echo "2. Checking login page accessibility..."
if curl -s http://localhost:3000/auth/login | grep -q "LXCloud Login" >/dev/null 2>&1; then
    echo "✅ Login page is accessible"
else
    echo "❌ Login page is not accessible"
fi

echo ""

# Check for HTTPS redirect issues
echo "3. Checking for HTTPS redirect issues..."
LOGIN_RESPONSE=$(curl -s -I http://localhost:3000/auth/login)
if echo "$LOGIN_RESPONSE" | grep -q "X-Local-Network: true"; then
    echo "✅ Local network detection is working"
    echo "✅ HTTPS redirect fix is active"
else
    echo "⚠️  Local network detection may not be working"
fi

# Check for redirects to HTTPS
if echo "$LOGIN_RESPONSE" | grep -q "Location.*https"; then
    echo "❌ HTTPS redirect detected - this may cause login issues"
    echo "   Run the HTTPS fix: npm run fix-https"
else
    echo "✅ No unwanted HTTPS redirects detected"
fi

echo ""

# Test actual login
echo "4. Testing login functionality..."
LOGIN_TEST=$(curl -s -X POST -d "email=admin@lxcloud.local&password=admin123" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    http://localhost:3000/auth/login)

if echo "$LOGIN_TEST" | grep -q "Redirecting to /dashboard"; then
    echo "✅ Login functionality is working"
else
    echo "❌ Login test failed"
    echo "   Response: $LOGIN_TEST"
fi

echo ""

# Check network connectivity from different IPs
echo "5. Testing local network detection..."
NETWORK_TEST=$(curl -s -H "X-Real-IP: 192.168.1.100" http://localhost:3000/auth/login)
if echo "$NETWORK_TEST" | grep -q "LXCloud Login"; then
    echo "✅ Local network IP (192.168.1.100) works correctly"
else
    echo "❌ Local network IP test failed"
fi

echo ""

# Check browser compatibility
echo "6. Common issues and solutions:"
echo ""
echo "   If you're getting 'connection refused':"
echo "   - Make sure the server is running: npm start"
echo "   - Check if port 3000 is available: lsof -i :3000"
echo "   - Try restarting: pkill -f node && npm start"
echo ""
echo "   If you're getting HTTPS redirects:"
echo "   - The fix is already implemented in this version"
echo "   - Make sure you're accessing via HTTP: http://your-ip:3000"
echo "   - Clear browser cache if redirects persist"
echo ""
echo "   If login button doesn't work:"
echo "   - Check browser console for JavaScript errors"
echo "   - Make sure JavaScript is enabled"
echo "   - Try a different browser"

echo ""
echo "🏁 Diagnostics complete!"
echo ""
echo "   Server accessible at: http://localhost:3000"
echo "   Default credentials: admin@lxcloud.local / admin123"
echo ""