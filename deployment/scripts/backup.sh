#!/bin/bash
#
# Backup Gate Controller data from Raspberry Pi
#
# Usage: ./backup.sh [backup_name]
#

set -e

# Configuration
RPI_HOST="${RPI_HOST:-fokhomerpi.local}"
RPI_USER="${RPI_USER:-pi}"
RPI_DEPLOY_DIR="/home/${RPI_USER}/gate_controller"
BACKUP_DIR="deployment/backups"

# Backup name
if [ -n "$1" ]; then
    BACKUP_NAME="$1"
else
    BACKUP_NAME="gate_controller_backup_$(date +%Y%m%d_%H%M%S)"
fi

echo "Gate Controller Backup"
echo "═══════════════════════"
echo ""
echo "▶ Creating backup: ${BACKUP_NAME}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup on Raspberry Pi
echo "▶ Creating backup archive..."
ssh "${RPI_USER}@${RPI_HOST}" << ENDSSH
cd ${RPI_DEPLOY_DIR}
tar -czf /tmp/${BACKUP_NAME}.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    config/ \
    logs/
ENDSSH

# Download backup
echo "▶ Downloading backup..."
scp "${RPI_USER}@${RPI_HOST}:/tmp/${BACKUP_NAME}.tar.gz" "${BACKUP_DIR}/"

# Clean up remote backup
ssh "${RPI_USER}@${RPI_HOST}" "rm /tmp/${BACKUP_NAME}.tar.gz"

echo ""
echo "✓ Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo ""
echo "Backup contains:"
echo "  - Configuration files (config.yaml)"
echo "  - Activity logs"
echo "  - Token database"
echo ""
echo "To restore:"
echo "  ./restore.sh ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo ""

