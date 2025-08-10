#!/bin/bash

# LXCloud Complete Installation Script
# This script completely removes any previous installation and performs a fresh setup
# Designed for Ubuntu Server LTS 24.04

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
INSTALL_DIR="/opt/LXCloud_2025"
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

# Check Ubuntu version
if ! grep -q "Ubuntu" /etc/os-release; then
    warn "This script is designed for Ubuntu. Continuing anyway..."
fi

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

# Function to install Node.js
install_nodejs() {
    log "Installing Node.js 18.x..."
    
    # Remove any existing Node.js
    sudo apt remove -y nodejs npm node 2>/dev/null || true
    
    # Install Node.js 18.x
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    # Verify installation
    node_version=$(node --version)
    npm_version=$(npm --version)
    log "Node.js version: $node_version"
    log "NPM version: $npm_version"
    
    # Ensure npm is up to date
    sudo npm install -g npm@latest
}

# Function to install and configure MariaDB
install_mariadb() {
    log "Installing and configuring MariaDB..."
    
    # Remove any existing MySQL/MariaDB
    sudo systemctl stop mysql mariadb 2>/dev/null || true
    sudo apt remove -y mysql-server mysql-client mariadb-server mariadb-client 2>/dev/null || true
    
    # Install MariaDB
    sudo apt update
    sudo DEBIAN_FRONTEND=noninteractive apt install -y mariadb-server mariadb-client
    
    # Start MariaDB
    sudo systemctl start mariadb
    sudo systemctl enable mariadb
    
    # Wait for MariaDB to be ready
    log "Waiting for MariaDB to start..."
    for i in {1..30}; do
        if sudo mysql -e "SELECT 1" &>/dev/null; then
            break
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
        CREATE DATABASE IF NOT EXISTS $DATABASE_NAME;
        CREATE USER IF NOT EXISTS '$DATABASE_USER'@'localhost' IDENTIFIED BY '$DATABASE_PASSWORD';
        GRANT ALL PRIVILEGES ON $DATABASE_NAME.* TO '$DATABASE_USER'@'localhost';
        
        FLUSH PRIVILEGES;
    "
    
    success "MariaDB installed and configured successfully"
}

# Function to install and configure Mosquitto MQTT
install_mosquitto() {
    log "Installing and configuring Mosquitto MQTT..."
    
    # Remove any existing Mosquitto
    sudo systemctl stop mosquitto 2>/dev/null || true
    sudo apt remove -y mosquitto mosquitto-clients 2>/dev/null || true
    
    # Install Mosquitto
    sudo apt install -y mosquitto mosquitto-clients
    
    # Create MQTT configuration
    sudo tee /etc/mosquitto/conf.d/lxcloud.conf > /dev/null <<EOF
# LXCloud MQTT Configuration
listener 1883 localhost
allow_anonymous false
password_file /etc/mosquitto/passwd

# Persistence
persistence true
persistence_location /var/lib/mosquitto/

# Logging
log_type error
log_type warning
log_type notice
log_type information
log_dest file /var/log/mosquitto/mosquitto.log

# Security
max_connections 1000
max_inflight_messages 20
max_queued_messages 100

# Connection settings
keepalive_interval 60
retry_interval 20
sys_interval 10
EOF

    # Create MQTT user and password file
    sudo mosquitto_passwd -c -b /etc/mosquitto/passwd "$MQTT_USER" "$MQTT_PASSWORD"
    sudo chown mosquitto:mosquitto /etc/mosquitto/passwd
    sudo chmod 600 /etc/mosquitto/passwd
    
    # Ensure log directory exists
    sudo mkdir -p /var/log/mosquitto
    sudo chown mosquitto:mosquitto /var/log/mosquitto
    
    # Start and enable Mosquitto
    sudo systemctl restart mosquitto
    sudo systemctl enable mosquitto
    
    # Test MQTT connection
    log "Testing MQTT connection..."
    timeout 5 mosquitto_pub -h localhost -u "$MQTT_USER" -P "$MQTT_PASSWORD" -t "lxcloud/test" -m "hello" || warn "MQTT test failed"
    
    success "Mosquitto MQTT installed and configured successfully"
}

# Function to install other dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
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
        lsb-release
    
    success "System dependencies installed successfully"
}

# Function to create system user and directories
setup_user_and_directories() {
    log "Setting up system user and directories..."
    
    # Create system user
    sudo useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER" || true
    
    # Create application directory
    sudo mkdir -p "$INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR/logs"
    sudo mkdir -p "$INSTALL_DIR/uploads"
    sudo mkdir -p "$INSTALL_DIR/backups"
    
    # Set ownership
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
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
    
    # Set correct ownership
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    # Install Node.js dependencies
    log "Installing Node.js dependencies..."
    cd "$INSTALL_DIR"
    sudo -u "$SERVICE_USER" npm install --omit=dev --no-audit --no-fund
    
    # Create environment file
    log "Creating environment configuration..."
    sudo -u "$SERVICE_USER" cp .env.example .env
    
    # Generate secure secrets
    JWT_SECRET=$(openssl rand -base64 32)
    SESSION_SECRET=$(openssl rand -base64 32)
    
    # Update environment file with proper escaping
    sudo -u "$SERVICE_USER" sed -i "s|your_jwt_secret_key_change_this|$JWT_SECRET|" "$INSTALL_DIR/.env"
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

# Function to create systemd service
create_systemd_service() {
    log "Creating systemd service..."
    
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

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/logs $INSTALL_DIR/uploads $INSTALL_DIR/backups

# Resource limits
LimitNOFILE=4096
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable lxcloud
    
    success "Systemd service created successfully"
}

# Function to configure Nginx
configure_nginx() {
    log "Configuring Nginx..."
    
    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Create LXCloud site configuration
    sudo tee /etc/nginx/sites-available/lxcloud > /dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    # Allow HTTP access for local networks (no HTTPS redirect)
    # This prevents the "Unable to connect to server" issue for local users
    
    # Security headers (optimized for local HTTP access)
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
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        
        # Buffer settings for better performance
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
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
        proxy_read_timeout 86400;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        expires 1M;
        add_header Cache-Control "public, immutable";
    }
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
    
    success "Nginx configured successfully"
}

# Function to configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (be careful not to lock ourselves out)
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 'Nginx Full'
    
    # Allow MQTT (only from local network)
    sudo ufw allow from 10.0.0.0/8 to any port 1883
    sudo ufw allow from 172.16.0.0/12 to any port 1883
    sudo ufw allow from 192.168.0.0/16 to any port 1883
    
    # Enable firewall
    sudo ufw --force enable
    
    success "Firewall configured successfully"
}

# Function to create maintenance scripts
create_maintenance_scripts() {
    log "Creating maintenance scripts..."
    
    # Create update script
    sudo tee "$INSTALL_DIR/update.sh" > /dev/null <<'EOF'
#!/bin/bash

set -e

# Colors for output
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

INSTALL_DIR="/opt/LXCloud_2025"
SERVICE_USER="lxcloud"

log "Starting LXCloud update..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
fi

# Stop service
log "Stopping LXCloud service..."
sudo systemctl stop lxcloud

# Backup current installation
BACKUP_DIR="/opt/LXCloud_2025.backup.$(date +%Y%m%d_%H%M%S)"
log "Creating backup at $BACKUP_DIR..."
sudo cp -r "$INSTALL_DIR" "$BACKUP_DIR"

# Pull latest changes
cd "$INSTALL_DIR"
if [ -d ".git" ]; then
    log "Updating from Git repository..."
    sudo -u "$SERVICE_USER" git pull origin main
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

# Clean up old backups (keep only last 5)
log "Cleaning up old backups..."
sudo find /opt -name "LXCloud_2025.backup.*" -type d | sort | head -n -5 | xargs sudo rm -rf 2>/dev/null || true

log "Update completed successfully!"
EOF

    # Create backup script
    sudo tee "$INSTALL_DIR/backup.sh" > /dev/null <<'EOF'
#!/bin/bash

set -e

INSTALL_DIR="/opt/LXCloud_2025"
BACKUP_DIR="$INSTALL_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)

log() {
    echo -e "\033[0;32m[$(date +'%Y-%m-%d %H:%M:%S')] $1\033[0m"
}

error() {
    echo -e "\033[0;31m[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1\033[0m"
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
    -czf "$BACKUP_DIR/application_$DATE.tar.gz" -C /opt LXCloud_2025

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

    # Create status check script
    sudo tee "$INSTALL_DIR/status.sh" > /dev/null <<'EOF'
#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== LXCloud System Status ===${NC}\n"

# Check services
services=("lxcloud" "nginx" "mariadb" "mosquitto")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✅ $service: Running${NC}"
    else
        echo -e "${RED}❌ $service: Not running${NC}"
    fi
done

echo ""

# Check network connectivity
echo -e "${BLUE}Network Status:${NC}"
if curl -s http://localhost:3000/api/health >/dev/null; then
    echo -e "${GREEN}✅ LXCloud API: Accessible${NC}"
else
    echo -e "${RED}❌ LXCloud API: Not accessible${NC}"
fi

if curl -s http://localhost >/dev/null; then
    echo -e "${GREEN}✅ Nginx: Accessible${NC}"
else
    echo -e "${RED}❌ Nginx: Not accessible${NC}"
fi

echo ""

# Show listening ports
echo -e "${BLUE}Listening Ports:${NC}"
ss -tlnp | grep -E ':(80|443|3000|1883|3306)' | while read line; do
    echo "  $line"
done

echo ""

# Show recent logs
echo -e "${BLUE}Recent LXCloud Logs:${NC}"
sudo journalctl -u lxcloud --no-pager -n 5 --output=short

echo ""
echo -e "${BLUE}Access your LXCloud dashboard at: ${GREEN}http://$(hostname -I | awk '{print $1}')${NC}"
echo -e "${BLUE}Default admin credentials: ${GREEN}admin@lxcloud.local / admin123${NC}"
EOF

    # Make scripts executable
    sudo chmod +x "$INSTALL_DIR/update.sh"
    sudo chmod +x "$INSTALL_DIR/backup.sh"
    sudo chmod +x "$INSTALL_DIR/status.sh"
    
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
            error "$service failed to start"
            all_good=false
        fi
    done
    
    if [ "$all_good" = false ]; then
        error "One or more services failed to start"
    fi
    
    # Test web interface
    log "Testing web interface..."
    for i in {1..30}; do
        if curl -s http://localhost:3000/api/health >/dev/null; then
            success "Web interface is accessible"
            break
        fi
        if [ $i -eq 30 ]; then
            error "Web interface is not accessible after 30 seconds"
        fi
        sleep 1
    done
    
    success "Installation verification completed successfully"
}

# Function to display completion message
show_completion_message() {
    local server_ip=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                 🎉 LXCloud Installation Complete! 🎉           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📋 Installation Summary:${NC}"
    echo -e "  ${GREEN}✅ Application URL:${NC} http://$server_ip"
    echo -e "  ${GREEN}✅ Default Admin Email:${NC} admin@lxcloud.local"
    echo -e "  ${GREEN}✅ Default Admin Password:${NC} admin123"
    echo -e "  ${GREEN}✅ Application Directory:${NC} $INSTALL_DIR"
    echo -e "  ${GREEN}✅ Database:${NC} MariaDB (lxcloud)"
    echo -e "  ${GREEN}✅ MQTT Broker:${NC} Mosquitto (localhost:1883)"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo -e "  ${GREEN}View Status:${NC} sudo $INSTALL_DIR/status.sh"
    echo -e "  ${GREEN}View Logs:${NC} sudo journalctl -u lxcloud -f"
    echo -e "  ${GREEN}Restart Service:${NC} sudo systemctl restart lxcloud"
    echo -e "  ${GREEN}Update System:${NC} sudo $INSTALL_DIR/update.sh"
    echo -e "  ${GREEN}Create Backup:${NC} sudo $INSTALL_DIR/backup.sh"
    echo ""
    echo -e "${YELLOW}⚠️  Important Security Steps:${NC}"
    echo -e "  1. ${YELLOW}Change the default admin password immediately${NC}"
    echo -e "  2. ${YELLOW}Configure SSL/TLS with: sudo certbot --nginx${NC}"
    echo -e "  3. ${YELLOW}Review firewall settings: sudo ufw status${NC}"
    echo -e "  4. ${YELLOW}Monitor system logs regularly${NC}"
    echo ""
    echo -e "${BLUE}📱 Next Steps:${NC}"
    echo -e "  1. Open your browser and go to ${GREEN}http://$server_ip${NC}"
    echo -e "  2. Login with the default admin credentials"
    echo -e "  3. Change the admin password in Profile Settings"
    echo -e "  4. Configure your first IoT controller devices"
    echo -e "  5. Explore the admin panel and dashboard features"
    echo ""
    echo -e "${GREEN}🚀 LXCloud is now ready to manage your IoT controllers!${NC}"
    echo ""
}

# Main installation function
main() {
    echo -e "${PURPLE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                     LXCloud Installation                       ║"
    echo "║              Complete Setup with Wipe & Reinstall             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    log "Starting LXCloud installation process..."
    
    # Installation steps
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