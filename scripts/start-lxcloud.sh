#!/bin/bash

# LXCloud Startup Script with Connection Diagnostics
# This script helps diagnose and fix common connection issues

echo "🚀 Starting LXCloud..."
echo "================================"

# Check if we're in the right directory
if [ ! -f "server.js" ]; then
    echo "❌ Error: server.js not found. Please run this script from the LXCloud directory."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Creating from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
    else
        echo "❌ Error: .env.example not found"
        exit 1
    fi
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Error: npm install failed"
        exit 1
    fi
fi

# Check database connectivity
echo ""
echo "🔍 Checking database connectivity..."
DB_CHECK=$(npm run test-db 2>&1)
if echo "$DB_CHECK" | grep -q "❌"; then
    echo "⚠️  Database connection failed - server will run in mock mode"
    echo "   This is normal for development. For production, ensure MySQL/MariaDB is running."
else
    echo "✅ Database connection successful"
fi

# Check if port 3000 is available
echo ""
echo "🔌 Checking port 3000..."
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 3000 is already in use. Stopping existing process..."
    pkill -f "node.*server.js" 2>/dev/null || true
    sleep 2
fi

# Start the server
echo ""
echo "🏁 Starting LXCloud server..."
echo "================================"
echo ""

# Set environment for better development experience
export NODE_ENV=development
export FORCE_HTTP=true

# Start the server
npm start