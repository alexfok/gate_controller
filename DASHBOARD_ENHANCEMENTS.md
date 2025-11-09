# Dashboard Enhancements - Phase 5

## New Features

### 1. Active Attribute for Tokens
- Added `active` field to token schema (default: True)
- Tokens can be enabled/disabled without deletion
- Only active tokens trigger gate opening

### 2. Full Beacon Scan
- New "Scan All Devices" button to discover ALL nearby beacons
- Shows iBeacons and regular BLE devices
- Similar to CLI `scan-devices` command

### 3. Edit Token Functionality
- Edit token name
- Toggle active/inactive status
- Changes save to config file

### 4. Smart Add Token Dialog
- Auto-scans for nearby beacons when dialog opens
- Shows list of discovered beacons to choose from
- Still allows manual UUID entry

## Backend Changes (Completed ✅)

### Config Class (`config/config.py`)
- Updated `add_token()` to include `active` parameter
- Added `update_token()` method for editing tokens

### TokenManager (`core/token_manager.py`)
- Updated `register_token()` to include `active`
- Added `update_token()` method

### API Endpoints (`web/server.py`)
- **POST `/api/tokens`** - Now includes `active` field
- **PATCH `/api/tokens/{uuid}`** - NEW: Update token attributes
- **GET `/api/scan/all?duration=10`** - NEW: Full beacon scan

## Frontend Changes (In Progress)

### Required UI Updates

1. **Token List Display**
   - Show active/inactive status with toggle
   - Add "Edit" button for each token
   - Visual indicator for inactive tokens (grayed out)

2. **Add Token Modal**
   - "Scan for Beacons" button
   - List of discovered beacons
   - Manual entry option
   - Active checkbox (default: checked)

3. **Edit Token Modal**
   - Edit name field
   - Active/Inactive toggle
   - Save/Cancel buttons

4. **Scan All Button**
   - New button in Tokens Management tab
   - Shows scanning progress
   - Displays results in modal/section

## Status
- ✅ Backend implementation complete
- ⏳ Frontend UI implementation in progress
- ⏳ Testing pending
- ⏳ Deployment pending

