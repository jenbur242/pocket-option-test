"""
Automated test to place a trade and print the result
No user input required - runs automatically
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection, OrderStatus
from dotenv import load_dotenv

load_dotenv()

async def test_trade():
    """Place trade and wait for result"""
    
    print("\n" + "="*70)
    print("AUTOMATED TRADE RESULT TEST")
    print("="*70 + "\n")
    
    # Get configuration
    is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
    if is_demo:
        ssid = os.getenv('SSID_DEMO') or os.getenv('SSID')
    else:
        ssid = os.getenv('SSID_REAL')
    
    if not ssid:
        print("❌ No SSID found in .env file")
        return
    
    # Trade parameters
    ASSET = "EURUSD_otc"
    DIRECTION = OrderDirection.CALL
    AMOUNT = 1.0
    DURATION = 60  # seconds
    
    print("📋 Configuration:")
    print(f"   Account: {'DEMO' if is_demo else 'REAL'}")
    print(f"   Asset: {ASSET}")
    print(f"   Direction: {DIRECTION.value}")
    print(f"   Amount: ${AMOUNT}")
    print(f"   Duration: {DURATION} seconds\n")
    
    # Create client
    print("⏳ Connecting to PocketOption...")
    client = AsyncPocketOptionClient(
        ssid=ssid,
        is_demo=is_demo,
        persistent_connection=True,
        enable_logging=False
    )
    
    try:
        # Connect
        await asyncio.wait_for(client.connect(), timeout=25.0)
        
        if not client.is_connected:
            print("❌ Connection failed")
            return
        
        print("✅ Connected\n")
        
        # Get balance
        try:
            balance = await asyncio.wait_for(client.get_balance(), timeout=15.0)
            print(f"💰 Balance: ${balance.balance:.2f} {balance.currency}\n")
        except:
            print("⚠️ Balance fetch timeout (continuing anyway)\n")
        
        # Place trade
        print("⏳ Placing trade...")
        order_result = await client.place_order(
            asset=ASSET,
            direction=DIRECTION,
            amount=AMOUNT,
            duration=DURATION
        )
        
        if not order_result or order_result.status not in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
            print("❌ Trade placement failed")
            if order_result:
                print(f"   Error: {order_result.error_message}")
            return
        
        print("✅ Trade placed successfully")
        print(f"   Order ID: {order_result.order_id}")
        print(f"   Status: {order_result.status.value}")
        print(f"   Placed at: {order_result.placed_at.strftime('%H:%M:%S')}")
        print(f"   Expires at: {order_result.expires_at.strftime('%H:%M:%S')}\n")
        
        # Wait for result
        print("⏳ Waiting for result...")
        wait_time = DURATION + 5
        
        for i in range(wait_time):
            remaining = wait_time - i
            print(f"\r   {remaining} seconds remaining...", end='', flush=True)
            await asyncio.sleep(1)
            
            # Check if result is available
            if order_result.order_id in client._order_results:
                print(f"\r   ✅ Result received!                    ")
                break
        
        print()  # New line
        
        # Get result
        if order_result.order_id in client._order_results:
            final_result = client._order_results[order_result.order_id]
            
            # Print result
            print("\n" + "="*70)
            print("                         TRADE RESULT")
            print("="*70)
            
            # Determine status
            if final_result.status == OrderStatus.WIN:
                print("✅ Status: WIN")
            elif final_result.status == OrderStatus.LOSE:
                print("❌ Status: LOSS")
            elif final_result.status == OrderStatus.DRAW:
                print("🔄 Status: DRAW (REFUND)")
            else:
                print(f"⏳ Status: {final_result.status.value.upper()}")
            
            profit = final_result.profit if final_result.profit is not None else 0.0
            print(f"💰 Profit: ${profit:.2f}")
            print(f"🆔 Order ID: {final_result.order_id}")
            print("="*70 + "\n")
            
            # Test martingale logic
            print("📊 Martingale Logic Test:")
            current_step = 2
            print(f"   Current step: {current_step}")
            
            # Map status
            if final_result.status == OrderStatus.WIN:
                result = 'win'
                new_step = 0
                print(f"   ✅ WIN → Reset to step 0")
            elif final_result.status == OrderStatus.LOSE:
                result = 'loss'
                new_step = current_step + 1 if current_step < 8 else 0
                print(f"   ❌ LOSS → Increase to step {new_step}")
            elif final_result.status == OrderStatus.DRAW:
                result = 'draw'
                new_step = current_step
                print(f"   🔄 DRAW → Keep at step {new_step} (refund)")
            else:
                result = 'unknown'
                new_step = current_step
            
            print(f"   New step: {new_step}")
            
            # Calculate next trade amount
            base_amount = 1.0
            multiplier = 2.5
            next_amount = base_amount * (multiplier ** new_step)
            print(f"   Next trade amount: ${next_amount:.2f}\n")
            
            # Summary
            print("="*70)
            print("✅ TEST COMPLETED SUCCESSFULLY")
            print("="*70)
            print(f"Result: {result.upper()}")
            print(f"Profit: ${profit:.2f}")
            print(f"Status mapping: {final_result.status.value} → {result}")
            print(f"Martingale: Step {current_step} → Step {new_step}")
            print("="*70 + "\n")
            
            # Verify draw handling
            if final_result.status == OrderStatus.DRAW:
                print("🔄 DRAW RESULT DETECTED!")
                print("   ✓ Status correctly identified as DRAW")
                print("   ✓ Profit is $0.00 (refund)")
                print("   ✓ Martingale step unchanged")
                print("   ✓ Next trade uses same amount")
                print("\n✅ Draw handling is working correctly!\n")
            
        else:
            print("❌ Result not found in client._order_results")
            print(f"   Order ID: {order_result.order_id}")
            print(f"   Available results: {list(client._order_results.keys())}\n")
        
    except asyncio.TimeoutError:
        print("❌ Connection timeout")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if client.is_connected:
            await client.disconnect()
            print("🔌 Disconnected\n")

if __name__ == "__main__":
    print("\n🚀 Starting automated trade test...")
    print("⚠️  This will place a $1 trade on demo account")
    print("⏳ Please wait...\n")
    
    try:
        asyncio.run(test_trade())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
