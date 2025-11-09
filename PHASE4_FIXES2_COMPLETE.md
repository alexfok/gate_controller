# Phase 4 Fixes 2 - Complete

## Date: 2025-11-09

## Overview
This document summarizes the completion of Phase 4 Fixes 2, addressing critical dashboard issues related to data refresh, WebSocket broadcasting, and service restart functionality.

## Issues Addressed

### 1. Activity Log Empty ("loading activity...")
**Problem**: Dashboard showed "loading activity..." but never loaded entries.
**Root Cause**: API returned `{"entries": [...]}` but JavaScript expected `{"activity": [...]}`.
**Fix**: Changed `/api/activity` endpoint to return `{"activity": entries}` instead of `{"entries": entries}`.
**Files Modified**:
- `gate_controller/web/server.py` (line 191)

### 2. Token Detection Not Broadcasting to Dashboard
**Problem**: Registered tokens stayed "offline" even when detected, and "Recently Detected Tokens" list remained empty.
**Root Cause**: 
- Controller wasn't calling `broadcast_token_detected()` when tokens were detected
- WebSocket broadcast didn't include RSSI and distance data
**Fix**: 
- Added `dashboard_server` parameter to `GateController`
- Modified controller to call `dashboard_server.broadcast_token_detected()` with RSSI and distance
- Updated `broadcast_token_detected()` to include RSSI and distance in WebSocket message
**Files Modified**:
- `gate_controller/core/controller.py` (added dashboard_server parameter, line 33, 44; added broadcast call, line 228-230)
- `gate_controller/web/server.py` (updated broadcast_token_detected signature, line 261-271)
- `gate_controller/web_main.py` (connected controller to dashboard, line 45)

### 3. WebSocket Initial Status Sending Enum Object
**Problem**: WebSocket sent `GateState` enum object instead of string value, causing JSON serialization issues.
**Fix**: Changed WebSocket initial status to send `gate_state.value` instead of `gate_state`.
**Files Modified**:
- `gate_controller/web/server.py` (line 211)

### 4. Tab State Not Persisted on Refresh
**Problem**: Manual page refresh always returned to "Gate Control" tab, losing context.
**Fix**: Added localStorage to save and restore active tab.
**Files Modified**:
- `gate_controller/web/static/js/dashboard.js` (lines 23-27, 55, 58-64)

### 5. Service Restart After Config Changes
**Problem**: No way to restart service after saving configuration changes.
**Fix**: 
- Added `/api/service/restart` POST endpoint that uses systemctl if running under systemd
- Updated dashboard to prompt user to restart service after saving config
**Files Modified**:
- `gate_controller/web/server.py` (added restart endpoint, lines 200-218; added os and subprocess imports, lines 6-7)
- `gate_controller/web/static/js/dashboard.js` (updated saveConfig and added restartService methods, lines 580-632)

## Technical Details

### WebSocket Token Detection Flow
1. BLE scanner detects token → calls `controller._on_token_detected()`
2. Controller calls `controller._handle_token_detected()` with RSSI and distance
3. Controller broadcasts via `dashboard_server.broadcast_token_detected(uuid, name, rssi, distance)`
4. Dashboard receives WebSocket message with type `token_detected`
5. Dashboard updates `detectedTokens` Map and re-renders token lists

### Service Restart Mechanism
- Checks for `INVOCATION_ID` environment variable to detect systemd
- Uses `subprocess.Popen(['sudo', 'systemctl', 'restart', 'gate-controller.service'])` to restart
- Requires sudoers configuration on Raspberry Pi for passwordless restart

### Tab Persistence
- Saves active tab name to localStorage on tab switch
- Restores saved tab on page load (after initial data loading)
- Also triggers data reload for specific tabs (tokens, activity, config)

## Testing Results

### Local Testing (Port 8888)
✅ `/api/status` returns `gate_status` as string value ("unknown", "closed", etc.)
✅ `/api/activity` returns `{"activity": [...]}`
✅ `/api/config` returns configuration with c4 and gate sections
✅ WebSocket initial status sends correct format
✅ Tab switching saves to localStorage

### Expected Behavior on Raspberry Pi
- Token detections will broadcast to dashboard in real-time
- Registered tokens will show online/offline status with RSSI and distance
- Recently detected tokens list will populate
- Activity log will load and display entries
- Manual page refresh will return to the same tab
- Config changes can be applied with automatic service restart (with proper sudoers setup)

## Deployment Notes

### Sudoers Configuration (Optional)
For automatic service restart to work, add the following to `/etc/sudoers.d/gate-controller` on Raspberry Pi:

```bash
afok ALL=(ALL) NOPASSWD: /bin/systemctl restart gate-controller.service
```

Without this, the restart endpoint will return a message asking for manual restart.

## Files Changed
1. `gate_controller/core/controller.py` - Added dashboard_server parameter and broadcast calls
2. `gate_controller/web/server.py` - Fixed activity API response, added restart endpoint, fixed WebSocket initial status, updated broadcast_token_detected
3. `gate_controller/web_main.py` - Connected controller to dashboard
4. `gate_controller/web/static/js/dashboard.js` - Added tab persistence and restart service functionality

## Next Steps
1. ✅ Local testing complete
2. ⏳ Deploy to Raspberry Pi
3. ⏳ Test on actual hardware with BLE token
4. ⏳ Optional: Configure sudoers for automatic restart

## Status
**Phase 4 Fixes 2: COMPLETE (Awaiting Deployment)**

