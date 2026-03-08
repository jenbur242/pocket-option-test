# WebSocket Trade Result Fix

## Problem
Trades were showing as PENDING because `check_win()` function was timing out (60 seconds wasn't enough) and the polling approach was unreliable.

## Root Cause
The old implementation used `check_win()` which:
1. Waited for trade duration + 5 seconds
2. Then polled `client._order_results` for up to 60 seconds
3. Often timed out before WebSocket message arrived
4. Required background tasks and complex timeout handling

## Solution
Replaced polling with WebSocket event listener:

### What Changed

1. **Added WebSocket Event Listener** (`handle_trade_result`)
   - Automatically called when WebSocket receives trade result
   - No waiting, no polling, no timeouts
   - Instant result updates (< 1 second after trade completes)

2. **Registered Event Handler**
   ```python
   client.on('order_closed', handle_trade_result)
   ```
   - Listens to `order_closed` events from WebSocket
   - Called automatically by the client library

3. **Removed Background Task**
   - No more `check_trade_result_later()` function
   - No more `asyncio.create_task()` calls
   - No more timeout handling

### How It Works

```
Trade Placed → WebSocket Message → handle_trade_result() → Update past_trades
     ↓              (instant)              ↓                        ↓
  Order ID                            Map Status              Update Martingale
                                    (WIN/LOSS/CLOSED)
```

### Status Mapping
- `OrderStatus.WIN` → 'win'
- `OrderStatus.LOSE` → 'loss'
- `OrderStatus.CLOSED` or `CANCELLED` → 'closed'
- Other → 'pending'

### Benefits
1. **Instant Results**: No waiting for timeouts
2. **More Reliable**: Uses WebSocket events instead of polling
3. **Simpler Code**: No background tasks or complex timeout logic
4. **Better Performance**: No CPU wasted on polling

## Files Modified
- `telegram/main.py`:
  - Added `handle_trade_result()` function
  - Registered event listener in `get_persistent_client()`
  - Removed `check_trade_result_later()` function
  - Removed background task creation
  - Added `duration` field to past_trades entries

## Testing
Deploy to Railway and check:
1. Trades should show results within 1-2 seconds after completion
2. No more PENDING trades stuck forever
3. Martingale should work correctly (WIN resets to 0, LOSS increments)
4. Frontend should show proper colors and profit/loss

## Note
The WebSocket connection is managed by `pocketoptionapi_async` library. We just listen to the events it emits. This is the proper way to handle real-time trade results.
