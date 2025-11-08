# Raspberry Pi Deployment - Ready for Review

## 📋 Overview

All Phase 3 deployment scripts and documentation are complete and ready for your review before actual deployment to `fokhomerpi.local`.

**Branch:** `feature/raspberry-pi-deployment`  
**GitHub:** https://github.com/alexfok/gate_controller/tree/feature/raspberry-pi-deployment

## 🎯 What's Included

### 1. Deployment Scripts (`deployment/scripts/`)

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup_rpi.sh` | Initial Pi setup (run once) | `ssh pi@fokhomerpi.local 'bash -s' < deployment/scripts/setup_rpi.sh` |
| `deploy.sh` | Main deployment | `./deployment/scripts/deploy.sh` |
| `update.sh` | Quick updates | `./deployment/scripts/update.sh` |
| `status.sh` | Check service status | `./deployment/scripts/status.sh` |
| `backup.sh` | Create backups | `./deployment/scripts/backup.sh` |
| `restore.sh` | Restore from backup | `./deployment/scripts/restore.sh backup.tar.gz` |

### 2. Systemd Service (`deployment/systemd/gate-controller.service`)

Configures the gate controller to run 24/7 with:
- ✅ Auto-start on boot
- ✅ Automatic restart on failure (up to 5 times in 5 minutes)
- ✅ Resource limits (512MB RAM, 50% CPU)
- ✅ Logging to systemd journal
- ✅ Runs as `pi` user
- ✅ Security hardening

### 3. Documentation

- **DEPLOYMENT.md** - Complete deployment guide (400+ lines)
  - Prerequisites
  - Step-by-step deployment
  - Service management
  - Troubleshooting
  - Maintenance
  - Security considerations

- **deployment/README.md** - Scripts reference
  - Quick start guide
  - Detailed script usage
  - Environment variables
  - Workflow examples

## 🔍 Review Checklist

Before deploying, please review:

### Configuration

- [ ] **Config file** - Your `config/config.yaml` contains correct:
  - Control4 IP: `192.168.100.30`
  - Control4 credentials
  - Gate device IDs
  - Notification agent ID
  - Timeouts and intervals

### Raspberry Pi Access

- [ ] **SSH connection** - Can you connect?
  ```bash
  ssh pi@fokhomerpi.local
  # or
  ssh pi@192.168.100.185
  ```

- [ ] **Raspberry Pi OS** - Is it updated?
  ```bash
  ssh pi@fokhomerpi.local 'cat /etc/os-release'
  ```

### Deployment Scripts Review

- [ ] **setup_rpi.sh** (lines 1-72)
  - Installs: Python 3, Bluetooth tools, dependencies
  - Enables Bluetooth service
  - Sets up permissions
  - Creates directories

- [ ] **deploy.sh** (lines 1-197)
  - Tests SSH connection
  - Creates automatic backup
  - Copies files via rsync (excludes venv, logs, config.yaml)
  - Creates virtual environment
  - Installs dependencies
  - Installs systemd service

- [ ] **Systemd service** (lines 1-38)
  - WorkingDirectory: `/home/pi/gate_controller`
  - ExecStart: Uses venv Python
  - Config: `/home/pi/gate_controller/config/config.yaml`
  - Port: `8000`
  - Restart policy: Always (with limits)

### Security Review

- [ ] **Config file** - NOT in git (only local)
- [ ] **Credentials** - Your C4 password in config.yaml
- [ ] **Network** - Pi and C4 controller can communicate
- [ ] **Port 8000** - Dashboard port (check firewall if needed)

## 🚀 Deployment Plan

### Phase 1: Setup (One-Time)

```bash
# 1. Run initial setup on Pi
ssh pi@fokhomerpi.local 'bash -s' < deployment/scripts/setup_rpi.sh

# 2. Reboot Pi
ssh pi@fokhomerpi.local 'sudo reboot'

# Wait 30 seconds for reboot
```

**Estimated time:** 5-10 minutes

### Phase 2: Deploy

```bash
# 3. Deploy application
./deployment/scripts/deploy.sh

# Output will show:
#   ✓ SSH connection
#   ✓ Files copied
#   ✓ Config copied
#   ✓ Dependencies installed
#   ✓ Service installed
```

**Estimated time:** 3-5 minutes

### Phase 3: Start Service

```bash
# 4. Enable auto-start
ssh pi@fokhomerpi.local 'sudo systemctl enable gate-controller'

# 5. Start service
ssh pi@fokhomerpi.local 'sudo systemctl start gate-controller'

# 6. Check status
./deployment/scripts/status.sh
```

**Estimated time:** 1 minute

### Phase 4: Verify

```bash
# Check service logs
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f'

# Access dashboard
open http://fokhomerpi.local:8000
# or
open http://192.168.100.185:8000
```

## 📊 What Will Happen

### On Raspberry Pi

1. **Directory Structure:**
   ```
   /home/pi/gate_controller/
   ├── gate_controller/        # Application code
   ├── config/
   │   └── config.yaml        # Your configuration (copied from Mac)
   ├── logs/                  # Activity and system logs
   ├── venv/                  # Python virtual environment
   ├── requirements.txt
   └── ...
   ```

2. **Service:**
   - Runs automatically on boot
   - Restarts on failure
   - Logs to systemd journal

3. **Network Services:**
   - Web dashboard on port 8000
   - BLE scanning for iBeacons
   - C4 API communication to 192.168.100.30

### Expected Behavior

- ✅ Service starts within 10 seconds of boot
- ✅ Web dashboard accessible immediately
- ✅ BLE scanning begins automatically
- ✅ Gate opens when registered token detected
- ✅ Notifications sent to C4 app
- ✅ Auto-close after timeout
- ✅ Activity logged

## 🔧 Management After Deployment

### Daily Operations

```bash
# Check status
./deployment/scripts/status.sh

# View live logs
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f'

# Restart service
ssh pi@fokhomerpi.local 'sudo systemctl restart gate-controller'
```

### Updates

```bash
# After code changes
git pull
./deployment/scripts/update.sh
```

### Backups

```bash
# Create backup before changes
./deployment/scripts/backup.sh "before_update"

# Restore if needed
./deployment/scripts/restore.sh deployment/backups/backup_file.tar.gz
```

## ⚠️ Important Notes

### Before Deployment

1. **Test config locally first:**
   ```bash
   python3 -m gate_controller.web_main --config config/config.yaml
   ```

2. **Verify C4 connectivity from Pi:**
   ```bash
   ssh pi@fokhomerpi.local 'ping -c 3 192.168.100.30'
   ```

3. **Backup existing setup** (if upgrading):
   - Manual backup of any existing files on Pi

### During Deployment

- Don't interrupt the deployment
- Ensure stable network connection
- Keep SSH session active

### After Deployment

- Monitor logs for first 30 minutes
- Test manual gate control via dashboard
- Register tokens and test auto-opening
- Verify notifications in C4 app

## 🐛 Rollback Plan

If something goes wrong:

```bash
# Stop service
ssh pi@fokhomerpi.local 'sudo systemctl stop gate-controller'

# Restore from backup
./deployment/scripts/restore.sh deployment/backups/[latest_backup].tar.gz

# Or remove service
ssh pi@fokhomerpi.local 'sudo systemctl disable gate-controller'
ssh pi@fokhomerpi.local 'sudo rm /etc/systemd/system/gate-controller.service'
```

## 📝 Checklist Summary

Before proceeding:

- [ ] Reviewed all scripts
- [ ] Config file ready with correct credentials
- [ ] SSH access to Pi verified
- [ ] Understand deployment steps
- [ ] Know how to check logs
- [ ] Know how to rollback if needed
- [ ] Ready to deploy!

## 🎯 Next Steps

**After your review:**

1. If everything looks good:
   - Follow the deployment plan above
   - Monitor for issues
   - Test functionality

2. If you find issues or have questions:
   - Let me know what needs to be changed
   - I'll update the scripts accordingly

3. After successful deployment:
   - Test for 24-48 hours
   - Fine-tune configuration
   - Consider merging to main branch

## 📞 Quick Reference

**Deployment Commands:**
```bash
# Setup (once)
ssh pi@fokhomerpi.local 'bash -s' < deployment/scripts/setup_rpi.sh
ssh pi@fokhomerpi.local 'sudo reboot'

# Deploy
./deployment/scripts/deploy.sh

# Start
ssh pi@fokhomerpi.local 'sudo systemctl enable gate-controller'
ssh pi@fokhomerpi.local 'sudo systemctl start gate-controller'

# Check
./deployment/scripts/status.sh
```

**Dashboard URLs:**
- http://fokhomerpi.local:8000
- http://192.168.100.185:8000

**Logs:**
```bash
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f'
```

---

**Ready to deploy?** Review the scripts and documentation, then follow the deployment plan above!

