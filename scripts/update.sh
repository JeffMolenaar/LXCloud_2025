#!/bin/bash

# LXCloud Update Script
# This script updates LXCloud to the latest version

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a regular user with sudo privileges."
fi

# Check if LXCloud is installed
if [ ! -d "/opt/lxcloud" ]; then
    error "LXCloud is not installed. Please run the installation script first."
fi

log "Starting LXCloud update process..."

# Get current version
CURRENT_VERSION=""
if [ -f "/opt/lxcloud/package.json" ]; then
    CURRENT_VERSION=$(grep '"version"' /opt/lxcloud/package.json | cut -d'"' -f4)
    log "Current version: $CURRENT_VERSION"
fi

# Create backup
BACKUP_DIR="/opt/lxcloud.backup.$(date +%Y%m%d_%H%M%S)"
log "Creating backup at: $BACKUP_DIR"
sudo cp -r /opt/lxcloud "$BACKUP_DIR"

# Stop LXCloud service
log "Stopping LXCloud service..."
sudo systemctl stop lxcloud

# Pull latest changes from repository
log "Pulling latest changes..."
cd /opt/lxcloud
sudo -u lxcloud git fetch origin
sudo -u lxcloud git reset --hard origin/main

# Get new version
NEW_VERSION=""
if [ -f "/opt/lxcloud/package.json" ]; then
    NEW_VERSION=$(grep '"version"' /opt/lxcloud/package.json | cut -d'"' -f4)
    log "New version: $NEW_VERSION"
fi

# Install/update dependencies
log "Installing/updating Node.js dependencies..."
sudo -u lxcloud npm install --production

# Run database migrations
log "Running database migrations..."
sudo -u lxcloud NODE_ENV=production node -e "
const database = require('./config/database');
database.initialize().then(() => {
    console.log('Database migrations completed successfully');
    process.exit(0);
}).catch((error) => {
    console.error('Database migration failed:', error);
    process.exit(1);
});
"

# Update file permissions
log "Updating file permissions..."
sudo chown -R lxcloud:lxcloud /opt/lxcloud
sudo chmod +x /opt/lxcloud/scripts/*.sh

# Restart services
log "Restarting LXCloud service..."
sudo systemctl daemon-reload
sudo systemctl start lxcloud

# Check if service started successfully
sleep 5
if sudo systemctl is-active --quiet lxcloud; then
    log "✅ LXCloud service restarted successfully"
else
    error "❌ LXCloud service failed to start. Check logs with: sudo journalctl -u lxcloud -f"
fi

# Restart Nginx (in case of configuration changes)
log "Restarting Nginx..."
sudo systemctl reload nginx

# Clean up old backups (keep last 5)
log "Cleaning up old backups..."
cd /opt
sudo find . -maxdepth 1 -name "lxcloud.backup.*" -type d | sort -r | tail -n +6 | sudo xargs rm -rf

# Update completed
log "🎉 LXCloud update completed successfully!"
log ""
log "📋 Update Summary:"
if [ -n "$CURRENT_VERSION" ] && [ -n "$NEW_VERSION" ]; then
    if [ "$CURRENT_VERSION" != "$NEW_VERSION" ]; then
        log "  - Version updated from $CURRENT_VERSION to $NEW_VERSION"
    else
        log "  - Version remains at $NEW_VERSION (already up to date)"
    fi
else
    log "  - Update completed (version info unavailable)"
fi
log "  - Backup created at: $BACKUP_DIR"
log "  - Application URL: http://$(hostname -I | awk '{print $1}')"
log ""
log "⚠️  If you experience any issues:"
log "  1. Check logs: sudo journalctl -u lxcloud -f"
log "  2. Restore backup: sudo systemctl stop lxcloud && sudo rm -rf /opt/lxcloud && sudo mv $BACKUP_DIR /opt/lxcloud && sudo systemctl start lxcloud"
log "  3. Contact support with error details"
log ""

exit 0