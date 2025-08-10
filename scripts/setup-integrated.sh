#!/bin/bash

# LXCloud Integrated Setup Script
# This script sets up MariaDB and MQTT for the integrated version

set -e

echo "=================================================="
echo "🚀 LXCloud Integrated v2.0 Setup"
echo "=================================================="
echo "Setting up MariaDB + MQTT for full functionality"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   print_status "Please run: ./scripts/setup-integrated.sh"
   exit 1
fi

print_status "Updating package repositories..."
sudo apt update

# Install MariaDB
print_status "Installing MariaDB server..."
if ! command -v mysql &> /dev/null; then
    sudo apt install -y mariadb-server mariadb-client
    print_success "MariaDB installed successfully"
else
    print_warning "MariaDB already installed"
fi

# Secure MariaDB installation
print_status "Starting MariaDB service..."
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Install MQTT broker (Mosquitto)
print_status "Installing MQTT broker (Mosquitto)..."
if ! command -v mosquitto &> /dev/null; then
    sudo apt install -y mosquitto mosquitto-clients
    print_success "Mosquitto MQTT broker installed successfully"
else
    print_warning "Mosquitto already installed"
fi

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
EOF

sudo systemctl restart mosquitto

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
    print_warning "LXCloud database already exists"
fi

# Test database connection
print_status "Testing database connection..."
if mysql -u lxcloud -plxcloud -e "USE lxcloud; SELECT 1;" > /dev/null 2>&1; then
    print_success "Database connection test successful"
else
    print_error "Database connection test failed"
    exit 1
fi

# Test MQTT broker
print_status "Testing MQTT broker..."
if timeout 5 mosquitto_pub -h localhost -t test/topic -m "test message" > /dev/null 2>&1; then
    print_success "MQTT broker test successful"
else
    print_warning "MQTT broker test failed - continuing anyway"
fi

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install

# Create uploads directory
print_status "Creating required directories..."
mkdir -p uploads data

# Set proper permissions
print_status "Setting file permissions..."
chmod 755 uploads data
chmod +x scripts/*.sh 2>/dev/null || true

print_success "Setup completed successfully!"
echo ""
echo "=================================================="
echo "🎯 LXCloud Integrated v2.0 - Setup Complete!"
echo "=================================================="
echo ""
echo "✅ MariaDB Database: Ready"
echo "✅ MQTT Broker: Running on port 1883"
echo "✅ Node.js Dependencies: Installed"
echo ""
echo "🚀 Start the server:"
echo "   npm start"
echo ""
echo "📍 Access URL:"
echo "   http://localhost:3000"
echo ""
echo "👤 Default Login:"
echo "   Email: admin@lxcloud.local"
echo "   Password: admin123"
echo ""
echo "🔧 System Services:"
echo "   - MariaDB: sudo systemctl status mariadb"
echo "   - MQTT: sudo systemctl status mosquitto"
echo ""
echo "=================================================="

# Show service status
print_status "Current service status:"
echo ""
echo "MariaDB:"
sudo systemctl is-active mariadb && echo "  ✅ Running" || echo "  ❌ Not running"
echo ""
echo "MQTT (Mosquitto):"
sudo systemctl is-active mosquitto && echo "  ✅ Running" || echo "  ❌ Not running"
echo ""

print_status "Setup complete! You can now run 'npm start' to launch LXCloud Integrated v2.0"