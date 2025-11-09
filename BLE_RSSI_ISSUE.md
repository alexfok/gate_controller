# BLE RSSI Issue on Raspberry Pi

## Problem
Activity logs show `RSSI: 0 dBm (Excellent)` with no distance estimation, even though the beacon is being detected successfully.

## Root Cause
The Raspberry Pi's BLE stack (BlueZ) is not populating the `rssi` field in the BLE device object during passive scanning. This is a known issue with:
- Certain Bluetooth adapters
- Newer BlueZ versions
- Passive scanning mode (vs active scanning)

## Why RSSI = 0 Leads to No Distance
```python
# Line 180 in scanner.py
if rssi == 0:
    return -1.0  # Unknown distance
```

When RSSI is 0 (invalid), distance estimation returns -1.0, which is then filtered out of the logs.

## Potential Solutions

### Option 1: Try advertisement_data.rssi (Implemented)
Updated scanner to check both `device.rssi` and `advertisement_data.rssi`:
```python
rssi = getattr(device, 'rssi', None)
if rssi is None:
    rssi = advertisement_data.rssi if hasattr(advertisement_data, 'rssi') else 0
```

### Option 2: Enable Active Scanning
Active scanning (sending scan requests) provides better RSSI accuracy but uses more power:
```python
scanner = BleakScanner(
    detection_callback=detection_callback,
    scanning_mode="active"  # vs "passive"
)
```

### Option 3: Use bluetoothctl (System Level)
Check if the system-level Bluetooth reports RSSI:
```bash
sudo bluetoothctl scan on
# Look for RSSI values in output
```

### Option 4: Update BlueZ
Upgrade to the latest BlueZ version:
```bash
sudo apt update
sudo apt upgrade bluez
```

### Option 5: Use Different BLE Library
Consider using `pybluez` or direct `dbus` communication instead of `bleak`.

## Diagnosis Steps

1. **Check if RSSI is available at all:**
```bash
ssh afok@192.168.100.185 'sudo hcitool lescan & sleep 5 && sudo hcitool leinfo <MAC_ADDRESS>'
```

2. **Check BlueZ version:**
```bash
ssh afok@192.168.100.185 'bluetoothctl --version'
```

3. **Check Bluetooth adapter info:**
```bash
ssh afok@192.168.100.185 'hciconfig -a'
```

4. **Monitor service logs for new warning:**
```bash
ssh afok@192.168.100.185 'sudo journalctl -u gate-controller -f | grep RSSI'
```

If you see "RSSI not available" warnings, the BLE adapter doesn't support RSSI reporting in passive mode.

## Current Status
- ✅ Beacon detection works
- ✅ Gate opens/closes properly
- ✅ Activity logging works
- ❌ RSSI values not available (showing as 0)
- ❌ Distance estimation not working (returns -1.0)

## Impact
- **Low**: RSSI and distance are nice-to-have features for troubleshooting and distance-based automation
- Gate opening/closing functionality is **NOT affected**
- Dashboard will show tokens as online/offline, just without signal strength info

## Next Steps
1. Deploy updated scanner with better RSSI detection
2. Check logs for "RSSI not available" warnings
3. If still failing, try active scanning mode
4. If still failing, may need to use different BLE approach or accept limitation

