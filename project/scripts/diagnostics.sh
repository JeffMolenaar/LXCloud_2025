#!/bin/bash
"""
LXCloud System Diagnostics
Comprehensive health check and debugging tool
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== LXCloud System Diagnostics ===${NC}"
echo

# Check systemd services
echo -e "${BLUE}1. Systemd Services Status${NC}"
echo -e "${BLUE}===========================${NC}"

services=("lxcloud" "lxcloud-debug-push" "lxcloud-debug-push.timer" "mariadb" "mosquitto" "nginx")

for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $service: ${GREEN}active${NC}"
    else
        echo -e "  ${RED}✗${NC} $service: ${RED}inactive/failed${NC}"
        # Show last few lines of failed service
        echo -e "    Last error:"
        systemctl status "$service" -n 5 --no-pager | tail -n 5 | sed 's/^/      /'
    fi
done
echo

# Check key files existence
echo -e "${BLUE}2. Critical Files Check${NC}"
echo -e "${BLUE}========================${NC}"

files=(
    "/home/lxcloud/LXCloud/run.py"
    "/home/lxcloud/LXCloud/project/app/__init__.py" 
    "/home/lxcloud/LXCloud/project/app/debug_reporter.py"
    "/home/lxcloud/LXCloud/project/scripts/push_debug_reports.py"
    "/home/lxcloud/debug_queue"
    "/etc/systemd/system/lxcloud.service"
    "/etc/systemd/system/lxcloud-debug-push.service"
    "/etc/systemd/system/lxcloud-debug-push.timer"
)

for file in "${files[@]}"; do
    if [ -e "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file ${RED}(missing)${NC}"
    fi
done
echo

# Check ports and processes
echo -e "${BLUE}3. Network & Processes${NC}"
echo -e "${BLUE}=======================${NC}"

echo -e "Port 5000 usage:"
if lsof -iTCP:5000 -sTCP:LISTEN -P -n 2>/dev/null; then
    echo -e "  ${YELLOW}Port 5000 is in use${NC}"
else
    echo -e "  ${GREEN}✓ Port 5000 is free${NC}"
fi

echo -e "\nPython processes:"
pgrep -f "python.*run.py" && echo -e "  ${YELLOW}Python LXCloud processes running${NC}" || echo -e "  ${GREEN}No Python LXCloud processes${NC}"
echo

# Check logs for errors
echo -e "${BLUE}4. Recent Errors${NC}"
echo -e "${BLUE}=================${NC}"

echo -e "LXCloud service errors (last 10 lines):"
journalctl -u lxcloud -n 10 --no-pager -p err 2>/dev/null | sed 's/^/  /' || echo -e "  ${GREEN}No recent errors${NC}"
echo

# Check debug queue
echo -e "${BLUE}5. Debug Queue Status${NC}"
echo -e "${BLUE}======================${NC}"

if [ -d "/home/lxcloud/debug_queue" ]; then
    count=$(ls -1 /home/lxcloud/debug_queue/*.json 2>/dev/null | wc -l)
    echo -e "  Debug reports waiting: ${YELLOW}$count${NC}"
    if [ "$count" -gt 0 ]; then
        echo -e "  Recent reports:"
        ls -lt /home/lxcloud/debug_queue/*.json 2>/dev/null | head -3 | sed 's/^/    /'
    fi
else
    echo -e "  ${RED}✗ Debug queue directory missing${NC}"
fi
echo

# Database connectivity
echo -e "${BLUE}6. Database Check${NC}"
echo -e "${BLUE}=================${NC}"

if systemctl is-active --quiet mariadb; then
    echo -e "  ${GREEN}✓ MariaDB service running${NC}"
    # Test basic connection
    if mysql -e "SELECT 1;" 2>/dev/null; then
        echo -e "  ${GREEN}✓ Database connection OK${NC}"
    else
        echo -e "  ${YELLOW}! Database connection failed${NC}"
    fi
else
    echo -e "  ${RED}✗ MariaDB service not running${NC}"
fi
echo

# Summary and recommendations
echo -e "${BLUE}7. Recommendations${NC}"
echo -e "${BLUE}==================${NC}"

# Check if main service is running
if ! systemctl is-active --quiet lxcloud; then
    echo -e "  ${RED}• Restart LXCloud service: systemctl restart lxcloud${NC}"
fi

# Check if debug directory exists
if [ ! -d "/home/lxcloud/debug_queue" ]; then
    echo -e "  ${YELLOW}• Create debug directory: mkdir -p /home/lxcloud/debug_queue${NC}"
    echo -e "    ${YELLOW}  chown lxcloud:lxcloud /home/lxcloud/debug_queue${NC}"
fi

# Check for port conflicts
if lsof -iTCP:5000 -sTCP:LISTEN -P -n >/dev/null 2>&1; then
    echo -e "  ${YELLOW}• Port 5000 conflict - check: lsof -iTCP:5000 -sTCP:LISTEN${NC}"
fi

echo
echo -e "${GREEN}Diagnostics complete!${NC}"