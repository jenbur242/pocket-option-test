"""
Simple trade test - place trade and check if result is received
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection, OrderStatus
from dotenv import load_dotenv

load_dotenv()

async def test():
    is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
    ssid = os.getenv('SSID_DEMO') or os.getenv('SSID') if is_demo else os.getenv('SSID_REAL')
    
    if not ssid:
        print("❌ No SSID")
        return
    
    print("\n" + "="*60)
    print("SIMPLE TRADE TEST")
    print("="*60)
    
    client = AsyncPocketOptionClient(ssid=ssid, is_demo=is_demo, persistent_connection=True, enable_logging=True)
    
    try:
        print("\n⏳ Connecting...")
        await asyncio.wait_for(client.connect(), timeout=25.0)
        print("✅ Connected\n")
        
        print("⏳ Placing trade...")
        order = await client.place_order(asset="EURUSD_otc", direction=OrderDirection.CALL, amount=1.0, duration=60)
        
        print(f"\n✅ Trade placed!")
        print(f"   Order ID: {order.order_id}")
        print(f"   Status: {order.status.value}")
        print(f"   Asset: {order.asset}")
        print(f"   Amount: ${order.amount}")
        
        print(f"\n📊 Checking storage...")
        print(f"   Active orders: {list(client._active_orders.keys())}")
        print(f"   Completed results: {list(client._order_results.keys())}")
        
        print(f"\n⏳ Waiting 70 seconds for result...")
        for i in range(70):
            await asyncio.sleep(1)
            if i % 10 == 0:
                print(f"   {70-i}s | Active: {len(client._active_orders)} | Results: {len(client._order_results)}")
            
            if order.order_id in client._order_results:
                print(f"\n✅ RESULT RECEIVED!")
                result = client._order_results[order.order_id]
                print(f"\n{'='*60}")
                print(f"RESULT")
                print(f"{'='*60}")
                print(f"Order ID: {result.order_id}")
                print(f"Status: {result.status.value}")
                print(f"Profit: ${result.profit:.2f}" if result.profit is not None else "Profit: N/A")
                print(f"{'='*60}\n")
                break
        else:
            print(f"\n❌ No result received")
            print(f"   Order ID: {order.order_id}")
            print(f"   Active: {list(client._active_orders.keys())}")
            print(f"   Results: {list(client._order_results.keys())}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client.is_connected:
            await client.disconnect()
            print("\n🔌 Disconnected\n")

if __name__ == "__main__":
    asyncio.run(test())
