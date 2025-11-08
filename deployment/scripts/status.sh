#!/bin/bash
#
# Check Gate Controller status on Raspberry Pi
#
# Usage: ./status.sh [--logs]
#

# Configuration
RPI_HOST="${RPI_HOST:-fokhomerpi.local}"
RPI_USER="${RPI_USER:-pi}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check arguments
SHOW_LOGS=false
if [ "$1" = "--logs" ]; then
    SHOW_LOGS=true
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Gate Controller Status                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check connection
echo -e "${GREEN}▶${NC} Checking connection to ${RPI_HOST}..."
if ! ssh -o ConnectTimeout=5 "${RPI_USER}@${RPI_HOST}" "echo ''" > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Cannot connect to ${RPI_HOST}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Connected"
echo ""

# Get system info
echo -e "${BLUE}System Information:${NC}"
ssh "${RPI_USER}@${RPI_HOST}" << 'ENDSSH'
echo "  Hostname:    $(hostname)"
echo "  Uptime:      $(uptime -p)"
echo "  Load:        $(uptime | awk -F'load average:' '{print $2}')"
echo "  Memory:      $(free -h | awk 'NR==2{printf "%s / %s (%.0f%%)", $3, $2, $3*100/$2}')"
echo "  Disk:        $(df -h / | awk 'NR==2{printf "%s / %s (%s)", $3, $2, $5}')"
echo "  Temperature: $(vcgencmd measure_temp 2>/dev/null || echo 'N/A')"
ENDSSH
echo ""

# Check service status
echo -e "${BLUE}Service Status:${NC}"
ssh "${RPI_USER}@${RPI_HOST}" << 'ENDSSH'
if systemctl is-active --quiet gate-controller 2>/dev/null; then
    echo -e "  Status:      \033[0;32m● Running\033[0m"
    
    # Get service info
    START_TIME=$(systemctl show gate-controller -p ActiveEnterTimestamp --value)
    if [ -n "$START_TIME" ]; then
        echo "  Started:     $START_TIME"
    fi
    
    # Get process info
    PID=$(systemctl show gate-controller -p MainPID --value)
    if [ "$PID" != "0" ]; then
        echo "  PID:         $PID"
        echo "  Memory:      $(ps -p $PID -o rss= | awk '{printf "%.1f MB", $1/1024}')"
        echo "  CPU:         $(ps -p $PID -o %cpu= | xargs)%"
    fi
else
    echo -e "  Status:      \033[0;31m○ Stopped\033[0m"
fi

# Check if enabled
if systemctl is-enabled --quiet gate-controller 2>/dev/null; then
    echo "  Auto-start:  Enabled"
else
    echo "  Auto-start:  Disabled"
fi
ENDSSH
echo ""

# Check web dashboard
echo -e "${BLUE}Web Dashboard:${NC}"
HTTP_STATUS=$(ssh "${RPI_USER}@${RPI_HOST}" "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000 2>/dev/null" || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "  Dashboard:   ${GREEN}✓ Available${NC}"
    echo "  URL:         http://${RPI_HOST}:8000"
    echo "               http://192.168.100.185:8000"
else
    echo -e "  Dashboard:   ${RED}✗ Not accessible${NC}"
fi
echo ""

# Check Bluetooth
echo -e "${BLUE}Bluetooth Status:${NC}"
ssh "${RPI_USER}@${RPI_HOST}" << 'ENDSSH'
if systemctl is-active --quiet bluetooth; then
    echo -e "  Bluetooth:   \033[0;32m● Active\033[0m"
    
    # Check if adapter is up
    if hciconfig hci0 2>/dev/null | grep -q "UP RUNNING"; then
        echo "  Adapter:     hci0 (UP)"
    else
        echo "  Adapter:     hci0 (DOWN)"
    fi
else
    echo -e "  Bluetooth:   \033[0;31m○ Inactive\033[0m"
fi
ENDSSH
echo ""

# Show recent logs if requested
if [ "$SHOW_LOGS" = true ]; then
    echo -e "${BLUE}Recent Logs (last 30 lines):${NC}"
    ssh "${RPI_USER}@${RPI_HOST}" "sudo journalctl -u gate-controller -n 30 --no-pager"
    echo ""
fi

# Show quick commands
echo -e "${YELLOW}Quick Commands:${NC}"
echo "  View logs:       ssh ${RPI_USER}@${RPI_HOST} 'sudo journalctl -u gate-controller -f'"
echo "  Restart:         ssh ${RPI_USER}@${RPI_HOST} 'sudo systemctl restart gate-controller'"
echo "  Stop:            ssh ${RPI_USER}@${RPI_HOST} 'sudo systemctl stop gate-controller'"
echo "  Start:           ssh ${RPI_USER}@${RPI_HOST} 'sudo systemctl start gate-controller'"
echo "  View config:     ssh ${RPI_USER}@${RPI_HOST} 'cat /home/pi/gate_controller/config/config.yaml'"
echo ""

