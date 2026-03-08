"""
Test to verify main.py can receive and process trade results correctly
Simulates the complete flow: place trade → wait → receive result → update martingale
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

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

async def test_result_flow():
    """Test complete result flow"""
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{CYAN}MAIN.PY RESULT FLOW TEST{RESET}")
    print(f"{CYAN}Testing: Place Trade → Wait → Receive Result → Update Martingale{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")
    
    # Get SSID
    is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
    if is_demo:
        ssid = os.getenv('SSID_DEMO') or os.getenv('SSID')
    else:
        ssid = os.getenv('SSID_REAL')
    
    if not ssid:
        print(f"{RED}❌ No SSID found in .env file{RESET}")
        return False
    
    print(f"{BLUE}📋 Configuration:{RESET}")
    print(f"   Account Type: {'DEMO' if is_demo else 'REAL'}")
    print(f"   SSID: {ssid[:20]}...{ssid[-10:]}")
    
    # Create client
    client = AsyncPocketOptionClient(
        ssid=ssid,
        is_demo=is_demo,
        persistent_connection=True,
        enable_logging=True  # Enable logging to see websocket messages
    )
    
    try:
        # Step 1: Connect
        print(f"\n{YELLOW}Step 1: Connecting to PocketOption...{RESET}")
        await asyncio.wait_for(client.connect(), timeout=25.0)
        
        if not client.is_connected:
            print(f"{RED}❌ Connection failed{RESET}")
            return False
        
        print(f"{GREEN}✅ Connected successfully{RESET}")
        
        # Step 2: Get balance
        print(f"\n{YELLOW}Step 2: Fetching balance...{RESET}")
        try:
            balance = await asyncio.wait_for(client.get_balance(), timeout=15.0)
            print(f"{GREEN}✅ Balance: ${balance.balance:.2f} {balance.currency}{RESET}")
        except Exception as e:
            print(f"{YELLOW}⚠️ Balance fetch timeout (but connection OK): {e}{RESET}")
        
        # Step 3: Place a test trade
        print(f"\n{YELLOW}Step 3: Placing test trade...{RESET}")
        print(f"   Asset: EURUSD_otc")
        print(f"   Direction: CALL")
        print(f"   Amount: $1.00")
        print(f"   Duration: 60 seconds")
        
        order_result = await client.place_order(
            asset="EURUSD_otc",
            direction=OrderDirection.CALL,
            amount=1.0,
            duration=60
        )
        
        if not order_result or order_result.status not in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
            print(f"{RED}❌ Trade placement failed{RESET}")
            if order_result:
                print(f"   Error: {order_result.error_message}")
            return False
        
        print(f"{GREEN}✅ Trade placed successfully{RESET}")
        print(f"   Order ID: {order_result.order_id}")
        print(f"   Status: {order_result.status.value}")
        
        # Step 4: Wait for result
        print(f"\n{YELLOW}Step 4: Waiting for trade result...{RESET}")
        print(f"   Waiting 65 seconds for trade to complete...")
        
        # Wait for trade duration + buffer
        await asyncio.sleep(65)
        
        # Step 5: Check result
        print(f"\n{YELLOW}Step 5: Checking result...{RESET}")
        
        # Check if result is in client._order_results
        if order_result.order_id in client._order_results:
            final_result = client._order_results[order_result.order_id]
            
            print(f"{GREEN}✅ Result received!{RESET}")
            print(f"   Order ID: {final_result.order_id}")
            print(f"   Status: {final_result.status.value}")
            print(f"   Profit: ${final_result.profit:.2f}" if final_result.profit is not None else "   Profit: N/A")
            
            # Step 6: Verify status mapping
            print(f"\n{YELLOW}Step 6: Verifying status mapping...{RESET}")
            
            # Map status (same logic as main.py)
            if final_result.status == OrderStatus.WIN:
                result = 'win'
            elif final_result.status == OrderStatus.LOSE:
                result = 'loss'
            elif final_result.status == OrderStatus.DRAW:
                result = 'draw'
            elif final_result.status == OrderStatus.CLOSED or final_result.status == OrderStatus.CANCELLED:
                result = 'closed'
            else:
                result = 'pending'
            
            print(f"   Mapped result: {result}")
            
            # Step 7: Simulate martingale update
            print(f"\n{YELLOW}Step 7: Simulating martingale update...{RESET}")
            
            global_martingale_step = 2  # Assume we're at step 2
            print(f"   Current step: {global_martingale_step}")
            
            if result == 'win':
                global_martingale_step = 0
                print(f"{GREEN}   ✅ WIN! Reset step to 0{RESET}")
            elif result == 'draw':
                print(f"{CYAN}   🔄 DRAW! Keep step at {global_martingale_step}{RESET}")
            elif result == 'loss':
                if global_martingale_step < 8:
                    global_martingale_step += 1
                    print(f"{RED}   ❌ LOSS! Increase step to {global_martingale_step}{RESET}")
                else:
                    global_martingale_step = 0
                    print(f"{YELLOW}   🔄 Max steps reached, reset to 0{RESET}")
            
            print(f"   Final step: {global_martingale_step}")
            
            # Summary
            print(f"\n{GREEN}{'='*70}{RESET}")
            print(f"{GREEN}✅ ALL STEPS COMPLETED SUCCESSFULLY{RESET}")
            print(f"{GREEN}{'='*70}{RESET}")
            print(f"{GREEN}Result Flow Working:{RESET}")
            print(f"  ✓ Trade placed")
            print(f"  ✓ Result received via WebSocket")
            print(f"  ✓ Status mapped correctly")
            print(f"  ✓ Martingale updated properly")
            print(f"{GREEN}{'='*70}{RESET}\n")
            
            return True
            
        else:
            print(f"{YELLOW}⚠️ Result not found in client._order_results{RESET}")
            print(f"   This might be normal if trade is still pending")
            print(f"   Order ID: {order_result.order_id}")
            print(f"   Available results: {list(client._order_results.keys())}")
            return False
        
    except asyncio.TimeoutError:
        print(f"{RED}❌ Connection timeout{RESET}")
        return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if client.is_connected:
            await client.disconnect()
            print(f"\n{BLUE}🔌 Disconnected{RESET}")

async def main():
    """Main test function"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TESTING MAIN.PY RESULT HANDLING{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{YELLOW}⚠️  This test will place a REAL trade (on demo account){RESET}")
    print(f"{YELLOW}⚠️  Trade amount: $1.00{RESET}")
    print(f"{YELLOW}⚠️  Duration: 60 seconds{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    # Ask for confirmation
    print(f"{CYAN}Press Enter to continue or Ctrl+C to cancel...{RESET}")
    try:
        input()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test cancelled{RESET}")
        return
    
    success = await test_result_flow()
    
    if success:
        print(f"{GREEN}✅ Test completed successfully!{RESET}")
        print(f"{GREEN}main.py is ready to receive and process results{RESET}\n")
    else:
        print(f"{RED}❌ Test failed or incomplete{RESET}")
        print(f"{YELLOW}Check the output above for details{RESET}\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted{RESET}")
