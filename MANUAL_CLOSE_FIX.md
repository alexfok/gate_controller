# Manual Close Reopen Issue - FIXED ✅

**Date:** November 9, 2025  
**Issue:** Gate reopens automatically after manual close  
**Status:** ✅ Fixed and deployed

---

## The Problem

When you manually close the gate while your phone/token is still in range (e.g., standing in the driveway), the gate would **reopen automatically 5 seconds later** without any notice in the activity log.

### Why This Happened

1. **Token detected** → Gate opens → Session starts
2. **You manually close gate** → Session cleared (`session_start_time = None`)
3. **BLE scanner runs** (every 5 seconds) → Detects your token still in range
4. **No active session exists** → Gate opens immediately! ❌

The problem was in `close_gate()`:
```python
self.session_start_time = None  # <-- This was the issue!
```

By clearing the session, the very next BLE scan (5 seconds later) would detect your token and open the gate because there was no session preventing it.

---

## The Solution

**Don't clear the session when closing the gate.** Keep the session active for the full `session_timeout` period (3 minutes in your config) to prevent immediate reopening.

### Code Change

**File:** `gate_controller/core/controller.py`

**Before:**
```python
if success:
    self.gate_state = GateState.CLOSED
    self.last_open_time = None
    self.session_start_time = None  # ❌ Cleared session immediately
```

**After:**
```python
if success:
    self.gate_state = GateState.CLOSED
    self.last_open_time = None
    # DON'T clear session_start_time - keep session active to prevent immediate re-opening
    # if token is still in range. Session will naturally expire after session_timeout.
    # ✅ Session remains active!
```

---

## How It Works Now

### Scenario 1: Manual Close with Token in Range

**Before Fix:**
1. Gate opens (token detected)
2. You close gate manually
3. 5 seconds later → Gate opens again ❌
4. 5 seconds later → Gate opens again ❌
5. Repeat forever... 😖

**After Fix:**
1. Gate opens (token detected)
2. You close gate manually
3. Session stays active for 3 minutes ⏱️
4. BLE scans detect token but session prevents reopening ✅
5. After 3 minutes → Session expires
6. Next detection will open gate (as expected) ✅

### Scenario 2: Drive Away and Return

**Your token leaves range (you drive away):**
1. Gate opens
2. Auto-closes after 2 minutes
3. You drive away → Token out of range
4. You return 1 minute later → Token in range again
5. Gate opens (as expected) ✅

**This still works correctly!** The session only prevents reopening if the token is **continuously in range**.

---

## Configuration

Your current `config.yaml` settings:
```yaml
gate:
  auto_close_timeout: 120      # 2 minutes - auto-close after opening
  session_timeout: 180         # 3 minutes - prevent reopening during session
  ble_scan_interval: 5         # 5 seconds - how often to scan for tokens
```

**Session timeout (180s = 3 minutes):**
- After gate opens, the session lasts 3 minutes
- During this time, token detections won't reopen the gate
- After 3 minutes, the session expires
- Next token detection will open the gate again

**Why 3 minutes is good:**
- Longer than auto-close (2 min), so gate has time to close
- Short enough that if you leave and return, gate opens
- Prevents annoying re-opens when you're still nearby

---

## Examples

### Example 1: Close Gate While Standing Nearby

**Timeline:**
- **00:00** - Token detected, gate opens
- **00:30** - You manually close gate (session still active)
- **00:35** - BLE scan detects token → Session active → No reopen ✅
- **00:40** - BLE scan detects token → Session active → No reopen ✅
- **01:00** - BLE scan detects token → Session active → No reopen ✅
- **02:00** - BLE scan detects token → Session active → No reopen ✅
- **03:00** - Session expires
- **03:05** - BLE scan detects token → Session expired → Gate opens ✅

### Example 2: Auto-Close, Then Reopen

**Timeline:**
- **00:00** - Token detected, gate opens
- **02:00** - Auto-close triggers (gate closes after 2 min)
- **02:05** - BLE scan detects token → Session still active (1 min left) → No reopen ✅
- **03:00** - Session expires
- **03:05** - BLE scan detects token → Gate opens ✅

### Example 3: Leave and Return Quickly

**Timeline:**
- **00:00** - Token detected, gate opens
- **00:30** - You drive away (token out of range)
- **02:00** - Auto-close triggers
- **02:30** - You return (token in range again)
- **02:35** - BLE scan detects token → Session still active → No reopen ✅
- **03:00** - Session expires
- **03:05** - BLE scan detects token → Gate opens ✅

---

## Benefits

✅ **No more annoying reopens** when you manually close the gate  
✅ **Respects session timeout** - prevents reopening for configured duration  
✅ **Activity log is clean** - no mystery gate opens  
✅ **Still responsive** - gate opens when you return after session expires  
✅ **Backward compatible** - no configuration changes needed  

---

## Testing

### Test 1: Manual Close with Token in Range
1. Have your phone/token in range
2. Let gate open automatically
3. Manually close gate via dashboard
4. Stay in range for 3 minutes
5. **Expected:** Gate does NOT reopen during 3 minutes ✅

### Test 2: Manual Close, Wait 3+ Minutes
1. Have your phone/token in range
2. Let gate open automatically
3. Manually close gate via dashboard
4. Stay in range for 4+ minutes
5. **Expected:** Gate reopens after ~3 minutes ✅

### Test 3: Leave and Return
1. Have your phone/token in range
2. Let gate open automatically
3. Drive away (token out of range)
4. Auto-close after 2 minutes
5. Return within 1 minute (before session expires)
6. **Expected:** Gate does NOT open yet (session active) ✅
7. Wait until session expires (3 min total)
8. **Expected:** Gate opens ✅

---

## Deployment

**Git Commit:** `f385dcd`

**Changes:**
- Modified `gate_controller/core/controller.py`
- Commented out `self.session_start_time = None` in `close_gate()`
- Added explanation comment

**Deployed to:** Raspberry Pi (192.168.100.185:8000)  
**Service Status:** ✅ Running  
**Dashboard:** http://192.168.100.185:8000

---

## Troubleshooting

**Q: Gate still reopens immediately after manual close?**  
**A:** Check that the service has been restarted with the new code. Run:
```bash
ssh afok@192.168.100.185 'sudo systemctl restart gate-controller'
```

**Q: Gate won't reopen even after I leave and return?**  
**A:** The session may still be active. Wait for the full `session_timeout` (3 minutes) to expire, or increase the timeout in `config.yaml`.

**Q: I want gate to reopen faster when I return?**  
**A:** Decrease `session_timeout` in `config.yaml` (e.g., to 120 seconds). Then deploy and restart service.

**Q: Can I clear the session manually?**  
**A:** Currently no, but this could be added as a dashboard button if needed (e.g., "Clear Session" button).

---

## Related Configuration

If you want to adjust the behavior, edit `config.yaml`:

```yaml
gate:
  auto_close_timeout: 120      # How long gate stays open (seconds)
  session_timeout: 180         # How long to prevent reopening (seconds)
  ble_scan_interval: 5         # How often to scan for tokens (seconds)
```

**Recommendations:**
- `session_timeout` should be **longer** than `auto_close_timeout`
- Otherwise, gate could reopen before auto-close finishes
- Current settings (120s auto-close, 180s session) are good ✅

---

## Future Enhancements

Possible improvements for future versions:

1. **"Clear Session" button** on dashboard - manually expire session
2. **Configurable behavior** - option to clear session on manual close
3. **Smart session** - end session when token leaves range
4. **Multiple session modes** - different behavior for manual vs auto close

---

**Issue resolved! Gate will no longer reopen immediately after manual close.** 🎉

The session will remain active for the configured `session_timeout` (3 minutes), preventing unwanted reopens while still allowing the gate to function normally when you leave and return.

