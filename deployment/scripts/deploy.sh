#!/bin/bash
#
# Gate Controller Deployment Script for Raspberry Pi
# 
# This script deploys the gate controller to fokhomerpi.local
# Usage: ./deploy.sh [--no-backup] [--config CONFIG_FILE]
#

set -e  # Exit on error

# Configuration
RPI_HOST="${RPI_HOST:-fokhomerpi.local}"
RPI_USER="${RPI_USER:-pi}"
RPI_DEPLOY_DIR="/home/${RPI_USER}/gate_controller"
LOCAL_CONFIG="${LOCAL_CONFIG:-config/config.yaml}"
BACKUP_DIR="deployment/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
DO_BACKUP=true
CUSTOM_CONFIG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-backup)
            DO_BACKUP=false
            shift
            ;;
        --config)
            CUSTOM_CONFIG="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Use custom config if provided
if [ -n "$CUSTOM_CONFIG" ]; then
    LOCAL_CONFIG="$CUSTOM_CONFIG"
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Gate Controller Raspberry Pi Deployment         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print step
print_step() {
    echo -e "${GREEN}▶${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Check if config file exists
if [ ! -f "$LOCAL_CONFIG" ]; then
    print_error "Configuration file not found: $LOCAL_CONFIG"
    echo "Please create your config.yaml from config.example.yaml"
    exit 1
fi

# Check SSH connection
print_step "Testing SSH connection to ${RPI_USER}@${RPI_HOST}..."
if ! ssh -o ConnectTimeout=5 "${RPI_USER}@${RPI_HOST}" "echo 'Connection successful'" > /dev/null 2>&1; then
    print_error "Cannot connect to ${RPI_USER}@${RPI_HOST}"
    echo "Please check:"
    echo "  1. Raspberry Pi is powered on and connected to network"
    echo "  2. SSH is enabled on Raspberry Pi"
    echo "  3. You can SSH manually: ssh ${RPI_USER}@${RPI_HOST}"
    exit 1
fi
print_success "SSH connection established"

# Create backup if requested and deployment exists
if [ "$DO_BACKUP" = true ]; then
    print_step "Checking for existing deployment..."
    if ssh "${RPI_USER}@${RPI_HOST}" "[ -d ${RPI_DEPLOY_DIR} ]" 2>/dev/null; then
        print_step "Creating backup of existing deployment..."
        BACKUP_NAME="gate_controller_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
        mkdir -p "$BACKUP_DIR"
        
        ssh "${RPI_USER}@${RPI_HOST}" "cd ${RPI_DEPLOY_DIR} && tar -czf /tmp/${BACKUP_NAME} --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' ."
        scp "${RPI_USER}@${RPI_HOST}:/tmp/${BACKUP_NAME}" "${BACKUP_DIR}/"
        ssh "${RPI_USER}@${RPI_HOST}" "rm /tmp/${BACKUP_NAME}"
        
        print_success "Backup created: ${BACKUP_DIR}/${BACKUP_NAME}"
    else
        print_warning "No existing deployment found, skipping backup"
    fi
fi

# Create deployment directory
print_step "Creating deployment directory..."
ssh "${RPI_USER}@${RPI_HOST}" "mkdir -p ${RPI_DEPLOY_DIR}"

# Copy application files
print_step "Copying application files..."
rsync -avz --delete \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='logs/' \
    --exclude='config/config.yaml' \
    --exclude='.pytest_cache/' \
    --exclude='*.log' \
    --exclude='deployment/backups/' \
    ./ "${RPI_USER}@${RPI_HOST}:${RPI_DEPLOY_DIR}/"

print_success "Application files copied"

# Copy configuration file
print_step "Copying configuration file..."
ssh "${RPI_USER}@${RPI_HOST}" "mkdir -p ${RPI_DEPLOY_DIR}/config"
scp "$LOCAL_CONFIG" "${RPI_USER}@${RPI_HOST}:${RPI_DEPLOY_DIR}/config/config.yaml"
print_success "Configuration file copied"

# Create logs directory
print_step "Creating logs directory..."
ssh "${RPI_USER}@${RPI_HOST}" "mkdir -p ${RPI_DEPLOY_DIR}/logs"

# Install Python dependencies
print_step "Installing Python dependencies..."
ssh "${RPI_USER}@${RPI_HOST}" << ENDSSH
cd ${RPI_DEPLOY_DIR}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install it first:"
    echo "  sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ENDSSH

print_success "Dependencies installed"

# Install systemd service
print_step "Installing systemd service..."
ssh "${RPI_USER}@${RPI_HOST}" << ENDSSH
# Replace pi user with actual user in service file
sed -e "s|/home/pi/|/home/${RPI_USER}/|g" \
    -e "s|User=pi|User=${RPI_USER}|g" \
    -e "s|Group=pi|Group=${RPI_USER}|g" \
    ${RPI_DEPLOY_DIR}/deployment/systemd/gate-controller.service | sudo tee /etc/systemd/system/gate-controller.service > /dev/null
sudo systemctl daemon-reload
ENDSSH

print_success "Systemd service installed"

# Ask user if they want to enable and start the service
echo ""
echo -e "${YELLOW}Deployment completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the deployed files on the Raspberry Pi"
echo "  2. Enable the service to start on boot:"
echo -e "     ${BLUE}ssh ${RPI_USER}@${RPI_HOST} 'sudo systemctl enable gate-controller'${NC}"
echo "  3. Start the service:"
echo -e "     ${BLUE}ssh ${RPI_USER}@${RPI_HOST} 'sudo systemctl start gate-controller'${NC}"
echo "  4. Check service status:"
echo -e "     ${BLUE}ssh ${RPI_USER}@${RPI_HOST} 'sudo systemctl status gate-controller'${NC}"
echo "  5. View logs:"
echo -e "     ${BLUE}ssh ${RPI_USER}@${RPI_HOST} 'sudo journalctl -u gate-controller -f'${NC}"
echo ""
echo "Web Dashboard will be available at:"
echo -e "  ${GREEN}http://fokhomerpi.local:8000${NC}"
echo -e "  ${GREEN}http://192.168.100.185:8000${NC}"
echo ""

print_success "Deployment completed!"

