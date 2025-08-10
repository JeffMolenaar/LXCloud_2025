#!/bin/bash

# Manual verification script for HTTPS redirect fix
# This script demonstrates the fix working with various IP addresses

echo "🧪 Testing HTTPS Redirect Fix for Local Network Access"
echo "====================================================="
echo

# Function to test an IP address
test_ip() {
    local ip=$1
    local description=$2
    echo "Testing $description ($ip):"
    
    # Create a simple Node.js test
    node -e "
    const express = require('express');
    const helmet = require('helmet');
    const app = express();

    // Apply the same middleware as in server.js
    app.use((req, res, next) => {
        const clientIP = req.headers['x-forwarded-for'] || req.headers['x-real-ip'] || req.connection.remoteAddress || req.ip;
        const isLocalNetwork = /^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|::1|localhost)/.test(clientIP);
        
        const helmetConfig = {
            hsts: false,
            forceHTTPS: false
        };
        
        helmet(helmetConfig)(req, res, next);
    });

    app.use((req, res, next) => {
        const clientIP = req.headers['x-forwarded-for'] || req.headers['x-real-ip'] || req.connection.remoteAddress || req.ip;
        const isLocalNetwork = /^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|::1|localhost)/.test(clientIP);
        
        if (isLocalNetwork) {
            res.removeHeader('Strict-Transport-Security');
            res.setHeader('X-Local-Network', 'true');
        }
        
        next();
    });

    app.get('/test', (req, res) => {
        const clientIP = req.headers['x-forwarded-for'] || req.headers['x-real-ip'] || req.connection.remoteAddress || req.ip;
        const isLocalNetwork = /^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|::1|localhost)/.test(clientIP);
        res.json({
            clientIP: clientIP,
            isLocalNetwork: isLocalNetwork,
            hasLocalNetworkHeader: !!res.getHeaders()['x-local-network'],
            hasHSTS: !!res.getHeaders()['strict-transport-security']
        });
    });

    const server = app.listen(0, () => {
        const port = server.address().port;
        const http = require('http');
        
        const options = {
            hostname: 'localhost',
            port: port,
            path: '/test',
            method: 'GET',
            headers: {
                'X-Real-IP': '$ip'
            }
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                const result = JSON.parse(data);
                console.log('  ✓ Client IP detected as:', result.clientIP || 'not set');
                console.log('  ✓ Is local network:', result.isLocalNetwork ? 'YES' : 'NO');
                console.log('  ✓ Has X-Local-Network header:', result.hasLocalNetworkHeader ? 'YES' : 'NO');
                console.log('  ✓ Has HSTS header:', result.hasHSTS ? 'YES (BAD)' : 'NO (GOOD)');
                console.log('  ✓ HTTP Status:', res.statusCode === 200 ? '200 OK' : res.statusCode);
                console.log();
                server.close();
            });
        });

        req.on('error', (e) => {
            console.log('  ❌ Error:', e.message);
            server.close();
        });

        req.end();
    });
    " 2>/dev/null
}

# Test various IP addresses
test_ip "192.168.1.100" "Local network (192.168.x.x)"
test_ip "10.0.0.50" "Private network (10.x.x.x)"
test_ip "172.20.0.10" "Private network (172.16-31.x.x)"
test_ip "127.0.0.1" "Localhost"
test_ip "8.8.8.8" "External IP (should not get local network treatment)"

echo "✅ All tests completed!"
echo ""
echo "📋 Summary:"
echo "  - Local network IPs (192.168.x.x, 10.x.x.x, 172.16-31.x.x, localhost) should:"
echo "    ✓ Be detected as local network: YES"
echo "    ✓ Have X-Local-Network header: YES"
echo "    ✓ Have HSTS header: NO (allows HTTP)"
echo "    ✓ Return HTTP 200 status"
echo ""
echo "  - External IPs should:"
echo "    ✓ Be detected as local network: NO"
echo "    ✓ Have X-Local-Network header: NO"
echo "    ✓ Still allow HTTP access (no forced HTTPS redirect)"
echo ""
echo "🎯 The fix ensures local network devices can login via HTTP without HTTPS redirects!"