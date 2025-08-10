#!/bin/bash

# LXCloud Installation Validation Test
# This script tests the installation components without actually installing services

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Test functions
log() {
    echo -e "${GREEN}[TEST] $1${NC}"
}

error() {
    echo -e "${RED}[FAIL] $1${NC}"
    ((TESTS_FAILED++))
}

success() {
    echo -e "${GREEN}[PASS] $1${NC}"
    ((TESTS_PASSED++))
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Test 1: Check if all installation scripts exist and are executable
test_script_files() {
    log "Testing installation script files..."
    
    local scripts=(
        "scripts/install.sh"
        "scripts/install-new.sh"
        "scripts/setup-database.js"
        "scripts/init-database.sh"
        "scripts/test-database.js"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                success "Script $script exists and is executable"
            else
                warn "Script $script exists but is not executable"
                chmod +x "$script"
                success "Made $script executable"
            fi
        else
            error "Script $script does not exist"
        fi
    done
}

# Test 2: Check database credentials consistency
test_database_credentials() {
    log "Testing database credentials consistency..."
    
    # Check .env.example
    if grep -q "DB_USER=lxcloud" .env.example; then
        success ".env.example has correct DB_USER"
    else
        error ".env.example does not have correct DB_USER"
    fi
    
    if grep -q "DB_PASSWORD=lxcloud" .env.example; then
        success ".env.example has correct DB_PASSWORD"
    else
        error ".env.example does not have correct DB_PASSWORD"
    fi
    
    # Check scripts for consistent database user
    local scripts_to_check=(
        "scripts/install.sh"
        "scripts/install-new.sh"
        "scripts/test-database.js"
        "scripts/init-database.sh"
    )
    
    for script in "${scripts_to_check[@]}"; do
        if [ -f "$script" ]; then
            if grep -q "lxcloud" "$script" && ! grep -q "lxadmin" "$script"; then
                success "Script $script uses correct database credentials"
            else
                if grep -q "lxadmin" "$script"; then
                    error "Script $script still contains old 'lxadmin' references"
                else
                    warn "Script $script may not reference database user"
                fi
            fi
        fi
    done
}

# Test 3: Check package.json scripts
test_package_scripts() {
    log "Testing package.json scripts..."
    
    local required_scripts=(
        "setup-db"
        "init-db"
        "test-db"
        "install-system"
    )
    
    for script in "${required_scripts[@]}"; do
        if npm run | grep -q "$script"; then
            success "npm script '$script' is defined"
        else
            error "npm script '$script' is missing"
        fi
    done
}

# Test 4: Test database connection in development mode
test_database_mock() {
    log "Testing database mock functionality..."
    
    if NODE_ENV=development node -e "
        const database = require('./config/database');
        database.initialize().then(() => {
            console.log('Database initialized successfully');
            process.exit(0);
        }).catch((error) => {
            console.error('Database initialization failed:', error);
            process.exit(1);
        });
    " &>/dev/null; then
        success "Database mock functionality works"
    else
        error "Database mock functionality failed"
    fi
}

# Test 5: Test application startup
test_application_startup() {
    log "Testing application startup..."
    
    # Start the application in the background
    NODE_ENV=development timeout 10s node server.js &>/dev/null &
    local app_pid=$!
    
    sleep 3
    
    # Check if the process is still running
    if kill -0 "$app_pid" 2>/dev/null; then
        success "Application starts and runs successfully"
        kill "$app_pid" 2>/dev/null || true
    else
        error "Application failed to start or crashed"
    fi
}

# Test 6: Validate install script syntax
test_install_script_syntax() {
    log "Testing install script syntax..."
    
    # Check bash syntax
    if bash -n scripts/install.sh; then
        success "install.sh has valid bash syntax"
    else
        error "install.sh has syntax errors"
    fi
    
    if bash -n scripts/install-new.sh; then
        success "install-new.sh has valid bash syntax"
    else
        error "install-new.sh has syntax errors"
    fi
    
    if bash -n scripts/init-database.sh; then
        success "init-database.sh has valid bash syntax"
    else
        error "init-database.sh has syntax errors"
    fi
}

# Test 7: Check for localhost-specific configurations
test_localhost_config() {
    log "Testing localhost-specific configurations..."
    
    # Check if install scripts use localhost properly
    if grep -q "localhost" scripts/install.sh && grep -q "127.0.0.1" scripts/install.sh; then
        success "install.sh properly configured for localhost"
    else
        warn "install.sh may not be properly configured for localhost"
    fi
    
    # Check nginx configuration
    if grep -q "localhost:3000" scripts/install.sh; then
        success "Nginx configuration points to localhost"
    else
        error "Nginx configuration does not point to localhost"
    fi
}

# Run all tests
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LXCloud Installation Validation Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

test_script_files
echo ""
test_database_credentials
echo ""
test_package_scripts
echo ""
test_database_mock
echo ""
test_application_startup
echo ""
test_install_script_syntax
echo ""
test_localhost_config
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}           Test Results Summary         ${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Installation should work correctly.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please review the issues above.${NC}"
    exit 1
fi