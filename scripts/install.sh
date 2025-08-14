#!/bin/bash

# LXCloud Installation Script for Ubuntu 22.04 LTS
# This script will install and configure LXCloud platform

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
DB_NAME="lxcloud"
DB_USER="lxcloud"
DB_PASSWORD=$(openssl rand -base64 32)

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  LXCloud Installation Script   ${NC}"
echo -e "${BLUE}    Ubuntu 22.04 LTS Only       ${NC}"
echo -e "${BLUE}================================${NC}"
echo

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Check Ubuntu version
if ! grep -q "22.04" /etc/os-release; then
    echo -e "${YELLOW}Warning: This script is designed for Ubuntu 22.04 LTS${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}Starting LXCloud installation...${NC}"

# Update system
echo -e "${BLUE}Updating system packages...${NC}"
apt update && apt upgrade -y

# Install required packages (excluding MariaDB - handled by database_install.sh)
echo -e "${BLUE}Installing required packages...${NC}"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    mosquitto \
    mosquitto-clients \
    nginx \
    git \
    curl \
    wget \
    supervisor \
    openssl \
    ufw

# Create system user
echo -e "${BLUE}Creating system user...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --home "$INSTALL_DIR" --shell /bin/bash "$SERVICE_USER"
fi

# Create installation directory
echo -e "${BLUE}Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Copy application files
echo -e "${BLUE}Copying application files...${NC}"
cp -r . "$INSTALL_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Make database installation script executable
if [[ -f "$INSTALL_DIR/database_install.sh" ]]; then
    chmod +x "$INSTALL_DIR/database_install.sh"
fi

# Verify critical files were copied correctly
echo -e "${BLUE}Verifying installation...${NC}"
CRITICAL_FILES=(
    "app/__init__.py"
    "templates/auth/login.html"
    "templates/auth/register.html"
    "templates/base.html"
    "run.py"
    "requirements.txt"
)

MISSING_FILES=()
for file in "${CRITICAL_FILES[@]}"; do
    if [[ ! -f "$INSTALL_DIR/$file" ]]; then
        MISSING_FILES+=("$file")
    fi
done

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    echo -e "${RED}ERROR: Critical files are missing after installation:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo -e "${RED}  - $file${NC}"
    done
    echo -e "${RED}Installation failed. Please check source directory and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All critical files verified successfully${NC}"

# Setup Python virtual environment
echo -e "${BLUE}Setting up Python virtual environment...${NC}"
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Install and configure MariaDB using the database installation script
echo -e "${BLUE}Installing and configuring MariaDB...${NC}"
if [[ -f "$INSTALL_DIR/database_install.sh" ]]; then
    # Use the comprehensive database installation script
    chmod +x "$INSTALL_DIR/database_install.sh"
    "$INSTALL_DIR/database_install.sh" --db-name "$DB_NAME" --db-user "$DB_USER" --db-password "$DB_PASSWORD"
else
    # Fallback to manual MariaDB configuration if script not found
    echo -e "${YELLOW}database_install.sh not found, using fallback configuration...${NC}"
    mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
    mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"
fi

# Configure Mosquitto MQTT
echo -e "${BLUE}Configuring Mosquitto MQTT...${NC}"
cat > /etc/mosquitto/conf.d/lxcloud.conf << EOF
# LXCloud MQTT Configuration
listener 1883 0.0.0.0
allow_anonymous true
log_type all
EOF

systemctl restart mosquitto
systemctl enable mosquitto

# Create database configuration file
echo -e "${BLUE}Creating database configuration...${NC}"
cat > "$INSTALL_DIR/database.conf" << EOF
[database]
host = localhost
port = 3306
user = $DB_USER
password = $DB_PASSWORD
database = $DB_NAME
charset = utf8mb4
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/database.conf"
chmod 600 "$INSTALL_DIR/database.conf"

# Create environment file (for non-database configurations)
echo -e "${BLUE}Creating environment configuration...${NC}"
cat > "$INSTALL_DIR/.env" << EOF
# MQTT Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC_PREFIX=lxcloud

# Security
SECRET_KEY=$(openssl rand -base64 32)

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
chmod 600 "$INSTALL_DIR/.env"

# Create systemd service
echo -e "${BLUE}Creating systemd service...${NC}"
cat > /etc/systemd/system/lxcloud.service << EOF
[Unit]
Description=LXCloud Platform
After=network.target mariadb.service mosquitto.service
Wants=mariadb.service mosquitto.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create supervisor configuration (alternative to systemd)
echo -e "${BLUE}Creating supervisor configuration...${NC}"
cat > /etc/supervisor/conf.d/lxcloud.conf << EOF
[program:lxcloud]
command=$INSTALL_DIR/venv/bin/python run.py
directory=$INSTALL_DIR
user=$SERVICE_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/lxcloud.log
EOF

# Configure Nginx
echo -e "${BLUE}Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/lxcloud << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /static {
        alias $INSTALL_DIR/static;
        expires 1d;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/lxcloud /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
systemctl enable nginx

# Configure firewall
echo -e "${BLUE}Configuring firewall...${NC}"
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 1883/tcp # MQTT

# Create log directory
mkdir -p /var/log/lxcloud
chown "$SERVICE_USER:$SERVICE_USER" /var/log/lxcloud

# Initialize database using the database utilities
echo -e "${BLUE}Initializing database schema...${NC}"
cd "$INSTALL_DIR"
if [[ -f "database_utils.py" ]]; then
    # Use the database utilities for initialization
    sudo -u "$SERVICE_USER" -H bash -c "source venv/bin/activate && python database_utils.py init"
else
    # Fallback to manual initialization
    sudo -u "$SERVICE_USER" -H bash -c "source venv/bin/activate && python -c 'from app import create_app; create_app()'"
fi

# Start services
echo -e "${BLUE}Starting services...${NC}"
systemctl daemon-reload
systemctl enable lxcloud
systemctl start lxcloud

# Wait for service to start
sleep 5

# Check service status
if systemctl is-active --quiet lxcloud; then
    echo -e "${GREEN}✓ LXCloud service is running${NC}"
else
    echo -e "${RED}✗ LXCloud service failed to start${NC}"
    systemctl status lxcloud
fi

# Installation complete
echo
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}   Installation Complete!       ${NC}"
echo -e "${GREEN}================================${NC}"
echo
echo -e "${BLUE}LXCloud has been installed to: ${NC}$INSTALL_DIR"
echo -e "${BLUE}Access the web interface at: ${NC}http://your-server-ip/"
echo
echo -e "${BLUE}Default admin credentials:${NC}"
echo -e "  Username: ${GREEN}admin${NC}"
echo -e "  Password: ${GREEN}admin123${NC}"
echo
echo -e "${YELLOW}⚠️  Please change the default admin password after first login!${NC}"
echo
echo -e "${BLUE}Database credentials:${NC}"
echo -e "  Database: $DB_NAME"
echo -e "  Username: $DB_USER"
echo -e "  Password: $DB_PASSWORD"
echo -e "  Config file: ${GREEN}$INSTALL_DIR/database.conf${NC}"
echo
echo -e "${BLUE}Database management:${NC}"
echo -e "  Test connection: ${GREEN}cd $INSTALL_DIR && python database_utils.py test${NC}"
echo -e "  Show config:     ${GREEN}cd $INSTALL_DIR && python database_utils.py config${NC}"
echo -e "  Create backup:   ${GREEN}cd $INSTALL_DIR && python database_utils.py backup${NC}"
echo
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  Check status: ${GREEN}systemctl status lxcloud${NC}"
echo -e "  View logs:    ${GREEN}journalctl -u lxcloud -f${NC}"
echo -e "  Restart:      ${GREEN}systemctl restart lxcloud${NC}"
echo
echo -e "${BLUE}MQTT Broker:${NC} localhost:1883"
echo -e "${BLUE}Log files:${NC} /var/log/lxcloud/"
echo