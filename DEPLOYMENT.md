# Raspberry Pi Deployment Guide

Complete guide for deploying the Gate Controller to your Raspberry Pi (fokhomerpi.local) for 24/7 operation.

## Overview

The Gate Controller will run as a systemd service on your Raspberry Pi, providing:
- 24/7 automated gate control
- BLE token scanning
- Web dashboard accessible on your local network
- Automatic restart on failures
- Logs via systemd journal

## Prerequisites

### Hardware
- Raspberry Pi 4/5 (recommended) or Pi 3B+
- Built-in Bluetooth or USB Bluetooth adapter
- SD card with Raspberry Pi OS installed
- Network connection (WiFi or Ethernet)

### Network
- Raspberry Pi accessible at `fokhomerpi.local` or `192.168.100.185`
- SSH access enabled on Raspberry Pi
- Pi and your Mac on the same network

### Local Machine
- SSH key-based authentication set up (or password access)
- Config file created: `config/config.yaml`

## Deployment Steps

### Step 1: Initial Raspberry Pi Setup

Run this **ONCE** to prepare your Raspberry Pi:

```bash
# From your Mac, run setup on the Pi
ssh pi@fokhomerpi.local 'bash -s' < deployment/scripts/setup_rpi.sh
```

This will:
- Update system packages
- Install Python 3, Bluetooth tools, and dependencies
- Configure Bluetooth for BLE scanning
- Create application directory
- Set proper permissions

**Reboot the Pi after setup:**
```bash
ssh pi@fokhomerpi.local 'sudo reboot'
```

Wait 30 seconds, then verify Bluetooth is working:
```bash
ssh pi@fokhomerpi.local 'hciconfig hci0'
```

### Step 2: Deploy Application

Deploy the gate controller from your Mac:

```bash
# Make scripts executable
chmod +x deployment/scripts/*.sh

# Deploy to Raspberry Pi
./deployment/scripts/deploy.sh
```

The deployment script will:
1. Test SSH connection
2. Create backup of existing deployment (if any)
3. Copy application files via rsync
4. Copy your configuration file
5. Install Python dependencies in a virtual environment
6. Install systemd service

### Step 3: Start the Service

Enable and start the gate controller:

```bash
# Enable service to start on boot
ssh pi@fokhomerpi.local 'sudo systemctl enable gate-controller'

# Start the service
ssh pi@fokhomerpi.local 'sudo systemctl start gate-controller'

# Check status
ssh pi@fokhomerpi.local 'sudo systemctl status gate-controller'
```

### Step 4: Verify Deployment

Check service status:

```bash
./deployment/scripts/status.sh
```

Or manually:

```bash
# View live logs
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f'

# Check if web dashboard is accessible
curl http://fokhomerpi.local:8000/api/status
```

Access the web dashboard:
- From your network: **http://fokhomerpi.local:8000**
- Or by IP: **http://192.168.100.185:8000**

## Management Scripts

All management scripts are in `deployment/scripts/`:

### Check Status

```bash
./deployment/scripts/status.sh          # Show system and service status
./deployment/scripts/status.sh --logs   # Include recent logs
```

### Update Application

```bash
# After making code changes, update the deployment
./deployment/scripts/update.sh
```

This will:
- Stop the service
- Deploy new code
- Restart the service
- Show recent logs

### Backup & Restore

```bash
# Create backup
./deployment/scripts/backup.sh

# Create named backup
./deployment/scripts/backup.sh "before_update"

# Restore from backup
./deployment/scripts/restore.sh deployment/backups/gate_controller_backup_20250108_120000.tar.gz
```

Backups include:
- Configuration files (`config.yaml`)
- Activity logs
- Token database

## Service Management

### Systemd Commands

```bash
# Start service
ssh pi@fokhomerpi.local 'sudo systemctl start gate-controller'

# Stop service
ssh pi@fokhomerpi.local 'sudo systemctl stop gate-controller'

# Restart service
ssh pi@fokhomerpi.local 'sudo systemctl restart gate-controller'

# Check status
ssh pi@fokhomerpi.local 'sudo systemctl status gate-controller'

# Enable auto-start on boot
ssh pi@fokhomerpi.local 'sudo systemctl enable gate-controller'

# Disable auto-start
ssh pi@fokhomerpi.local 'sudo systemctl disable gate-controller'
```

### View Logs

```bash
# Live logs (follow mode)
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f'

# Last 100 lines
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -n 100'

# Logs since today
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller --since today'

# Logs with errors only
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -p err'
```

## Configuration

### Update Configuration

1. Edit your local `config/config.yaml`
2. Deploy the updated config:

```bash
# Option 1: Full deployment
./deployment/scripts/deploy.sh

# Option 2: Copy config only
scp config/config.yaml pi@fokhomerpi.local:/home/pi/gate_controller/config/
ssh pi@fokhomerpi.local 'sudo systemctl restart gate-controller'
```

### Configuration File Location

On Raspberry Pi: `/home/pi/gate_controller/config/config.yaml`

## Troubleshooting

### Service Won't Start

Check logs for errors:
```bash
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -n 50'
```

Common issues:
- **Config file not found**: Ensure config.yaml was copied
- **Bluetooth permission error**: Run setup script again
- **Module import errors**: Reinstall dependencies in venv
- **Port 8000 in use**: Check for other processes

### BLE Scanning Not Working

Check Bluetooth status:
```bash
ssh pi@fokhomerpi.local 'hciconfig hci0'
ssh pi@fokhomerpi.local 'sudo systemctl status bluetooth'
```

Reset Bluetooth:
```bash
ssh pi@fokhomerpi.local 'sudo systemctl restart bluetooth'
ssh pi@fokhomerpi.local 'sudo hciconfig hci0 down && sudo hciconfig hci0 up'
```

### Web Dashboard Not Accessible

Check if service is running:
```bash
./deployment/scripts/status.sh
```

Test locally on Pi:
```bash
ssh pi@fokhomerpi.local 'curl http://localhost:8000'
```

Check firewall:
```bash
ssh pi@fokhomerpi.local 'sudo ufw status'
```

### High CPU Usage

Check process stats:
```bash
ssh pi@fokhomerpi.local 'top -p $(pgrep -f gate_controller)'
```

Adjust scan intervals in `config.yaml`:
```yaml
gate:
  ble_scan_interval: 10  # Increase from 5 to 10 seconds
  status_check_interval: 60  # Increase from 30 to 60 seconds
```

### Service Crashes on Startup

View full logs:
```bash
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller --since "5 minutes ago"'
```

Test manually:
```bash
ssh pi@fokhomerpi.local
cd /home/pi/gate_controller
source venv/bin/activate
python3 -m gate_controller.web_main --config config/config.yaml
```

## Monitoring

### Service Health

```bash
# Quick status check
./deployment/scripts/status.sh

# Check if service is active
ssh pi@fokhomerpi.local 'systemctl is-active gate-controller'

# Check uptime
ssh pi@fokhomerpi.local 'systemctl show gate-controller -p ActiveEnterTimestamp'
```

### System Resources

```bash
# CPU and memory
ssh pi@fokhomerpi.local 'htop'

# Disk space
ssh pi@fokhomerpi.local 'df -h'

# Temperature
ssh pi@fokhomerpi.local 'vcgencmd measure_temp'
```

### Network Access

Check if dashboard is accessible from other devices on your network:
```bash
# From any device on your network
http://fokhomerpi.local:8000
http://192.168.100.185:8000
```

## Maintenance

### Regular Tasks

**Weekly:**
- Check service status
- Review logs for errors
- Monitor disk space

**Monthly:**
- Create backup
- Update Raspberry Pi OS: `ssh pi@fokhomerpi.local 'sudo apt update && sudo apt upgrade'`
- Review activity logs

**As Needed:**
- Update gate controller code
- Add/remove tokens
- Adjust configuration

### Log Rotation

Logs are managed by systemd journal. Configure retention:

```bash
ssh pi@fokhomerpi.local 'sudo nano /etc/systemd/journald.conf'
```

Add/modify:
```ini
[Journal]
SystemMaxUse=100M
MaxRetentionSec=7day
```

Apply changes:
```bash
ssh pi@fokhomerpi.local 'sudo systemctl restart systemd-journald'
```

## Security Considerations

### Network Security

- Dashboard has no authentication (designed for local network)
- Run behind firewall
- Consider VPN for remote access
- Optionally restrict to local network only

### System Security

```bash
# Keep system updated
ssh pi@fokhomerpi.local 'sudo apt update && sudo apt upgrade'

# Enable firewall (optional)
ssh pi@fokhomerpi.local 'sudo ufw enable'
ssh pi@fokhomerpi.local 'sudo ufw allow 8000/tcp'  # Dashboard
ssh pi@fokhomerpi.local 'sudo ufw allow 22/tcp'    # SSH
```

### Credentials

- `config.yaml` is never committed to git
- Stored only on Pi at `/home/pi/gate_controller/config/config.yaml`
- Readable only by `pi` user
- Included in backups (store backups securely)

## Uninstall

To remove the gate controller from Raspberry Pi:

```bash
# Stop and disable service
ssh pi@fokhomerpi.local 'sudo systemctl stop gate-controller'
ssh pi@fokhomerpi.local 'sudo systemctl disable gate-controller'

# Remove service file
ssh pi@fokhomerpi.local 'sudo rm /etc/systemd/system/gate-controller.service'
ssh pi@fokhomerpi.local 'sudo systemctl daemon-reload'

# Remove application directory
ssh pi@fokhomerpi.local 'rm -rf /home/pi/gate_controller'
```

## Next Steps

After successful deployment:

1. **Test the System**
   - Open web dashboard
   - Test manual gate control
   - Register test tokens
   - Verify BLE scanning

2. **Configure Tokens**
   - Register your iBeacons/phones
   - Test automatic gate opening
   - Adjust timeouts as needed

3. **Monitor for First Few Days**
   - Check logs regularly
   - Verify reliability
   - Fine-tune configuration

4. **Set Up Monitoring Alerts** (optional)
   - Configure email alerts for service failures
   - Set up uptime monitoring
   - Create dashboard bookmarks

## Support

If you encounter issues:

1. Check logs: `./deployment/scripts/status.sh --logs`
2. Verify configuration: `ssh pi@fokhomerpi.local 'cat /home/pi/gate_controller/config/config.yaml'`
3. Test connectivity: Ensure Pi and Control4 can communicate
4. Review this documentation for troubleshooting steps

## Summary

**Quick Reference:**

```bash
# Deploy
./deployment/scripts/deploy.sh

# Check status
./deployment/scripts/status.sh

# Update
./deployment/scripts/update.sh

# Backup
./deployment/scripts/backup.sh

# View logs
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f'

# Web dashboard
http://fokhomerpi.local:8000
```

