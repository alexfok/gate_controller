#!/bin/bash
#
# Restore Gate Controller data to Raspberry Pi
#
# Usage: ./restore.sh backup_file.tar.gz
#

set -e

# Configuration
RPI_HOST="${RPI_HOST:-fokhomerpi.local}"
RPI_USER="${RPI_USER:-pi}"
RPI_DEPLOY_DIR="/home/${RPI_USER}/gate_controller"

# Check arguments
if [ $# -eq 0 ]; then
    echo "Error: Backup file not specified"
    echo "Usage: $0 <backup_file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -1 deployment/backups/ 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Gate Controller Restore"
echo "════════════════════════"
echo ""
echo "⚠ WARNING: This will overwrite current configuration and data!"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo ""
echo "▶ Stopping service..."
ssh "${RPI_USER}@${RPI_HOST}" "sudo systemctl stop gate-controller" 2>/dev/null || true

echo "▶ Uploading backup..."
scp "$BACKUP_FILE" "${RPI_USER}@${RPI_HOST}:/tmp/restore_backup.tar.gz"

echo "▶ Extracting backup..."
ssh "${RPI_USER}@${RPI_HOST}" << ENDSSH
cd ${RPI_DEPLOY_DIR}
tar -xzf /tmp/restore_backup.tar.gz
rm /tmp/restore_backup.tar.gz
ENDSSH

echo "▶ Starting service..."
ssh "${RPI_USER}@${RPI_HOST}" "sudo systemctl start gate-controller"

echo ""
echo "✓ Restore completed!"
echo ""
echo "Check service status:"
echo "  ssh ${RPI_USER}@${RPI_HOST} 'sudo systemctl status gate-controller'"
echo ""

