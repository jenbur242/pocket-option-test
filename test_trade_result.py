"""
Simple test to place a trade and print the result
Shows WIN/LOSS/DRAW status clearly
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
MAGENTA = '\033[95m'
RESET = '\033[0m'

def print_header(text):
    """Print colored header"""
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{CYAN}{text}{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")

def print_result_box(status, profit, order_id):
    """Print result in a nice box"""
    print(f"\n{YELLOW}{'='*70}{RESET}")
    print(f"{YELLOW}                         TRADE RESULT                              {RESET}")
    print(f"{YELLOW}{'='*70}{RESET}")
    
    # Determine color and emoji based on status
    if status == OrderStatus.WIN:
        color = GREEN
        emoji = "✅"
        status_text = "WIN"
    elif status == OrderStatus.LOSE:
        color = RED
        emoji = "❌"
        status_text = "LOSS"
    elif status == OrderStatus.DRAW:
        color = CYAN
        emoji = "🔄"
        status_text = "DRAW (REFUND)"
    else:
        color = YELLOW
        emoji = "⏳"
        status_text = status.value.upper()
    
    print(f"{color}{emoji} Status: {status_text}{RESET}")
    print(f"💰 Profit: ${profit:.2f}")
    print(f"🆔 Order ID: {order_id}")
    print(f"{YELLOW}{'='*70}{RESET}\n")

async def test_trade_and_result():
    """Place trade and wait for result"""
    
    print_header("TRADE RESULT TEST")
    
    # Get configuration
    is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
    if is_demo:
        ssid = os.getenv('SSID_DEMO') or os.getenv('SSID')
    else:
        ssid = os.getenv('SSID_REAL')
    
    if not ssid:
        print(f"{RED}❌ No SSID found in .env file{RESET}")
        return
    
    # Trade parameters
    ASSET = "EURUSD_otc"
    DIRECTION = OrderDirection.CALL
    AMOUNT = 1.0
    DURATION = 60  # seconds
    
    print(f"{BLUE}📋 Configuration:{RESET}")
    print(f"   Account: {'DEMO' if is_demo else 'REAL'}")
    print(f"   Asset: {ASSET}")
    print(f"   Direction: {DIRECTION.value}")
    print(f"   Amount: ${AMOUNT}")
    print(f"   Duration: {DURATION} seconds")
    
    # Create client
    print(f"\n{YELLOW}⏳ Connecting to PocketOption...{RESET}")
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
            print(f"{RED}❌ Connection failed{RESET}")
            return
        
        print(f"{GREEN}✅ Connected{RESET}")
        
        # Get balance
        try:
            balance = await asyncio.wait_for(client.get_balance(), timeout=15.0)
            print(f"{GREEN}💰 Balance: ${balance.balance:.2f} {balance.currency}{RESET}")
        except:
            print(f"{YELLOW}⚠️ Balance fetch timeout (continuing anyway){RESET}")
        
        # Place trade
        print(f"\n{YELLOW}⏳ Placing trade...{RESET}")
        order_result = await client.place_order(
            asset=ASSET,
            direction=DIRECTION,
            amount=AMOUNT,
            duration=DURATION
        )
        
        if not order_result or order_result.status not in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
            print(f"{RED}❌ Trade placement failed{RESET}")
            if order_result:
                print(f"   Error: {order_result.error_message}")
            return
        
        print(f"{GREEN}✅ Trade placed successfully{RESET}")
        print(f"   Order ID: {order_result.order_id}")
        print(f"   Placed at: {order_result.placed_at.strftime('%H:%M:%S')}")
        print(f"   Expires at: {order_result.expires_at.strftime('%H:%M:%S')}")
        
        # Wait for result
        print(f"\n{YELLOW}⏳ Waiting for result...{RESET}")
        wait_time = DURATION + 5
        
        for i in range(wait_time):
            remaining = wait_time - i
            print(f"\r   {remaining} seconds remaining...", end='', flush=True)
            await asyncio.sleep(1)
            
            # Check if result is available
            if order_result.order_id in client._order_results:
                print(f"\r{GREEN}   ✅ Result received early!{RESET}                    ")
                break
        
        print()  # New line
        
        # Get result
        if order_result.order_id in client._order_results:
            final_result = client._order_results[order_result.order_id]
            
            # Print result box
            print_result_box(
                final_result.status,
                final_result.profit if final_result.profit is not None else 0.0,
                final_result.order_id
            )
            
            # Test martingale logic
            print(f"{BLUE}📊 Martingale Logic Test:{RESET}")
            
            # Simulate current step
            current_step = 2
            print(f"   Current martingale step: {current_step}")
            
            # Map status
            if final_result.status == OrderStatus.WIN:
                result = 'win'
                new_step = 0
                print(f"{GREEN}   ✅ WIN → Reset to step 0{RESET}")
            elif final_result.status == OrderStatus.LOSE:
                result = 'loss'
                new_step = current_step + 1 if current_step < 8 else 0
                print(f"{RED}   ❌ LOSS → Increase to step {new_step}{RESET}")
            elif final_result.status == OrderStatus.DRAW:
                result = 'draw'
                new_step = current_step
                print(f"{CYAN}   🔄 DRAW → Keep at step {new_step} (refund){RESET}")
            else:
                result = 'unknown'
                new_step = current_step
                print(f"{YELLOW}   ⚠️ Unknown status{RESET}")
            
            print(f"   New martingale step: {new_step}")
            
            # Calculate next trade amount
            base_amount = 1.0
            multiplier = 2.5
            next_amount = base_amount * (multiplier ** new_step)
            print(f"   Next trade amount: ${next_amount:.2f}")
            
            # Summary
            print(f"\n{GREEN}{'='*70}{RESET}")
            print(f"{GREEN}✅ TEST COMPLETED SUCCESSFULLY{RESET}")
            print(f"{GREEN}{'='*70}{RESET}")
            print(f"Result: {result.upper()}")
            print(f"Profit: ${final_result.profit:.2f}" if final_result.profit is not None else "Profit: N/A")
            print(f"Status mapping: {final_result.status.value} → {result}")
            print(f"Martingale: Step {current_step} → Step {new_step}")
            print(f"{GREEN}{'='*70}{RESET}\n")
            
        else:
            print(f"{RED}❌ Result not found in client._order_results{RESET}")
            print(f"   Order ID: {order_result.order_id}")
            print(f"   Available results: {list(client._order_results.keys())}")
            print(f"\n{YELLOW}This might mean:{RESET}")
            print(f"   - Trade is still pending")
            print(f"   - WebSocket didn't receive result")
            print(f"   - Need to wait longer")
        
    except asyncio.TimeoutError:
        print(f"{RED}❌ Connection timeout{RESET}")
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️ Test interrupted by user{RESET}")
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if client.is_connected:
            await client.disconnect()
            print(f"{BLUE}🔌 Disconnected{RESET}\n")

async def main():
    """Main function"""
    print(f"\n{MAGENTA}{'='*70}{RESET}")
    print(f"{MAGENTA}           POCKET OPTION - TRADE RESULT TEST                    {RESET}")
    print(f"{MAGENTA}{'='*70}{RESET}")
    print(f"{YELLOW}⚠️  This will place a REAL trade on your account{RESET}")
    print(f"{YELLOW}⚠️  Amount: $1.00 (Demo account){RESET}")
    print(f"{YELLOW}⚠️  Duration: 60 seconds{RESET}")
    print(f"{MAGENTA}{'='*70}{RESET}\n")
    
    print(f"{CYAN}Press Enter to start test or Ctrl+C to cancel...{RESET}")
    try:
        input()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test cancelled{RESET}")
        return
    
    await test_trade_and_result()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted{RESET}")
