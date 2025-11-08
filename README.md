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

## Development

### Run tests:

```bash
pytest tests/
```

### Run with verbose logging:

```bash
python -m gate_controller --verbose
```

## Phases

### Phase 1: Core Backend (Current)
- ✅ C4 API integration
- ✅ BLE token scanning
- ✅ Gate control logic
- ✅ Token management
- ✅ Tests

### Phase 2: Web Dashboard
- Web UI for monitoring and control
- Real-time gate activity log
- Token management interface
- Manual open/close controls

### Phase 3: Raspberry Pi Deployment
- Deployment scripts for fokhomerpi.local
- Systemd service configuration
- Auto-start on boot
- Log rotation and monitoring

## License

MIT

