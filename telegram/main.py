import asyncio
import os
import re
import sys
import time
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime, timedelta
from typing import Dict

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PocketOption API
from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection, OrderStatus

# Load environment variables
load_dotenv()

# Get credentials from environment variables
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')

# Channel username (without t.me/)
CHANNEL_USERNAME = 'testpob1234'

# Trading configuration
TRADE_AMOUNT = 1.0
IS_DEMO = True
MULTIPLIER = 2.5

# Signal storage
pending_signals = {}
upcoming_trades = []
import threading

# Track asset trading state for martingale strategy
asset_states = {}

# Global martingale step (shared across all assets)
global_martingale_step = 0

# Track past trades
past_trades = []  # List of completed trades

# Track recent signals for display
recent_signals = []  # List of recent signals received

def log_to_file(message: str):
    """Helper function to log messages with UTF-8 encoding"""
    try:
        with open('telegram/trading_log.txt', 'a', encoding='utf-8') as f:
            f.write(message)
    except Exception as e:
        print(f"Log error: {e}")

def display_upcoming_trades_loop():
    """Continuously display upcoming trades"""
    while True:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("=" * 90)
            print("🤖 POCKET OPTION BOT - testpob1234 Channel")
            print("=" * 90)
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 💰 ${TRADE_AMOUNT} | 🔢 {MULTIPLIER}x | 🎮 {'DEMO' if IS_DEMO else 'REAL'}")
            print("=" * 90)
            
            if not upcoming_trades:
                print("\n📅 No upcoming trades scheduled")
                print("\n⏳ Waiting for signals from Telegram channel...")
            else:
                print(f"\n📅 UPCOMING TRADES ({len(upcoming_trades)}):")
                print("-" * 90)
                print(f"{'#':<3} | {'Time':<8} | {'Asset':<16} | {'Dir':<4} | {'Amount':<9} | {'Step':<4} | {'Result':<12}")
                print("-" * 90)
                
                for i, trade in enumerate(upcoming_trades, 1):
                    signal = trade['signal']
                    execution_time = trade['execution_time']
                    
                    now = datetime.now(execution_time.tzinfo) if execution_time.tzinfo else datetime.now()
                    time_remaining = (execution_time - now).total_seconds()
                    
                    if time_remaining > 0:
                        minutes = int(time_remaining // 60)
                        seconds = int(time_remaining % 60)
                        time_str = f"{minutes}m {seconds}s"
                    else:
                        time_str = "Now"
                    
                    # Use global martingale step for all assets
                    trade_amount = TRADE_AMOUNT * (MULTIPLIER ** global_martingale_step)
                    
                    # Get result from past trades if available
                    result = "⏳ Pending"
                    for past_trade in reversed(past_trades):
                        if past_trade['asset'] == signal['pair']:
                            if past_trade['result'] == 'win':
                                result = "✅ Win"
                            elif past_trade['result'] == 'loss':
                                result = "❌ Loss"
                            elif past_trade['result'] == 'failed':
                                result = "⚠️ Failed"
                            elif past_trade['result'] == 'pending':
                                result = "⏳ Pending"
                            break
                    
                    print(f"{i:<3} | {time_str:<8} | {signal['pair']:<16} | {signal['direction']:<4} | ${trade_amount:<8.2f} | {global_martingale_step:<4} | {result:<12}")
                
                print("-" * 90)
            
            print("\n" + "=" * 90)
            print("Press Ctrl+C to stop")
            print("=" * 90)
            
            time.sleep(0.01)  # 10ms
            
        except Exception as e:
            print(f"Display error: {e}")
            time.sleep(0.01)  # 10ms
                    

def process_signal_message(message_text: str, message_time: datetime, is_historical: bool = False):
    """Process message text to extract trading signals"""
    global pending_signals, upcoming_trades, recent_signals
    
    # Skip all historical messages on startup to prevent multiple old signals from executing
    if is_historical:
        return
    
    # Pattern 1: Asset and time - handle emoji variations
    # Matches: 📈 Pair: AUD/USD OTC\n⌛️ time: 1 min
    asset_time_pattern = r'📈\s*Pair:\s*([A-Z]+/[A-Z]+(?:\s+OTC)?)\s*\n?\s*⌛[️]?\s*time:\s*(\d+)\s*min'
    
    # Pattern 2: Direction (Buy or Sell) - exact match
    direction_pattern = r'^(Buy|Sell)\s*$'
    
    asset_time_match = re.search(asset_time_pattern, message_text, re.IGNORECASE | re.MULTILINE)
    direction_match = re.search(direction_pattern, message_text, re.IGNORECASE | re.MULTILINE)
    
    if asset_time_match:
        pair = asset_time_match.group(1).strip()
        time_minutes = int(asset_time_match.group(2))
        
        signal_key = f"{pair}_{message_time.strftime('%Y%m%d_%H%M%S')}"
        # Execute immediately when direction comes (no delay)
        # Make sure trade_time has same timezone as message_time
        if message_time.tzinfo:
            trade_time = datetime.now(message_time.tzinfo)
        else:
            trade_time = datetime.now()
        
        pending_signals[signal_key] = {
            'pair': pair,
            'time_minutes': time_minutes,
            'direction': None,
            'timestamp': message_time,
            'message_time': message_time,
            'trade_time': trade_time,
            'scheduled': False,
            'processed_directions': []
        }
        
        # Add to recent signals for display
        recent_signals.append({
            'time': message_time.strftime('%H:%M:%S'),
            'pair': pair,
            'direction': None,
            'duration': time_minutes,
            'scheduled': False
        })
    
    elif direction_match:
        direction = direction_match.group(1).upper()
        
        if pending_signals:
            # Find the most recent signal (regardless of whether it has direction or is scheduled)
            recent_signal = None
            recent_key = None
            
            for key, signal in pending_signals.items():
                if recent_signal is None or signal['timestamp'] > recent_signal['timestamp']:
                    recent_signal = signal
                    recent_key = key
            
            if recent_signal:
                # Create a new signal based on the most recent one
                new_signal_key = f"{recent_signal['pair']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Use same timezone as message_time
                if message_time.tzinfo:
                    current_time = datetime.now(message_time.tzinfo)
                else:
                    current_time = datetime.now()
                
                new_signal = {
                    'pair': recent_signal['pair'],
                    'time_minutes': recent_signal['time_minutes'],
                    'direction': direction,
                    'timestamp': current_time,
                    'message_time': message_time,
                    'trade_time': current_time,
                    'scheduled': False,
                    'processed_directions': [direction]
                }
                
                # Add to pending signals
                pending_signals[new_signal_key] = new_signal
                
                # Update recent signals display
                recent_signals.append({
                    'time': message_time.strftime('%H:%M:%S'),
                    'pair': recent_signal['pair'],
                    'direction': direction,
                    'duration': recent_signal['time_minutes'],
                    'scheduled': False
                })
                
                # Schedule the trade immediately
                schedule_trade(new_signal, new_signal_key)

def schedule_trade(signal: Dict, signal_key: str):
    """Schedule trade for immediate execution"""
    global upcoming_trades, recent_signals
    
    signal['scheduled'] = True
    
    # Execute immediately (0.001 second = 1ms delay)
    delay_seconds = 0.001
    
    # Log scheduling
    log_to_file(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📅 Scheduling trade: {signal['pair']} {signal['direction']} in {delay_seconds}s\n")
    
    upcoming_trades.append({
        'signal': signal,
        'signal_key': signal_key,
        'execution_time': datetime.now() + timedelta(seconds=delay_seconds),
        'delay_seconds': delay_seconds
    })
    
    timer = threading.Timer(delay_seconds, execute_scheduled_trade, args=[signal, signal_key])
    timer.start()
    
    log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Trade scheduled, timer started\n")
    
    # Update recent signals to show scheduled
    for sig in recent_signals:
        if sig['pair'] == signal['pair'] and sig['direction'] == signal['direction']:
            sig['scheduled'] = True
            break

def execute_scheduled_trade(signal: Dict, signal_key: str):
    """Execute scheduled trade"""
    global upcoming_trades
    
    # Log execution start
    log_to_file(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⚡ Executing scheduled trade: {signal['pair']} {signal['direction']}\n")
    
    upcoming_trades = [trade for trade in upcoming_trades if trade['signal_key'] != signal_key]
    
    # Create a new event loop for this thread
    try:
        log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] Creating event loop for trade execution\n")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] Running trade execution\n")
        
        loop.run_until_complete(execute_trade_signal(signal))
        loop.close()
        
        log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Trade execution completed\n")
        
    except Exception as e:
        log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error executing trade: {e}\n")
        import traceback
        log_to_file(f"{traceback.format_exc()}\n")
        
        print(f"\n❌ Error executing trade: {e}")

def map_asset_name(pair: str) -> str:
    """Map asset pair to Pocket Option format"""
    clean_pair = pair.replace(' ', '').replace('/', '').upper()
    
    if 'otc' in pair.upper() or clean_pair.endswith('OTC'):
        if clean_pair.endswith('OTC'):
            base_name = clean_pair[:-3]
            result = f"{base_name}_otc"
        else:
            result = f"{clean_pair}_otc"
        return result
    else:
        return clean_pair

def validate_ssid(ssid: str) -> bool:
    """Basic SSID validation"""
    if not ssid:
        return False
    if not ssid.startswith('42["auth"'):
        return False
    if '"session"' not in ssid or '"isDemo"' not in ssid:
        return False
    return True

async def get_client_for_trade():
    """Create a new independent client for each trade"""
    ssid = os.getenv('SSID')
    if not ssid:
        raise Exception("SSID not found in environment variables")
    
    if not validate_ssid(ssid):
        raise Exception("Invalid SSID format")
    
    log_to_file(f"🔑 Creating new client for trade\n")
    
    client = AsyncPocketOptionClient(
        ssid=ssid,
        is_demo=IS_DEMO,
        persistent_connection=False,
        auto_reconnect=False,
        enable_logging=False
    )
    
    try:
        log_to_file("🔌 Connecting to PocketOption...\n")
        await asyncio.wait_for(client.connect(), timeout=15.0)
        balance = await asyncio.wait_for(client.get_balance(), timeout=10.0)
        
        log_to_file(f"✅ Connected! {'DEMO' if IS_DEMO else 'REAL'} Account\n")
        log_to_file(f"💰 Balance: ${balance.balance:.2f}\n")
        
        if not client.is_connected:
            raise Exception("Connection failed")
        
        return client
        
    except asyncio.TimeoutError:
        log_to_file("❌ Connection timeout - SSID may be expired\n")
        if client:
            try:
                await client.disconnect()
            except:
                pass
        raise Exception("Connection timeout")
        
    except Exception as e:
        log_to_file(f"❌ Error: {e}\n")
        if client:
            try:
                await client.disconnect()
            except:
                pass
        raise

async def execute_trade_signal(signal: Dict):
    """Execute trade on Pocket Option"""
    client = None
    try:
        # Log trade signal received
        log_to_file(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📥 Trade signal received: {signal['pair']} {signal['direction']}\n")
        
        # Create independent client for this trade
        client = await get_client_for_trade()
        asset_name = map_asset_name(signal['pair'])
        
        log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] 📍 Mapped asset: {asset_name}\n")
        
        order_direction = OrderDirection.CALL if signal['direction'] == 'BUY' else OrderDirection.PUT
        
        await execute_strategy_trade(client, asset_name, order_direction, signal)
        
    except Exception as e:
        log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Trade execution error: {e}\n")
        import traceback
        log_to_file(f"{traceback.format_exc()}\n")
        
        print(f"❌ Trade execution error: {e}")
    finally:
        # Always disconnect the client when done
        if client:
            try:
                await client.disconnect()
                log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] 🔌 Client disconnected\n")
            except:
                pass

async def execute_strategy_trade(client, asset_name: str, order_direction: OrderDirection, signal: Dict):
    """Execute trade using global martingale strategy"""
    global past_trades, global_martingale_step
    
    try:
        if not client.is_connected:
            print(f"\n❌ Client not connected for {asset_name}")
            
            # Log to file
            log_to_file(f"\n[{datetime.now().strftime('%H:%M:%S')}] ERROR: Client not connected for {asset_name}\n")
            
            # Add failed trade to past trades
            past_trades.append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'asset': asset_name,
                'direction': signal['direction'],
                'amount': TRADE_AMOUNT * (MULTIPLIER ** global_martingale_step),
                'step': global_martingale_step,
                'result': 'failed'
            })
            return
        
        # Use global martingale step for all assets
        current_amount = TRADE_AMOUNT * (MULTIPLIER ** global_martingale_step)
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Log trade attempt
        log_to_file(f"\n[{timestamp}] Placing order: {asset_name} {signal['direction']} ${current_amount:.2f} Global Step {global_martingale_step}\n")
        
        order_result = await client.place_order(
            asset=asset_name,
            direction=order_direction,
            amount=current_amount,
            duration=signal['time_minutes'] * 60
        )
        
        if order_result and order_result.status in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
            trade_info = {
                'order_id': order_result.order_id,
                'amount': current_amount,
                'step': global_martingale_step,
                'direction': signal['direction'],
                'timestamp': timestamp,
                'duration': signal['time_minutes'],
                'asset': asset_name
            }
            
            # Store in asset states for tracking
            if asset_name not in asset_states:
                asset_states[asset_name] = {'last_trade': None, 'history': []}
            
            asset_states[asset_name]['last_trade'] = trade_info
            asset_states[asset_name]['history'].append(trade_info)
            
            # Add to past trades as pending
            past_trades.append({
                'time': timestamp,
                'asset': asset_name,
                'direction': signal['direction'],
                'amount': current_amount,
                'step': global_martingale_step,
                'result': 'pending'
            })
            
            # Log success
            log_to_file(f"[{timestamp}] ✅ Order placed! ID: {order_result.order_id}\n")
            
            # Wait for trade duration + buffer
            await asyncio.sleep(signal['time_minutes'] * 60 + 5)
            
            log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] ⏰ Trade duration completed, checking result...\n")
            
            # Check actual trade result using API
            try:
                result_data = await client.check_win(order_result.order_id, max_wait_time=30.0)
                
                log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Result data: {result_data}\n")
                
                if result_data and result_data.get('completed'):
                    result = result_data.get('result', 'loss')  # 'win', 'loss', or 'draw'
                    profit = result_data.get('profit', 0)
                    
                    # Log result
                    log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] Result: {result.upper()} | Profit: ${profit:.2f}\n")
                else:
                    # Couldn't get result, assume loss
                    result = 'loss'
                    log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] Could not verify result, assuming loss\n")
            except Exception as e:
                # Error checking result, assume loss
                result = 'loss'
                log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] Error checking result: {e}, assuming loss\n")
                import traceback
                log_to_file(f"{traceback.format_exc()}\n")
            
            # Update past trade result
            for trade in reversed(past_trades):
                if trade['asset'] == asset_name and trade['result'] == 'pending':
                    trade['result'] = result
                    break
            
            # Update GLOBAL martingale step based on result
            if result == 'win':
                # WIN: Reset global step to 0 and clear ALL past trades
                global_martingale_step = 0
                past_trades.clear()
                
                log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ WIN! Reset global step to 0 and cleared all history\n")
            else:
                # LOSS: Keep record and step up globally
                if global_martingale_step < 3:
                    global_martingale_step += 1
                    next_amount = TRADE_AMOUNT * (MULTIPLIER ** global_martingale_step)
                    log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ LOSS! Global step increased to {global_martingale_step} (${next_amount:.2f})\n")
                else:
                    # Max steps reached, reset but keep the loss records
                    global_martingale_step = 0
                    log_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] Max steps reached, reset global step to 0\n")
                
        else:
            error_msg = order_result.error_message if order_result and order_result.error_message else 'Unknown error'
            
            # Log failure
            log_to_file(f"[{timestamp}] ❌ Trade failed: {error_msg}\n")
            
            # Add failed trade to past trades
            past_trades.append({
                'time': timestamp,
                'asset': asset_name,
                'direction': signal['direction'],
                'amount': current_amount,
                'step': global_martingale_step,
                'result': 'failed'
            })
            
    except Exception as e:
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Log exception
        log_to_file(f"[{timestamp}] ❌ Exception in strategy trade: {e}\n")
        import traceback
        log_to_file(f"{traceback.format_exc()}\n")
        
        print(f"\n❌ Strategy trade error: {e}")

async def fetch_channel_messages():
    """Fetch messages from testpob1234 channel"""
    
    # Use unique session for this bot
    client = TelegramClient('session_testpob1234', API_ID, API_HASH)
    
    try:
        await client.start(PHONE_NUMBER)
        
        try:
            channel = await client.get_entity(CHANNEL_USERNAME)
        except Exception as e:
            print(f"\n❌ Error finding channel: {e}")
            print(f"💡 Make sure you're a member of t.me/{CHANNEL_USERNAME}")
            return
        
        # Get messages from last 30 minutes
        recent_time = datetime.now() - timedelta(minutes=30)
        
        messages = await client(GetHistoryRequest(
            peer=channel,
            limit=50,
            offset_date=recent_time,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        
        # Process initial messages silently (mark as historical to skip execution)
        processed_count = 0
        for message in reversed(messages.messages):
            if message.message:
                process_signal_message(message.message, message.date, is_historical=True)
                processed_count += 1
        
        # Log startup info to a file so it doesn't interfere with display
        with open('telegram/trading_log.txt', 'w', encoding='utf-8') as f:
            f.write(f"Bot started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Connected to: {channel.title}\n")
            f.write(f"Processed {processed_count} historical messages (skipped for execution)\n")
            f.write(f"⏳ Waiting for new signals...\n")
            f.write(f"\nNote: Only NEW messages received after bot startup will be executed.\n")
            f.write(f"This prevents multiple old signals from executing simultaneously.\n")
        
        # Wait 10ms before starting display loop
        await asyncio.sleep(0.01)  # 10ms
        
        last_message_id = messages.messages[0].id if messages.messages else 0
        
        while True:
            try:
                # Get latest messages (don't use offset_id, just get latest)
                new_messages = await client(GetHistoryRequest(
                    peer=channel,
                    limit=10,
                    offset_date=None,
                    offset_id=0,  # Get latest messages
                    max_id=0,
                    min_id=0,
                    add_offset=0,
                    hash=0
                ))
                
                if new_messages.messages:
                    # Check for messages newer than last_message_id
                    for message in reversed(new_messages.messages):
                        if message.message and message.id > last_message_id:
                            process_signal_message(message.message, message.date, is_historical=False)
                            last_message_id = message.id
                            
                            # Log new message
                            log_to_file(f"\n[{datetime.now().strftime('%H:%M:%S')}] New message ID {message.id}\n")
                            log_to_file(f"Pending signals: {len(pending_signals)}, Upcoming trades: {len(upcoming_trades)}\n")
                
                await asyncio.sleep(0.01)  # 10ms
                
            except Exception as e:
                await asyncio.sleep(0.01)  # 10ms
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await client.disconnect()

async def cleanup_shared_client():
    """Cleanup function (no longer needed with independent clients)"""
    log_to_file("👋 Bot shutting down\n")

def get_user_config():
    """Get user configuration"""
    global TRADE_AMOUNT, IS_DEMO, MULTIPLIER
    
    ssid = os.getenv('SSID')
    if not ssid:
        print("❌ SSID not found in .env file")
        return False
    
    api_id = os.getenv('TELEGRAM_API_ID')
    if not api_id:
        print("❌ TELEGRAM_API_ID not found")
        return False
    
    api_hash = os.getenv('TELEGRAM_API_HASH')
    if not api_hash:
        print("❌ TELEGRAM_API_HASH not found")
        return False
    
    phone = os.getenv('TELEGRAM_PHONE')
    if not phone:
        print("❌ TELEGRAM_PHONE not found")
        return False
    
    TRADE_AMOUNT = 1.0
    IS_DEMO = True
    MULTIPLIER = 2.5
    
    return True

def main():
    """Main function"""
    if not get_user_config():
        return
    
    # Enable display thread
    display_thread = threading.Thread(target=display_upcoming_trades_loop, daemon=True)
    display_thread.start()
    
    try:
        asyncio.run(fetch_channel_messages())
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        asyncio.run(cleanup_shared_client())
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        asyncio.run(cleanup_shared_client())

if __name__ == "__main__":
    main()
s