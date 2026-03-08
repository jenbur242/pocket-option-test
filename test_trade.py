"""
Test file for placing trades and checking results with PocketOption API
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

from pocketoptionapi_async.client import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection, OrderStatus

# Load environment variables
load_dotenv()


async def test_place_trade_and_check_result():
    """
    Test placing a trade and checking its result
    """
    # Get SSID from environment
    ssid = os.getenv("SSID_DEMO")
    if not ssid:
        logger.error("SSID_DEMO not found in .env file")
        return

    # Initialize client
    client = AsyncPocketOptionClient(
        ssid=ssid,
        is_demo=True,
        persistent_connection=False,
        auto_reconnect=True,
        enable_logging=True
    )

    try:
        # Connect to PocketOption
        logger.info("Connecting to PocketOption...")
        connected = await client.connect()
        
        if not connected:
            logger.error("Failed to connect to PocketOption")
            return

        logger.success("✅ Connected successfully!")

        # Wait a bit for initialization
        await asyncio.sleep(2)

        # Get balance
        balance = await client.get_balance()
        logger.info(f"💰 Current balance: ${balance.balance:.2f} ({balance.currency})")

        # Trade parameters
        asset = "EURUSD_otc"
        amount = 1.0
        direction = OrderDirection.CALL
        duration = 60  # 60 seconds

        logger.info(f"\n📊 Placing trade:")
        logger.info(f"   Asset: {asset}")
        logger.info(f"   Amount: ${amount}")
        logger.info(f"   Direction: {direction.value.upper()}")
        logger.info(f"   Duration: {duration}s")

        # Place the order
        order_result = await client.place_order(
            asset=asset,
            amount=amount,
            direction=direction,
            duration=duration
        )

        logger.success(f"\n✅ Order placed successfully!")
        logger.info(f"   Order ID: {order_result.order_id}")
        logger.info(f"   Status: {order_result.status.value}")
        logger.info(f"   Placed at: {order_result.placed_at.strftime('%H:%M:%S')}")
        logger.info(f"   Expires at: {order_result.expires_at.strftime('%H:%M:%S')}")

        # Check order result immediately
        logger.info(f"\n🔍 Checking order status...")
        check_result = await client.check_order_result(order_result.order_id)
        
        if check_result:
            logger.info(f"   Current status: {check_result.status.value}")
            if check_result.profit is not None:
                logger.info(f"   Profit: ${check_result.profit:.2f}")
        
        # Wait for trade to complete using check_win
        logger.info(f"\n⏳ Waiting for trade to complete (max {duration + 30}s)...")
        
        win_result = await client.check_win(
            order_id=order_result.order_id,
            max_wait_time=duration + 30  # Wait for duration + 30 seconds buffer
        )

        # Display final result
        logger.info(f"\n{'='*50}")
        logger.info(f"📊 TRADE RESULT")
        logger.info(f"{'='*50}")
        
        if win_result and win_result.get("completed"):
            result_type = win_result.get("result", "unknown")
            profit = win_result.get("profit", 0)
            
            if result_type == "win":
                logger.success(f"🎉 WINNER! Profit: ${profit:.2f}")
            elif result_type == "loss":
                logger.warning(f"❌ LOSS! Profit: ${profit:.2f}")
            else:
                logger.info(f"⚖️ DRAW! Profit: ${profit:.2f}")
                
            logger.info(f"   Order ID: {win_result.get('order_id')}")
            logger.info(f"   Status: {win_result.get('status')}")
        else:
            logger.warning(f"⏰ Trade result not received (timeout or error)")
            if win_result:
                logger.info(f"   Timeout: {win_result.get('timeout', False)}")

        # Get updated balance
        await asyncio.sleep(2)
        final_balance = await client.get_balance()
        logger.info(f"\n💰 Final balance: ${final_balance.balance:.2f}")
        
        balance_change = final_balance.balance - balance.balance
        if balance_change > 0:
            logger.success(f"   Change: +${balance_change:.2f}")
        elif balance_change < 0:
            logger.warning(f"   Change: ${balance_change:.2f}")
        else:
            logger.info(f"   Change: ${balance_change:.2f}")

    except Exception as e:
        logger.error(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Disconnect
        logger.info("\n🔌 Disconnecting...")
        await client.disconnect()
        logger.info("✅ Disconnected")


async def test_multiple_trades():
    """
    Test placing multiple trades and checking their results
    """
    ssid = os.getenv("SSID_DEMO")
    if not ssid:
        logger.error("SSID_DEMO not found in .env file")
        return

    client = AsyncPocketOptionClient(
        ssid=ssid,
        is_demo=True,
        persistent_connection=False,
        auto_reconnect=True,
        enable_logging=True
    )

    try:
        logger.info("Connecting to PocketOption...")
        connected = await client.connect()
        
        if not connected:
            logger.error("Failed to connect")
            return

        logger.success("✅ Connected!")
        await asyncio.sleep(2)

        # Get initial balance
        balance = await client.get_balance()
        logger.info(f"💰 Initial balance: ${balance.balance:.2f}")

        # Place multiple trades
        trades = [
            {"asset": "EURUSD_otc", "direction": OrderDirection.CALL, "amount": 1.0},
            {"asset": "GBPUSD_otc", "direction": OrderDirection.PUT, "amount": 1.0},
            {"asset": "USDJPY_otc", "direction": OrderDirection.CALL, "amount": 1.0},
        ]

        order_results = []
        
        for i, trade in enumerate(trades, 1):
            logger.info(f"\n📊 Placing trade {i}/{len(trades)}: {trade['asset']} {trade['direction'].value.upper()}")
            
            try:
                order = await client.place_order(
                    asset=trade["asset"],
                    amount=trade["amount"],
                    direction=trade["direction"],
                    duration=60
                )
                
                order_results.append(order)
                logger.success(f"✅ Trade {i} placed: {order.order_id}")
                
                # Small delay between trades
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Failed to place trade {i}: {e}")

        # Wait for all trades to complete
        logger.info(f"\n⏳ Waiting for {len(order_results)} trades to complete...")
        
        results = []
        for order in order_results:
            win_result = await client.check_win(order.order_id, max_wait_time=90)
            results.append(win_result)

        # Summary
        logger.info(f"\n{'='*50}")
        logger.info(f"📊 TRADES SUMMARY")
        logger.info(f"{'='*50}")
        
        wins = 0
        losses = 0
        total_profit = 0
        
        for i, result in enumerate(results, 1):
            if result and result.get("completed"):
                result_type = result.get("result")
                profit = result.get("profit", 0)
                total_profit += profit
                
                if result_type == "win":
                    wins += 1
                    logger.success(f"Trade {i}: WIN (+${profit:.2f})")
                elif result_type == "loss":
                    losses += 1
                    logger.warning(f"Trade {i}: LOSS (${profit:.2f})")
                else:
                    logger.info(f"Trade {i}: DRAW (${profit:.2f})")
            else:
                logger.warning(f"Trade {i}: TIMEOUT/ERROR")

        logger.info(f"\n📈 Results: {wins} wins, {losses} losses")
        logger.info(f"💰 Total profit: ${total_profit:.2f}")

        # Final balance
        final_balance = await client.get_balance()
        logger.info(f"💰 Final balance: ${final_balance.balance:.2f}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.disconnect()
        logger.info("✅ Disconnected")


if __name__ == "__main__":
    # Run single trade test
    logger.info("="*60)
    logger.info("TEST 1: Single Trade")
    logger.info("="*60)
    asyncio.run(test_place_trade_and_check_result())
    
    # Uncomment to run multiple trades test
    # logger.info("\n" + "="*60)
    # logger.info("TEST 2: Multiple Trades")
    # logger.info("="*60)
    # asyncio.run(test_multiple_trades())
