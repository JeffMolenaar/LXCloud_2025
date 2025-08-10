#!/bin/bash

# LXCloud HTTPS Redirect Fix Script
# This script fixes HTTPS redirect issues for local network access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running with sudo
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root or with sudo"
fi

log "Starting HTTPS redirect fix for local network access..."

# Backup current nginx configuration
if [ -f /etc/nginx/sites-available/lxcloud ]; then
    log "Backing up current nginx configuration..."
    cp /etc/nginx/sites-available/lxcloud /etc/nginx/sites-available/lxcloud.backup.$(date +%Y%m%d_%H%M%S)
fi

# Copy the fixed nginx configuration
log "Installing fixed nginx configuration..."
if [ -f /opt/LXCloud_2025/config/nginx-local.conf ]; then
    cp /opt/LXCloud_2025/config/nginx-local.conf /etc/nginx/sites-available/lxcloud
else
    error "nginx-local.conf not found in /opt/LXCloud_2025/config/"
fi

# Test nginx configuration
log "Testing nginx configuration..."
nginx -t || error "Nginx configuration test failed"

# Restart nginx
log "Restarting nginx..."
systemctl restart nginx

# Check if nginx is running
if systemctl is-active --quiet nginx; then
    log "✅ Nginx restarted successfully"
else
    error "❌ Nginx failed to restart"
fi

# Restart LXCloud service to apply middleware changes
log "Restarting LXCloud service..."
systemctl restart lxcloud

# Check if LXCloud is running
sleep 3
if systemctl is-active --quiet lxcloud; then
    log "✅ LXCloud service restarted successfully"
else
    error "❌ LXCloud service failed to restart"
fi

# Get local IP for testing
LOCAL_IP=$(hostname -I | awk '{print $1}')

log "🎉 HTTPS redirect fix completed successfully!"
log ""
log "📋 Fix Summary:"
log "  - Updated nginx configuration to prevent HTTPS redirects for local networks"
log "  - Added middleware to handle local network requests over HTTP"
log "  - Disabled HSTS headers for local access"
log ""
log "🔗 Access URLs:"
log "  - Local network: http://$LOCAL_IP"
log "  - Localhost: http://localhost"
log "  - Local IP: http://127.0.0.1"
log ""
log "⚠️  Important Notes:"
log "  1. Local network (192.168.x.x, 10.x.x.x, 172.16-31.x.x) can now access via HTTP"
log "  2. External access may still use HTTPS if SSL certificates are configured"
log "  3. Test login from your local network device"
log ""
log "🧪 Testing:"
log "  Try accessing: http://$LOCAL_IP from your local network device"
log "  Login should now work without HTTPS redirects"

exit 0