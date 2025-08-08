#!/bin/bash

# LXCloud Installation Script for Ubuntu Server LTS 24
# This script installs and configures LXCloud on a fresh Ubuntu Server

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

# Check Ubuntu version
if ! grep -q "Ubuntu 24" /etc/os-release; then
    warn "This script is designed for Ubuntu 24.04 LTS. Continuing anyway..."
fi

log "Starting LXCloud installation..."

# Update system
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Node.js 18.x
log "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify Node.js installation
node_version=$(node --version)
npm_version=$(npm --version)
log "Node.js version: $node_version"
log "NPM version: $npm_version"

# Install MariaDB
log "Installing MariaDB..."
sudo apt install -y mariadb-server mariadb-client

# Secure MariaDB installation
log "Securing MariaDB installation..."
sudo mysql_secure_installation

# Install Mosquitto MQTT Broker
log "Installing Mosquitto MQTT Broker..."
sudo apt install -y mosquitto mosquitto-clients

# Install additional dependencies
log "Installing additional dependencies..."
sudo apt install -y git nginx certbot python3-certbot-nginx

# Create LXCloud user
log "Creating LXCloud system user..."
sudo useradd -r -s /bin/false -d /opt/lxcloud lxcloud || true

# Create application directory
log "Creating application directory..."
sudo mkdir -p /opt/lxcloud
sudo chown lxcloud:lxcloud /opt/lxcloud

# Copy application files
log "Copying application files..."
sudo cp -r . /opt/lxcloud/
sudo chown -R lxcloud:lxcloud /opt/lxcloud

# Install Node.js dependencies
log "Installing Node.js dependencies..."
cd /opt/lxcloud
sudo -u lxcloud npm install --omit=dev

# Create environment file
log "Creating environment configuration..."
sudo -u lxcloud cp .env.example .env

# Generate random secrets
JWT_SECRET=$(openssl rand -base64 32)
SESSION_SECRET=$(openssl rand -base64 32)
DB_PASSWORD=$(openssl rand -base64 16)
MQTT_PASSWORD=$(openssl rand -base64 16)

# Escape secrets for sed
ESCAPED_JWT_SECRET=$(printf '%s\n' "$JWT_SECRET" | sed 's/[\/&]/\\&/g')
ESCAPED_SESSION_SECRET=$(printf '%s\n' "$SESSION_SECRET" | sed 's/[\/&]/\\&/g')
ESCAPED_DB_PASSWORD=$(printf '%s\n' "$DB_PASSWORD" | sed 's/[\/&]/\\&/g')
ESCAPED_MQTT_PASSWORD=$(printf '%s\n' "$MQTT_PASSWORD" | sed 's/[\/&]/\\&/g')

# Update environment file
sudo -u lxcloud sed -i "s|your_jwt_secret_key_change_this|$ESCAPED_JWT_SECRET|" /opt/lxcloud/.env
sudo -u lxcloud sed -i "s|your_session_secret_change_this|$ESCAPED_SESSION_SECRET|" /opt/lxcloud/.env
sudo -u lxcloud sed -i "s|change_this_password|lxadmin|" /opt/lxcloud/.env
sudo -u lxcloud sed -i "s|lxcloud_user|lxadmin|" /opt/lxcloud/.env
sudo -u lxcloud sed -i "s|change_this_mqtt_password|$ESCAPED_MQTT_PASSWORD|" /opt/lxcloud/.env

# Create MariaDB database and user
log "Setting up MariaDB database..."
mysql -u root -p <<EOF
CREATE DATABASE IF NOT EXISTS lxcloud;
CREATE USER IF NOT EXISTS 'lxadmin'@'localhost' IDENTIFIED BY 'lxadmin';
GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxadmin'@'localhost';
FLUSH PRIVILEGES;
EOF

# Configure Mosquitto MQTT
log "Configuring Mosquitto MQTT..."
sudo tee /etc/mosquitto/conf.d/lxcloud.conf > /dev/null <<EOF
# LXCloud MQTT Configuration
listener 1883 localhost
allow_anonymous false
password_file /etc/mosquitto/passwd

# Persistence
persistence true

# Logging
log_type error
log_type warning
log_type notice
log_type information

# Security
max_connections 1000
max_inflight_messages 20
max_queued_messages 100
EOF

# Create MQTT user and fix permissions
sudo mosquitto_passwd -c -b /etc/mosquitto/passwd lxcloud_mqtt "$MQTT_PASSWORD"
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd
sudo chmod 600 /etc/mosquitto/passwd

# Restart Mosquitto
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto

# Create systemd service
log "Creating systemd service..."
sudo tee /etc/systemd/system/lxcloud.service > /dev/null <<EOF
[Unit]
Description=LXCloud Web Application
After=network.target mariadb.service mosquitto.service
Requires=mariadb.service

[Service]
Type=simple
User=lxcloud
Group=lxcloud
WorkingDirectory=/opt/lxcloud
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=5
Environment=NODE_ENV=production

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/lxcloud/logs /opt/lxcloud/uploads

[Install]
WantedBy=multi-user.target
EOF

# Create log directories
sudo mkdir -p /opt/lxcloud/logs /opt/lxcloud/uploads
sudo chown -R lxcloud:lxcloud /opt/lxcloud/logs /opt/lxcloud/uploads

# Setup database schema
log "Setting up database schema..."
cd /opt/lxcloud
sudo -u lxcloud NODE_ENV=production node -e "
const database = require('./config/database');
database.initialize().then(() => {
    console.log('Database initialized successfully');
    process.exit(0);
}).catch((error) => {
    console.error('Database initialization failed:', error);
    process.exit(1);
});
"

# Configure Nginx
log "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/lxcloud > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # WebSocket support for Socket.IO
    location /socket.io/ {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/lxcloud /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Enable and start LXCloud service
log "Starting LXCloud service..."
sudo systemctl daemon-reload
sudo systemctl enable lxcloud
sudo systemctl start lxcloud

# Configure firewall
log "Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Create update script
log "Creating update script..."
sudo tee /opt/lxcloud/update.sh > /dev/null <<'EOF'
#!/bin/bash

set -e

log() {
    echo -e "\033[0;32m[$(date +'%Y-%m-%d %H:%M:%S')] $1\033[0m"
}

error() {
    echo -e "\033[0;31m[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1\033[0m"
    exit 1
}

log "Starting LXCloud update..."

# Stop service
sudo systemctl stop lxcloud

# Backup current installation
sudo cp -r /opt/lxcloud /opt/lxcloud.backup.$(date +%Y%m%d_%H%M%S)

# Pull latest changes
cd /opt/lxcloud
sudo -u lxcloud git pull origin main

# Install/update dependencies
sudo -u lxcloud npm install --omit=dev

# Run database migrations
sudo -u lxcloud NODE_ENV=production node -e "
const database = require('./config/database');
database.initialize().then(() => {
    console.log('Database migrations completed');
    process.exit(0);
}).catch((error) => {
    console.error('Database migration failed:', error);
    process.exit(1);
});
"

# Restart service
sudo systemctl start lxcloud

log "LXCloud updated successfully!"
EOF

sudo chmod +x /opt/lxcloud/update.sh

# Final status check
log "Checking service status..."
sleep 5
if sudo systemctl is-active --quiet lxcloud; then
    log "✅ LXCloud service is running"
else
    error "❌ LXCloud service failed to start. Check logs with: sudo journalctl -u lxcloud -f"
fi

if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx is running"
else
    error "❌ Nginx failed to start"
fi

if sudo systemctl is-active --quiet mariadb; then
    log "✅ MariaDB is running"
else
    error "❌ MariaDB failed to start"
fi

if sudo systemctl is-active --quiet mosquitto; then
    log "✅ Mosquitto MQTT is running"
else
    error "❌ Mosquitto MQTT failed to start"
fi

# Installation complete
log "🎉 LXCloud installation completed successfully!"
log ""
log "📋 Installation Summary:"
log "  - Application URL: http://$(hostname -I | awk '{print $1}')"
log "  - Default Admin Email: admin@lxcloud.local"
log "  - Default Admin Password: admin123"
log "  - Application Directory: /opt/lxcloud"
log "  - Logs: sudo journalctl -u lxcloud -f"
log "  - Update Command: sudo /opt/lxcloud/update.sh"
log ""
log "⚠️  Important:"
log "  1. Change the default admin password immediately"
log "  2. Configure SSL/TLS with: sudo certbot --nginx"
log "  3. Backup your .env file before updates"
log "  4. Monitor logs for any issues"
log ""
log "🔧 Next Steps:"
log "  1. Access the web interface at http://$(hostname -I | awk '{print $1}')"
log "  2. Login with the default admin credentials"
log "  3. Change the admin password in User Management"
log "  4. Configure your first controller devices"
log ""

exit 0
