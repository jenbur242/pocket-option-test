"""
Test trade with full logging enabled to see what's happening
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

async def test_with_logging():
    """Place trade with logging enabled"""
    
    print("\n" + "="*70)
    print("TRADE TEST WITH FULL LOGGING")
    print("="*70 + "\n")
    
    # Get configuration
    is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
    if is_demo:
        ssid = os.getenv('SSID_DEMO') or os.getenv('SSID')
    else:
        ssid = os.getenv('SSID_REAL')
    
    if not ssid:
        print("❌ No SSID found")
        return
    
    print(f"Account: {'DEMO' if is_demo else 'REAL'}")
    print(f"Asset: EURUSD_otc")
    print(f"Amount: $1.00")
    print(f"Duration: 60 seconds\n")
    
    # Create client with logging ENABLED
    print("Creating client with logging enabled...")
    client = AsyncPocketOptionClient(
        ssid=ssid,
        is_demo=is_demo,
        persistent_connection=True,
        enable_logging=True  # ✅ ENABLE LOGGING
    )
    
    try:
        # Connect
        print("\n⏳ Connecting...")
        await asyncio.wait_for(client.connect(), timeout=25.0)
        
        if not client.is_connected:
            print("❌ Connection failed")
            return
        
        print("✅ Connected\n")
        
        # Place trade
        print("⏳ Placing trade...")
        order_result = await client.place_order(
            asset="EURUSD_otc",
            direction=OrderDirection.CALL,
            amount=1.0,
            duration=60
        )
        
        if not order_result or order_result.status not in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
            print(f"❌ Trade failed: {order_result.error_message if order_result else 'Unknown'}")
            return
        
        print(f"\n✅ Trade placed!")
        print(f"   Order ID: {order_result.order_id}")
        print(f"   Status: {order_result.status.value}")
        
        # Check active orders
        print(f"\n📊 Active orders: {list(client._active_orders.keys())}")
        print(f"📊 Completed results: {list(client._order_results.keys())}")
        
        # Wait for result
        print(f"\n⏳ Waiting 70 seconds for result...")
        print("   (Watch the logs above for WebSocket messages)\n")
        
        for i in range(70):
            await asyncio.sleep(1)
            
            # Check every 5 seconds
            if i % 5 == 0:
                print(f"   {70-i}s remaining | Active: {len(client._active_orders)} | Results: {len(client._order_results)}")
            
            # Check if result arrived
            if order_result.order_id in client._order_results:
                print(f"\n✅ Result received at {i} seconds!")
                break
        
        # Final check
        print(f"\n📊 Final state:")
        print(f"   Active orders: {list(client._active_orders.keys())}")
        print(f"   Completed results: {list(client._order_results.keys())}")
        
        if order_result.order_id in client._order_results:
            result = client._order_results[order_result.order_id]
            print(f"\n{'='*70}")
            print(f"RESULT FOUND!")
            print(f"{'='*70}")
            print(f"Status: {result.status.value}")
            print(f"Profit: ${result.profit:.2f}" if result.profit is not None else "Profit: N/A")
            print(f"{'='*70}\n")
        else:
            print(f"\n❌ Result not found")
            print(f"   This means WebSocket didn't receive the result message")
            print(f"   Check the logs above for 'deals' messages\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client.is_connected:
            await client.disconnect()
            print("\n🔌 Disconnected\n")

if __name__ == "__main__":
    print("\n🚀 Starting test with full logging...")
    print("⚠️  This will place a $1 trade and show all WebSocket messages\n")
    
    try:
        asyncio.run(test_with_logging())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
