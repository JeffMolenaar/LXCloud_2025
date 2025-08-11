#!/bin/bash

# LXCloud Update Script
# Simple update and maintenance script for LXCloud platform

set -e

echo "=============================================================================="
echo "🔄 LXCloud Update & Maintenance"
echo "=============================================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the correct directory
if [ ! -f "package.json" ]; then
    print_error "Please run this script from the LXCloud project root directory"
    exit 1
fi

print_status "Starting LXCloud update process..."

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System packages updated"

# Update Node.js dependencies
print_status "Updating Node.js dependencies..."
npm update
print_success "Node.js dependencies updated"

# Restart services
print_status "Restarting system services..."
sudo systemctl restart mariadb
sudo systemctl restart mosquitto
print_success "System services restarted"

# Test services
print_status "Testing system services..."

# Test MariaDB
if mysql -u lxcloud -plxcloud -e "USE lxcloud; SELECT 1;" > /dev/null 2>&1; then
    print_success "MariaDB connection test passed"
else
    print_error "MariaDB connection test failed"
fi

# Test MQTT
if timeout 5 mosquitto_pub -h localhost -t test/update -m "update test" > /dev/null 2>&1; then
    print_success "MQTT broker test passed"
else
    print_warning "MQTT broker test failed"
fi

# Clean up temporary files
print_status "Cleaning up temporary files..."
rm -rf /tmp/lxcloud-* 2>/dev/null || true
npm cache clean --force > /dev/null 2>&1 || true
print_success "Temporary files cleaned"

# Show system status
print_status "System status check:"
echo ""
echo "Services:"
sudo systemctl is-active mariadb >/dev/null && echo "  • MariaDB:    ✅ Running" || echo "  • MariaDB:    ❌ Not running"
sudo systemctl is-active mosquitto >/dev/null && echo "  • MQTT:       ✅ Running" || echo "  • MQTT:       ❌ Not running"

echo ""
echo "Disk Usage:"
df -h . | tail -1 | awk '{print "  • Available:  " $4 " (" $5 " used)"}'

echo ""
echo "Memory Usage:"
free -h | grep "Mem:" | awk '{print "  • Available:  " $7 " / " $2}'

print_success "Update completed successfully!"
echo ""
echo "🎯 LXCloud system is up to date and running optimally"
echo "   You can now restart the application if needed: npm start"
echo "=============================================================================="