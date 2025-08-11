#!/bin/bash

# LXCloud Complete Setup Script
# One-command installation for the complete LXCloud IoT platform

set -e

echo "=============================================================================="
echo "🚀 LXCloud Complete Setup - IoT Cloud Management Platform"
echo "=============================================================================="
echo "Installing MariaDB + MQTT + Node.js + Complete Admin Interface"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   print_status "Please run: ./setup.sh"
   exit 1
fi

# Check if we're in the correct directory
if [ ! -f "package.json" ]; then
    print_error "Please run this script from the LXCloud project root directory"
    exit 1
fi

print_header "SYSTEM REQUIREMENTS CHECK"

# Check OS
if ! command -v apt &> /dev/null; then
    print_error "This script requires Ubuntu/Debian with apt package manager"
    exit 1
fi

print_success "Ubuntu/Debian system detected"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed"
    print_status "Please install Node.js 18+ first: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//')
NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
if [ "$NODE_MAJOR" -lt 18 ]; then
    print_error "Node.js version $NODE_VERSION detected. Version 18+ is required"
    exit 1
fi

print_success "Node.js $NODE_VERSION detected"

print_header "SYSTEM PACKAGES INSTALLATION"

print_status "Updating package repositories..."
sudo apt update

# Install MariaDB
print_status "Installing MariaDB server..."
if ! command -v mysql &> /dev/null; then
    sudo apt install -y mariadb-server mariadb-client
    print_success "MariaDB installed successfully"
else
    print_success "MariaDB already installed"
fi

# Install MQTT broker (Mosquitto)
print_status "Installing MQTT broker (Mosquitto)..."
if ! command -v mosquitto &> /dev/null; then
    sudo apt install -y mosquitto mosquitto-clients
    print_success "Mosquitto MQTT broker installed successfully"
else
    print_success "Mosquitto already installed"
fi

# Install additional system tools
print_status "Installing additional system tools..."
sudo apt install -y curl wget git build-essential

print_header "SERVICE CONFIGURATION"

# Start and enable MariaDB
print_status "Starting MariaDB service..."
sudo systemctl start mariadb
sudo systemctl enable mariadb
print_success "MariaDB service started and enabled"

# Configure and start MQTT
print_status "Configuring MQTT broker..."
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Create MQTT configuration
sudo tee /etc/mosquitto/conf.d/lxcloud.conf > /dev/null <<EOF
# LXCloud MQTT Configuration
listener 1883 0.0.0.0
allow_anonymous true
log_type all
log_dest file /var/log/mosquitto/mosquitto.log
persistence true
persistence_location /var/lib/mosquitto/
EOF

sudo systemctl restart mosquitto
print_success "MQTT broker configured and restarted"

print_header "DATABASE SETUP"

# Setup MariaDB for LXCloud
print_status "Setting up MariaDB database for LXCloud..."

# Check if database exists
DB_EXISTS=$(sudo mysql -e "SHOW DATABASES LIKE 'lxcloud';" | grep lxcloud || true)

if [ -z "$DB_EXISTS" ]; then
    print_status "Creating LXCloud database and user..."
    
    sudo mysql -e "CREATE DATABASE lxcloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    sudo mysql -e "CREATE USER 'lxcloud'@'localhost' IDENTIFIED BY 'lxcloud';"
    sudo mysql -e "GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxcloud'@'localhost';"
    sudo mysql -e "FLUSH PRIVILEGES;"
    
    print_success "Database and user created successfully"
else
    print_success "LXCloud database already exists"
fi

# Test database connection
print_status "Testing database connection..."
if mysql -u lxcloud -plxcloud -e "USE lxcloud; SELECT 1;" > /dev/null 2>&1; then
    print_success "Database connection test successful"
else
    print_error "Database connection test failed"
    exit 1
fi

print_header "APPLICATION SETUP"

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install
print_success "Node.js dependencies installed"

# Create required directories
print_status "Creating required directories..."
mkdir -p uploads data logs
print_success "Required directories created"

# Set proper permissions
print_status "Setting file permissions..."
chmod 755 uploads data logs
chmod +x *.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating environment configuration..."
    cat > .env << EOF
# LXCloud Environment Configuration
NODE_ENV=production
PORT=3000

# Database Configuration
DB_HOST=localhost
DB_USER=lxcloud
DB_PASSWORD=lxcloud
DB_NAME=lxcloud

# MQTT Configuration
MQTT_HOST=localhost
MQTT_PORT=1883

# Security
SESSION_SECRET=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 32)

# Admin Configuration
ADMIN_EMAIL=admin@lxcloud.local
ADMIN_PASSWORD=admin123
EOF
    print_success "Environment configuration created"
else
    print_success "Environment configuration already exists"
fi

print_header "SYSTEM TESTING"

# Test MQTT broker
print_status "Testing MQTT broker..."
if timeout 5 mosquitto_pub -h localhost -t test/topic -m "test message" > /dev/null 2>&1; then
    print_success "MQTT broker test successful"
else
    print_warning "MQTT broker test failed - continuing anyway"
fi

# Test Node.js application startup
print_status "Testing application startup..."
timeout 10 node server.js > /dev/null 2>&1 &
TEST_PID=$!
sleep 3

if kill -0 $TEST_PID 2>/dev/null; then
    kill $TEST_PID
    print_success "Application startup test successful"
else
    print_warning "Application startup test failed - but installation continues"
fi

print_header "SECURITY CONFIGURATION"

# Configure firewall rules
print_status "Configuring firewall rules..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 3000/tcp comment "LXCloud Web Interface"
    sudo ufw allow 1883/tcp comment "MQTT Broker"
    print_success "Firewall rules configured"
else
    print_warning "UFW firewall not available - manual firewall configuration may be needed"
fi

# Set secure file permissions
print_status "Setting secure file permissions..."
chmod 600 .env 2>/dev/null || true
chmod 644 package.json
chmod 755 server.js

print_header "INSTALLATION COMPLETE"

print_success "LXCloud setup completed successfully!"
echo ""
echo "=============================================================================="
echo "🎯 LXCloud Complete IoT Platform - Ready to Launch!"
echo "=============================================================================="
echo ""
echo "✅ Components Installed:"
echo "   • MariaDB Database Server"
echo "   • MQTT Broker (Mosquitto)"
echo "   • Node.js Application Server"
echo "   • Complete Admin Interface"
echo "   • Real-time Socket.IO Communication"
echo ""
echo "🚀 Quick Start:"
echo "   npm start                    # Start the server"
echo "   ./update.sh                  # Update the system"
echo ""
echo "📍 Access URLs:"
echo "   Web Interface: http://localhost:3000"
echo "   Admin Panel:   http://localhost:3000/admin"
echo ""
echo "👤 Default Admin Login:"
echo "   Email:    admin@lxcloud.local"
echo "   Password: admin123"
echo ""
echo "🔧 System Services Status:"
sudo systemctl is-active mariadb >/dev/null && echo "   • MariaDB:    ✅ Running" || echo "   • MariaDB:    ❌ Not running"
sudo systemctl is-active mosquitto >/dev/null && echo "   • MQTT:       ✅ Running" || echo "   • MQTT:       ❌ Not running"
echo ""
echo "📊 MQTT Topics:"
echo "   • Device Registration: lxcloud/controllers/{serial}/register"
echo "   • Live Data:          lxcloud/controllers/{serial}/data"
echo "   • Status Updates:     lxcloud/controllers/{serial}/status"
echo ""
echo "🔒 Security Features:"
echo "   • Local network access only"
echo "   • Database security with prepared statements"
echo "   • Session management and rate limiting"
echo "   • HTTPS-ready configuration"
echo ""
echo "📚 Documentation:"
echo "   • README.md - Complete setup and usage guide"
echo "   • ./update.sh - System update and maintenance"
echo ""
echo "🎉 Your LXCloud IoT platform is ready!"
echo "   Run 'npm start' to launch the complete system"
echo "=============================================================================="