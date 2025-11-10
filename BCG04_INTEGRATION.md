# BCG04 External BLE Scanner Integration

## Overview

This guide explains how to use an external BCG04 BLE gateway to scan for beacons and trigger gate opening via HTTP API.

**Benefits of external BCG04:**
- ✅ **Better range**: Commercial-grade BLE scanner (100m+ range)
- ✅ **Optimal placement**: Can be positioned near driveway entry
- ✅ **Better signal**: Not affected by RPI's metal enclosure
- ✅ **Dedicated hardware**: No interference with RPI's other tasks

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Car with  │         │    BCG04    │         │  RPI Gate   │
│   Beacon    │  BLE    │   Gateway   │  HTTP   │ Controller  │
│             │────────>│             │────────>│             │
│ (BC-U1 Pro) │         │  (Scanner)  │         │ (Business   │
└─────────────┘         └─────────────┘         │  Logic)     │
                                                 └─────────────┘
```

## API Endpoint

### `GET /api/token/detected` (Recommended for BCG04)

Endpoint for external BLE scanners to report token detections via HTTP GET.

**URL:** `http://192.168.100.185:8000/api/token/detected`

**Method:** `GET` (also supports `POST`)

**Query Parameters:**
- `uuid` (required) - Token UUID, e.g., `426c7565-4368-6172-6d42-6561636f6e67`
- `name` (optional) - Token name, e.g., `BCPro_Alex`
- `rssi` (optional) - Signal strength in dBm, e.g., `-45`
- `distance` (optional) - Estimated distance in meters, e.g., `0.5`

**Example GET Request:**
```
GET http://192.168.100.185:8000/api/token/detected?uuid=426c7565-4368-6172-6d42-6561636f6e67&rssi=-45
```

**Example POST Request (alternative):**
```bash
curl -X POST http://192.168.100.185:8000/api/token/detected \
     -H "Content-Type: application/json" \
     -d '{"uuid": "426c7565-4368-6172-6d42-6561636f6e67", "rssi": -45}'
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Token detected and processed",
  "token": "BCPro_Alex",
  "action": "processed"
}
```

**Response (Token Not Registered):**
```json
{
  "success": false,
  "message": "Token not registered",
  "action": "ignored"
}
```

**Response (Token Paused):**
```json
{
  "success": false,
  "message": "Token is paused",
  "action": "ignored"
}
```

## Business Logic

The endpoint automatically handles:

1. **Token Validation**: Checks if token is registered
2. **Active Status**: Respects token's `active` flag (paused tokens ignored)
3. **Session Management**: Prevents re-opening within session timeout
4. **Cooldown**: Respects gate state and cooldown periods
5. **Activity Logging**: Logs all detection events
6. **WebSocket Broadcast**: Updates dashboard in real-time

**This is the same logic as internal BLE scanning!**

## BCG04 Configuration

### Option 1: BCG04 with HTTP GET (Most Common)

Most BCG04 gateways only support HTTP GET on beacon detection.

**Configuration:**
1. Access BCG04 web interface (usually `http://bcg04-ip`)
2. Go to **Settings** → **iBeacon Detection** or **HTTP Notification**
3. Enable **HTTP Notification** or **Webhook**
4. Set **Target URL**: 
   ```
   http://192.168.100.185:8000/api/token/detected?uuid={UUID}&rssi={RSSI}
   ```
5. Set **Method**: `GET` (or leave as default)

**Common variable placeholders:**
- `{UUID}` or `%UUID%` or `$UUID` - iBeacon UUID
- `{RSSI}` or `%RSSI%` or `$RSSI` - Signal strength
- `{MAJOR}` or `%MAJOR%` - iBeacon Major value
- `{MINOR}` or `%MINOR%` - iBeacon Minor value

**Example URL formats:**
```
http://192.168.100.185:8000/api/token/detected?uuid={UUID}
http://192.168.100.185:8000/api/token/detected?uuid={UUID}&rssi={RSSI}
http://192.168.100.185:8000/api/token/detected?uuid=%UUID%&rssi=%RSSI%
```

### Option 2: BCG04 with HTTP POST (Less Common)

Some BCG04 models support HTTP POST.

**Configuration:**
1. Access BCG04 web interface (usually `http://bcg04-ip`)
2. Go to **Settings** → **iBeacon Detection**
3. Enable **HTTP Notification**
4. Set **Target URL**: `http://192.168.100.185:8000/api/token/detected`
5. Set **Method**: `POST`
6. Set **Body Template**:
   ```json
   {
     "uuid": "{UUID}",
     "rssi": {RSSI}
   }
   ```

### Option 2: BCG04 with MQTT Bridge

If your BCG04 supports MQTT, use a simple bridge script:

**Python Bridge Script:**
```python
import paho.mqtt.client as mqtt
import requests
import json

CONTROLLER_URL = "http://192.168.100.185:8000/api/token/detected"
MQTT_BROKER = "bcg04-ip"
MQTT_TOPIC = "bcg04/beacons/+/detected"

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    requests.post(CONTROLLER_URL, json={
        "uuid": data['uuid'],
        "rssi": data.get('rssi'),
        "distance": data.get('distance')
    })

client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER)
client.subscribe(MQTT_TOPIC)
client.loop_forever()
```

### Option 3: Custom Script on BCG04

If BCG04 supports custom scripts (e.g., Linux-based), run a scanner script:

**Bash Example:**
```bash
#!/bin/bash
CONTROLLER="http://192.168.100.185:8000/api/token/detected"

# Scan for beacons
hcitool lescan --duplicates | while read addr type rest; do
    # Parse UUID from advertisement data
    UUID=$(parse_uuid "$addr")  # Implement based on BCG04
    
    # POST to controller
    curl -X POST "$CONTROLLER" \
         -H "Content-Type: application/json" \
         -d "{\"uuid\":\"$UUID\"}"
done
```

## Testing

### Local Test (Before BCG04 Setup)

```bash
# Test the endpoint manually
python3 test_bcg04_endpoint.py

# Simulate a single detection
python3 test_bcg04_endpoint.py simulate
```

### cURL Test

**GET Method (Recommended):**
```bash
# Test with registered token (UUID only)
curl "http://192.168.100.185:8000/api/token/detected?uuid=426c7565-4368-6172-6d42-6561636f6e67"

# Test with UUID and RSSI
curl "http://192.168.100.185:8000/api/token/detected?uuid=426c7565-4368-6172-6d42-6561636f6e67&rssi=-45"

# Expected response:
# {"success":true,"message":"Token detected and processed","token":"BCPro_Alex","action":"processed"}
```

**POST Method (Alternative):**
```bash
# Test with registered token
curl -X POST http://192.168.100.185:8000/api/token/detected \
     -H "Content-Type: application/json" \
     -d '{
       "uuid": "426c7565-4368-6172-6d42-6561636f6e67",
       "rssi": -45,
       "distance": 0.5
     }'
```

### Check Activity Log

```bash
# View activity log to verify detections
curl http://192.168.100.185:8000/api/activity?limit=10
```

## Dual Scanner Setup (Optional)

You can run **both** internal BLE scanning and BCG04 simultaneously!

**Benefits:**
- **Redundancy**: If one fails, the other still works
- **Coverage**: Internal scanner covers close range, BCG04 covers far range
- **Reliability**: Better detection accuracy

**How it works:**
1. Internal RPI BLE scanner runs as before
2. BCG04 also scans and posts detections
3. Both call `_handle_token_detected`
4. Session management prevents duplicate gate opens

**No configuration needed** - just works!

## Troubleshooting

### Token Not Detected

1. **Check BCG04 is scanning:**
   ```bash
   # Check BCG04 logs (if accessible)
   ssh bcg04-ip
   tail -f /var/log/beacon_scanner.log
   ```

2. **Test endpoint manually:**
   ```bash
   curl -X POST http://192.168.100.185:8000/api/token/detected \
        -H "Content-Type: application/json" \
        -d '{"uuid":"YOUR-TOKEN-UUID"}'
   ```

3. **Check token is registered:**
   ```bash
   curl http://192.168.100.185:8000/api/tokens
   ```

### Token Detected But Gate Doesn't Open

1. **Check token is active:**
   - Go to dashboard → Tokens Management
   - Verify token shows "✅ Active" (not "⏸️ Paused")

2. **Check session timeout:**
   - If gate recently opened, session timeout prevents immediate re-opening
   - Wait for `session_timeout` to expire (default: 180s)

3. **Check activity log:**
   ```bash
   curl http://192.168.100.185:8000/api/activity?limit=20
   ```
   Look for "Token detected" and gate opening events

### BCG04 Can't Reach Controller

1. **Network connectivity:**
   ```bash
   # From BCG04, test connectivity
   ping 192.168.100.185
   curl http://192.168.100.185:8000/api/status
   ```

2. **Firewall:**
   ```bash
   # On RPI, allow port 8000
   sudo ufw allow 8000
   ```

## Optimal Placement

### BCG04 Placement
- **Location**: Near driveway entrance, where cars slow down
- **Height**: 1-2 meters high for best signal propagation
- **Line of sight**: Minimize obstacles to car path
- **Power**: Near power outlet or use PoE if supported
- **Weather protection**: Use weatherproof enclosure if outdoor

### Beacon Placement in Car
- **Dashboard**: Best - near windshield (glass allows BLE signals)
- **Sun visor**: Good - elevated, minimal obstruction
- **Rear-view mirror**: Good - central, elevated
- **Avoid**: Glove compartment, under seats, trunk (metal shielding)

## Performance Optimization

### Increase Detection Range

1. **Beacon TX Power**: Set to max (+4 dBm) in BlueCharm app
2. **Beacon Broadcast Interval**: Set to 100ms (fastest)
3. **BCG04 Scan Interval**: Set to continuous or 1-second intervals
4. **Multiple BCG04s**: Place at entry and exit points

### Reduce False Opens

1. **Increase session timeout**: Prevent rapid re-triggering
   ```yaml
   gate:
     session_timeout: 300  # 5 minutes
   ```

2. **RSSI threshold**: Only trigger on strong signals
   - Modify endpoint to check `rssi > -70` before processing

## Security Considerations

### Authentication (Optional)

Add API key authentication to prevent unauthorized triggers:

**nginx proxy with basic auth:**
```nginx
location /api/token/detected {
    auth_basic "BCG04";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000;
}
```

**Or add to endpoint:**
```python
# In server.py
API_KEY = "your-secret-key"

if request.headers.get("X-API-Key") != API_KEY:
    raise HTTPException(status_code=401, detail="Unauthorized")
```

### Network Security

1. **Firewall**: Restrict port 8000 to local network only
2. **VPN**: Access controller via VPN if exposed to internet
3. **HTTPS**: Use SSL/TLS for production (nginx reverse proxy)

## Migration from Internal to External Scanning

### Step 1: Deploy New Endpoint
```bash
# Already done! Endpoint is live after latest deployment
```

### Step 2: Keep Internal Scanning (Recommended)
```yaml
# config.yaml - no changes needed
gate:
  ble_scan_interval: 5  # Keep internal scanning
```

### Step 3: Configure BCG04
- Set up HTTP POST to `http://192.168.100.185:8000/api/token/detected`
- Test with `curl` first

### Step 4: Monitor Both
- Check dashboard activity log
- Both scanners will report detections
- Session management prevents duplicates

### Step 5: (Optional) Disable Internal Scanning
If BCG04 works perfectly and you want to free up RPI resources:

```yaml
# config.yaml
gate:
  ble_scan_interval: 9999  # Effectively disable (scan every 2.7 hours)
```

## Summary

✅ **New endpoint**: `POST /api/token/detected`  
✅ **Same logic**: Uses identical token detection flow as internal scanner  
✅ **Smart**: Validates tokens, respects sessions, prevents duplicates  
✅ **Dual mode**: Can run with internal scanner simultaneously  
✅ **Tested**: Test script provided for validation  

**Ready to use!** Deploy to RPI and configure your BCG04 to start using external scanning.

