#!/bin/bash

# LXCloud Database Initialization Script
# This script sets up the database for localhost installations automatically

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Database configuration
DB_NAME="lxcloud"
DB_USER="lxcloud"
DB_PASSWORD="lxcloud"

log "Initializing LXCloud database for localhost..."

# Function to test if MySQL/MariaDB is running
test_mysql_service() {
    if systemctl is-active --quiet mysql || systemctl is-active --quiet mariadb; then
        return 0
    else
        return 1
    fi
}

# Function to test database connectivity
test_db_connectivity() {
    mysql -u "$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME; SELECT 1;" &>/dev/null
}

# Check if MySQL/MariaDB is running
if ! test_mysql_service; then
    error "MySQL/MariaDB service is not running"
    info "Please start the service with one of these commands:"
    info "  sudo systemctl start mysql"
    info "  sudo systemctl start mariadb"
    exit 1
fi

log "MySQL/MariaDB service is running"

# Try to create database automatically using sudo mysql
log "Setting up database and user..."

# Method 1: Try sudo mysql (works for most localhost MariaDB installations)
if sudo mysql -e "
CREATE DATABASE IF NOT EXISTS $DB_NAME;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
" &>/dev/null; then
    log "✅ Database setup completed successfully using sudo mysql"
else
    warn "sudo mysql failed, trying alternative methods..."
    
    # Method 2: Try mysql as root without password
    if mysql -u root -e "
CREATE DATABASE IF NOT EXISTS $DB_NAME;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
" &>/dev/null; then
        log "✅ Database setup completed successfully using mysql root"
    else
        error "Automatic database setup failed"
        echo ""
        echo "Please run this command manually:"
        echo "sudo mysql -e \"CREATE DATABASE IF NOT EXISTS $DB_NAME; CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD'; GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost'; FLUSH PRIVILEGES;\""
        echo ""
        echo "Or connect to MySQL manually and run:"
        echo "CREATE DATABASE IF NOT EXISTS $DB_NAME;"
        echo "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
        echo "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
        echo "FLUSH PRIVILEGES;"
        exit 1
    fi
fi

# Test the connection
log "Testing database connection..."
if test_db_connectivity; then
    log "✅ Database connection test successful"
    log "✅ Database '$DB_NAME' is ready for LXCloud"
    echo ""
    info "Database configuration:"
    info "  Database: $DB_NAME"
    info "  Username: $DB_USER"
    info "  Password: $DB_PASSWORD"
    info "  Host: localhost"
    echo ""
else
    error "Database connection test failed"
    error "Please verify the database setup manually"
    exit 1
fi

log "Database initialization completed successfully!"