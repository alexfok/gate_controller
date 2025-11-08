# Deployment Instructions

## Phase 1: Core Backend (✅ COMPLETED)

The core backend is complete and ready for deployment. The following features are implemented:

### Completed Features
- ✅ C4 API integration (open/close gate, send notifications)
- ✅ BLE token scanning for automatic gate opening
- ✅ Token management (register/unregister)
- ✅ Automatic gate closing with timeout
- ✅ Session management to prevent re-opening
- ✅ Comprehensive test suite
- ✅ CLI for management and manual control
- ✅ Configuration management with YAML

### Project Structure
```
gate_controller/
├── gate_controller/          # Main package
│   ├── api/                  # C4 API integration
│   │   └── c4_client.py      # Control4 client
│   ├── ble/                  # BLE token scanning
│   │   └── scanner.py        # BLE scanner
│   ├── core/                 # Core business logic
│   │   ├── controller.py     # Main controller
│   │   └── token_manager.py  # Token management
│   ├── config/               # Configuration
│   │   └── config.py         # Config manager
│   └── utils/                # Utilities
│       └── logger.py         # Logging
├── tests/                    # Test suite
├── config/                   # Configuration files
│   └── config.example.yaml   # Example config
└── scripts/                  # Scripts (future)
```

## Pushing to GitHub

### Step 1: Authenticate with GitHub

```bash
gh auth login
```

Follow the prompts to authenticate with your GitHub account.

### Step 2: Create GitHub Repository

```bash
# Create public repository
gh repo create gate_controller --public --source=. --description "Automated gate control system with BLE token detection and Control4 integration"

# Push code
git push -u origin main
```

### Alternative: Manual GitHub Setup

If you prefer to use the GitHub web interface:

1. Go to https://github.com/new
2. Repository name: `gate_controller`
3. Description: "Automated gate control system with BLE token detection and Control4 integration"
4. Make it Public
5. Click "Create repository"

Then push your code:

```bash
git remote add origin https://github.com/YOUR_USERNAME/gate_controller.git
git branch -M main
git push -u origin main
```

## Setting Up for Development

### 1. Install Dependencies

```bash
pip install -r requirements-dev.txt
```

### 2. Configure the System

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit configuration
nano config/config.yaml
```

Update with your Control4 credentials:
- `c4.ip`: Your Control4 controller IP (192.168.100.30)
- `c4.username`: Your Control4 account (alexfokil@gmail.com)
- `c4.password`: Your Control4 password
- `c4.open_gate_scenario`: Scenario 21 (or your open gate scenario)
- `c4.close_gate_scenario`: Scenario 22 (or your close gate scenario)

### 3. Test C4 Integration

```bash
# Test opening gate
python -m gate_controller.cli open-gate --config config/config.yaml

# Test closing gate
python -m gate_controller.cli close-gate --config config/config.yaml

# Check gate status
python -m gate_controller.cli check-status --config config/config.yaml
```

### 4. Register BLE Tokens

```bash
# Scan for nearby devices
python -m gate_controller.cli scan-devices --duration 10

# Register a token (use address from scan results)
python -m gate_controller.cli register-token --uuid "AA:BB:CC:DD:EE:FF" --name "John's iPhone"

# List registered tokens
python -m gate_controller.cli list-tokens
```

### 5. Run Tests

```bash
pytest tests/
```

### 6. Start Gate Controller Service

```bash
# Run in foreground (verbose)
python -m gate_controller --config config/config.yaml --verbose

# Run in background
nohup python -m gate_controller --config config/config.yaml > logs/controller.log 2>&1 &
```

## Next Steps

### Phase 2: Web Dashboard (TODO)

Features to implement:
- Web UI for monitoring gate status
- Real-time activity log
- Token management interface
- Manual open/close controls
- Configuration management via UI

Technologies to use:
- Backend: FastAPI or Flask
- Frontend: React or Vue.js
- Real-time: WebSockets for live updates

### Phase 3: Raspberry Pi Deployment (TODO)

Features to implement:
- Systemd service configuration
- Auto-start on boot
- Log rotation
- Watchdog for service monitoring
- Update script
- Backup/restore configuration

Deployment steps:
1. Install dependencies on Raspberry Pi
2. Configure systemd service
3. Set up auto-start
4. Configure log rotation
5. Test and verify

Target: `fokhomerpi.local` (192.168.100.185)

## Troubleshooting

### BLE Scanning Issues

On macOS, BLE scanning requires system permissions:
```bash
# System Preferences → Security & Privacy → Bluetooth
# Allow Terminal or your IDE to access Bluetooth
```

On Linux/Raspberry Pi:
```bash
# Install bluez
sudo apt-get install bluez

# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER
```

### Control4 Connection Issues

- Verify controller IP is correct
- Ensure controller is on same network
- Check credentials are correct
- Verify gate device ID and scenario numbers

### Permission Issues

```bash
# Make sure you have write permissions
chmod 755 gate_controller/
chmod 644 config/config.yaml
```

## Support

For issues or questions:
1. Check the README.md for usage documentation
2. Review test cases in `tests/` for examples
3. Check logs in `logs/gate_controller.log`

