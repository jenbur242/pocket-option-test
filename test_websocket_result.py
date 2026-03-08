#!/usr/bin/env python3
"""
Test WebSocket trade result handling
"""
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv()

# Import PocketOption API
from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection, OrderStatus

# Test configuration
SSID_DEMO = os.getenv('SSID_DEMO') or os.getenv('SSID')
TEST_ASSET = "EURUSD_otc"
TEST_AMOUNT = 1.0
TEST_DURATION = 60  # 1 minute

# Track if event was triggered
event_triggered = False
result_received = None

async def handle_trade_result(order_result):
    """Event handler for trade results"""
    global event_triggered, result_received
    
    print(f"\n{'='*60}")
    print(f"WEBSOCKET EVENT TRIGGERED!")
    print(f"{'='*60}")
    print(f"Order ID: {order_result.order_id}")
    print(f"Asset: {order_result.asset}")
    print(f"Status: {order_result.status.value}")
    print(f"Profit: ${order_result.profit if order_result.profit else 0:.2f}")
    print(f"Direction: {order_result.direction.value}")
    print(f"Amount: ${order_result.amount}")
    print(f"{'='*60}\n")
    
    event_triggered = True
    result_received = order_result

async def test_trade_with_websocket():
    """Test placing a trade and receiving result via WebSocket"""
    
    print("\n" + "="*60)
    print("WEBSOCKET TRADE RESULT TEST")
    print("="*60)
    
    if not SSID_DEMO:
        print("❌ SSID_DEMO not found in .env")
        return
    
    print(f"\n1. Creating client...")
    client = AsyncPocketOptionClient(
        ssid=SSID_DEMO,
        is_demo=True,
        persistent_connection=True,
        auto_reconnect=True,
        enable_logging=True  # Enable logging to see WebSocket messages
    )
    
    print(f"2. Registering event listener...")
    client.add_event_callback('order_closed', handle_trade_result)
    print(f"   Event listener registered")
    
    try:
        print(f"\n3. Connecting to PocketOption...")
        await client.connect()
        print(f"   Connected")
        
        print(f"\n4. Getting balance...")
        try:
            balance = await client.get_balance()
            print(f"   Balance: ${balance.balance:.2f}")
        except Exception as e:
            print(f"   Balance check skipped: {e}")
            print(f"   (Continuing with trade test anyway...)")
        
        print(f"\n5. Placing test trade...")
        print(f"   Asset: {TEST_ASSET}")
        print(f"   Direction: CALL")
        print(f"   Amount: ${TEST_AMOUNT}")
        print(f"   Duration: {TEST_DURATION}s")
        
        order_result = await client.place_order(
            asset=TEST_ASSET,
            direction=OrderDirection.CALL,
            amount=TEST_AMOUNT,
            duration=TEST_DURATION
        )
        
        if order_result and order_result.order_id:
            print(f"   Trade placed successfully!")
            print(f"   Order ID: {order_result.order_id}")
            print(f"   Status: {order_result.status.value}")
            
            # Wait for trade to complete + buffer
            wait_time = TEST_DURATION + 10
            print(f"\n6. Waiting {wait_time} seconds for trade to complete...")
            print(f"   (WebSocket should trigger event automatically)")
            
            for i in range(wait_time):
                await asyncio.sleep(1)
                if event_triggered:
                    print(f"\n   Event triggered after {i+1} seconds!")
                    break
                if (i + 1) % 10 == 0:
                    print(f"   {i+1}s elapsed... (event_triggered={event_triggered})")
            
            print(f"\n7. Test Results:")
            print(f"   {'='*50}")
            if event_triggered:
                print(f"   SUCCESS: WebSocket event WAS triggered")
                print(f"   Result received: {result_received.status.value}")
                print(f"   Profit: ${result_received.profit if result_received.profit else 0:.2f}")
            else:
                print(f"   FAILED: WebSocket event was NOT triggered")
                print(f"   Checking manually with check_win()...")
                
                # Try manual check
                result_data = await client.check_win(order_result.order_id, max_wait_time=30.0)
                if result_data and result_data.get('completed'):
                    print(f"   Manual check found result: {result_data.get('result')}")
                    print(f"   Profit: ${result_data.get('profit', 0):.2f}")
                    print(f"\n   ISSUE: WebSocket event didn't trigger but result exists!")
                else:
                    print(f"   Manual check also failed")
            print(f"   {'='*50}")
            
        else:
            print(f"   Trade placement failed")
            if order_result:
                print(f"   Error: {order_result.error_message}")
        
        print(f"\n8. Disconnecting...")
        await client.disconnect()
        print(f"   Disconnected")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            await client.disconnect()
        except:
            pass

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting WebSocket Trade Result Test")
    print("="*60)
    asyncio.run(test_trade_with_websocket())
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60 + "\n")
