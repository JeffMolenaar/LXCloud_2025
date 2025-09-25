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
DB_PASSWORD="lxcloud"

# Optional behaviours (change before running or export as env vars)
# Set INSTALL_MARIADB to "yes" to auto-install MariaDB during install
INSTALL_MARIADB="yes"
# Whether to allow anonymous MQTT connections (set to "false" in prod)
MQTT_ALLOW_ANONYMOUS="false"
# MySQL/MariaDB root credentials (optional). If empty, the script will try socket auth.
MYSQL_ROOT_USER="${MYSQL_ROOT_USER:-root}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-}"

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

# Check Ubuntu version (accept 22.04 and 24.04)
if ! grep -Eq "22.04|24.04" /etc/os-release; then
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

# Install required packages (build deps included)
echo -e "${BLUE}Installing required packages...${NC}"
apt update
apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    pkg-config \
    default-libmysqlclient-dev \
    rsync \
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

# Optionally install MariaDB if requested
if [[ "$INSTALL_MARIADB" == "yes" ]]; then
    echo -e "${BLUE}Installing MariaDB server...${NC}"
    apt install -y mariadb-server
    systemctl enable --now mariadb
fi

if [[ "$INSTALL_MARIADB" == "yes" ]]; then
    echo -e "${BLUE}Creating MariaDB database and user...${NC}"
    # Wait for MariaDB to be ready
    for i in 1 2 3 4 5 6 7 8 9 10; do
        if mysqladmin ping >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # If no MYSQL_ROOT_PASSWORD provided and running interactively, prompt for it.
    if [[ -z "$MYSQL_ROOT_PASSWORD" && -t 0 ]]; then
        echo -n "Enter MariaDB root password (leave empty to use socket auth): "
        read -s MYSQL_ROOT_PASSWORD
        echo
    fi

    # Create database and user (idempotent)
    SQL="CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    SQL+="CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
    SQL+="GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';"
    SQL+="FLUSH PRIVILEGES;"

    # Build auth args for mysql client. If MYSQL_ROOT_PASSWORD is provided, use it.
    MYSQL_AUTH_ARGS=""
    if [[ -n "$MYSQL_ROOT_PASSWORD" ]]; then
        MYSQL_AUTH_ARGS="-p$MYSQL_ROOT_PASSWORD"
    fi

    if ! mysql -u "$MYSQL_ROOT_USER" $MYSQL_AUTH_ARGS -e "$SQL" ; then
        echo -e "${YELLOW}Warning: automatic creation of database/user failed.${NC}"
        echo -e "${YELLOW}Possible reasons:${NC}"
        echo -e "  - MariaDB is not running"
        echo -e "  - The root user requires a password and it was not provided"
        echo -e "  - The provided root credentials are incorrect"
        echo
        echo -e "${BLUE}If your root user requires a password, re-run this script with the environment variable:${NC}"
        echo -e "  ${GREEN}MYSQL_ROOT_PASSWORD='your_root_password' sudo ./scripts/install.sh${NC}"
        echo
        echo -e "${YELLOW}You can also run the following SQL manually as an admin user:${NC}"
        printf '%s
' "$SQL"
    else
        echo -e "${GREEN}✓ Database and user ensured.${NC}"
    fi
fi

# Create system user
echo -e "${BLUE}Creating system user...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --home "$INSTALL_DIR" --shell /bin/bash "$SERVICE_USER"
fi

# Create installation directory
echo -e "${BLUE}Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Determine source directory to copy from (prefer `project` folder)
## Determine source directory to copy from (prefer `project` folder)
# Use the script location to reliably find the repo root even if the script
# is executed from elsewhere or via sudo from a different working directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -d "$REPO_ROOT/project" ]]; then
    INSTALL_SRC="$REPO_ROOT/project"
else
    INSTALL_SRC="$REPO_ROOT"
fi

# Copy application files (use rsync, exclude repo internals)
echo -e "${BLUE}Copying application files from $INSTALL_SRC ...${NC}"
rsync -a --delete --exclude='.git' --exclude='removed' --exclude='archive' "$INSTALL_SRC/" "$INSTALL_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Make database installation script executable
if [[ -f "$INSTALL_DIR/database_install.sh" ]]; then
    chmod +x "$INSTALL_DIR/database_install.sh"
fi

# Verify critical files were copied correctly
echo -e "${BLUE}Verifying installation...${NC}"
CRITICAL_FILES="app/__init__.py
templates/auth/login.html
templates/auth/register.html
templates/base.html
run.py
requirements.txt"

MISSING_FILES=""
while IFS= read -r file; do
    if [[ -n "$file" ]]; then
        if [[ ! -f "$INSTALL_DIR/$file" ]]; then
            MISSING_FILES+="$file"$'\n'
        fi
    fi
done < <(printf '%s\n' "$CRITICAL_FILES")

if [[ -n "$MISSING_FILES" ]]; then
    echo -e "${RED}ERROR: Critical files are missing after installation:${NC}"
    # Print each missing file
    printf "%s" "$MISSING_FILES" | while IFS= read -r mf; do
        echo -e "${RED}  - $mf${NC}"
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

# Database setup - use manual setup script
echo -e "${BLUE}Setting up database connection...${NC}"
if [[ -f "$INSTALL_DIR/database_setup_manual.sh" ]]; then
    # Use the manual database setup script
    chmod +x "$INSTALL_DIR/database_setup_manual.sh"
    cd "$INSTALL_DIR"
    if ! ./database_setup_manual.sh --db-name "$DB_NAME" --db-user "$DB_USER" --db-password "$DB_PASSWORD"; then
        echo -e "${RED}Database connection test failed!${NC}"
        echo -e "${YELLOW}Please complete the manual database setup as shown above, then re-run this script.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Manual database setup script not found. Creating minimal configuration...${NC}"
    # Create basic database configuration files
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
    
    echo -e "${YELLOW}Database configuration created. You will need to set up MariaDB manually.${NC}"
fi

# Configure Mosquitto MQTT
echo -e "${BLUE}Configuring Mosquitto MQTT...${NC}"
cat > /etc/mosquitto/conf.d/lxcloud.conf << EOF
# LXCloud MQTT Configuration
listener 1883 0.0.0.0
allow_anonymous ${MQTT_ALLOW_ANONYMOUS}
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
Environment=PATH=$INSTALL_DIR/venv/bin:$PATH
ExecStart=$INSTALL_DIR/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create supervisor configuration (alternative to systemd)
echo -e "${BLUE}Creating supervisor configuration...${NC}"
mkdir -p /var/log/lxcloud
touch /var/log/lxcloud/lxcloud.log
chown "$SERVICE_USER:$SERVICE_USER" /var/log/lxcloud /var/log/lxcloud/lxcloud.log
cat > /etc/supervisor/conf.d/lxcloud.conf << EOF
[program:lxcloud]
command=$INSTALL_DIR/venv/bin/python run.py
directory=$INSTALL_DIR
user=$SERVICE_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/lxcloud/lxcloud.log
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

# Configure firewall (allow ports before enabling to avoid lockout)
echo -e "${BLUE}Configuring firewall...${NC}"
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 1883/tcp # MQTT
ufw --force enable

# Create log directory
mkdir -p /var/log/lxcloud
touch /var/log/lxcloud/lxcloud.log
chown "$SERVICE_USER:$SERVICE_USER" /var/log/lxcloud /var/log/lxcloud/lxcloud.log

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

## Perform idempotent DB migration to add map_config column if missing
echo -e "${BLUE}Ensuring ui_customization.map_config column exists...${NC}"
if [[ -d "$INSTALL_DIR/venv" ]]; then
    MIGRATE_PY="$INSTALL_DIR/tmp_migrate_map_config.py"
    cat > "$MIGRATE_PY" << 'PY'
import os, sys

# Ensure project directory is on sys.path so 'import app' works
sys.path.insert(0, os.getcwd())

try:
    from app import create_app
    from app.models import db
except Exception as e:
    print('ERROR: could not import app package:', e)
    raise

app = create_app()
with app.app_context():
    conn = db.engine.connect()
    try:
        url = app.config.get('SQLALCHEMY_DATABASE_URI', '') or ''
        if url.startswith('sqlite'):
            res = conn.execute(db.text("PRAGMA table_info(ui_customization)")).fetchall()
            cols = [r[1] for r in res]
            if 'map_config' not in cols:
                conn.execute(db.text("ALTER TABLE ui_customization ADD COLUMN map_config TEXT"))
                print('Added map_config column to ui_customization (sqlite)')
            else:
                print('map_config column already present (sqlite)')
        else:
            try:
                db_name = url.rsplit('/', 1)[-1]
                res = conn.execute(db.text(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = 'ui_customization'"
                ), {"db_name": db_name}).fetchall()
                cols = [r[0] for r in res]
                if 'map_config' not in cols:
                    conn.execute(db.text("ALTER TABLE ui_customization ADD COLUMN map_config TEXT"))
                    print('Added map_config column to ui_customization (mysql)')
                else:
                    print('map_config column already present (mysql)')
            except Exception as e:
                print('Could not determine MySQL schema or perform migration:', e)
    except Exception as e:
        print('Migration check failed or not needed:', e)
    finally:
        conn.close()
PY

    chown "$SERVICE_USER:$SERVICE_USER" "$MIGRATE_PY"
    sudo -u "$SERVICE_USER" -H bash -c "cd '$INSTALL_DIR' && source venv/bin/activate && python $(basename $MIGRATE_PY)"
    rm -f "$MIGRATE_PY"
else
    echo -e "${YELLOW}Warning: virtualenv not found at $INSTALL_DIR/venv; skipping migration step${NC}"
fi

# Start services
echo -e "${BLUE}Starting services...${NC}"
systemctl daemon-reload
systemctl enable lxcloud
systemctl start lxcloud

# Setup debug reporting if git repository and GitHub token available
echo -e "${BLUE}Setting up debug reporting...${NC}"
if [ -d "$INSTALL_DIR/.git" ] && [ -n "$GITHUB_TOKEN" ]; then
    # Create debug pusher systemd service
    cat > /etc/systemd/system/lxcloud-debug-push.service << EOF
[Unit]
Description=LXCloud Debug Report Pusher
After=network.target

[Service]
Type=oneshot
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=GITHUB_TOKEN=$GITHUB_TOKEN
ExecStart=$INSTALL_DIR/venv/bin/python scripts/push_debug_reports.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Create timer for automatic pushes
    cat > /etc/systemd/system/lxcloud-debug-push.timer << EOF
[Unit]
Description=LXCloud Debug Report Pusher Timer
Requires=lxcloud-debug-push.service

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Set permissions and start timer
    systemctl daemon-reload
    systemctl enable lxcloud-debug-push.timer
    systemctl start lxcloud-debug-push.timer
    
    echo -e "${GREEN}✓ Debug reporting configured with automatic daily push at 06:00${NC}"
else
    if [ ! -d "$INSTALL_DIR/.git" ]; then
        echo -e "${YELLOW}! Git repository not found - debug reporting disabled${NC}"
    fi
    if [ -z "$GITHUB_TOKEN" ]; then
        echo -e "${YELLOW}! GITHUB_TOKEN not set - debug reporting disabled${NC}"
        echo -e "${YELLOW}  Set environment variable GITHUB_TOKEN to enable automatic debug reports${NC}"
    fi
fi

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
# Admin credentials are not printed to stdout for security.
echo
echo -e "${BLUE}Admin account:${NC} Default 'admin' account is created if missing."
echo -e "Credentials (if auto-generated) are stored at: ${GREEN}/etc/lxcloud/admin_credentials${NC} (owner root, mode 600)"
echo -e "${YELLOW}⚠️  Please change the admin password after first login!${NC}"
echo
echo -e "${BLUE}Database credentials:${NC}"
echo -e "  Database: $DB_NAME"
echo -e "  Username: $DB_USER"
echo -e "  Password: $DB_PASSWORD"
echo -e "  Config file: ${GREEN}$INSTALL_DIR/database.conf${NC}"
echo
echo -e "${BLUE}Database management:${NC}"
echo -e "  Test connection: ${GREEN}cd $INSTALL_DIR && ./database_setup_manual.sh${NC}"
echo -e "  Manual setup guide: ${GREEN}$INSTALL_DIR/DATABASE_SETUP_MANUAL.md${NC}"
echo -e "  Show config:     ${GREEN}cd $INSTALL_DIR && python database_utils.py config${NC}"
echo -e "  Create backup:   ${GREEN}cd $INSTALL_DIR && python database_utils.py backup${NC}"
echo
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  Check status: ${GREEN}systemctl status lxcloud${NC}"
echo -e "  View logs:    ${GREEN}journalctl -u lxcloud -f${NC}"
echo -e "  Restart:      ${GREEN}systemctl restart lxcloud${NC}"
echo
echo -e "${BLUE}Debug Reports:${NC}"
echo -e "  Push reports: ${GREEN}systemctl start lxcloud-debug-push${NC}"
echo -e "  Auto push:    ${GREEN}systemctl enable lxcloud-debug-push.timer${NC}"
echo -e "  View queue:   ${GREEN}ls -la /tmp/lxcloud_debug_queue/${NC}"
echo
echo -e "${BLUE}MQTT Broker:${NC} localhost:1883"
echo -e "${BLUE}Log files:${NC} /var/log/lxcloud/"
echo