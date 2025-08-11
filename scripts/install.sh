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

# Install required packages
echo -e "${BLUE}Installing required packages...${NC}"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    mariadb-server \
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

# Setup Python virtual environment
echo -e "${BLUE}Setting up Python virtual environment...${NC}"
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Configure MariaDB
echo -e "${BLUE}Configuring MariaDB...${NC}"
mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Configure Mosquitto MQTT
echo -e "${BLUE}Configuring Mosquitto MQTT...${NC}"
cat > /etc/mosquitto/conf.d/lxcloud.conf << EOF
# LXCloud MQTT Configuration
listener 1883 0.0.0.0
allow_anonymous true
log_type all
log_dest file /var/log/mosquitto/mosquitto.log
EOF

systemctl restart mosquitto
systemctl enable mosquitto

# Create environment file
echo -e "${BLUE}Creating environment configuration...${NC}"
cat > "$INSTALL_DIR/.env" << EOF
# Database Configuration
DB_HOST=localhost
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME

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

# Initialize database
echo -e "${BLUE}Initializing database...${NC}"
cd "$INSTALL_DIR"
sudo -u "$SERVICE_USER" -H bash -c "source venv/bin/activate && python -c 'from app import create_app; create_app()'"

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
echo
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  Check status: ${GREEN}systemctl status lxcloud${NC}"
echo -e "  View logs:    ${GREEN}journalctl -u lxcloud -f${NC}"
echo -e "  Restart:      ${GREEN}systemctl restart lxcloud${NC}"
echo
echo -e "${BLUE}MQTT Broker:${NC} localhost:1883"
echo -e "${BLUE}Log files:${NC} /var/log/lxcloud/"
echo