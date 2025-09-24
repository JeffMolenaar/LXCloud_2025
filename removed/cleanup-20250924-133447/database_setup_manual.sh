#!/bin/bash

# LXCloud Manual Database Setup Script
# This script assumes MariaDB is already installed and only tests connection

set -e  # Exit on any error

# Configuration variables
DB_NAME="lxcloud"
DB_USER="lxcloud"
DB_PASSWORD="lxcloud"
DB_HOST="localhost"
DB_PORT="3306"

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

# Function to display manual setup instructions
show_manual_setup_instructions() {
    echo
    echo -e "${YELLOW}=== MANUAL DATABASE SETUP REQUIRED ===${NC}"
    echo
    echo "Please follow these steps to set up the database manually:"
    echo
    echo "1. Install MariaDB if not already installed:"
    echo "   sudo apt update"
    echo "   sudo apt install mariadb-server mariadb-client"
    echo "   sudo systemctl start mariadb"
    echo "   sudo systemctl enable mariadb"
    echo
    echo "2. Secure your MariaDB installation:"
    echo "   sudo mysql_secure_installation"
    echo
    echo "3. Create the LXCloud database and user:"
    echo "   sudo mysql -u root -p"
    echo "   Then run these SQL commands:"
    echo "   CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    echo "   CREATE USER IF NOT EXISTS '$DB_USER'@'$DB_HOST' IDENTIFIED BY '$DB_PASSWORD';"
    echo "   GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'$DB_HOST';"
    echo "   FLUSH PRIVILEGES;"
    echo "   EXIT;"
    echo
    echo "4. Test the connection manually:"
    echo "   mysql -u $DB_USER -p$DB_PASSWORD -h $DB_HOST -P $DB_PORT -D $DB_NAME -e 'SELECT 1;'"
    echo
    echo "5. Once manual setup is complete, re-run this script to verify the connection."
    echo
}

# Function to test database connection
test_database_connection() {
    log "Testing database connection..."
    
    # Test connection with detailed error output
    local connection_output
    connection_output=$(mysql -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" -P "$DB_PORT" -D "$DB_NAME" -e "SELECT 1;" 2>&1)
    local connection_status=$?
    
    if [[ $connection_status -eq 0 ]]; then
        log_success "Database connection successful"
        return 0
    else
        log_error "Database connection failed"
        log_error "Connection details: mysql -u $DB_USER -h $DB_HOST -P $DB_PORT -D $DB_NAME"
        log_error "Error output: $connection_output"
        
        # Show manual setup instructions on failure
        show_manual_setup_instructions
        
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

# Function to display help
show_help() {
    echo "LXCloud Manual Database Setup Script"
    echo
    echo "This script assumes MariaDB is already installed and configured."
    echo "It only tests the database connection and creates configuration files."
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  --db-name NAME          Database name (default: lxcloud)"
    echo "  --db-user USER          Database user (default: lxcloud)"
    echo "  --db-password PASS      Database password (default: lxcloud)"
    echo "  --db-host HOST          Database host (default: localhost)"
    echo "  --db-port PORT          Database port (default: 3306)"
    echo
    echo "Examples:"
    echo "  $0                                          # Test with defaults"
    echo "  $0 --db-password mypassword                 # Custom database password"
    echo "  $0 --db-host 192.168.1.100                  # Remote database"
    echo
}

# Parse command line arguments
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
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main setup process
main() {
    log "Starting LXCloud database connection test..."
    
    echo
    echo -e "${BLUE}=== Database Configuration ===${NC}"
    echo "Database Host: $DB_HOST"
    echo "Database Port: $DB_PORT"
    echo "Database Name: $DB_NAME"
    echo "Database User: $DB_USER"
    echo "Database Password: $DB_PASSWORD"
    echo
    
    # Test database connection
    if test_database_connection; then
        log_success "Database connection test passed!"
        
        # Create configuration files
        create_database_config
        update_env_file
        
        echo
        log_success "Database setup completed successfully!"
        echo
        echo -e "${GREEN}=== Next Steps ===${NC}"
        echo "1. Start the LXCloud application:"
        echo "   python3 run.py"
        echo
        echo "2. Or start with Gunicorn (production):"
        echo "   gunicorn -c config/gunicorn.conf.py run:app"
        echo
        echo "3. Access the web interface at: http://localhost:5000"
        echo
    else
        log_error "Database connection test failed!"
        echo
        log_error "Please complete the manual database setup and try again."
        exit 1
    fi
}

# Run main function
main "$@"