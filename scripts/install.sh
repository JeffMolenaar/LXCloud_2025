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

# Error handling function
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    echo -e "${YELLOW}Installation failed. Check the log above for details.${NC}" >&2
    
    # Attempt basic cleanup if possible
    if [ -n "$SERVICE_USER" ] && id "$SERVICE_USER" >/dev/null 2>&1; then
        echo -e "${BLUE}Stopping any running services...${NC}"
        systemctl stop lxcloud >/dev/null 2>&1 || true
        systemctl disable lxcloud >/dev/null 2>&1 || true
    fi
    
    exit 1
}

# Warning function for non-critical issues
warning() {
    echo -e "${YELLOW}WARNING: $1${NC}" >&2
    echo -e "${YELLOW}Continuing installation...${NC}" >&2
}

# Set up error trap for critical errors only
# We'll handle non-critical errors manually with warning()
trap 'error_exit "Critical script error on line $LINENO"' ERR
# Disable automatic exit on error - we'll handle errors manually
set +e
# Make failures in pipes visible
set -o pipefail

# CLI flags (default: interactive, no smoke test)
NONINTERACTIVE=false
RUN_SMOKE=false

print_usage() {
    cat <<'USAGE'
Usage: sudo ./scripts/install.sh [--yes] [--run-smoke] [--help]

Options:
  --yes, -y        Run non-interactive (DEBIAN_FRONTEND=noninteractive, auto-yes to apt)
  --run-smoke      Run an optional create_app smoke-test after installing Python deps (opt-in)
  --help           Show this help message
USAGE
}

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        -y|--yes)
            NONINTERACTIVE=true; shift ;;
        --run-smoke)
            RUN_SMOKE=true; shift ;;
        --help)
            print_usage; exit 0 ;;
        *)
            echo "Unknown arg: $1"; print_usage; exit 1 ;;
    esac
done

# If non-interactive, set apt options
if [ "$NONINTERACTIVE" = true ]; then
    export DEBIAN_FRONTEND=noninteractive
    APT_OPTS="-y"
else
    APT_OPTS=""
fi

# Helper: retry a command N times with delay (useful for transient systemctl failures)
retry_cmd() {
    local -r cmd="$1"
    local -r attempts=${2:-5}
    local -r delay=${3:-3}
    local i=0
    while [ $i -lt $attempts ]; do
        if eval "$cmd"; then
            return 0
        fi
        i=$((i+1))
        echo -e "${YELLOW}Command failed, retrying ($i/$attempts): $cmd${NC}"
        sleep $delay
    done
    return 1
}

# Helper: rsync with --chown if available, fallback to plain rsync + chown
safe_rsync() {
    local src="$1"
    local dst="$2"
    if rsync --version >/dev/null 2>&1 && rsync --help 2>&1 | grep -q -- '--chown'; then
        rsync -a --delete --chown="$SERVICE_USER:$SERVICE_USER" --exclude='.git' --exclude='removed' --exclude='archive' "$src" "$dst/"
    else
        rsync -a --delete --exclude='.git' --exclude='removed' --exclude='archive' "$src" "$dst/"
        chown -R "$SERVICE_USER:$SERVICE_USER" "$dst"
    fi
}

# Configuration
INSTALL_DIR="/home/lxcloud/LXCloud"
SERVICE_USER="lxcloud"
DB_NAME="lxcloud"
DB_USER="lxcloud"
DB_PASSWORD="lxcloud"
DEBUG_QUEUE_DIR="/home/$SERVICE_USER/debug_queue"

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
if ! apt update; then
    error_exit "Failed to update package lists"
fi

if ! apt upgrade $APT_OPTS; then
    warning "System upgrade had issues, but continuing..."
fi

# Install required packages (build deps included)
echo -e "${BLUE}Installing required packages...${NC}"
REQUIRED_PACKAGES="build-essential libssl-dev libffi-dev python3-dev pkg-config default-libmysqlclient-dev rsync python3 python3-pip python3-venv mosquitto mosquitto-clients nginx git curl wget supervisor openssl ufw"

if ! apt install $APT_OPTS $REQUIRED_PACKAGES; then
    error_exit "Failed to install required packages"
fi

echo -e "${GREEN}✓ Required packages installed successfully${NC}"

# Optionally install MariaDB if requested
if [[ "$INSTALL_MARIADB" == "yes" ]]; then
    echo -e "${BLUE}Installing MariaDB server...${NC}"
    if ! apt install $APT_OPTS mariadb-server; then
        error_exit "Failed to install MariaDB server"
    fi

    # Start/enable with retries
    retry_cmd "systemctl enable --now mariadb" 3 2 || error_exit "Failed to start MariaDB service"
    
    echo -e "${GREEN}✓ MariaDB installed and started${NC}"
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

# Create system user (system account with a real home directory)
echo -e "${BLUE}Creating system user...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    # Create a system user but ensure a home directory exists at /home/<user>
    useradd --system --create-home --home "/home/$SERVICE_USER" --shell /bin/bash "$SERVICE_USER" || true
    mkdir -p "/home/$SERVICE_USER"
    chown "$SERVICE_USER:$SERVICE_USER" "/home/$SERVICE_USER"
    echo -e "${GREEN}✓ Created system user: $SERVICE_USER with home /home/$SERVICE_USER${NC}"
fi

# Create installation directory
echo -e "${BLUE}Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Ensure debug queue exists and has correct ownership/permissions
mkdir -p "$DEBUG_QUEUE_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$DEBUG_QUEUE_DIR"
chmod 755 "$DEBUG_QUEUE_DIR"

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

# Copy application files (use safe_rsync helper to preserve ownership where possible)
echo -e "${BLUE}Copying application files from $INSTALL_SRC ...${NC}"
safe_rsync "$INSTALL_SRC/" "$INSTALL_DIR"
echo -e "${GREEN}✓ Files copied${NC}"

# Make database installation script executable
if [[ -f "$INSTALL_DIR/database_install.sh" ]]; then
    chmod +x "$INSTALL_DIR/database_install.sh"
fi

# Verify critical files were copied correctly
echo -e "${BLUE}Verifying installation...${NC}"
CRITICAL_FILES="app/__init__.py
app/debug_reporter.py
scripts/push_debug_reports.py
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

# Service user creation handled earlier; ensure home directory exists and owned by service user
if [[ ! -d "/home/$SERVICE_USER" ]]; then
    mkdir -p "/home/$SERVICE_USER"
    chown "$SERVICE_USER:$SERVICE_USER" "/home/$SERVICE_USER"
fi

# Setup Python virtual environment
echo -e "${BLUE}Setting up Python virtual environment...${NC}"

if ! sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"; then
    error_exit "Failed to create Python virtual environment"
fi

echo -e "${BLUE}Upgrading pip...${NC}"
if ! sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip; then
    error_exit "Failed to upgrade pip"
fi

echo -e "${BLUE}Installing Python requirements...${NC}"
if ! sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"; then
    error_exit "Failed to install Python requirements"
fi

if [ "$RUN_SMOKE" = true ]; then
    # Run a quick create_app smoke-test to detect import-time errors early
    echo -e "${BLUE}Running create_app smoke-test...${NC}"
    if ! sudo -u "$SERVICE_USER" -H bash -c "cd '$INSTALL_DIR' && source venv/bin/activate && python - <<PY
try:
    from app import create_app
    app = create_app()
    print('CREATE_APP_OK')
except Exception as e:
    import traceback
    traceback.print_exc()
    raise
PY"; then
        echo -e "${YELLOW}Warning: create_app smoke-test failed. See traceback above.${NC}"
        warning "Continuing installation but application may be broken - check logs and fix errors"
    else
        echo -e "${GREEN}✓ create_app smoke-test passed${NC}"
    fi
fi

echo -e "${GREEN}✓ Python virtual environment setup completed${NC}"

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

# Test MQTT configuration with version-aware approach
echo -e "${BLUE}Testing Mosquitto configuration...${NC}"
MOSQUITTO_VERSION=$(mosquitto -h 2>&1 | grep -o "mosquitto version [0-9.]*" | grep -o "[0-9.]*" || echo "unknown")
echo -e "${BLUE}Detected Mosquitto version: $MOSQUITTO_VERSION${NC}"

# For mosquitto 2.x, the -t option doesn't exist, so we use a different approach
CONFIG_TEST_PASSED=false

# Method 1: Try to validate config by starting mosquitto in test mode (if available)
if mosquitto --help 2>&1 | grep -q "\-t"; then
    echo -e "${BLUE}Using -t option for config test...${NC}"
    if mosquitto -c /etc/mosquitto/mosquitto.conf -t >/dev/null 2>&1; then
        CONFIG_TEST_PASSED=true
    fi
else
    echo -e "${BLUE}Mosquitto -t option not available, using alternative test...${NC}"
    # Method 2: Check if config file has valid syntax by parsing it
    if [ -f /etc/mosquitto/conf.d/lxcloud.conf ]; then
        # Basic syntax check - ensure the file is readable and contains expected content
        if grep -q "listener.*1883" /etc/mosquitto/conf.d/lxcloud.conf && \
           grep -q "allow_anonymous" /etc/mosquitto/conf.d/lxcloud.conf; then
            CONFIG_TEST_PASSED=true
            echo -e "${GREEN}✓ Configuration file syntax appears valid${NC}"
        else
            echo -e "${YELLOW}! Configuration file missing expected directives${NC}"
        fi
    fi
fi

# Start Mosquitto and test if it works
systemctl restart mosquitto
sleep 2

# Verify MQTT is running properly
if systemctl is-active --quiet mosquitto; then
    echo -e "${GREEN}✓ Mosquitto service started successfully${NC}"
    
    # Additional test: try to connect using mosquitto_pub if available
    if command -v mosquitto_pub >/dev/null 2>&1; then
        echo -e "${BLUE}Testing MQTT connectivity...${NC}"
        if timeout 3 mosquitto_pub -h localhost -p 1883 -t "lxcloud/test" -m "installation_test" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ MQTT connectivity test successful${NC}"
        else
            echo -e "${YELLOW}! MQTT connectivity test failed (this may be normal if auth is required)${NC}"
        fi
    fi
else
    echo -e "${RED}✗ Mosquitto failed to start${NC}"
    systemctl status mosquitto --no-pager -l
    echo -e "${YELLOW}Continuing installation - you may need to fix MQTT configuration manually${NC}"
fi

retry_cmd "systemctl enable mosquitto" 3 2 || warning "Failed to enable mosquitto unit"
echo -e "${GREEN}✓ Mosquitto MQTT configured${NC}"

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
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/run.py
Restart=on-failure
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
retry_cmd "systemctl enable lxcloud" 3 2 || warning "Failed to enable lxcloud unit"

# Start service and check status (retry if transient failures)
retry_cmd "systemctl start lxcloud" 5 3 || warning "Failed to start lxcloud service"
sleep 5

# Comprehensive health check
echo -e "${BLUE}Performing health checks...${NC}"
HEALTH_CHECK_PASSED=true

# Check systemd service status
if systemctl is-active --quiet lxcloud; then
    echo -e "${GREEN}✓ LXCloud systemd service is running${NC}"
else
    echo -e "${RED}✗ LXCloud systemd service is not active${NC}"
    systemctl status lxcloud
    HEALTH_CHECK_PASSED=false
fi

# Check if application is responding on port 5000
if command -v curl >/dev/null 2>&1; then
    if curl -s http://localhost:5000 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Web application responding on port 5000${NC}"
    else
        echo -e "${RED}✗ Web application not responding on port 5000${NC}"
        HEALTH_CHECK_PASSED=false
    fi
else
    echo -e "${YELLOW}! curl not available, skipping HTTP response check${NC}"
fi

# Check database connectivity
echo -e "${BLUE}Testing database connectivity...${NC}"
if sudo -u "$SERVICE_USER" -H bash -c "cd '$INSTALL_DIR' && source venv/bin/activate && python -c 'from app import create_app; app = create_app(); app.app_context().push(); from app.models import db; db.engine.connect().close(); print(\"Database connection successful\")'"; then
    echo -e "${GREEN}✓ Database connectivity verified${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    HEALTH_CHECK_PASSED=false
fi

# Check MQTT broker
if systemctl is-active --quiet mosquitto; then
    echo -e "${GREEN}✓ Mosquitto MQTT broker is running${NC}"
else
    echo -e "${RED}✗ Mosquitto MQTT broker is not active${NC}"
    HEALTH_CHECK_PASSED=false
fi

# Check nginx
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx web server is running${NC}"
else
    echo -e "${RED}✗ Nginx web server is not active${NC}"
    HEALTH_CHECK_PASSED=false
fi

# Show overall status
if [ "$HEALTH_CHECK_PASSED" = true ]; then
    echo -e "${GREEN}✓ All health checks passed${NC}"
else
    echo -e "${RED}⚠ Some health checks failed - please review the errors above${NC}"
fi

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
echo -e "  View queue:   ${GREEN}ls -la /home/$SERVICE_USER/debug_queue/${NC}"
echo
echo -e "${BLUE}MQTT Broker:${NC} localhost:1883"
echo -e "${BLUE}Log files:${NC} /var/log/lxcloud/"
echo