# Deployment Scripts

Scripts for deploying and managing the Gate Controller on Raspberry Pi.

## Quick Start

```bash
# 1. Initial Raspberry Pi setup (run once)
ssh pi@fokhomerpi.local 'bash -s' < scripts/setup_rpi.sh

# 2. Deploy application
./scripts/deploy.sh

# 3. Enable and start service
ssh pi@fokhomerpi.local 'sudo systemctl enable gate-controller'
ssh pi@fokhomerpi.local 'sudo systemctl start gate-controller'

# 4. Check status
./scripts/status.sh
```

## Scripts

### `deploy.sh`
Main deployment script. Copies application files, configuration, and installs dependencies.

**Usage:**
```bash
./scripts/deploy.sh                    # Full deployment with backup
./scripts/deploy.sh --no-backup        # Deploy without backup
./scripts/deploy.sh --config myconfig.yaml  # Use custom config
```

**Environment Variables:**
- `RPI_HOST` - Raspberry Pi hostname (default: fokhomerpi.local)
- `RPI_USER` - SSH user (default: pi)

### `setup_rpi.sh`
Initial Raspberry Pi setup. Installs system packages and configures Bluetooth.

**Usage:**
```bash
ssh pi@fokhomerpi.local 'bash -s' < scripts/setup_rpi.sh
```

**Run this only once** before first deployment.

### `update.sh`
Quick update script. Stops service, deploys new code, restarts service.

**Usage:**
```bash
./scripts/update.sh
```

Equivalent to:
1. Stop service
2. Deploy (without backup)
3. Start service
4. Show logs

### `status.sh`
Check system and service status.

**Usage:**
```bash
./scripts/status.sh          # Show status
./scripts/status.sh --logs   # Show status with recent logs
```

Shows:
- System information (uptime, memory, disk, temperature)
- Service status (running, PID, memory, CPU)
- Web dashboard availability
- Bluetooth status
- Quick commands

### `backup.sh`
Create backup of configuration and data.

**Usage:**
```bash
./scripts/backup.sh                      # Auto-named backup
./scripts/backup.sh "before_update"      # Named backup
```

Backups are saved to `deployment/backups/`

**Includes:**
- Configuration files
- Activity logs
- Token database

**Excludes:**
- Virtual environment
- Python cache files
- Temporary files

### `restore.sh`
Restore from backup.

**Usage:**
```bash
./scripts/restore.sh deployment/backups/gate_controller_backup_20250108_120000.tar.gz
```

**Warning:** This will overwrite current configuration and data.

## Directory Structure

```
deployment/
├── README.md                    # This file
├── systemd/
│   └── gate-controller.service  # Systemd service definition
├── scripts/
│   ├── deploy.sh               # Main deployment script
│   ├── setup_rpi.sh            # Initial Pi setup
│   ├── update.sh               # Quick update
│   ├── status.sh               # Status checker
│   ├── backup.sh               # Backup creator
│   └── restore.sh              # Backup restorer
└── backups/                    # Backup storage (created automatically)
```

## Systemd Service

The gate controller runs as a systemd service for 24/7 operation.

**Service file:** `systemd/gate-controller.service`

**Features:**
- Automatic restart on failure
- Starts after network and Bluetooth
- Runs as `pi` user
- Logs to systemd journal
- Resource limits (512MB RAM, 50% CPU)

**Commands:**
```bash
# Start
sudo systemctl start gate-controller

# Stop
sudo systemctl stop gate-controller

# Restart
sudo systemctl restart gate-controller

# Status
sudo systemctl status gate-controller

# Enable auto-start
sudo systemctl enable gate-controller

# Disable auto-start
sudo systemctl disable gate-controller

# View logs
sudo journalctl -u gate-controller -f
```

## Environment Variables

All scripts support these environment variables:

```bash
export RPI_HOST=fokhomerpi.local   # Or use IP: 192.168.100.185
export RPI_USER=pi
export RPI_DEPLOY_DIR=/home/pi/gate_controller

# Then run any script
./scripts/deploy.sh
```

## Workflow Examples

### First-Time Deployment

```bash
# 1. Setup Pi (once)
ssh pi@fokhomerpi.local 'bash -s' < scripts/setup_rpi.sh

# 2. Reboot Pi
ssh pi@fokhomerpi.local 'sudo reboot'

# Wait 30 seconds...

# 3. Deploy application
./scripts/deploy.sh

# 4. Enable and start
ssh pi@fokhomerpi.local 'sudo systemctl enable gate-controller'
ssh pi@fokhomerpi.local 'sudo systemctl start gate-controller'

# 5. Verify
./scripts/status.sh
open http://fokhomerpi.local:8000
```

### Update After Code Changes

```bash
# Quick method
./scripts/update.sh

# Or manual method
git pull
./scripts/deploy.sh
ssh pi@fokhomerpi.local 'sudo systemctl restart gate-controller'
```

### Create Backup Before Major Change

```bash
# Create backup
./scripts/backup.sh "before_v2_update"

# Make changes and deploy
./scripts/deploy.sh

# If something goes wrong, restore
./scripts/restore.sh deployment/backups/gate_controller_backup_before_v2_update.tar.gz
```

### Check Service Health

```bash
# Quick check
./scripts/status.sh

# Detailed with logs
./scripts/status.sh --logs

# Follow logs in real-time
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f'
```

### Troubleshooting

```bash
# View service status
ssh pi@fokhomerpi.local 'sudo systemctl status gate-controller'

# View recent logs
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -n 100'

# Test manually
ssh pi@fokhomerpi.local
cd /home/pi/gate_controller
source venv/bin/activate
python3 -m gate_controller.web_main --config config/config.yaml

# Check Bluetooth
ssh pi@fokhomerpi.local 'hciconfig hci0'
ssh pi@fokhomerpi.local 'sudo systemctl status bluetooth'

# Check web dashboard locally
ssh pi@fokhomerpi.local 'curl http://localhost:8000/api/status'
```

## Notes

- All scripts use SSH to communicate with the Raspberry Pi
- SSH key-based authentication recommended (faster, more secure)
- Scripts are idempotent - safe to run multiple times
- Backups don't include the virtual environment (recreated on deploy)
- Service automatically restarts on failure
- Logs are managed by systemd journal (automatic rotation)

## See Also

- [DEPLOYMENT.md](../DEPLOYMENT.md) - Complete deployment guide
- [README.md](../README.md) - Main project documentation
- [WEB_DASHBOARD.md](../WEB_DASHBOARD.md) - Web dashboard documentation

