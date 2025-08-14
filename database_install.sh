#!/bin/bash

# LXCloud MariaDB Installation Script
# This script installs and configures MariaDB for LXCloud

set -e  # Exit on any error

# Configuration variables
DB_NAME="lxcloud"
DB_USER="lxcloud"
DB_PASSWORD="lxcloud123"
DB_HOST="localhost"
DB_PORT="3306"
ROOT_PASSWORD=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect the operating system
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    elif command_exists lsb_release; then
        OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
        VERSION=$(lsb_release -sr)
    elif [[ -f /etc/redhat-release ]]; then
        OS="centos"
    else
        OS="unknown"
    fi
    
    log "Detected OS: $OS $VERSION"
}

# Function to install MariaDB on Ubuntu/Debian
install_mariadb_debian() {
    log "Installing MariaDB on Debian/Ubuntu..."
    
    # Update package list
    sudo apt-get update
    
    # Install MariaDB server
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y mariadb-server mariadb-client
    
    # Start and enable MariaDB
    sudo systemctl start mariadb
    sudo systemctl enable mariadb
    
    log_success "MariaDB installed successfully on Debian/Ubuntu"
}

# Function to install MariaDB on CentOS/RHEL/Rocky
install_mariadb_rhel() {
    log "Installing MariaDB on RHEL/CentOS/Rocky..."
    
    # Install MariaDB
    if command_exists dnf; then
        sudo dnf install -y mariadb-server mariadb
    else
        sudo yum install -y mariadb-server mariadb
    fi
    
    # Start and enable MariaDB
    sudo systemctl start mariadb
    sudo systemctl enable mariadb
    
    log_success "MariaDB installed successfully on RHEL/CentOS/Rocky"
}

# Function to install MariaDB on Arch Linux
install_mariadb_arch() {
    log "Installing MariaDB on Arch Linux..."
    
    # Install MariaDB
    sudo pacman -S --noconfirm mariadb
    
    # Initialize MariaDB data directory
    sudo mysql_install_db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
    
    # Start and enable MariaDB
    sudo systemctl start mariadb
    sudo systemctl enable mariadb
    
    log_success "MariaDB installed successfully on Arch Linux"
}

# Function to secure MariaDB installation
secure_mariadb() {
    log "Securing MariaDB installation..."
    
    # Generate a random root password if not provided
    if [[ -z "$ROOT_PASSWORD" ]]; then
        ROOT_PASSWORD=$(openssl rand -base64 32)
        log "Generated random root password: $ROOT_PASSWORD"
    fi
    
    # Set root password and secure installation
    sudo mysql -e "
        UPDATE mysql.user SET Password=PASSWORD('$ROOT_PASSWORD') WHERE User='root';
        DELETE FROM mysql.user WHERE User='';
        DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
        DROP DATABASE IF EXISTS test;
        DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
        FLUSH PRIVILEGES;
    " 2>/dev/null || {
        # If the above fails (newer MariaDB versions), try this approach
        sudo mysql -e "
            ALTER USER 'root'@'localhost' IDENTIFIED BY '$ROOT_PASSWORD';
            DELETE FROM mysql.user WHERE User='';
            DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
            DROP DATABASE IF EXISTS test;
            DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
            FLUSH PRIVILEGES;
        " 2>/dev/null || log_warning "Could not set root password automatically. Please run mysql_secure_installation manually."
    }
    
    log_success "MariaDB installation secured"
}

# Function to create LXCloud database and user
create_lxcloud_database() {
    log "Creating LXCloud database and user..."
    
    # Create database and user
    if [[ -n "$ROOT_PASSWORD" ]]; then
        mysql -u root -p"$ROOT_PASSWORD" -e "
            CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            CREATE USER IF NOT EXISTS '$DB_USER'@'$DB_HOST' IDENTIFIED BY '$DB_PASSWORD';
            GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'$DB_HOST';
            FLUSH PRIVILEGES;
        "
    else
        # Try without password (for fresh installations)
        mysql -u root -e "
            CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            CREATE USER IF NOT EXISTS '$DB_USER'@'$DB_HOST' IDENTIFIED BY '$DB_PASSWORD';
            GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'$DB_HOST';
            FLUSH PRIVILEGES;
        " 2>/dev/null || {
            log_error "Could not create database. Please ensure MariaDB is running and accessible."
            log "You may need to run: sudo mysql_secure_installation"
            log "Then manually create the database and user:"
            log "  CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            log "  CREATE USER '$DB_USER'@'$DB_HOST' IDENTIFIED BY '$DB_PASSWORD';"
            log "  GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'$DB_HOST';"
            log "  FLUSH PRIVILEGES;"
            return 1
        }
    fi
    
    log_success "Database '$DB_NAME' and user '$DB_USER' created successfully"
}

# Function to test database connection
test_database_connection() {
    log "Testing database connection..."
    
    if mysql -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" -P "$DB_PORT" -D "$DB_NAME" -e "SELECT 1;" >/dev/null 2>&1; then
        log_success "Database connection successful"
        return 0
    else
        log_error "Database connection failed"
        return 1
    fi
}

# Function to create database configuration file
create_database_config() {
    log "Creating database configuration file..."
    
    cat > database.conf << EOF
# LXCloud Database Configuration
# This file contains the database connection settings for all LXCloud components

[database]
# Database connection settings
host = $DB_HOST
port = $DB_PORT
user = $DB_USER
password = $DB_PASSWORD
database = $DB_NAME

# Connection settings
charset = utf8mb4
connect_timeout = 10
autocommit = true

# SQLite fallback (used when MariaDB is unavailable)
sqlite_fallback = sqlite:///lxcloud_fallback.db

# Connection pool settings (for production)
pool_size = 5
max_overflow = 10
pool_recycle = 3600
EOF
    
    # Set appropriate permissions
    chmod 600 database.conf
    
    log_success "Database configuration file created: database.conf"
}

# Function to update environment file
update_env_file() {
    log "Updating .env file..."
    
    if [[ -f .env ]]; then
        # Backup existing .env
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        log "Backed up existing .env file"
    fi
    
    # Create or update .env file
    cat > .env << EOF
# LXCloud Environment Configuration
# Database Configuration
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME

# SQLite Fallback (used when MariaDB is unavailable)
SQLITE_FALLBACK_URI=sqlite:///lxcloud_fallback.db

# MQTT Configuration
MQTT_ENABLED=true
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC_PREFIX=lxcloud

# Controller Status Management
CONTROLLER_OFFLINE_TIMEOUT=300
CONTROLLER_STATUS_CHECK_INTERVAL=60

# Security
SECRET_KEY=$(openssl rand -base64 32)

# Flask
FLASK_ENV=production
FLASK_DEBUG=false
EOF
    
    # Set appropriate permissions
    chmod 600 .env
    
    log_success "Environment file updated: .env"
}

# Function to install Python dependencies
install_python_dependencies() {
    log "Installing Python dependencies..."
    
    if [[ -f requirements.txt ]]; then
        if command_exists pip3; then
            pip3 install -r requirements.txt
        elif command_exists pip; then
            pip install -r requirements.txt
        else
            log_warning "pip not found. Please install Python dependencies manually:"
            log "  pip install -r requirements.txt"
            return 1
        fi
        log_success "Python dependencies installed"
    else
        log_warning "requirements.txt not found. Skipping Python dependencies."
    fi
}

# Function to initialize LXCloud database
initialize_lxcloud_database() {
    log "Initializing LXCloud database schema..."
    
    if [[ -f run.py ]]; then
        if command_exists python3; then
            python3 -c "
from app import create_app
from app.models import db

app = create_app()
with app.app_context():
    db.create_all()
    print('Database schema initialized successfully')
" || {
            log_warning "Could not initialize database schema automatically."
            log "Please run the application once to initialize the database schema."
        }
        else
            log_warning "python3 not found. Please initialize database manually by running the application."
        fi
    else
        log_warning "run.py not found. Please ensure you're in the LXCloud directory."
    fi
}

# Function to show configuration summary
show_configuration_summary() {
    log_success "MariaDB installation and configuration completed!"
    echo
    echo "=== Configuration Summary ==="
    echo "Database Host: $DB_HOST"
    echo "Database Port: $DB_PORT"
    echo "Database Name: $DB_NAME"
    echo "Database User: $DB_USER"
    echo "Database Password: $DB_PASSWORD"
    echo
    echo "Configuration files created:"
    echo "  - database.conf (database configuration)"
    echo "  - .env (environment variables)"
    echo
    echo "=== Next Steps ==="
    echo "1. Start the LXCloud application:"
    echo "   python3 run.py"
    echo
    echo "2. Or start with Gunicorn (production):"
    echo "   gunicorn -c config/gunicorn.conf.py run:app"
    echo
    echo "3. Access the web interface at: http://localhost:5000"
    echo "   Default login: admin / admin123"
    echo
    echo "=== Troubleshooting ==="
    echo "- Check MariaDB status: sudo systemctl status mariadb"
    echo "- Test database connection: mysql -u $DB_USER -p$DB_PASSWORD -D $DB_NAME"
    echo "- View application logs: journalctl -u lxcloud -f"
    echo
}

# Function to display help
show_help() {
    echo "LXCloud MariaDB Installation Script"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  --db-name NAME          Database name (default: lxcloud)"
    echo "  --db-user USER          Database user (default: lxcloud)"
    echo "  --db-password PASS      Database password (default: lxcloud123)"
    echo "  --db-host HOST          Database host (default: localhost)"
    echo "  --db-port PORT          Database port (default: 3306)"
    echo "  --root-password PASS    MariaDB root password (auto-generated if not provided)"
    echo "  --skip-install          Skip MariaDB installation (configure existing installation)"
    echo "  --skip-secure           Skip MariaDB security configuration"
    echo "  --skip-python           Skip Python dependencies installation"
    echo
    echo "Examples:"
    echo "  $0                                          # Install with defaults"
    echo "  $0 --db-password mypassword                 # Custom database password"
    echo "  $0 --skip-install --db-host 192.168.1.100  # Configure for remote database"
    echo
}

# Parse command line arguments
SKIP_INSTALL=false
SKIP_SECURE=false
SKIP_PYTHON=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --db-name)
            DB_NAME="$2"
            shift 2
            ;;
        --db-user)
            DB_USER="$2"
            shift 2
            ;;
        --db-password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        --db-host)
            DB_HOST="$2"
            shift 2
            ;;
        --db-port)
            DB_PORT="$2"
            shift 2
            ;;
        --root-password)
            ROOT_PASSWORD="$2"
            shift 2
            ;;
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        --skip-secure)
            SKIP_SECURE=true
            shift
            ;;
        --skip-python)
            SKIP_PYTHON=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main installation process
main() {
    log "Starting LXCloud MariaDB installation..."
    
    # Check if running as root for installation steps
    if [[ "$SKIP_INSTALL" == false ]] && [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. This is fine for installation, but don't run the application as root."
    fi
    
    # Detect operating system
    detect_os
    
    # Install MariaDB if not skipped
    if [[ "$SKIP_INSTALL" == false ]]; then
        log "Installing MariaDB..."
        
        case $OS in
            ubuntu|debian)
                install_mariadb_debian
                ;;
            centos|rhel|rocky)
                install_mariadb_rhel
                ;;
            arch)
                install_mariadb_arch
                ;;
            *)
                log_error "Unsupported operating system: $OS"
                log "Please install MariaDB manually and run this script with --skip-install"
                exit 1
                ;;
        esac
        
        # Secure MariaDB installation
        if [[ "$SKIP_SECURE" == false ]]; then
            secure_mariadb
        fi
    else
        log "Skipping MariaDB installation (--skip-install specified)"
    fi
    
    # Create database and user
    create_lxcloud_database || {
        log_error "Failed to create database. Please check the configuration and try again."
        exit 1
    }
    
    # Test database connection
    test_database_connection || {
        log_error "Database connection test failed. Please check the configuration."
        exit 1
    }
    
    # Create configuration files
    create_database_config
    update_env_file
    
    # Install Python dependencies
    if [[ "$SKIP_PYTHON" == false ]]; then
        install_python_dependencies
    fi
    
    # Initialize database schema
    initialize_lxcloud_database
    
    # Show summary
    show_configuration_summary
    
    log_success "Installation completed successfully!"
}

# Run main function
main "$@"