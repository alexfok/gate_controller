# BLE Signal Strength and Distance Troubleshooting Guide

## Overview

The gate controller now includes comprehensive signal strength monitoring and distance estimation to help you troubleshoot detection issues and optimize your beacon placement.

## Features

### 📊 Signal Strength (RSSI)

**RSSI** (Received Signal Strength Indicator) measures the power of the received radio signal in dBm (decibels relative to one milliwatt).

**Signal Quality Ranges:**
- 🟢 **Excellent** (-60 dBm or higher): Very close, strong signal
- 🟡 **Good** (-70 to -60 dBm): Close range, reliable
- 🟠 **Fair** (-80 to -70 dBm): Medium range, generally reliable
- 🔴 **Weak** (-90 to -80 dBm): Far range, may be unreliable
- ⚫ **Very Weak** (below -90 dBm): Too far, likely unreliable

### 📏 Distance Estimation

The system estimates distance using the **path loss model**:

```
distance = 10^((TxPower - RSSI) / (10 * n))
```

Where:
- **TxPower**: Transmission power at 1 meter (extracted from iBeacon data, typically -59 dBm)
- **RSSI**: Measured signal strength
- **n**: Path loss exponent (2.0 for free space, 2-4 for indoor)

**Note:** Distance is an estimate and affected by:
- Walls and obstacles
- Interference from other devices
- Physical orientation of beacon
- Metal objects and reflections
- Human bodies

## Using Signal Data

### View Signal Info When Scanning

```bash
python3 -m gate_controller.cli --config config/config.yaml scan-devices
```

**Example Output:**

```
📡 Found 2 iBeacon(s):
════════════════════════════════════════════════════════════════════════════════
#  Name              UUID                                  Major  Minor  RSSI      Distance  Signal
─  ────              ────                                  ─────  ─────  ────      ────────  ──────
1  Alex's iPhone     2F234454-CF6D-4A0F-ADF2-F4911BA9FFA6  1      1      -65 dBm   ~2.5m     🟡 Good
2  Test Beacon       E2C56DB5-DFFB-48D2-B060-D0F5A71096E0  0      0      -82 dBm   ~8.3m     🟠 Fair
```

### Monitor Detections in Real-Time

View live logs with signal strength:

```bash
# On Raspberry Pi
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f'

# Or locally
python3 -m gate_controller.web_main --config config/config.yaml
```

**Example Log Output:**

```
2025-11-08 10:15:43 - Detected iBeacon: Alex's iPhone | RSSI: -65 dBm (Good), Distance: ~2.5m
2025-11-08 10:15:48 - Detected iBeacon: Alex's iPhone | RSSI: -68 dBm (Good), Distance: ~3.1m
2025-11-08 10:15:53 - Detected iBeacon: Alex's iPhone | RSSI: -72 dBm (Fair), Distance: ~4.2m
```

### Check Activity Log

The activity log stores signal data for historical analysis:

```bash
# Via CLI
ssh pi@fokhomerpi.local 'cat /home/pi/gate_controller/logs/activity.json'

# Via web dashboard
http://fokhomerpi.local:8000
# View Activity Log section
```

**Activity Log Entry:**

```json
{
  "timestamp": "2025-11-08T10:15:43",
  "type": "token_detected",
  "message": "Token detected: Alex's iPhone | RSSI: -65 dBm (Good) | Distance: ~2.5m",
  "details": {
    "token_uuid": "2f234454-cf6d-4a0f-adf2-f4911ba9ffa6",
    "token_name": "Alex's iPhone",
    "rssi": -65,
    "signal_quality": "Good",
    "distance_meters": 2.5
  }
}
```

## Troubleshooting Scenarios

### 🔴 Issue: Token Not Detected

**Check Signal Strength:**

```bash
# Scan for devices while near the gate
python3 -m gate_controller.cli --config config/config.yaml scan-devices
```

**Analysis:**

| RSSI | Distance | Likely Cause | Solution |
|------|----------|--------------|----------|
| Not visible | N/A | Beacon not transmitting | Check battery, enable Bluetooth |
| < -90 dBm | > 15m | Too far away | Move closer, increase TX power |
| -85 to -90 | 10-15m | Marginal range | Add repeater, optimize placement |

### 🟠 Issue: Intermittent Detection

**Monitor Signal Stability:**

Watch logs for RSSI fluctuations:

```bash
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f | grep RSSI'
```

**Patterns to Look For:**

1. **Steady RSSI (-65, -66, -65, -67)**: Good
   - Normal variation
   - Reliable detection

2. **Fluctuating RSSI (-65, -82, -70, -85)**: Problem
   - Interference or obstacles
   - Check for:
     - WiFi routers nearby
     - Metal objects
     - Moving obstacles (people, doors)

3. **Declining RSSI (-65, -70, -75, -82)**: Moving away
   - Normal as you leave
   - Check session timeout settings

### 🟡 Issue: Opens Too Early/Late

**Optimize Detection Range:**

1. **Measure Your Desired Range:**

```bash
# Stand at desired trigger distance
# Scan and note the RSSI
python3 -m gate_controller.cli --config config/config.yaml scan-devices
```

2. **Adjust Beacon Power:**

- Most beacons allow TX power adjustment (app settings)
- Reduce power to shrink range
- Increase power to extend range

**Distance Guidelines:**

| Desired Range | Target RSSI | Recommended TX Power |
|---------------|-------------|---------------------|
| 1-2m (very close) | -55 to -65 dBm | Low (-20 dBm) |
| 3-5m (close) | -65 to -75 dBm | Medium (-12 dBm) |
| 5-10m (medium) | -75 to -85 dBm | High (-4 dBm) |

### 🔵 Issue: Different Behavior Indoors/Outdoors

**Environment Affects Signal:**

**Indoor** (n = 2.5-3.5):
- More obstacles
- Signal degradation
- Shorter effective range
- More reflections

**Outdoor** (n = 2.0-2.5):
- Line of sight
- Longer range
- More predictable
- Less interference

**Solution:**

Test in actual environment and adjust beacon placement accordingly.

## Best Practices

### 1. Beacon Placement

**Optimal Placement:**
- ✅ Eye level (1.5m height)
- ✅ Clear line of sight to Pi
- ✅ Away from metal surfaces
- ✅ Not in pockets/bags (for testing)

**Avoid:**
- ❌ Behind walls
- ❌ In metal enclosures
- ❌ Near WiFi routers
- ❌ Ground level

### 2. Testing Procedure

**Initial Setup:**

```bash
# 1. Position beacon at desired trigger distance
# 2. Scan and record RSSI
python3 -m gate_controller.cli --config config/config.yaml scan-devices

# 3. Walk approach path 3 times
# 4. Monitor logs for consistent detection
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f'

# 5. Check activity log for signal patterns
```

**What to Look For:**
- Consistent detection at trigger point
- RSSI >= -80 dBm for reliability
- Distance estimate matches reality
- No false positives from far away

### 3. Tuning Configuration

**Scan Interval:**

```yaml
# config.yaml
gate:
  ble_scan_interval: 5  # Scan every 5 seconds
```

- **Faster (2-3s)**: More responsive, more CPU
- **Slower (8-10s)**: Less responsive, less CPU
- **Recommended**: 5 seconds

**Session Timeout:**

```yaml
gate:
  session_timeout: 60  # Don't re-open for 60 seconds
```

- Prevents multiple opens
- Based on RSSI stability
- Adjust based on signal patterns

### 4. Analyzing Historical Data

**Extract Signal Data from Logs:**

```bash
# On Raspberry Pi
cd /home/pi/gate_controller
cat logs/activity.json | grep -A 10 "token_detected"
```

**Look for Patterns:**
- Typical RSSI at trigger point
- Signal strength trends
- Detection reliability
- Distance accuracy

## Advanced Troubleshooting

### Path Loss Exponent Adjustment

The distance calculation uses n=2.0 (free space). For your environment, you might need to adjust this.

**Edit:** `gate_controller/ble/scanner.py`

```python
def _estimate_distance(self, rssi: int, tx_power: int = -59) -> float:
    # Path loss exponent
    n = 2.5  # Change from 2.0 to 2.5 for indoor with obstacles
    
    distance = math.pow(10, (tx_power - rssi) / (10 * n))
    return round(distance, 2)
```

**Calibration:**
1. Measure actual distance
2. Record RSSI
3. Adjust n until distance estimate matches
4. Typical values: 2.0-2.5 (outdoor), 2.5-4.0 (indoor)

### Signal Quality Thresholds

If you want different quality ranges, edit `scanner.py`:

```python
def _format_signal_info(self, rssi: int, distance: float) -> str:
    if rssi >= -55:      # Changed from -60
        quality = "Excellent"
    elif rssi >= -65:    # Changed from -70
        quality = "Good"
    # ... etc
```

### Custom Signal Filtering

Add RSSI threshold to ignore weak signals:

```python
# In scan_once callback
if rssi < -85:  # Ignore signals weaker than -85 dBm
    return
```

## Diagnostic Commands

### Quick Signal Check

```bash
# View all nearby beacons with signal info
python3 -m gate_controller.cli --config config/config.yaml scan-devices

# Check if your beacon is in range
python3 -m gate_controller.cli --config config/config.yaml list-tokens
```

### Signal History

```bash
# View recent detections with signal data
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller --since "1 hour ago" | grep RSSI'

# Count detections by signal quality
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller --since today | grep -o "Good\|Fair\|Weak" | sort | uniq -c'
```

### Live Signal Monitor

```bash
# Watch signal strength in real-time
ssh pi@fokhomerpi.local 'sudo journalctl -u gate-controller -f | grep --line-buffered "RSSI"'
```

## Understanding Your Results

### Good Signal Profile

```
10:15:43 - RSSI: -62 dBm (Good), Distance: ~2.1m
10:15:48 - RSSI: -64 dBm (Good), Distance: ~2.4m
10:15:53 - RSSI: -63 dBm (Good), Distance: ~2.2m
```

✅ Stable, consistent readings  
✅ Signal quality "Good" or better  
✅ Distance estimates reasonable  

### Problem Signal Profile

```
10:15:43 - RSSI: -65 dBm (Good), Distance: ~2.5m
10:15:48 - RSSI: -88 dBm (Weak), Distance: ~12.1m
10:15:53 - RSSI: -72 dBm (Fair), Distance: ~4.2m
```

❌ Erratic RSSI jumps  
❌ Unrealistic distance changes  
❌ Indicates interference or obstacles  

**Actions:**
1. Check for interference sources
2. Reposition beacon
3. Add signal filtering
4. Increase scan interval

## FAQ

**Q: Why does distance seem inaccurate?**  
A: Distance is estimated based on signal strength, which is affected by many factors. It's a useful relative indicator but not precise like GPS.

**Q: What's a "good" RSSI for reliable detection?**  
A: Aim for -70 dBm or better at your trigger point. -80 dBm can work but may be less reliable.

**Q: My beacon shows different RSSI on iPhone vs Raspberry Pi?**  
A: Normal. Different Bluetooth chips have different sensitivities. Calibrate for your Pi.

**Q: Can I set a minimum RSSI threshold?**  
A: Yes, you can add filtering in the scanner code (see Advanced section).

**Q: Does battery level affect RSSI?**  
A: Yes, low battery can reduce transmission power. Replace batteries when signal weakens.

## Summary

**For Best Results:**

1. 🔍 **Test**: Scan at your desired trigger point
2. 📊 **Measure**: Record RSSI and signal quality
3. 📍 **Place**: Position beacon for optimal signal
4. ⚙️ **Tune**: Adjust TX power and scan interval
5. 📝 **Monitor**: Watch logs for consistent behavior
6. 🔄 **Iterate**: Refine based on real-world usage

**Target Metrics:**
- RSSI: -65 to -75 dBm at trigger point
- Signal Quality: "Good" or "Fair"
- Detection Rate: 100% when in range
- False Positives: 0%

With signal strength monitoring, you can now scientifically tune your gate controller for perfect performance! 🎯

