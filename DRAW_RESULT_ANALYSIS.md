# Draw Result Analysis - Critical Issue Found

## Summary
Your code has a **CRITICAL BUG** in handling draw results. The websocket client determines win/loss based on profit, but **treats zero profit as LOSS instead of DRAW**.

---

## Issue #1: Zero Profit = LOSS (WRONG!)

### Location: `pocketoptionapi_async/client.py` (Lines 1298-1304)

```python
# Determine status
if profit > 0:
    status = OrderStatus.WIN
elif profit < 0:
    status = OrderStatus.LOSE
else:
    status = OrderStatus.LOSE  # ❌ BUG: Default for zero profit
```

### Problem:
- When `profit == 0` (draw/refund), the code sets status to `LOSE`
- This causes martingale to increase step on draws
- Draws should NOT increase martingale step (it's a refund!)

---

## Issue #2: Missing DRAW Status in OrderStatus Enum

### Location: `pocketoptionapi_async/models.py` (Lines 23-40)

```python
class OrderStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    WIN = "win"
    LOSE = "lose"
    # ❌ MISSING: DRAW = "draw"
```

### Problem:
- No `DRAW` status defined in the enum
- Cannot properly represent draw results

---

## Issue #3: No Draw Handling in Martingale Logic

### Location: `telegram/main.py` (Lines 442-454)

```python
# Update martingale step
if result == 'win':
    global_martingale_step = 0
    past_trades[:] = [t for t in past_trades if t['result'] == 'pending']
    log_to_file(f"✅ WIN! Reset step to 0\n")
elif result == 'loss' or result == 'closed':
    if global_martingale_step < 8:
        global_martingale_step += 1
        log_to_file(f"❌ LOSS! Step increased to {global_martingale_step}\n")
    else:
        global_martingale_step = 0
        log_to_file(f"🔄 Max steps reached, reset to 0\n")
# ❌ MISSING: elif result == 'draw': ...
```

### Problem:
- No handling for `result == 'draw'`
- Draw results will be ignored or treated incorrectly

---

## Issue #4: Result Mapping Missing DRAW

### Location: `telegram/main.py` (Lines 420-428)

```python
# Map status
if order_result.status == OrderStatus.WIN:
    result = 'win'
elif order_result.status == OrderStatus.LOSE:
    result = 'loss'
elif order_result.status == OrderStatus.CLOSED or order_result.status == OrderStatus.CANCELLED:
    result = 'closed'
else:
    result = 'pending'
# ❌ MISSING: elif order_result.status == OrderStatus.DRAW: result = 'draw'
```

---

## Complete Fix Required

### Step 1: Add DRAW to OrderStatus Enum

**File:** `pocketoptionapi_async/models.py`

```python
class OrderStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"  # ✅ ADD THIS
```

### Step 2: Fix Profit-Based Status Logic

**File:** `pocketoptionapi_async/client.py` (Line 1298)

```python
# Determine status
if profit > 0:
    status = OrderStatus.WIN
elif profit < 0:
    status = OrderStatus.LOSE
else:
    status = OrderStatus.DRAW  # ✅ FIX: Zero profit = DRAW (refund)
```

### Step 3: Add DRAW Mapping in main.py

**File:** `telegram/main.py` (Line 420)

```python
# Map status
if order_result.status == OrderStatus.WIN:
    result = 'win'
elif order_result.status == OrderStatus.LOSE:
    result = 'loss'
elif order_result.status == OrderStatus.DRAW:  # ✅ ADD THIS
    result = 'draw'
elif order_result.status == OrderStatus.CLOSED or order_result.status == OrderStatus.CANCELLED:
    result = 'closed'
else:
    result = 'pending'
```

### Step 4: Handle DRAW in Martingale Logic

**File:** `telegram/main.py` (Line 442)

```python
# Update martingale step
if result == 'win':
    global_martingale_step = 0
    past_trades[:] = [t for t in past_trades if t['result'] == 'pending']
    log_to_file(f"✅ WIN! Reset step to 0\n")
elif result == 'draw':  # ✅ ADD THIS
    # Draw = refund, don't change step, just remove from pending
    past_trades[:] = [t for t in past_trades if t.get('order_id') != order_id]
    log_to_file(f"🔄 DRAW! Refunded - no change to step {global_martingale_step}\n")
elif result == 'loss' or result == 'closed':
    if global_martingale_step < 8:
        global_martingale_step += 1
        log_to_file(f"❌ LOSS! Step increased to {global_martingale_step}\n")
    else:
        global_martingale_step = 0
        log_to_file(f"🔄 Max steps reached, reset to 0\n")
```

---

## Impact of Bug

### Current Behavior (WRONG):
1. Trade results in draw (profit = 0)
2. Status set to `LOSE` instead of `DRAW`
3. Martingale step increases unnecessarily
4. Next trade uses higher amount (wasting money)

### Correct Behavior (AFTER FIX):
1. Trade results in draw (profit = 0)
2. Status set to `DRAW`
3. Martingale step stays the same
4. Next trade uses same amount (refund handled correctly)

---

## Testing Recommendation

After applying fixes, test with a trade that results in a draw:
1. Place a trade that expires exactly at market price
2. Verify profit = 0
3. Verify status = 'draw'
4. Verify martingale step does NOT increase
5. Verify balance is refunded

---

## Priority: CRITICAL

This bug causes financial loss by:
- Increasing bet size on draws (should stay same)
- Treating refunds as losses
- Incorrect martingale progression

**Fix immediately before live trading!**
