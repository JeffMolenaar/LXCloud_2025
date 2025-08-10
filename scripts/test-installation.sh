#!/bin/bash

# LXCloud Installation Test Script
# Tests all components of the LXCloud installation to ensure everything works

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test configuration
INSTALL_DIR="/opt/LXCloud_2025"
DATABASE_USER="lxcloud"
DATABASE_PASSWORD="lxcloud"
DATABASE_NAME="lxcloud"

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    return 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

# Test counter
total_tests=0
passed_tests=0
failed_tests=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    total_tests=$((total_tests + 1))
    info "Running test: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        success "✅ $test_name: PASSED"
        passed_tests=$((passed_tests + 1))
        return 0
    else
        error "❌ $test_name: FAILED"
        failed_tests=$((failed_tests + 1))
        return 1
    fi
}

run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    
    total_tests=$((total_tests + 1))
    info "Running test: $test_name"
    
    if eval "$test_command"; then
        success "✅ $test_name: PASSED"
        passed_tests=$((passed_tests + 1))
        return 0
    else
        error "❌ $test_name: FAILED"
        failed_tests=$((failed_tests + 1))
        return 1
    fi
}

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                  LXCloud Installation Test Suite                ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# Test 1: Check if Ubuntu 22.04
log "Starting Ubuntu version check..."
if grep -q "22.04" /etc/os-release; then
    success "✅ Ubuntu 22.04 LTS detected"
else
    warn "⚠️  Not Ubuntu 22.04 LTS: $(lsb_release -d | cut -f2)"
fi

# Test 2: System Prerequisites
log "Testing system prerequisites..."
run_test "Node.js installed" "command -v node"
run_test "NPM installed" "command -v npm"
run_test "MySQL/MariaDB client installed" "command -v mysql"
run_test "Nginx installed" "command -v nginx"
# Note: mosquitto_pub is not required since the app uses Node.js MQTT client
if command -v mosquitto_pub >/dev/null 2>&1; then
    success "✅ Mosquitto client installed: AVAILABLE (optional)"
else
    info "Mosquitto client not installed (this is okay - app uses Node.js MQTT client)"
fi

# Test 3: Node.js version check
log "Checking Node.js version..."
node_version=$(node --version 2>/dev/null || echo "none")
if [[ "$node_version" =~ ^v1[8-9]\.|^v[2-9][0-9]\. ]]; then
    success "✅ Node.js version $node_version is compatible"
else
    warn "⚠️  Node.js version $node_version may not be optimal (recommended: v18+)"
fi

# Test 4: Service Status
log "Testing service status..."
services=("mariadb" "mosquitto" "nginx")
for service in "${services[@]}"; do
    run_test "$service service running" "systemctl is-active --quiet $service"
done

# Test 5: Application Directory Structure
log "Testing application directory structure..."
run_test "Application directory exists" "[ -d '$INSTALL_DIR' ]"
run_test "Application files exist" "[ -f '$INSTALL_DIR/server.js' ]"
run_test "Package.json exists" "[ -f '$INSTALL_DIR/package.json' ]"
run_test "Environment file exists" "[ -f '$INSTALL_DIR/.env' ]"
run_test "Node modules installed" "[ -d '$INSTALL_DIR/node_modules' ]"

# Test 6: File Permissions
log "Testing file permissions..."
run_test "Application directory ownership" "[ \$(stat -c '%U' '$INSTALL_DIR') = 'lxcloud' ]"
run_test "Logs directory writable" "[ -w '$INSTALL_DIR/logs' ]"
run_test "Uploads directory writable" "[ -w '$INSTALL_DIR/uploads' ]"

# Test 7: Database Connectivity
log "Testing database connectivity..."
run_test "Database connection" "mysql -u '$DATABASE_USER' -p'$DATABASE_PASSWORD' '$DATABASE_NAME' -e 'SELECT 1'"
run_test "Database tables exist" "mysql -u '$DATABASE_USER' -p'$DATABASE_PASSWORD' '$DATABASE_NAME' -e 'SHOW TABLES' | grep -q users"

# Test 8: MQTT Connectivity
log "Testing MQTT connectivity..."
# Use Node.js-based MQTT test for better reliability
if [ -f "$INSTALL_DIR/.env" ]; then
    MQTT_PASSWORD=$(grep "MQTT_PASSWORD=" "$INSTALL_DIR/.env" | cut -d= -f2)
    if [ -n "$MQTT_PASSWORD" ]; then
        # Use the Node.js MQTT test script
        run_test "MQTT broker connectivity" "cd '$INSTALL_DIR' && node scripts/test-mqtt-connection.js"
    else
        warn "⚠️  MQTT password not found in environment file"
    fi
else
    warn "⚠️  Environment file not found, skipping MQTT test"
fi

# Test 9: Network Ports
log "Testing network ports..."
run_test "Port 80 (HTTP) listening" "ss -tlnp | grep -q ':80 '"
run_test "Port 3000 (LXCloud) listening" "ss -tlnp | grep -q ':3000 '"
run_test "Port 1883 (MQTT) listening" "ss -tlnp | grep -q ':1883 '"
run_test "Port 3306 (MySQL) listening" "ss -tlnp | grep -q ':3306 '"

# Test 10: LXCloud Service
log "Testing LXCloud service..."
if systemctl is-active --quiet lxcloud; then
    success "✅ LXCloud service is running"
    
    # Test application startup
    log "Waiting for application to be ready..."
    sleep 5
    
    # Test API health endpoint
    run_test "Application API health check" "curl -s --max-time 10 http://localhost:3000/api/health | grep -q 'ok'"
    
    # Test nginx proxy
    run_test "Nginx proxy working" "curl -s --max-time 10 http://localhost | grep -q 'LXCloud\\|login\\|html'"
    
else
    error "❌ LXCloud service is not running"
    info "Checking LXCloud service logs..."
    sudo journalctl -u lxcloud --no-pager -n 10
fi

# Test 11: Systemd Configuration
log "Testing systemd configuration..."
run_test "LXCloud service file exists" "[ -f '/etc/systemd/system/lxcloud.service' ]"
run_test "LXCloud service enabled" "systemctl is-enabled --quiet lxcloud"

# Test 12: Nginx Configuration
log "Testing nginx configuration..."
run_test "Nginx configuration valid" "nginx -t"
run_test "LXCloud nginx site exists" "[ -f '/etc/nginx/sites-available/lxcloud' ]"
run_test "LXCloud nginx site enabled" "[ -f '/etc/nginx/sites-enabled/lxcloud' ]"

# Test 13: Firewall Configuration
log "Testing firewall configuration..."
if command -v ufw >/dev/null; then
    run_test "UFW firewall enabled" "ufw status | grep -q 'Status: active'"
    run_test "HTTP traffic allowed" "ufw status | grep -q 'Nginx Full'"
else
    warn "⚠️  UFW not available, skipping firewall tests"
fi

# Test 14: SSL/TLS (if configured)
log "Testing SSL/TLS configuration (optional)..."
if ss -tlnp | grep -q ':443 '; then
    info "HTTPS port 443 is listening"
    run_test "HTTPS connectivity" "curl -k -s --max-time 10 https://localhost | grep -q 'html'"
else
    info "HTTPS not configured (this is normal for new installations)"
fi

# Test 15: Application Dependencies
log "Testing application dependencies..."
cd "$INSTALL_DIR"
run_test "Node.js dependencies check" "npm list --depth=0 --production"

# Test 16: Log Files
log "Testing log files..."
run_test "Application logs directory exists" "[ -d '$INSTALL_DIR/logs' ]"
run_test "Systemd logs accessible" "journalctl -u lxcloud --no-pager -n 1"

# Test 17: Backup and Maintenance Scripts
log "Testing maintenance scripts..."
run_test "Status script exists" "[ -f '$INSTALL_DIR/status.sh' ]"
run_test "Backup script exists" "[ -f '$INSTALL_DIR/backup.sh' ]"
run_test "Update script exists" "[ -f '$INSTALL_DIR/update.sh' ]"
run_test "Diagnose script exists" "[ -f '$INSTALL_DIR/diagnose.sh' ]"

# Test 18: Security Configuration
log "Testing security configuration..."
run_test "Service user exists" "id lxcloud"
run_test "Service runs as non-root" "! systemctl show lxcloud | grep -q 'User=root'"

# Test 19: Memory and Disk Usage
log "Testing resource usage..."
memory_usage=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')
disk_usage=$(df /opt/LXCloud_2025 | tail -1 | awk '{print $5}' | sed 's/%//')

if [ "${memory_usage%.*}" -lt 80 ]; then
    success "✅ Memory usage: ${memory_usage%.*}% (acceptable)"
else
    warn "⚠️  High memory usage: ${memory_usage%.*}%"
fi

if [ "$disk_usage" -lt 90 ]; then
    success "✅ Disk usage: ${disk_usage}% (acceptable)"
else
    warn "⚠️  High disk usage: ${disk_usage}%"
fi

# Test 20: End-to-End Web Test
log "Testing end-to-end web functionality..."
if command -v curl >/dev/null; then
    # Test login page
    run_test "Login page accessible" "curl -s --max-time 10 http://localhost/auth/login | grep -q 'login\\|password'"
    
    # Test API endpoints
    run_test "Health API endpoint" "curl -s --max-time 10 http://localhost/api/health | grep -q 'ok'"
else
    warn "⚠️  curl not available, skipping web tests"
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                        Test Results Summary                     ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Total tests run: $total_tests${NC}"
echo -e "${GREEN}Tests passed: $passed_tests${NC}"
echo -e "${RED}Tests failed: $failed_tests${NC}"
echo ""

if [ "$failed_tests" -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! LXCloud installation is working correctly.${NC}"
    echo ""
    echo -e "${CYAN}You can now access LXCloud at:${NC}"
    echo -e "${GREEN}  Local: http://localhost${NC}"
    hostname -I | tr ' ' '\n' | grep -v '^$' | while read ip; do
        echo -e "${GREEN}  Network: http://$ip${NC}"
    done
    echo ""
    echo -e "${CYAN}Default credentials:${NC}"
    echo -e "${GREEN}  Email: admin@lxcloud.local${NC}"
    echo -e "${GREEN}  Password: admin123${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the output above and fix any issues.${NC}"
    echo ""
    echo -e "${YELLOW}Common troubleshooting steps:${NC}"
    echo -e "${YELLOW}  1. Check service status: sudo systemctl status lxcloud nginx mariadb mosquitto${NC}"
    echo -e "${YELLOW}  2. Check logs: sudo journalctl -u lxcloud -f${NC}"
    echo -e "${YELLOW}  3. Run diagnostics: sudo $INSTALL_DIR/diagnose.sh${NC}"
    echo -e "${YELLOW}  4. Restart services: sudo systemctl restart lxcloud nginx${NC}"
    echo ""
    exit 1
fi