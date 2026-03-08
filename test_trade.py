#!/usr/bin/env python3
"""
Quick test to verify trading functionality
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_trade():
    """Test if we can place a trade"""
    from pocketoptionapi_async import AsyncPocketOptionClient
    from pocketoptionapi_async.models import OrderDirection
    
    # Get SSID
    ssid = os.getenv('SSID_DEMO') or os.getenv('SSID')
    if not ssid:
        print("❌ SSID_DEMO not found in .env")
        return False
    
    print(f"✅ SSID found: {ssid[:30]}...")
    
    # Create client
    print("🔌 Connecting to PocketOption...")
    client = AsyncPocketOptionClient(ssid=ssid, is_demo=True)
    
    try:
        # Connect
        await asyncio.wait_for(client.connect(), timeout=20.0)
        print("✅ Connected!")
        
        # Get balance
        balance = await asyncio.wait_for(client.get_balance(), timeout=10.0)
        print(f"💰 Balance: ${balance.balance:.2f} {balance.currency}")
        
        # Try to place a test trade
        print("\n🎯 Attempting to place test trade...")
        print("   Asset: EURUSD_otc")
        print("   Direction: CALL")
        print("   Amount: $1.00")
        print("   Duration: 60 seconds")
        
        order = await client.place_order(
            asset="EURUSD_otc",
            direction=OrderDirection.CALL,
            amount=1.0,
            duration=60
        )
        
        if order and order.order_id:
            print(f"\n✅ Trade placed successfully!")
            print(f"   Order ID: {order.order_id}")
            print(f"   Status: {order.status}")
            print(f"\n🎉 TRADING IS WORKING!")
            return True
        else:
            print(f"\n❌ Trade failed!")
            if order and order.error_message:
                print(f"   Error: {order.error_message}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.disconnect()
        print("\n🔌 Disconnected")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TRADING FUNCTIONALITY TEST")
    print("=" * 60)
    
    result = asyncio.run(test_trade())
    
    print("\n" + "=" * 60)
    if result:
        print("✅ TEST PASSED - Trading is working!")
    else:
        print("❌ TEST FAILED - Trading is not working")
    print("=" * 60)
