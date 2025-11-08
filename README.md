# Gate Controller

Automated gate control system with BLE token detection and Control4 integration.

## Features

- **BLE Token Detection**: Automatically scan for registered Bluetooth Low Energy tokens
- **Automatic Gate Control**: Open gate when registered tokens are detected
- **Control4 Integration**: Control gates through Control4 system
- **Notifications**: Send push notifications when gate is opened/closed
- **Token Management**: Register and manage authorized BLE tokens
- **Web Dashboard**: (Phase 2) Web interface for monitoring and control
- **Raspberry Pi Deployment**: (Phase 3) Ready for deployment on Raspberry Pi

## Architecture

```
gate_controller/
├── gate_controller/          # Main package
│   ├── api/                  # API integrations (C4, Home Assistant)
│   ├── ble/                  # BLE token scanning
│   ├── core/                 # Core business logic
│   ├── config/               # Configuration management
│   └── utils/                # Utility functions
├── tests/                    # Test suite
├── config/                   # Configuration files
└── scripts/                  # Deployment and utility scripts
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

### Run the gate controller service:

```bash
python -m gate_controller
```

### Manage tokens:

```bash
# Register a new token
python -m gate_controller.cli register-token --uuid "ABC123" --name "John's Phone"

# List registered tokens
python -m gate_controller.cli list-tokens

# Remove a token
python -m gate_controller.cli remove-token --uuid "ABC123"
```

### Manual gate control:

```bash
# Open gate
python -m gate_controller.cli open-gate

# Close gate
python -m gate_controller.cli close-gate

# Check gate status
python -m gate_controller.cli check-status
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

