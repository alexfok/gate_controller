#!/bin/bash
#
# Update Gate Controller on Raspberry Pi
# 
# This script updates the running gate controller without losing configuration
# Usage: ./update.sh
#

set -e

# Configuration
RPI_HOST="${RPI_HOST:-fokhomerpi.local}"
RPI_USER="${RPI_USER:-pi}"
RPI_DEPLOY_DIR="/home/${RPI_USER}/gate_controller"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Gate Controller Update                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if service is running
echo -e "${GREEN}▶${NC} Checking service status..."
if ssh "${RPI_USER}@${RPI_HOST}" "systemctl is-active --quiet gate-controller" 2>/dev/null; then
    SERVICE_RUNNING=true
    echo -e "${YELLOW}⚠${NC} Service is currently running"
else
    SERVICE_RUNNING=false
    echo "Service is not running"
fi

# Stop service if running
if [ "$SERVICE_RUNNING" = true ]; then
    echo -e "${GREEN}▶${NC} Stopping gate-controller service..."
    ssh "${RPI_USER}@${RPI_HOST}" "sudo systemctl stop gate-controller"
    echo -e "${GREEN}✓${NC} Service stopped"
fi

# Run deployment (without backup to save time)
echo -e "${GREEN}▶${NC} Deploying updates..."
./deployment/scripts/deploy.sh --no-backup

# Restart service if it was running
if [ "$SERVICE_RUNNING" = true ]; then
    echo -e "${GREEN}▶${NC} Starting gate-controller service..."
    ssh "${RPI_USER}@${RPI_HOST}" "sudo systemctl start gate-controller"
    
    # Wait a bit for service to start
    sleep 3
    
    # Check if service started successfully
    if ssh "${RPI_USER}@${RPI_HOST}" "systemctl is-active --quiet gate-controller" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Service started successfully"
        
        # Show recent logs
        echo ""
        echo -e "${BLUE}Recent logs:${NC}"
        ssh "${RPI_USER}@${RPI_HOST}" "sudo journalctl -u gate-controller -n 20 --no-pager"
    else
        echo -e "${YELLOW}⚠${NC} Service failed to start. Check logs:"
        echo "  ssh ${RPI_USER}@${RPI_HOST} 'sudo journalctl -u gate-controller -n 50'"
    fi
fi

echo ""
echo -e "${GREEN}✓${NC} Update completed!"
echo ""

