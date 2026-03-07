import asyncio
import os
import re
import sys
import time
import pandas as pd
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PocketOption API
from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection, OrderStatus

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')

# Channel ID from the URL
CHANNEL_ID = -1002420379150

# Trading configuration
TRADE_AMOUNT = 1.0  # Base trade amount (will be set by user input)
IS_DEMO = True  # Use demo account (will be set by user input)
STRATEGY = "multi_asset"  # Trading strategy (will be set by user input)
MULTIPLIER = 2.5  # Martingale multiplier

# Shared client for trading (to prevent multiple connections)
shared_client = None
client_lock = asyncio.Lock()

# Signal storage
pending_signals = {}  # {signal_key: {pair, time, direction, timestamp, message_time}}
upcoming_trades = []  # List of scheduled trades
import threading

# Track asset trading state for martingale strategy
asset_states = {}  # {asset_name: {'step': 0, 'last_trade': None, 'history': []}}

def display_upcoming_trades_loop():
    """Continuously display upcoming trades"""
    while True:
        try:
            # Clear screen (Windows)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("=" * 60)
            print("🤖 POCKET OPTION TRADING BOT - UPCOMING TRADES")
            print("=" * 60)
            print(f"⏰ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"💰 Base Amount: ${TRADE_AMOUNT}")
            print(f"📊 Strategy: Martingale")
            print(f"🔢 Multiplier: {MULTIPLIER}x")
            print(f"🎮 Mode: {'DEMO' if IS_DEMO else 'REAL'}")
            print("=" * 60)
            
            # Show asset states
            if asset_states:
                print("\n📊 ASSET MARTINGALE STATUS:")
                print("-" * 60)
                for asset, state in asset_states.items():
                    step = state['step']
                    next_amount = TRADE_AMOUNT * (MULTIPLIER ** step)
                    print(f"  {asset}: Step {step} | Next Trade: ${next_amount:.2f}")
                print("-" * 60)
            
            if not upcoming_trades:
                print("\n📅 No upcoming trades scheduled")
                print("\n⏳ Waiting for signals from Telegram channel...")
            else:
                print(f"\n📅 UPCOMING SCHEDULED TRADES ({len(upcoming_trades)}):")
                print("-" * 60)
                
                for i, trade in enumerate(upcoming_trades, 1):
                    signal = trade['signal']
                    execution_time = trade['execution_time']
                    
                    # Calculate time remaining
                    now = datetime.now(execution_time.tzinfo) if execution_time.tzinfo else datetime.now()
                    time_remaining = (execution_time - now).total_seconds()
                    
                    if time_remaining > 0:
                        minutes = int(time_remaining // 60)
                        seconds = int(time_remaining % 60)
                        time_str = f"{minutes}m {seconds}s"
                    else:
                        time_str = "Executing..."
                    
                    # Get asset name and calculate trade amount
                    asset_name = map_asset_name(signal['pair'])
                    if asset_name not in asset_states:
                        asset_states[asset_name] = {'step': 0, 'last_trade': None, 'history': []}
                    
                    current_step = asset_states[asset_name]['step']
                    trade_amount = TRADE_AMOUNT * (MULTIPLIER ** current_step)
                    
                    print(f"\n{i}. {signal['direction']} {signal['pair']}")
                    print(f"   ⏰ Execution Time: {execution_time.strftime('%H:%M:%S')}")
                    print(f"   ⏱️  Time Remaining: {time_str}")
                    print(f"   💰 Duration: {signal['time_minutes']} min")
                    print(f"   💵 Trade Amount: ${trade_amount:.2f} (Step {current_step})")
            
            print("\n" + "=" * 60)
            print("Press Ctrl+C to stop")
            print("=" * 60)
            
            time.sleep(1)  # Update every second
            
        except Exception as e:
            print(f"Display error: {e}")
            time.sleep(1)








async def fetch_channel_messages():
    """Fetch messages from the specified Telegram channel with minimal logging"""
    
    # Use the same session name as the message formatter
    client = TelegramClient('session_formatter', API_ID, API_HASH)
    
    try:
        await client.start(PHONE_NUMBER)
        
        # Get the channel entity
        channel = await client.get_entity(CHANNEL_ID)
        
        # Get only recent messages (last 5 minutes) to avoid processing old signals
        recent_time = datetime.now() - timedelta(minutes=5)
        
        # Get initial message history
        messages = await client(GetHistoryRequest(
            peer=channel,
            limit=20,
            offset_date=recent_time,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        
        # Process only recent messages
        for i, message in enumerate(reversed(messages.messages), 1):
            if message.message:
                process_signal_message(message.message, message.date)
        
        # Monitor for new messages
        last_message_id = messages.messages[0].id if messages.messages else 0
        
        while True:
            try:
                # Get new messages
                new_messages = await client(GetHistoryRequest(
                    peer=channel,
                    limit=10,
                    offset_id=last_message_id,
                    offset_date=None,
                    max_id=0,
                    min_id=0,
                    add_offset=0,
                    hash=0
                ))
                
                if new_messages.messages:
                    # Process new messages (oldest first)
                    for message in reversed(new_messages.messages):
                        if message.message:
                            process_signal_message(message.message, message.date)
                            # Update last message ID
                            last_message_id = message.id
                
                # Wait before checking again
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                await asyncio.sleep(5)  # Wait longer on error
        
        return messages.messages
        
    except Exception as e:
        return None
    finally:
        await client.disconnect()

def process_signal_message(message_text: str, message_time: datetime):
    """Process message text to extract trading signals with minimal logging"""
    global pending_signals, upcoming_trades
    
    # Only process messages from the last 5 minutes to avoid old signals
    now = datetime.now(message_time.tzinfo) if message_time.tzinfo else datetime.now()
    time_diff = (now - message_time).total_seconds()
    
    # Skip messages older than 5 minutes
    if time_diff > 300:  # 5 minutes = 300 seconds
        return
    
    # Pattern 1: Asset and time (📈 Pair: EUR/CHF OTC, ⌛ time: 1 min)
    asset_time_pattern = r'📈\s*Pair:\s*([A-Z]+/[A-Z]+(?:\s+OTC)?)\s*⌛\s*time:\s*(\d+)\s*min'
    
    # Pattern 2: Direction (Buy or Sell) - standalone message
    direction_pattern = r'^(Buy|Sell)$'
    
    # Extract asset and time
    asset_time_match = re.search(asset_time_pattern, message_text, re.IGNORECASE)
    direction_match = re.search(direction_pattern, message_text, re.IGNORECASE)
    
    if asset_time_match:
        pair = asset_time_match.group(1).strip()
        time_minutes = int(asset_time_match.group(2))
        
        # Create signal key with timestamp to handle multiple signals for same asset
        signal_key = f"{pair}_{message_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate exact trade time (signal time + 1 minute buffer for execution)
        trade_time = message_time + timedelta(minutes=1)
        
        # Store or update pending signal
        pending_signals[signal_key] = {
            'pair': pair,
            'time_minutes': time_minutes,
            'direction': None,
            'timestamp': message_time,
            'message_time': message_time,
            'trade_time': trade_time,
            'scheduled': False,
            'processed_directions': []  # Track processed directions for this signal
        }
    
    # Extract direction (standalone Buy/Sell message)
    elif direction_match:
        direction = direction_match.group(1).upper()
        
        # Try to match with most recent pending signal
        if pending_signals:
            # Find the most recent signal without direction
            recent_signal = None
            recent_key = None
            
            for key, signal in pending_signals.items():
                if signal['direction'] is None and not signal['scheduled']:
                    # Check if this direction hasn't been processed for this signal
                    if direction not in signal.get('processed_directions', []):
                        if recent_signal is None or signal['timestamp'] > recent_signal['timestamp']:
                            recent_signal = signal
                            recent_key = key
            
            if recent_signal:
                # Update the original signal with direction
                recent_signal['direction'] = direction
                recent_signal['processed_directions'].append(direction)
                
                # Schedule the trade for this signal
                schedule_trade(recent_signal, recent_key)

def schedule_trade(signal: Dict, signal_key: str):
    """Schedule trade for exact time with minimal logging - only future trades"""
    global upcoming_trades
    
    # Mark as scheduled
    signal['scheduled'] = True
    
    # Calculate delay until trade time
    now = datetime.now(signal['trade_time'].tzinfo) if signal['trade_time'].tzinfo else datetime.now()
    delay_seconds = (signal['trade_time'] - now).total_seconds()
    
    # Only schedule if trade time is in the future (at least 5 seconds ahead)
    if delay_seconds > 5:
        # Add to upcoming trades
        upcoming_trades.append({
            'signal': signal,
            'signal_key': signal_key,
            'execution_time': signal['trade_time'],
            'delay_seconds': delay_seconds
        })
        
        # Schedule the trade execution
        timer = threading.Timer(delay_seconds, execute_scheduled_trade, args=[signal, signal_key])
        timer.start()
    else:
        # Skip past signals
        print(f"⏭️  Skipping past signal: {signal['pair']} {signal['direction']} (was {abs(delay_seconds):.0f}s ago)")

def execute_scheduled_trade(signal: Dict, signal_key: str):
    """Execute scheduled trade with minimal logging"""
    # Remove from upcoming trades
    global upcoming_trades
    upcoming_trades = [trade for trade in upcoming_trades if trade['signal_key'] != signal_key]
    
    # Execute the trade
    asyncio.create_task(execute_trade_signal(signal))



def map_asset_name(pair: str) -> str:
    """Map asset pair to Pocket Option format in AUDCAD_otc style"""
    # Convert to format: AUDCAD_otc or AUDCAD
    
    # Remove spaces and convert to UPPERCASE for base name
    clean_pair = pair.replace(' ', '').replace('/', '').upper()
    
    # Check if the original message contains "OTC" (handle both "OTC" and "OTC" at end)
    if 'otc' in pair.upper() or clean_pair.endswith('OTC'):
        # Message contains OTC or asset name ends with OTC
        if clean_pair.endswith('OTC'):
            # Handle case like "USDJPYOTC" -> "USDJPY_otc"
            base_name = clean_pair[:-3]  # Remove "OTC"
            result = f"{base_name}_otc"
        else:
            # Normal case: add _otc suffix
            result = f"{clean_pair}_otc"
        return result
    else:
        # Message does NOT contain OTC → keep without _otc
        return clean_pair

def validate_ssid(ssid: str) -> bool:
    """Basic SSID validation"""
    if not ssid:
        return False
    
    # Check if it looks like a valid PocketOption SSID
    if not ssid.startswith('42["auth"'):
        return False
    
    # Check for basic structure
    if '"session"' not in ssid or '"isDemo"' not in ssid:
        return False
    
    return True

async def get_shared_client():
    """Get or create a shared PocketOption client using exact app.py pattern"""
    global shared_client
    
    async with client_lock:
        if shared_client and shared_client.is_connected:
            return shared_client
        
        # Create new client
        ssid = os.getenv('SSID')
        if not ssid:
            raise Exception("SSID not found in environment variables")
        
        # Validate SSID format
        if not validate_ssid(ssid):
            raise Exception("Invalid SSID format - please get a fresh SSID from PocketOption")
        
        print(f"🔑 Using SSID: {ssid[:50]}...")
        
        # Use exact pattern from app.py
        shared_client = AsyncPocketOptionClient(
            ssid=ssid,
            is_demo=IS_DEMO,
            persistent_connection=False,
            auto_reconnect=False,
            enable_logging=False
        )
        
        try:
            print("� Connecting to PocketOption...")
            
            # Exact timeout and pattern from app.py
            await asyncio.wait_for(shared_client.connect(), timeout=15.0)
            balance = await asyncio.wait_for(shared_client.get_balance(), timeout=10.0)
            
            print(f"✅ Connected! {'DEMO' if IS_DEMO else 'REAL'} Account")
            print(f"💰 Balance: ${balance.balance:.2f}")
            
            # Verify connection is actually working
            if not shared_client.is_connected:
                raise Exception("Connection failed - client not connected after setup")
            
            return shared_client
            
        except asyncio.TimeoutError:
            print("❌ Connection timeout - SSID may be expired")
            print("� Please get a fresh SSID from PocketOption:")
            print("   1. Open PocketOption in browser")
            print("   2. Press F12 → Network → WS filter")
            print("   3. Look for 42[\"auth\",{\"session\":...")
            print("   4. Copy and update .env file")
            
            if shared_client:
                try:
                    await shared_client.disconnect()
                except:
                    pass
                shared_client = None
            raise Exception("Connection timeout - SSID expired")
            
        except Exception as e:
            error_msg = str(e)
            if "Not connected" in error_msg or "Connection" in error_msg:
                print(f"❌ Connection failed: {e}")
                print("💡 This usually means the SSID is expired or invalid")
                print("💡 Please get a fresh SSID from PocketOption")
            else:
                print(f"❌ Error: {e}")
            
            if shared_client:
                try:
                    await shared_client.disconnect()
                except:
                    pass
                shared_client = None
            raise Exception(f"Connection failed: {e}")

async def execute_trade_signal(signal: Dict):
    """Execute trade on Pocket Option using selected strategy with minimal logging"""
    try:
        # Get shared client (creates new one if needed)
        client = await get_shared_client()
        
        # Map asset name
        asset_name = map_asset_name(signal['pair'])
        print(f"📍 Trading asset: {asset_name}")
        
        # Convert direction
        order_direction = OrderDirection.CALL if signal['direction'] == 'Buy' else OrderDirection.PUT
        
        # Execute based on strategy
        if STRATEGY == 'multi_asset':
            await execute_strategy_trade(client, asset_name, order_direction, signal)
        elif STRATEGY == 'simple':
            await execute_simple_trade(client, asset_name, order_direction, signal)
        
    except Exception as e:
        print(f"❌ Trade execution error: {e}")
        # Reset shared client on error to force reconnection next time
        global shared_client
        async with client_lock:
            if shared_client:
                try:
                    await shared_client.disconnect()
                except:
                    pass
                shared_client = None
        print("🔄 Client reset - will reconnect on next signal")

async def execute_strategy_trade(client, asset_name: str, order_direction: OrderDirection, signal: Dict):
    """Execute trade using martingale strategy - each asset tracked independently"""
    try:
        # Verify client is still connected
        if not client.is_connected:
            print("❌ Client not connected in strategy trade")
            return
        
        # Initialize asset state if needed
        if asset_name not in asset_states:
            asset_states[asset_name] = {'step': 0, 'last_trade': None, 'history': []}
        
        # Get current step and calculate amount
        current_step = asset_states[asset_name]['step']
        current_amount = TRADE_AMOUNT * (MULTIPLIER ** current_step)
        
        # Place order
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n{'='*60}")
        print(f"📈 PLACING ORDER - {timestamp}")
        print(f"   Asset: {asset_name}")
        print(f"   Direction: {signal['direction']}")
        print(f"   Amount: ${current_amount:.2f}")
        print(f"   Step: {current_step}")
        print(f"   Duration: {signal['time_minutes']} min")
        print(f"{'='*60}")
        
        order_result = await client.place_order(
            asset=asset_name,
            direction=order_direction,
            amount=current_amount,
            duration=signal['time_minutes'] * 60
        )
        
        if order_result and order_result.status in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
            print(f"✅ Order placed successfully! Order ID: {order_result.order_id}")
            
            # Store trade info
            trade_info = {
                'order_id': order_result.order_id,
                'amount': current_amount,
                'step': current_step,
                'direction': signal['direction'],
                'timestamp': timestamp,
                'duration': signal['time_minutes'],
                'asset': asset_name
            }
            
            asset_states[asset_name]['last_trade'] = trade_info
            asset_states[asset_name]['history'].append(trade_info)
            
            # Wait for trade to complete
            print(f"⏳ Waiting {signal['time_minutes']} minute(s) for trade result...")
            await asyncio.sleep(signal['time_minutes'] * 60 + 5)  # Wait duration + 5 seconds buffer
            
            # Check trade result
            try:
                # Get trade history to check result
                result = await check_trade_result(client, order_result.order_id)
                
                if result == 'win':
                    print(f"✅ WIN! ${current_amount:.2f} profit")
                    print(f"🔄 Resetting {asset_name} to Step 0")
                    asset_states[asset_name]['step'] = 0
                    
                elif result == 'loss':
                    print(f"❌ LOSS! ${current_amount:.2f}")
                    
                    # Step up martingale
                    if current_step < 3:  # Max 3 steps (0, 1, 2, 3)
                        next_step = current_step + 1
                        next_amount = TRADE_AMOUNT * (MULTIPLIER ** next_step)
                        asset_states[asset_name]['step'] = next_step
                        print(f"📈 Stepping up {asset_name} to Step {next_step}")
                        print(f"💰 Next trade amount: ${next_amount:.2f}")
                    else:
                        print(f"⚠️  Max martingale steps reached for {asset_name}")
                        print(f"🔄 Resetting to Step 0")
                        asset_states[asset_name]['step'] = 0
                        
            except Exception as e:
                print(f"⚠️  Could not verify trade result: {e}")
                print(f"💡 Assuming loss and stepping up martingale")
                
                # On error, assume loss and step up
                if current_step < 3:
                    next_step = current_step + 1
                    asset_states[asset_name]['step'] = next_step
                    next_amount = TRADE_AMOUNT * (MULTIPLIER ** next_step)
                    print(f"📈 Stepping up {asset_name} to Step {next_step} (${next_amount:.2f})")
                else:
                    asset_states[asset_name]['step'] = 0
                    print(f"🔄 Resetting {asset_name} to Step 0")
                
        else:
            print(f"❌ Trade failed: {order_result.error_message if order_result and order_result.error_message else 'Unknown error'}")
            
    except Exception as e:
        print(f"❌ Strategy trade error: {e}")

async def check_trade_result(client, order_id: str) -> str:
    """Check if trade was win or loss"""
    try:
        # Try to get order status/result
        # This is a placeholder - you'll need to implement actual result checking
        # based on your API's capabilities
        
        # For now, return 'unknown' - you should implement proper result checking
        return 'loss'  # Default to loss to continue martingale
        
    except Exception as e:
        print(f"Error checking trade result: {e}")
        return 'loss'  # Default to loss on error

async def execute_simple_trade(client, asset_name: str, order_direction: OrderDirection, signal: Dict):
    """Execute simple single trade"""
    try:
        # Verify client is still connected
        if not client.is_connected:
            print("❌ Client not connected in simple trade")
            return
            
        print(f"🔄 Placing SIMPLE trade: {signal['direction']} {asset_name} for ${TRADE_AMOUNT}")
        print(f"⏰ Signal time: {signal['timestamp']}, Duration: {signal['time_minutes']} min")
        
        # Convert direction if needed (in case it's passed as string)
        if isinstance(order_direction, str):
            order_direction = OrderDirection.CALL if order_direction == 'Buy' else OrderDirection.PUT
        
        # Place order
        order_result = await client.place_order(
            asset=asset_name,
            direction=order_direction,
            amount=TRADE_AMOUNT,
            duration=signal['time_minutes'] * 60
        )
        
        if order_result and order_result.status in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
            print(f"✅ Simple trade placed successfully! Order ID: {order_result.order_id}")
        else:
            print(f"❌ Simple trade failed: {order_result.error_message if order_result and order_result.error_message else 'Unknown error'}")
            
    except Exception as e:
        print(f"❌ Simple trade error: {e}")

def get_user_config():
    """Get user configuration from .env file with minimal logging"""
    global TRADE_AMOUNT, IS_DEMO, MULTIPLIER, STRATEGY
    
    # Get SSID
    ssid = os.getenv('SSID')
    if not ssid:
        print("❌ SSID not found in .env file")
        return False
    
    # Get Telegram credentials
    api_id = os.getenv('TELEGRAM_API_ID')
    if not api_id:
        print("❌ TELEGRAM_API_ID not found in .env file")
        return False
    
    api_hash = os.getenv('TELEGRAM_API_HASH')
    if not api_hash:
        print("❌ TELEGRAM_API_HASH not found in .env file")
        return False
    
    phone = os.getenv('TELEGRAM_PHONE')
    if not phone:
        print("❌ TELEGRAM_PHONE not found in .env file")
        return False
    
    # Set default trade amount
    TRADE_AMOUNT = 1.0
    
    # Get account type
    IS_DEMO = True
    
    # Get multiplier
    MULTIPLIER = 2.5
    
    # Set default strategy to multi_asset
    STRATEGY = 'multi_asset'
    
    return True

async def cleanup_shared_client():
    """Cleanup shared client connection"""
    global shared_client
    async with client_lock:
        if shared_client:
            try:
                await shared_client.disconnect()
                print("🔌 Disconnected from Pocket Option")
            except:
                pass
            shared_client = None

def main():
    """Main function to run the trading bot with minimal logging"""
    # Get user configuration
    if not get_user_config():
        return
    
    # Start display thread
    display_thread = threading.Thread(target=display_upcoming_trades_loop, daemon=True)
    display_thread.start()
    
    # Start live trading
    try:
        # Run the message fetcher and trader
        asyncio.run(fetch_channel_messages())
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        # Cleanup connection on exit
        asyncio.run(cleanup_shared_client())
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        # Cleanup connection on error
        asyncio.run(cleanup_shared_client())

if __name__ == "__main__":
    main()
