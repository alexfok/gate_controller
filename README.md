# Gate Controller

Automated gate control system with BLE token detection and Control4 integration.

## Features

- **BLE Token Detection**: Automatically scan for registered Bluetooth Low Energy tokens (iBeacon support)
- **Automatic Gate Control**: Open gate when registered tokens are detected
- **Control4 Integration**: Control gates through Control4 system with retry logic
- **Push Notifications**: Send push notifications to Control4 app when gate is opened/closed
- **Token Management**: Register and manage authorized BLE tokens via CLI or web interface
- **Web Dashboard**: ✨ **NEW** Beautiful web interface with real-time monitoring and control
- **Activity Logging**: Complete history of all gate and token events
- **Raspberry Pi Deployment**: (Phase 3) Ready for deployment on Raspberry Pi 5

## Architecture

```
gate_controller/
├── gate_controller/          # Main package
│   ├── api/                  # API integrations (Control4)
│   ├── ble/                  # BLE token scanning (iBeacon support)
│   ├── core/                 # Core business logic & activity logging
│   ├── web/                  # Web dashboard (FastAPI + WebSocket)
│   ├── config/               # Configuration management
│   └── utils/                # Utility functions
├── tests/                    # Test suite
├── config/                   # Configuration files
└── docs/                     # Documentation
```

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copy `config/config.example.yaml` to `config/config.yaml` and update with your settings:

```yaml
c4:
  ip: "192.168.100.30"
  username: "your-email@example.com"
  password: "your-password"
  gate_device_id: 348
  open_gate_scenario: 21
  close_gate_scenario: 22

gate:
  auto_close_timeout: 300  # seconds
  session_timeout: 60      # seconds
  status_check_interval: 30
  ble_scan_interval: 5

tokens:
  registered: []
```

## Usage

### Option 1: Run with Web Dashboard (Recommended)

```bash
python -m gate_controller.web_main --config config/config.yaml
```

Then open your browser to: **http://localhost:8000**

The dashboard provides:
- 📊 Real-time gate status monitoring
- 🎮 Manual gate control (open/close buttons)
- 🔑 Token management interface
- 📜 Activity log viewer
- 🔄 Live WebSocket updates

See [WEB_DASHBOARD.md](WEB_DASHBOARD.md) for full documentation.

### Option 2: Run CLI Mode Only

```bash
python -m gate_controller --config config/config.yaml
```

### Manage tokens via CLI:

```bash
# Register a new token
python -m gate_controller.cli --config config/config.yaml register-token --uuid "ABC123" --name "John's Phone"

# List registered tokens with live detection status
python -m gate_controller.cli --config config/config.yaml list-tokens

# Remove a token
python -m gate_controller.cli --config config/config.yaml unregister-token --uuid "ABC123"

# Scan for nearby BLE devices
python -m gate_controller.cli --config config/config.yaml scan-devices
```

### Manual gate control via CLI:

```bash
# Open gate
python -m gate_controller.cli --config config/config.yaml open-gate

# Close gate
python -m gate_controller.cli --config config/config.yaml close-gate

# Check gate status
python -m gate_controller.cli --config config/config.yaml check-status
```

## Raspberry Pi Deployment

Deploy the gate controller to your Raspberry Pi for 24/7 operation:

```bash
# 1. Initial Pi setup (run once)
ssh pi@fokhomerpi.local 'bash -s' < deployment/scripts/setup_rpi.sh

# 2. Deploy application
./deployment/scripts/deploy.sh

# 3. Enable and start service
ssh pi@fokhomerpi.local 'sudo systemctl enable gate-controller'
ssh pi@fokhomerpi.local 'sudo systemctl start gate-controller'

# 4. Check status
./deployment/scripts/status.sh
```

**Web dashboard will be available at:**
- http://fokhomerpi.local:8000
- http://192.168.100.185:8000

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide.

## Development

### Run tests:

```bash
pytest tests/
```

### Run with verbose logging:

```bash
python -m gate_controller --verbose
```

## Project Phases

### Phase 1: Core Backend ✅ Complete
- ✅ C4 API integration with retry logic
- ✅ BLE token scanning with iBeacon support
- ✅ Automated gate control logic
- ✅ Token management via CLI
- ✅ Comprehensive tests
- ✅ Pushed to GitHub

### Phase 2: Web Dashboard ✅ Complete
- ✅ FastAPI REST API server
- ✅ WebSocket for real-time updates
- ✅ Modern responsive UI
- ✅ Activity logging system
- ✅ Token management interface
- ✅ Manual gate controls
- ✅ Pushed to GitHub

### Phase 3: Raspberry Pi Deployment ✅ Complete
- ✅ Systemd service for 24/7 operation
- ✅ Automated deployment scripts
- ✅ Backup and restore tools
- ✅ Status monitoring scripts
- ✅ Complete documentation
- ⏳ Ready for deployment review

## License

MIT

