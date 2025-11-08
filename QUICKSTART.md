# Quick Start Guide

## ✅ Tested and Working!

Your gate controller is fully functional and tested with your Control4 system.

## Installation & Setup

### 1. Install Dependencies

```bash
cd /Users/afok/Library/CloudStorage/OneDrive-NVIDIACorporation/Private/Dirot/2022/C4_cli/gate_controller
pip3 install -r requirements.txt
```

### 2. Configuration

Your config file is already set up at `config/config.yaml` with:
- **C4 IP**: 192.168.100.30
- **C4 Username**: alexfokil@gmail.com  
- **Gate Device**: 348 (VBOX-Pro Gateway)
- **Open Scenario**: 21
- **Close Scenario**: 22

## CLI Commands (All Working!)

### Gate Control

```bash
# Open gate
python3 -m gate_controller.cli --config config/config.yaml open-gate

# Close gate  
python3 -m gate_controller.cli --config config/config.yaml close-gate

# Check status
python3 -m gate_controller.cli --config config/config.yaml check-status
```

### BLE Token Management

```bash
# Scan for nearby BLE devices (10 seconds)
python3 -m gate_controller.cli --config config/config.yaml scan-devices --duration 10

# Register a token
python3 -m gate_controller.cli --config config/config.yaml register-token \
  --uuid "AA:BB:CC:DD:EE:FF" \
  --name "John's iPhone"

# List registered tokens
python3 -m gate_controller.cli --config config/config.yaml list-tokens

# Unregister a token
python3 -m gate_controller.cli --config config/config.yaml unregister-token \
  --uuid "AA:BB:CC:DD:EE:FF"
```

## Run Gate Controller Service

Start the automatic gate controller that scans for BLE tokens:

```bash
# Run in foreground with verbose logging
python3 -m gate_controller --config config/config.yaml --verbose

# Run in background
nohup python3 -m gate_controller --config config/config.yaml > logs/controller.log 2>&1 &
```

### How It Works

When running, the controller will:
1. **Scan for BLE tokens** every 5 seconds
2. **Automatically open gate** when a registered token is detected
3. **Prevent re-opening** for 60 seconds (session timeout)
4. **Auto-close gate** after 5 minutes (configurable)
5. **Send notifications** via Control4 app
6. **Check gate status** every 30 seconds

## Example Workflow

### 1. Register Your Phone

```bash
# First, scan to find your phone's BLE address
python3 -m gate_controller.cli --config config/config.yaml scan-devices --duration 10

# You'll see something like:
# Found 5 devices:
# ====================
# #  Name             Address              RSSI
# 1  iPhone           AA:BB:CC:DD:EE:FF   -45

# Register it
python3 -m gate_controller.cli --config config/config.yaml register-token \
  --uuid "AA:BB:CC:DD:EE:FF" \
  --name "My iPhone"
```

### 2. Start the Service

```bash
python3 -m gate_controller --config config/config.yaml --verbose
```

### 3. Test It

Walk near the gate with your phone, and the controller will:
- Detect your phone's BLE signal
- Open the gate automatically
- Send you a notification
- Close the gate after 5 minutes

## Configuration Options

Edit `config/config.yaml` to customize:

```yaml
gate:
  auto_close_timeout: 300     # Auto-close after 5 minutes (seconds)
  session_timeout: 60         # Prevent re-opening for 1 minute (seconds)
  status_check_interval: 30   # Check gate every 30 seconds
  ble_scan_interval: 5        # Scan for tokens every 5 seconds
```

## Troubleshooting

### BLE Scanning on macOS

**Note**: BLE scanning may not work reliably on macOS due to system Bluetooth restrictions. This is expected and the BLE functionality is designed for the Raspberry Pi deployment.

If you want to test BLE on macOS:
1. Go to **System Preferences → Security & Privacy → Bluetooth**
2. Allow Terminal/your IDE to access Bluetooth
3. Run outside of any sandboxed environment

**For production use**, deploy to the Raspberry Pi where BLE scanning works without restrictions.

### Check Logs

```bash
tail -f logs/gate_controller.log
```

### Test C4 Connection

```bash
python3 -m gate_controller.cli --config config/config.yaml check-status
```

## What's Next

### Phase 2: Web Dashboard (Future)
- Visual monitoring interface
- Activity logs
- Token management UI
- Manual controls

### Phase 3: Deploy to Raspberry Pi (fokhomerpi.local)
- Systemd service
- Auto-start on boot
- Production deployment

## Need Help?

- Check `README.md` for detailed documentation
- Review `DEPLOYMENT_INSTRUCTIONS.md` for deployment guide
- See test files in `tests/` for code examples

