"""
Test script to use SSID from .env, place a trade, and check the result
"""
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from pocketoptionapi_async.client import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection

# Load environment variables
load_dotenv()

async def test_trade_with_ssid():
    """Test placing a trade using SSID from .env and checking the result"""
    
    # Get SSID from environment
    ssid = os.getenv('SSID_DEMO')  # Using demo SSID
    if not ssid:
        print("❌ SSID_DEMO not found in .env file")
        return
    
    print(f"✅ Loaded SSID from .env")
    print(f"📝 SSID length: {len(ssid)} characters")
    
    # Create client
    client = AsyncPocketOptionClient(
        ssid=ssid,
        is_demo=True,
        enable_logging=True
    )
    
    try:
        # Connect to PocketOption
        print("\n🔌 Connecting to PocketOption...")
        connected = await client.connect()
        
        if not connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected successfully")
        
        # Get balance
        print("\n💰 Getting balance...")
        balance = await client.get_balance()
        print(f"✅ Balance: ${balance.balance:.2f} {balance.currency}")
        
        # Place a trade
        asset = "EURUSD_otc"
        amount = 1.0
        direction = OrderDirection.CALL
        duration = 60  # 60 seconds
        
        print(f"\n📊 Placing trade:")
        print(f"   Asset: {asset}")
        print(f"   Amount: ${amount}")
        print(f"   Direction: {direction.value}")
        print(f"   Duration: {duration}s")
        
        order_result = await client.place_order(
            asset=asset,
            amount=amount,
            direction=direction,
            duration=duration
        )
        
        print(f"\n✅ Order placed successfully!")
        print(f"   Order ID: {order_result.order_id}")
        print(f"   Status: {order_result.status.value}")
        print(f"   Placed at: {order_result.placed_at.strftime('%H:%M:%S')}")
        print(f"   Expires at: {order_result.expires_at.strftime('%H:%M:%S')}")
        
        # Check the result using check_win
        print(f"\n⏳ Waiting for trade result (max 5 minutes)...")
        result = await client.check_win(order_result.order_id, max_wait_time=300)
        
        if result:
            print(f"\n📊 Trade Result:")
            print(f"   Order ID: {result.get('order_id')}")
            print(f"   Result: {result.get('result', 'unknown').upper()}")
            print(f"   Profit: ${result.get('profit', 0):.2f}")
            print(f"   Completed: {result.get('completed', False)}")
            
            if result.get('result') == 'win':
                print("   🎉 WIN!")
            elif result.get('result') == 'loss':
                print("   ❌ LOSS")
            elif result.get('result') == 'draw':
                print("   🤝 DRAW")
            elif result.get('timeout'):
                print("   ⏰ TIMEOUT - Result not received in time")
        else:
            print("❌ No result received")
        
        # Also check using check_order_result
        print(f"\n🔍 Checking order result directly...")
        order_check = await client.check_order_result(order_result.order_id)
        
        if order_check:
            print(f"   Order ID: {order_check.order_id}")
            print(f"   Status: {order_check.status.value}")
            print(f"   Profit: ${order_check.profit if order_check.profit else 0:.2f}")
        else:
            print("   ❌ Order not found in results")
        
        # Get final balance
        print("\n💰 Getting final balance...")
        final_balance = await client.get_balance()
        print(f"✅ Final Balance: ${final_balance.balance:.2f} {final_balance.currency}")
        
        balance_change = final_balance.balance - balance.balance
        print(f"📈 Balance change: ${balance_change:+.2f}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Disconnect
        print("\n🔌 Disconnecting...")
        await client.disconnect()
        print("✅ Disconnected")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 PocketOption Trade Test with SSID from .env")
    print("=" * 60)
    
    asyncio.run(test_trade_with_ssid())
    
    print("\n" + "=" * 60)
    print("✅ Test completed")
    print("=" * 60)
