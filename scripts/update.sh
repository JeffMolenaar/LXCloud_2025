#!/bin/bash

# LXCloud Update Script
# Updates LXCloud to the latest version from GitHub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/LXCloud"
SERVICE_USER="lxcloud"
BACKUP_DIR="/opt/LXCloud_backup_$(date +%Y%m%d_%H%M%S)"
REPO_URL="https://github.com/JeffMolenaar/LXCloud_2025.git"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}    LXCloud Update Script       ${NC}"
echo -e "${BLUE}================================${NC}"
echo

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Check if LXCloud is installed
if [[ ! -d "$INSTALL_DIR" ]]; then
    echo -e "${RED}LXCloud installation not found at $INSTALL_DIR${NC}"
    echo -e "${BLUE}Please run the installation script first.${NC}"
    exit 1
fi

# Get current version
CURRENT_VERSION="Unknown"
if [[ -f "$INSTALL_DIR/VERSION" ]]; then
    CURRENT_VERSION=$(cat "$INSTALL_DIR/VERSION")
fi

echo -e "${BLUE}Current version: ${NC}$CURRENT_VERSION"

# Confirm update
echo -e "${YELLOW}This will update LXCloud to the latest version.${NC}"
echo -e "${YELLOW}A backup will be created at: $BACKUP_DIR${NC}"
read -p "Continue with update? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Update cancelled."
    exit 0
fi

# Stop LXCloud service
echo -e "${BLUE}Stopping LXCloud service...${NC}"
systemctl stop lxcloud || true

# Create backup
echo -e "${BLUE}Creating backup...${NC}"
cp -r "$INSTALL_DIR" "$BACKUP_DIR"
echo -e "${GREEN}Backup created at: $BACKUP_DIR${NC}"

# Create temporary directory for new version
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download latest version
echo -e "${BLUE}Downloading latest version...${NC}"
git clone "$REPO_URL" lxcloud_new
cd lxcloud_new

# Get new version
NEW_VERSION="Unknown"
if [[ -f "VERSION" ]]; then
    NEW_VERSION=$(cat "VERSION")
fi

echo -e "${BLUE}New version: ${NC}$NEW_VERSION"

# Preserve configuration and data
echo -e "${BLUE}Preserving configuration...${NC}"
if [[ -f "$INSTALL_DIR/.env" ]]; then
    cp "$INSTALL_DIR/.env" ".env"
fi

# Preserve uploads directory
if [[ -d "$INSTALL_DIR/static/uploads" ]]; then
    cp -r "$INSTALL_DIR/static/uploads" "static/"
fi

# Preserve logs directory
if [[ -d "$INSTALL_DIR/logs" ]]; then
    cp -r "$INSTALL_DIR/logs" "./"
fi

# Update application files
echo -e "${BLUE}Updating application files...${NC}"
rm -rf "$INSTALL_DIR"/*
cp -r * "$INSTALL_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Update Python dependencies
echo -e "${BLUE}Updating Python dependencies...${NC}"
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Run database migrations (if any)
echo -e "${BLUE}Updating database schema...${NC}"
cd "$INSTALL_DIR"
sudo -u "$SERVICE_USER" -H bash -c "source venv/bin/activate && python -c 'from app import create_app; create_app()'" || true

# Start LXCloud service
echo -e "${BLUE}Starting LXCloud service...${NC}"
systemctl start lxcloud

# Wait for service to start
sleep 5

# Check service status
if systemctl is-active --quiet lxcloud; then
    echo -e "${GREEN}✓ LXCloud service is running${NC}"
    
    # Clean up temporary directory
    rm -rf "$TEMP_DIR"
    
    echo
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}    Update Complete!            ${NC}"
    echo -e "${GREEN}================================${NC}"
    echo
    echo -e "${BLUE}Updated from version: ${NC}$CURRENT_VERSION"
    echo -e "${BLUE}Updated to version:   ${NC}$NEW_VERSION"
    echo
    echo -e "${BLUE}Backup location: ${NC}$BACKUP_DIR"
    echo -e "${BLUE}Service status:  ${NC}$(systemctl is-active lxcloud)"
    echo
    echo -e "${YELLOW}You can remove the backup after confirming everything works:${NC}"
    echo -e "${YELLOW}  sudo rm -rf $BACKUP_DIR${NC}"
    echo
else
    echo -e "${RED}✗ LXCloud service failed to start${NC}"
    echo -e "${YELLOW}Attempting to restore from backup...${NC}"
    
    # Restore from backup
    systemctl stop lxcloud || true
    rm -rf "$INSTALL_DIR"/*
    cp -r "$BACKUP_DIR"/* "$INSTALL_DIR/"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    systemctl start lxcloud
    
    echo -e "${BLUE}Service restored. Check logs: ${NC}journalctl -u lxcloud -f"
    exit 1
fi