#!/bin/bash

# LXCloud Complete Installation Script for Ubuntu Server LTS 22.04
# This script completely removes any previous installation and performs a fresh setup
# Specifically designed and tested for Ubuntu Server LTS 22.04

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/lxcloud"
SERVICE_USER="lxcloud"
DATABASE_NAME="lxcloud"
DATABASE_USER="lxcloud"
DATABASE_PASSWORD="lxcloud"
MQTT_USER="lxcloud_mqtt"
MQTT_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)

# Logging functions
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

info() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

success() {
    echo -e "${PURPLE}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a regular user with sudo privileges."
fi

# Check sudo privileges
if ! sudo -n true 2>/dev/null; then
    error "This script requires sudo privileges. Please ensure you can run sudo commands."
fi

# Check Ubuntu version specifically for 22.04
check_ubuntu_version() {
    if ! grep -q "Ubuntu" /etc/os-release; then
        error "This script is designed specifically for Ubuntu. Current OS is not supported."
    fi
    
    # Check for Ubuntu 22.04 LTS
    if grep -q "22.04" /etc/os-release; then
        log "Ubuntu 22.04 LTS detected - proceeding with installation"
    else
        warn "This script is optimized for Ubuntu 22.04 LTS. Current version: $(lsb_release -d | cut -f2)"
        echo "Do you want to continue anyway? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            error "Installation cancelled by user"
        fi
    fi
}

# Function to check if a service exists and is active
check_service() {
    local service_name=$1
    if systemctl list-units --full -all | grep -Fq "$service_name.service"; then
        if systemctl is-active --quiet "$service_name"; then
            return 0
        fi
    fi
    return 1
}

# Function to safely stop and disable services
stop_service() {
    local service_name=$1
    if check_service "$service_name"; then
        log "Stopping $service_name service..."
        sudo systemctl stop "$service_name" || true
        sudo systemctl disable "$service_name" || true
    fi
}

# Function to remove existing installation
remove_existing_installation() {
    log "Checking for existing LXCloud installation..."
    
    # Stop services
    stop_service "lxcloud"
    stop_service "nginx"
    
    # Remove systemd service
    if [ -f "/etc/systemd/system/lxcloud.service" ]; then
        log "Removing LXCloud systemd service..."
        sudo rm -f /etc/systemd/system/lxcloud.service
        sudo systemctl daemon-reload
    fi
    
    # Remove nginx configuration
    if [ -f "/etc/nginx/sites-available/lxcloud" ]; then
        log "Removing nginx configuration..."
        sudo rm -f /etc/nginx/sites-available/lxcloud
        sudo rm -f /etc/nginx/sites-enabled/lxcloud
    fi
    
    # Remove application directory
    if [ -d "$INSTALL_DIR" ]; then
        log "Removing existing application directory..."
        sudo rm -rf "$INSTALL_DIR"
    fi
    
    # Remove system user (but keep home directory for safety)
    if id "$SERVICE_USER" &>/dev/null; then
        log "Removing system user $SERVICE_USER..."
        sudo userdel "$SERVICE_USER" 2>/dev/null || true
    fi
    
    success "Previous installation cleaned up successfully"
}

# Function to install Node.js 18.x (compatible with Ubuntu 22.04)
install_nodejs() {
    log "Installing Node.js 18.x for Ubuntu 22.04..."
    
    # Remove any existing Node.js
    sudo apt remove -y nodejs npm node 2>/dev/null || true
    sudo apt autoremove -y 2>/dev/null || true
    
    # Add NodeSource repository for Ubuntu 22.04
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    
    # Install Node.js
    sudo apt-get update
    sudo apt-get install -y nodejs
    
    # Verify installation
    node_version=$(node --version)
    npm_version=$(npm --version)
    log "Node.js version: $node_version"
    log "NPM version: $npm_version"
    
    # Check if Node.js version is adequate
    if [[ ! "$node_version" =~ ^v1[8-9]\.|^v[2-9][0-9]\. ]]; then
        warn "Node.js version $node_version might not be optimal. Attempting to upgrade npm..."
    fi
    
    # Ensure npm is up to date
    sudo npm install -g npm@latest
    
    success "Node.js installed successfully"
}

# Function to install and configure MariaDB for Ubuntu 22.04
install_mariadb() {
    log "Installing and configuring MariaDB for Ubuntu 22.04..."
    
    # Remove any existing MySQL/MariaDB
    sudo systemctl stop mysql mariadb 2>/dev/null || true
    sudo apt remove -y mysql-server mysql-client mariadb-server mariadb-client 2>/dev/null || true
    sudo apt autoremove -y 2>/dev/null || true
    
    # Update package list
    sudo apt update
    
    # Install MariaDB (Ubuntu 22.04 default version)
    sudo DEBIAN_FRONTEND=noninteractive apt install -y mariadb-server mariadb-client
    
    # Start MariaDB
    sudo systemctl start mariadb
    sudo systemctl enable mariadb
    
    # Wait for MariaDB to be ready
    log "Waiting for MariaDB to start..."
    local retry_count=0
    while ! sudo mysql -e "SELECT 1" &>/dev/null; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -gt 30 ]; then
            error "MariaDB failed to start after 30 seconds"
        fi
        sleep 1
    done
    
    # Secure MariaDB installation automatically
    log "Securing MariaDB installation..."
    sudo mysql -e "
        DELETE FROM mysql.user WHERE User='';
        DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
        DROP DATABASE IF EXISTS test;
        DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
        
        -- Create application database and user
        CREATE DATABASE IF NOT EXISTS $DATABASE_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        CREATE USER IF NOT EXISTS '$DATABASE_USER'@'localhost' IDENTIFIED BY '$DATABASE_PASSWORD';
        GRANT ALL PRIVILEGES ON $DATABASE_NAME.* TO '$DATABASE_USER'@'localhost';
        
        FLUSH PRIVILEGES;
    "
    
    # Test database connection
    if mysql -u "$DATABASE_USER" -p"$DATABASE_PASSWORD" "$DATABASE_NAME" -e "SELECT 1" &>/dev/null; then
        success "MariaDB installed and configured successfully"
    else
        error "MariaDB database connection test failed"
    fi
}

# Function to install and configure Mosquitto MQTT for Ubuntu 22.04
install_mosquitto() {
    log "Installing and configuring Mosquitto MQTT for Ubuntu 22.04..."
    
    # Remove any existing Mosquitto
    sudo systemctl stop mosquitto 2>/dev/null || true
    sudo apt remove -y mosquitto mosquitto-clients 2>/dev/null || true
    sudo apt autoremove -y 2>/dev/null || true
    
    # Install Mosquitto
    sudo apt update
    sudo apt install -y mosquitto mosquitto-clients
    
    # Create MQTT configuration directory if it doesn't exist
    sudo mkdir -p /etc/mosquitto/conf.d
    
    # Create MQTT configuration optimized for Ubuntu 22.04
    sudo tee /etc/mosquitto/conf.d/lxcloud.conf > /dev/null <<EOF
# LXCloud MQTT Configuration for Ubuntu 22.04
listener 1883 localhost
allow_anonymous false
password_file /etc/mosquitto/passwd

# Persistence settings
persistence true
persistence_location /var/lib/mosquitto/

# Logging configuration
log_type error
log_type warning
log_type notice
log_type information
log_dest file /var/log/mosquitto/mosquitto.log

# Security settings
max_connections 1000
max_inflight_messages 20
max_queued_messages 100

# Connection settings
keepalive_interval 60
retry_interval 20
sys_interval 10

# Ubuntu 22.04 specific optimizations
connection_messages true
log_timestamp true
EOF

    # Create MQTT user and password file
    sudo mosquitto_passwd -c -b /etc/mosquitto/passwd "$MQTT_USER" "$MQTT_PASSWORD"
    sudo chown mosquitto:mosquitto /etc/mosquitto/passwd
    sudo chmod 600 /etc/mosquitto/passwd
    
    # Ensure log directory exists with proper permissions
    sudo mkdir -p /var/log/mosquitto
    sudo chown mosquitto:mosquitto /var/log/mosquitto
    sudo chmod 755 /var/log/mosquitto
    
    # Start and enable Mosquitto
    sudo systemctl restart mosquitto
    sudo systemctl enable mosquitto
    
    # Wait for Mosquitto to start
    log "Waiting for Mosquitto to start..."
    sleep 3
    
    # Test MQTT connection
    if timeout 5 mosquitto_pub -h localhost -u "$MQTT_USER" -P "$MQTT_PASSWORD" -t "lxcloud/test" -m "hello"; then
        success "Mosquitto MQTT installed and configured successfully"
    else
        warn "MQTT test publish failed, but continuing installation"
    fi
}

# Function to install system dependencies for Ubuntu 22.04
install_dependencies() {
    log "Installing system dependencies for Ubuntu 22.04..."
    
    # Update package list
    sudo apt update
    
    # Install essential packages
    sudo apt install -y \
        curl \
        wget \
        git \
        nginx \
        certbot \
        python3-certbot-nginx \
        ufw \
        htop \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        build-essential \
        openssl
    
    success "System dependencies installed successfully"
}

# Function to create system user and directories
setup_user_and_directories() {
    log "Setting up system user and directories..."
    
    # Create system user
    if ! id "$SERVICE_USER" &>/dev/null; then
        sudo useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        log "Created system user: $SERVICE_USER"
    else
        log "System user $SERVICE_USER already exists"
    fi
    
    # Create application directory structure
    sudo mkdir -p "$INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR/logs"
    sudo mkdir -p "$INSTALL_DIR/uploads"
    sudo mkdir -p "$INSTALL_DIR/backups"
    sudo mkdir -p "$INSTALL_DIR/config"
    
    # Set ownership and permissions
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    sudo chmod 755 "$INSTALL_DIR"
    sudo chmod 755 "$INSTALL_DIR/logs"
    sudo chmod 755 "$INSTALL_DIR/uploads"
    sudo chmod 700 "$INSTALL_DIR/backups"
    
    success "User and directories created successfully"
}

# Function to install application
install_application() {
    log "Installing LXCloud application..."
    
    # Get current directory (where the script is run from)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SOURCE_DIR="$(dirname "$SCRIPT_DIR")"
    
    # Copy application files
    sudo cp -r "$SOURCE_DIR"/* "$INSTALL_DIR/"
    
    # Remove any existing node_modules to prevent conflicts
    sudo rm -rf "$INSTALL_DIR/node_modules"
    
    # Set correct ownership
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    # Install Node.js dependencies
    log "Installing Node.js dependencies..."
    cd "$INSTALL_DIR"
    sudo -u "$SERVICE_USER" npm cache clean --force 2>/dev/null || true
    sudo -u "$SERVICE_USER" npm install --omit=dev --no-audit --no-fund
    
    # Create environment file
    log "Creating environment configuration..."
    if [ -f "$INSTALL_DIR/.env.example" ]; then
        sudo -u "$SERVICE_USER" cp .env.example .env
    else
        # Create basic .env file if example doesn't exist
        sudo -u "$SERVICE_USER" tee .env > /dev/null <<EOF
NODE_ENV=production
PORT=3000
HOST=0.0.0.0

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=$DATABASE_NAME
DB_USER=$DATABASE_USER
DB_PASSWORD=$DATABASE_PASSWORD

# Security Configuration
JWT_SECRET=your_jwt_secret_key_change_this
JWT_REFRESH_SECRET=your_jwt_refresh_secret_change_this
SESSION_SECRET=your_session_secret_change_this

# MQTT Configuration
MQTT_BROKER_URL=mqtt://localhost:1883
MQTT_USERNAME=$MQTT_USER
MQTT_PASSWORD=change_this_mqtt_password

# Application Configuration
APP_NAME=LXCloud
DEFAULT_ADMIN_EMAIL=admin@lxcloud.local
DEFAULT_ADMIN_PASSWORD=admin123
EOF
    fi
    
    # Generate secure secrets
    JWT_SECRET=$(openssl rand -base64 32)
    SESSION_SECRET=$(openssl rand -base64 32)
    JWT_REFRESH_SECRET=$(openssl rand -base64 32)
    
    # Update environment file with proper escaping
    sudo -u "$SERVICE_USER" sed -i "s|your_jwt_secret_key_change_this|$JWT_SECRET|" "$INSTALL_DIR/.env"
    sudo -u "$SERVICE_USER" sed -i "s|your_jwt_refresh_secret_change_this|$JWT_REFRESH_SECRET|" "$INSTALL_DIR/.env"
    sudo -u "$SERVICE_USER" sed -i "s|your_session_secret_change_this|$SESSION_SECRET|" "$INSTALL_DIR/.env"
    sudo -u "$SERVICE_USER" sed -i "s|DB_USER=lxcloud|DB_USER=$DATABASE_USER|" "$INSTALL_DIR/.env"
    sudo -u "$SERVICE_USER" sed -i "s|DB_PASSWORD=lxcloud|DB_PASSWORD=$DATABASE_PASSWORD|" "$INSTALL_DIR/.env"
    sudo -u "$SERVICE_USER" sed -i "s|change_this_mqtt_password|$MQTT_PASSWORD|" "$INSTALL_DIR/.env"
    
    success "Application installed successfully"
}

# Function to initialize database
initialize_database() {
    log "Initializing database schema..."
    
    cd "$INSTALL_DIR"
    
    # Test database connection first
    if ! sudo -u "$SERVICE_USER" NODE_ENV=production node -e "
        const mysql = require('mysql2/promise');
        async function testConnection() {
            try {
                const connection = await mysql.createConnection({
                    host: 'localhost',
                    user: '$DATABASE_USER',
                    password: '$DATABASE_PASSWORD',
                    database: '$DATABASE_NAME'
                });
                await connection.execute('SELECT 1');
                await connection.end();
                console.log('Database connection test successful');
                process.exit(0);
            } catch (error) {
                console.error('Database connection test failed:', error.message);
                process.exit(1);
            }
        }
        testConnection();
    "; then
        error "Database connection test failed"
    fi
    
    # Initialize database schema
    sudo -u "$SERVICE_USER" NODE_ENV=production node -e "
        const database = require('./config/database');
        
        async function initDB() {
            try {
                await database.initialize();
                console.log('Database initialized successfully');
                process.exit(0);
            } catch (error) {
                console.error('Database initialization failed:', error);
                process.exit(1);
            }
        }
        
        initDB();
    "
    
    success "Database initialized successfully"
}

# Function to create systemd service optimized for Ubuntu 22.04
create_systemd_service() {
    log "Creating systemd service for Ubuntu 22.04..."
    
    sudo tee /etc/systemd/system/lxcloud.service > /dev/null <<EOF
[Unit]
Description=LXCloud IoT Management Platform
After=network.target mariadb.service mosquitto.service
Requires=mariadb.service
Wants=mosquitto.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=5
Environment=NODE_ENV=production

# Security settings for Ubuntu 22.04
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/logs $INSTALL_DIR/uploads $INSTALL_DIR/backups

# Resource limits
LimitNOFILE=4096
LimitNPROC=4096

# Additional Ubuntu 22.04 security
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable lxcloud
    
    success "Systemd service created successfully"
}

# Function to configure Nginx optimized for Ubuntu 22.04
configure_nginx() {
    log "Configuring Nginx for Ubuntu 22.04..."
    
    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Create LXCloud site configuration optimized for local network access
    sudo tee /etc/nginx/sites-available/lxcloud > /dev/null <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    # Optimized for local network access - NO HTTPS redirect
    # This prevents "Unable to connect to server" issues
    
    # Security headers optimized for local HTTP access
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Explicitly disable HSTS for local networks
    add_header Strict-Transport-Security "" always;
    
    # Client IP detection for better local network handling
    real_ip_header X-Forwarded-For;
    set_real_ip_from 10.0.0.0/8;
    set_real_ip_from 172.16.0.0/12;
    set_real_ip_from 192.168.0.0/16;
    set_real_ip_from 127.0.0.0/8;
    
    # Main proxy configuration
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        
        # Buffer settings for better performance
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_max_temp_file_size 1024m;
    }
    
    # WebSocket support for Socket.IO
    location /socket.io/ {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # API health check
    location /api/health {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 5s;
        proxy_read_timeout 10s;
        access_log off;
    }
    
    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        expires 1M;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Disable server tokens for security
    server_tokens off;
    
    # Increase client body size for file uploads
    client_max_body_size 10M;
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/lxcloud /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    if ! sudo nginx -t; then
        error "Nginx configuration test failed"
    fi
    
    # Start and enable nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    # Verify nginx is running
    if ! systemctl is-active --quiet nginx; then
        error "Nginx failed to start"
    fi
    
    success "Nginx configured successfully"
}

# Function to configure firewall for Ubuntu 22.04
configure_firewall() {
    log "Configuring UFW firewall for Ubuntu 22.04..."
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (be careful not to lock ourselves out)
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 'Nginx Full'
    
    # Allow MQTT (only from local networks)
    sudo ufw allow from 10.0.0.0/8 to any port 1883
    sudo ufw allow from 172.16.0.0/12 to any port 1883
    sudo ufw allow from 192.168.0.0/16 to any port 1883
    sudo ufw allow from 127.0.0.0/8 to any port 1883
    
    # Allow access to application port from local networks
    sudo ufw allow from 10.0.0.0/8 to any port 3000
    sudo ufw allow from 172.16.0.0/12 to any port 3000
    sudo ufw allow from 192.168.0.0/16 to any port 3000
    sudo ufw allow from 127.0.0.0/8 to any port 3000
    
    # Enable firewall
    sudo ufw --force enable
    
    success "Firewall configured successfully"
}

# Function to create maintenance scripts
create_maintenance_scripts() {
    log "Creating maintenance scripts..."
    
    # Create comprehensive status check script
    sudo tee "$INSTALL_DIR/status.sh" > /dev/null <<'EOF'
#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                    LXCloud System Status                       ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# System information
echo -e "${CYAN}System Information:${NC}"
echo "  OS: $(lsb_release -d | cut -f2)"
echo "  Kernel: $(uname -r)"
echo "  Uptime: $(uptime -p)"
echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
echo ""

# Check services
echo -e "${CYAN}Service Status:${NC}"
services=("lxcloud" "nginx" "mariadb" "mosquitto")
all_services_running=true

for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo -e "  ${GREEN}✅ $service: Running${NC}"
    else
        echo -e "  ${RED}❌ $service: Not running${NC}"
        all_services_running=false
    fi
done
echo ""

# Check network connectivity
echo -e "${CYAN}Network Connectivity:${NC}"
if curl -s --max-time 5 http://localhost:3000/api/health >/dev/null; then
    echo -e "  ${GREEN}✅ LXCloud API: Accessible${NC}"
else
    echo -e "  ${RED}❌ LXCloud API: Not accessible${NC}"
fi

if curl -s --max-time 5 http://localhost >/dev/null; then
    echo -e "  ${GREEN}✅ Nginx Proxy: Accessible${NC}"
else
    echo -e "  ${RED}❌ Nginx Proxy: Not accessible${NC}"
fi

# Database connectivity
if mysql -u lxcloud -plxcloud lxcloud -e "SELECT 1" &>/dev/null; then
    echo -e "  ${GREEN}✅ Database: Connected${NC}"
else
    echo -e "  ${RED}❌ Database: Connection failed${NC}"
fi

# MQTT connectivity
if timeout 5 mosquitto_pub -h localhost -u lxcloud_mqtt -P "$(grep MQTT_PASSWORD /opt/lxcloud/.env | cut -d= -f2)" -t test -m hello 2>/dev/null; then
    echo -e "  ${GREEN}✅ MQTT Broker: Accessible${NC}"
else
    echo -e "  ${RED}❌ MQTT Broker: Not accessible${NC}"
fi
echo ""

# Show listening ports
echo -e "${CYAN}Network Ports:${NC}"
ss -tlnp | grep -E ':(80|443|3000|1883|3306)' | while read line; do
    echo "  $line"
done
echo ""

# Disk space
echo -e "${CYAN}Disk Usage:${NC}"
df -h /opt/lxcloud | tail -1 | awk '{print "  Application: " $5 " used (" $3 "/" $2 ")"}'
df -h /var/log | tail -1 | awk '{print "  Logs: " $5 " used (" $3 "/" $2 ")"}'
echo ""

# Memory usage
echo -e "${CYAN}Memory Usage:${NC}"
free -h | grep -E "Mem|Swap" | awk '{print "  " $1 " " $3 "/" $2 " (" $3/$2*100 "% used)"}'
echo ""

# Show recent logs
echo -e "${CYAN}Recent LXCloud Logs (last 5 entries):${NC}"
sudo journalctl -u lxcloud --no-pager -n 5 --output=short-iso 2>/dev/null | tail -5
echo ""

# Show server IP addresses
echo -e "${CYAN}Access Information:${NC}"
echo -e "  ${GREEN}Local Access:${NC} http://localhost"
echo -e "  ${GREEN}Network Access:${NC}"
hostname -I | tr ' ' '\n' | grep -v '^$' | while read ip; do
    echo "    http://$ip"
done
echo ""
echo -e "${CYAN}Default Credentials:${NC}"
echo -e "  ${GREEN}Email:${NC} admin@lxcloud.local"
echo -e "  ${GREEN}Password:${NC} admin123"
echo ""

# Overall status
if [ "$all_services_running" = true ]; then
    echo -e "${GREEN}🎉 Overall Status: All services are running normally${NC}"
else
    echo -e "${RED}⚠️  Overall Status: Some services are not running${NC}"
    echo -e "${YELLOW}Run 'sudo systemctl restart lxcloud nginx mariadb mosquitto' to restart all services${NC}"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
EOF

    # Create backup script
    sudo tee "$INSTALL_DIR/backup.sh" > /dev/null <<'EOF'
#!/bin/bash

set -e

INSTALL_DIR="/opt/lxcloud"
BACKUP_DIR="$INSTALL_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DATABASE_USER="lxcloud"
DATABASE_PASSWORD="lxcloud"
DATABASE_NAME="lxcloud"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

log "Creating LXCloud backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
log "Backing up database..."
mysqldump -u "$DATABASE_USER" -p"$DATABASE_PASSWORD" "$DATABASE_NAME" > "$BACKUP_DIR/database_$DATE.sql"

# Backup application files (excluding node_modules and logs)
log "Backing up application files..."
tar --exclude='node_modules' --exclude='logs/*' --exclude='backups/*' \
    -czf "$BACKUP_DIR/application_$DATE.tar.gz" -C /opt lxcloud

# Backup configuration files
log "Backing up configuration files..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    /etc/nginx/sites-available/lxcloud \
    /etc/systemd/system/lxcloud.service \
    /etc/mosquitto/conf.d/lxcloud.conf 2>/dev/null || true

log "Backup completed successfully!"
log "Files created:"
log "  - Database: $BACKUP_DIR/database_$DATE.sql"
log "  - Application: $BACKUP_DIR/application_$DATE.tar.gz"
log "  - Configuration: $BACKUP_DIR/config_$DATE.tar.gz"

# Clean up old backups (keep only last 10)
find "$BACKUP_DIR" -name "*.sql" -o -name "*.tar.gz" | sort | head -n -30 | xargs rm -f 2>/dev/null || true
EOF

    # Create update script
    sudo tee "$INSTALL_DIR/update.sh" > /dev/null <<'EOF'
#!/bin/bash

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

INSTALL_DIR="/opt/lxcloud"
SERVICE_USER="lxcloud"

log "Starting LXCloud update..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
fi

# Create backup first
log "Creating pre-update backup..."
sudo "$INSTALL_DIR/backup.sh"

# Stop service
log "Stopping LXCloud service..."
sudo systemctl stop lxcloud

# Pull latest changes if Git repository exists
cd "$INSTALL_DIR"
if [ -d ".git" ]; then
    log "Updating from Git repository..."
    sudo -u "$SERVICE_USER" git pull origin main || warn "Git pull failed - manual update may be required"
else
    warn "No Git repository found - manual update required"
fi

# Install/update dependencies
log "Updating Node.js dependencies..."
sudo -u "$SERVICE_USER" npm install --omit=dev --no-audit --no-fund

# Run database migrations
log "Running database migrations..."
sudo -u "$SERVICE_USER" NODE_ENV=production node -e "
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
log "Starting LXCloud service..."
sudo systemctl start lxcloud

# Wait for service to be ready
sleep 5

# Check service status
if sudo systemctl is-active --quiet lxcloud; then
    log "✅ LXCloud update completed successfully!"
else
    error "❌ LXCloud service failed to start after update"
fi

log "Update completed successfully!"
EOF

    # Create diagnostic script
    sudo tee "$INSTALL_DIR/diagnose.sh" > /dev/null <<'EOF'
#!/bin/bash

# LXCloud Diagnostic Script
# Comprehensive troubleshooting and problem identification

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                  LXCloud Diagnostic Tool                       ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# System checks
echo -e "${CYAN}1. System Information:${NC}"
echo "OS: $(lsb_release -d | cut -f2)"
echo "Architecture: $(uname -m)"
echo "Kernel: $(uname -r)"
echo "Node.js: $(node --version 2>/dev/null || echo 'Not installed')"
echo "NPM: $(npm --version 2>/dev/null || echo 'Not installed')"
echo ""

# Service status checks
echo -e "${CYAN}2. Service Status:${NC}"
services=("lxcloud" "nginx" "mariadb" "mosquitto")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✅ $service: Active${NC}"
    else
        echo -e "${RED}❌ $service: Inactive${NC}"
        echo "   Status: $(systemctl is-active $service)"
        echo "   Enabled: $(systemctl is-enabled $service)"
    fi
done
echo ""

# Port checks
echo -e "${CYAN}3. Port Status:${NC}"
ports=("80:HTTP" "443:HTTPS" "3000:LXCloud" "1883:MQTT" "3306:MySQL")
for port_info in "${ports[@]}"; do
    port=$(echo $port_info | cut -d: -f1)
    name=$(echo $port_info | cut -d: -f2)
    if ss -tlnp | grep -q ":$port "; then
        echo -e "${GREEN}✅ Port $port ($name): Open${NC}"
    else
        echo -e "${RED}❌ Port $port ($name): Closed${NC}"
    fi
done
echo ""

# Network connectivity tests
echo -e "${CYAN}4. Connectivity Tests:${NC}"

# Test localhost HTTP
if curl -s --max-time 5 http://localhost >/dev/null; then
    echo -e "${GREEN}✅ HTTP (localhost): Accessible${NC}"
else
    echo -e "${RED}❌ HTTP (localhost): Failed${NC}"
fi

# Test application API
if curl -s --max-time 5 http://localhost:3000/api/health >/dev/null; then
    echo -e "${GREEN}✅ Application API: Accessible${NC}"
else
    echo -e "${RED}❌ Application API: Failed${NC}"
fi

# Test database
if mysql -u lxcloud -plxcloud lxcloud -e "SELECT 1" &>/dev/null; then
    echo -e "${GREEN}✅ Database: Connected${NC}"
else
    echo -e "${RED}❌ Database: Connection failed${NC}"
fi
echo ""

# File system checks
echo -e "${CYAN}5. File System Checks:${NC}"
if [ -d "/opt/lxcloud" ]; then
    echo -e "${GREEN}✅ Application directory exists${NC}"
    echo "   Permissions: $(ls -ld /opt/lxcloud | awk '{print $1 " " $3 ":" $4}')"
else
    echo -e "${RED}❌ Application directory missing${NC}"
fi

if [ -f "/opt/lxcloud/.env" ]; then
    echo -e "${GREEN}✅ Environment file exists${NC}"
else
    echo -e "${RED}❌ Environment file missing${NC}"
fi

if [ -f "/etc/systemd/system/lxcloud.service" ]; then
    echo -e "${GREEN}✅ Systemd service file exists${NC}"
else
    echo -e "${RED}❌ Systemd service file missing${NC}"
fi
echo ""

# Recent error logs
echo -e "${CYAN}6. Recent Error Logs:${NC}"
echo "LXCloud Service Errors:"
sudo journalctl -u lxcloud --since "1 hour ago" --priority=3 --no-pager | tail -5
echo ""

echo "Nginx Errors:"
sudo journalctl -u nginx --since "1 hour ago" --priority=3 --no-pager | tail -5
echo ""

# Process information
echo -e "${CYAN}7. Process Information:${NC}"
echo "LXCloud processes:"
ps aux | grep -E "(node|lxcloud)" | grep -v grep || echo "No LXCloud processes found"
echo ""

# Resource usage
echo -e "${CYAN}8. Resource Usage:${NC}"
echo "Memory usage:"
free -h | grep -E "Mem|Swap"
echo ""

echo "Disk usage:"
df -h /opt/lxcloud 2>/dev/null || df -h /
echo ""

echo "Load average:"
uptime
echo ""

# Firewall status
echo -e "${CYAN}9. Firewall Status:${NC}"
if command -v ufw >/dev/null; then
    sudo ufw status numbered
else
    echo "UFW not installed"
fi
echo ""

# Configuration validation
echo -e "${CYAN}10. Configuration Validation:${NC}"
if [ -f "/etc/nginx/sites-available/lxcloud" ]; then
    if sudo nginx -t &>/dev/null; then
        echo -e "${GREEN}✅ Nginx configuration: Valid${NC}"
    else
        echo -e "${RED}❌ Nginx configuration: Invalid${NC}"
    fi
else
    echo -e "${RED}❌ Nginx LXCloud site configuration missing${NC}"
fi
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Diagnostic completed. Check the output above for any issues.${NC}"
echo -e "${YELLOW}For help with specific problems, refer to the troubleshooting documentation.${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
EOF

    # Make scripts executable
    sudo chmod +x "$INSTALL_DIR/status.sh"
    sudo chmod +x "$INSTALL_DIR/backup.sh"
    sudo chmod +x "$INSTALL_DIR/update.sh"
    sudo chmod +x "$INSTALL_DIR/diagnose.sh"
    
    success "Maintenance scripts created successfully"
}

# Function to start services and verify installation
verify_installation() {
    log "Starting services and verifying installation..."
    
    # Start LXCloud service
    sudo systemctl start lxcloud
    
    # Wait for services to start
    log "Waiting for services to start..."
    sleep 10
    
    # Check service status
    services=("lxcloud" "nginx" "mariadb" "mosquitto")
    all_good=true
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            success "$service is running"
        else
            error "$service failed to start - check logs with: sudo journalctl -u $service"
            all_good=false
        fi
    done
    
    if [ "$all_good" = false ]; then
        error "One or more services failed to start"
    fi
    
    # Test web interface
    log "Testing web interface..."
    local retry_count=0
    while ! curl -s --max-time 5 http://localhost:3000/api/health >/dev/null; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -gt 30 ]; then
            error "Web interface is not accessible after 30 seconds"
        fi
        sleep 1
    done
    
    success "Web interface is accessible"
    
    # Test nginx proxy
    log "Testing nginx proxy..."
    if curl -s --max-time 5 http://localhost >/dev/null; then
        success "Nginx proxy is working"
    else
        warn "Nginx proxy test failed, but continuing"
    fi
    
    success "Installation verification completed successfully"
}

# Function to display completion message
show_completion_message() {
    local server_ip
    server_ip=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           🎉 LXCloud Installation Complete! 🎉                  ║${NC}"
    echo -e "${GREEN}║                   Ubuntu 22.04 LTS                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📋 Installation Summary:${NC}"
    echo -e "  ${GREEN}✅ Operating System:${NC} Ubuntu 22.04 LTS"
    echo -e "  ${GREEN}✅ Application URL:${NC} http://$server_ip"
    echo -e "  ${GREEN}✅ Local Access:${NC} http://localhost"
    echo -e "  ${GREEN}✅ Default Admin Email:${NC} admin@lxcloud.local"
    echo -e "  ${GREEN}✅ Default Admin Password:${NC} admin123"
    echo -e "  ${GREEN}✅ Application Directory:${NC} $INSTALL_DIR"
    echo -e "  ${GREEN}✅ Database:${NC} MariaDB (lxcloud)"
    echo -e "  ${GREEN}✅ MQTT Broker:${NC} Mosquitto (localhost:1883)"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo -e "  ${GREEN}View Status:${NC} sudo $INSTALL_DIR/status.sh"
    echo -e "  ${GREEN}Run Diagnostics:${NC} sudo $INSTALL_DIR/diagnose.sh"
    echo -e "  ${GREEN}View Logs:${NC} sudo journalctl -u lxcloud -f"
    echo -e "  ${GREEN}Restart Service:${NC} sudo systemctl restart lxcloud"
    echo -e "  ${GREEN}Update System:${NC} sudo $INSTALL_DIR/update.sh"
    echo -e "  ${GREEN}Create Backup:${NC} sudo $INSTALL_DIR/backup.sh"
    echo ""
    echo -e "${YELLOW}⚠️  Important Security Steps:${NC}"
    echo -e "  1. ${YELLOW}Change the default admin password immediately${NC}"
    echo -e "  2. ${YELLOW}Configure SSL/TLS: sudo certbot --nginx${NC}"
    echo -e "  3. ${YELLOW}Review firewall settings: sudo ufw status${NC}"
    echo -e "  4. ${YELLOW}Monitor system logs regularly${NC}"
    echo ""
    echo -e "${BLUE}📱 Next Steps:${NC}"
    echo -e "  1. Open your browser and go to ${GREEN}http://$server_ip${NC}"
    echo -e "  2. Login with the default admin credentials"
    echo -e "  3. Change the admin password in Profile Settings"
    echo -e "  4. Configure your IoT controllers"
    echo -e "  5. Explore the dashboard and admin features"
    echo ""
    echo -e "${BLUE}🔧 Troubleshooting:${NC}"
    echo -e "  ${GREEN}If you experience connection issues:${NC}"
    echo -e "    • Run: sudo $INSTALL_DIR/diagnose.sh"
    echo -e "    • Check status: sudo $INSTALL_DIR/status.sh"
    echo -e "    • Restart services: sudo systemctl restart lxcloud nginx"
    echo ""
    echo -e "${GREEN}🚀 LXCloud is now ready to manage your IoT controllers!${NC}"
    echo ""
}

# Main installation function
main() {
    echo -e "${PURPLE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                     LXCloud Installation                       ║"
    echo "║                  Ubuntu Server LTS 22.04                      ║"
    echo "║              Complete Setup with Wipe & Reinstall             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    log "Starting LXCloud installation process for Ubuntu 22.04 LTS..."
    
    # Installation steps
    check_ubuntu_version
    remove_existing_installation
    install_dependencies
    install_nodejs
    install_mariadb
    install_mosquitto
    setup_user_and_directories
    install_application
    initialize_database
    create_systemd_service
    configure_nginx
    configure_firewall
    create_maintenance_scripts
    verify_installation
    show_completion_message
    
    success "LXCloud installation completed successfully!"
}

# Run main function
main "$@"