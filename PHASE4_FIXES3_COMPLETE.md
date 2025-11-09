# Phase 4 Fixes 3 - Multiple Gate Opens Issue

## Date: 2025-11-09

## Issue
Gate was opening multiple times (every 2 minutes) when beacon remained in range, with no corresponding gate close events between opens.

### Timeline of Issue
- 11:07:47 AM - Gate opened (first detection after service restart)
- 11:09:47 AM - Gate opened (2 minutes later)
- 11:11:48 AM - Gate opened (2 minutes later)

## Root Cause
The session timeout (2 minutes) was shorter than the auto-close timeout (5 minutes), causing a problematic cycle:

1. T=0: Token detected → Gate opens → Session starts
2. T=0-2min: Token continuously detected, but session prevents re-opening
3. T=2min: Session expires (time_since_session >= session_timeout)
4. T=2min+: Next token detection → **Opens gate again** (even though already open!)
5. T=2min+: Last_open_time resets, auto-close timer resets
6. Repeat every 2 minutes...

**The gate never closed** because the auto-close timer kept resetting before it could reach 5 minutes.

## Solution
Added a check to prevent opening the gate if it's already OPEN or OPENING, regardless of session timeout status.

### Code Change
**File:** `gate_controller/core/controller.py`

**Before:**
```python
# Check if we're in an active session
if self.session_start_time:
    time_since_session = (datetime.now() - self.session_start_time).total_seconds()
    
    if time_since_session < self.config.session_timeout:
        self.logger.debug(f"Still in active session ({time_since_session}s)")
        return

# Start new session BEFORE opening gate to prevent race condition
self.session_start_time = datetime.now()

# Open the gate
await self.open_gate(f"Token detected: {name}")
```

**After:**
```python
# Don't open if gate is already open or opening
if self.gate_state in [GateState.OPEN, GateState.OPENING]:
    self.logger.debug(f"Gate is already {self.gate_state.value}, not opening again")
    return

# Check if we're in an active session
if self.session_start_time:
    time_since_session = (datetime.now() - self.session_start_time).total_seconds()
    
    if time_since_session < self.config.session_timeout:
        self.logger.debug(f"Still in active session ({time_since_session}s)")
        return

# Start new session BEFORE opening gate to prevent race condition
self.session_start_time = datetime.now()

# Open the gate
await self.open_gate(f"Token detected: {name}")
```

## Expected Behavior After Fix
1. **T=0**: Token detected → Gate opens → Session starts
2. **T=0-5min**: Token continuously detected, but gate is OPEN so no action taken
3. **T=5min**: Auto-close timeout triggers → Gate closes → Session ends
4. **T=5min+**: If token still in range → Gate opens again (new session)
5. **T=5min+ to T=10min**: Cycle repeats

## Key Improvements
- ✅ Gate will only open once until it closes
- ✅ Auto-close timeout will work properly (gate closes after 5 minutes)
- ✅ Activity log will show proper open/close pairs
- ✅ Session timeout still prevents rapid re-opening after gate closes
- ✅ Multiple "gate opened" events without corresponding closes are eliminated

## Testing Notes
With beacon continuously in range:
- **Expected**: Gate opens → waits 5 min → gate closes → token still detected → gate opens → repeat
- **Activity log pattern**: Open, [5min wait], Close, Open, [5min wait], Close, ...
- **Not**: Open, Open, Open (every 2 minutes) ❌

## Files Modified
1. `gate_controller/core/controller.py` - Added gate state check before opening

## Status
**Ready for deployment**

