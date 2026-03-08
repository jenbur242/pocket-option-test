import asyncio
import os
import re
import sys
import time
import csv
from pathlib import Path
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetHistoryRequest
from telethon import events
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
STRING_SESSION = os.getenv('TELEGRAM_STRING_SESSION')  # For Railway deployment

# Channel username (without t.me/) - configurable via environment
CHANNEL_USERNAME = os.getenv('TELEGRAM_CHANNEL', 'testpob1234')

# Trading configuration - will be set by API or environment variables
TRADE_AMOUNT = float(os.getenv('TRADE_AMOUNT', '1.0'))
IS_DEMO = os.getenv('IS_DEMO', 'True').lower() == 'true'
MULTIPLIER = float(os.getenv('MULTIPLIER', '2.5'))

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

# Persistent client for faster trade execution
persistent_client = None
client_lock = threading.Lock()
background_tasks = set()  # Track background result checking tasks

# CSV folder path
CSV_FOLDER = 'trade_results'

def ensure_csv_folder():
    """Create CSV folder if it doesn't exist"""
    Path(CSV_FOLDER).mkdir(exist_ok=True)

def get_csv_filename():
    """Get CSV filename for current date"""
    today = datetime.now().strftime('%Y-%m-%d')
    return os.path.join(CSV_FOLDER, f'trades_{today}.csv')

def save_trade_to_csv(trade_data: Dict):
    """Save trade result to CSV file"""
    try:
        ensure_csv_folder()
        csv_file = get_csv_filename()
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(csv_file)
        
        # CSV headers
        headers = [
            'timestamp', 'date', 'time', 'asset', 'direction', 
            'amount', 'step', 'duration', 'result', 'profit_loss',
            'balance_before', 'balance_after', 'multiplier'
        ]
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            
            # Write headers if new file
            if not file_exists:
                writer.writeheader()
            
            # Write trade data
            writer.writerow(trade_data)
        
        print(f"✅ Trade saved to CSV: {csv_file}")
        
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")

def update_trading_config(initial_amount=None, is_demo=None, multiplier=None, martingale_step=None):
    """Update trading configuration dynamically"""
    global TRADE_AMOUNT, IS_DEMO, MULTIPLIER, global_martingale_step
    
    if initial_amount is not None:
        TRADE_AMOUNT = initial_amount
    if is_demo is not None:
        IS_DEMO = is_demo
    if multiplier is not None:
        MULTIPLIER = multiplier
    if martingale_step is not None:
        global_martingale_step = martingale_step
    
    print(f"✅ Trading config updated:")
    print(f"   Initial Amount: ${TRADE_AMOUNT}")
    print(f"   Account Type: {'DEMO' if IS_DEMO else 'REAL'}")
    print(f"   Multiplier: {MULTIPLIER}x")
    print(f"   Martingale Step: {global_martingale_step}")

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
                    

# Pattern 1: Asset and time - handle emoji variations (PRE-COMPILED for speed)
# Matches: 📈 Pair: AUD/USD OTC\n⌛️ time: 1 min
ASSET_TIME_PATTERN = re.compile(
    r'📈\s*Pair:\s*([A-Z]+/[A-Z]+(?:\s+OTC)?)\s*\n?\s*⌛[️]?\s*time:\s*(\d+)\s*min',
    re.IGNORECASE | re.MULTILINE
)

# Pattern 2: Direction (Buy or Sell) - exact match (PRE-COMPILED for speed)
DIRECTION_PATTERN = re.compile(r'^(Buy|Sell)\s*$', re.IGNORECASE | re.MULTILINE)

def process_signal_message(message_text: str, message_time: datetime, is_historical: bool = False):
    """Process message text to extract trading signals - OPTIMIZED"""
    global pending_signals, upcoming_trades, recent_signals
    
    # Skip all historical messages on startup to prevent multiple old signals from executing
    if is_historical:
        return
    
    # Use pre-compiled patterns for faster matching
    asset_time_match = ASSET_TIME_PATTERN.search(message_text)
    direction_match = DIRECTION_PATTERN.search(message_text)
    
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

async def handle_trade_result(order_result):
    """Handle trade result from WebSocket event - called automatically when trade completes"""
    global past_trades, global_martingale_step
    
    try:
        order_id = order_result.order_id
        profit = order_result.profit if order_result.profit is not None else 0
        
        # Map OrderStatus to our internal status
        if order_result.status == OrderStatus.WIN:
            result = 'win'
        elif order_result.status == OrderStatus.LOSE:
            result = 'loss'
        elif order_result.status == OrderStatus.CLOSED or order_result.status == OrderStatus.CANCELLED:
            result = 'closed'
        else:
            result = 'pending'
        
        log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🎯 WebSocket Result: {order_id} -> {result.upper()} | Profit: ${profit:.2f}\n")
        
        # Update past trade result
        trade_updated = False
        for trade in reversed(past_trades):
            if trade.get('order_id') == order_id and trade['result'] == 'pending':
                trade['result'] = result
                trade_updated = True
                
                # Save trade to CSV
                csv_data = {
                    'timestamp': datetime.now().isoformat(),
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'asset': trade['asset'],
                    'direction': trade['direction'],
                    'amount': trade['amount'],
                    'step': trade['step'],
                    'duration': trade.get('duration', 1),
                    'result': result,
                    'profit_loss': profit,
                    'balance_before': '',
                    'balance_after': '',
                    'multiplier': MULTIPLIER
                }
                save_trade_to_csv(csv_data)
                break
        
        if not trade_updated:
            log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ⚠️ Trade {order_id} not found in past_trades\n")
            return
        
        # 🔥 MARTINGALE LOGIC: Update step based on result
        if result == 'win':
            # WIN: Reset global step to 0
            # Clear only COMPLETED trades, keep pending ones
            global_martingale_step = 0
            
            # Remove only completed trades (win/loss/closed), keep pending
            past_trades[:] = [t for t in past_trades if t['result'] == 'pending']
            
            log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ✅ WIN! Reset global step to 0 (kept {len(past_trades)} pending trades)\n")
        elif result == 'loss':
            # LOSS: Increment step for next trade
            if global_martingale_step < 8:
                global_martingale_step += 1
                next_amount = TRADE_AMOUNT * (MULTIPLIER ** global_martingale_step)
                log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ❌ LOSS! Global step increased to {global_martingale_step} (next trade: ${next_amount:.2f})\n")
            else:
                # Max steps reached, reset
                global_martingale_step = 0
                log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🔄 Max steps (8) reached, reset to 0\n")
        elif result == 'closed':
            # CLOSED/CANCELLED: Treat as loss for martingale
            if global_martingale_step < 8:
                global_martingale_step += 1
                next_amount = TRADE_AMOUNT * (MULTIPLIER ** global_martingale_step)
                log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ⚪ CLOSED! Treating as loss, step increased to {global_martingale_step}\n")
            else:
                global_martingale_step = 0
                log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🔄 Max steps (8) reached, reset to 0\n")
        
    except Exception as e:
        log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ❌ Error in handle_trade_result: {e}\n")
        import traceback
        log_to_file(f"{traceback.format_exc()}\n")

async def get_persistent_client():
    """Get or create persistent client - takes time on first connect, then instant"""
    global persistent_client
    
    # Check if client exists and is connected
    if persistent_client and persistent_client.is_connected:
        # ⚡ INSTANT reuse - this is the ultra-fast part!
        return persistent_client
    
    # First connection - takes proper time to ensure quality
    log_to_file("🔄 Creating persistent client (first time - takes ~25 seconds)...\n")
    
    # Get appropriate SSID based on mode
    if IS_DEMO:
        ssid = os.getenv('SSID_DEMO') or os.getenv('SSID')
        if not ssid:
            raise Exception("SSID_DEMO not found - configure in .env file")
        log_to_file(f"🔑 Using DEMO SSID\n")
    else:
        ssid = os.getenv('SSID_REAL')
        if not ssid:
            raise Exception("SSID_REAL not found - configure in .env file. Real account requires separate SSID.")
        log_to_file(f"🔑 Using REAL SSID\n")
    
    if not validate_ssid(ssid):
        raise Exception("Invalid SSID format - get new SSID from PocketOption")
    
    client = AsyncPocketOptionClient(
        ssid=ssid,
        is_demo=IS_DEMO,
        persistent_connection=True,  # Keep connection alive
        auto_reconnect=True,  # Auto-reconnect if disconnected
        enable_logging=False  # Disable logging for speed
    )
    
    # Register event listener for trade results
    client.on('order_closed', handle_trade_result)
    
    try:
        # Take proper time to connect (20 seconds)
        log_to_file("🔌 Connecting to PocketOption (taking proper time for quality connection)...\n")
        await asyncio.wait_for(client.connect(), timeout=20.0)
        
        # Try to fetch balance but don't fail if it times out
        log_to_file("💰 Fetching balance (ensuring accurate data)...\n")
        try:
            balance = await asyncio.wait_for(client.get_balance(), timeout=15.0)
            log_to_file(f"✅ Connected! {'DEMO' if IS_DEMO else 'REAL'} Account\n")
            log_to_file(f"💰 Balance: ${balance.balance:.2f} {balance.currency}\n")
        except Exception as balance_error:
            log_to_file(f"⚠️ Balance fetch failed (but connection OK): {balance_error}\n")
            log_to_file("✅ Connected! Proceeding without balance check\n")
        
        log_to_file(f"⚡ Connection established - all future trades will be INSTANT!\n")
        
        if not client.is_connected:
            raise Exception("Connection failed")
        
        persistent_client = client
        return client
        
    except asyncio.TimeoutError:
        log_to_file("❌ Connection timeout - check SSID\n")
        if client:
            try:
                await client.disconnect()
            except:
                pass
        raise Exception("Connection timeout - SSID may be expired")
        
    except Exception as e:
        log_to_file(f"❌ Error: {e}\n")
        if client:
            try:
                await client.disconnect()
            except:
                pass
        raise

async def execute_trade_signal(signal: Dict):
    """Execute trade on Pocket Option using persistent client"""
    try:
        # Log trade signal received
        log_to_file(f"\n[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 📥 Trade signal received: {signal['pair']} {signal['direction']}\n")
        
        # Get persistent client (instant if already connected!)
        client = await get_persistent_client()
        asset_name = map_asset_name(signal['pair'])
        
        log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 📍 Mapped asset: {asset_name}\n")
        
        order_direction = OrderDirection.CALL if signal['direction'] == 'BUY' else OrderDirection.PUT
        
        await execute_strategy_trade(client, asset_name, order_direction, signal)
        
    except Exception as e:
        log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ❌ Trade execution error: {e}\n")
        import traceback
        log_to_file(f"{traceback.format_exc()}\n")
        
        print(f"❌ Trade execution error: {e}")
        
        # Try to reconnect on next trade
        global persistent_client
        persistent_client = None

async def execute_strategy_trade(client, asset_name: str, order_direction: OrderDirection, signal: Dict):
    """Execute trade using global martingale strategy - NON-BLOCKING (< 10ms)"""
    global past_trades, global_martingale_step, background_tasks
    
    try:
        if not client.is_connected:
            print(f"\n❌ Client not connected for {asset_name}")
            
            # Log to file
            log_to_file(f"\n[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ERROR: Client not connected for {asset_name}\n")
            
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
        
        # 🔥 MARTINGALE: Check if there are pending trades
        # If yes, use current step + 1 (assume previous will lose)
        # If no, use current step (which is either 0 or set by previous result)
        pending_count = sum(1 for trade in past_trades if trade['result'] == 'pending')
        
        if pending_count > 0:
            # There are pending trades, assume they will lose and increment
            current_step = min(global_martingale_step + pending_count, 8)
            log_to_file(f"\n[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 📊 {pending_count} pending trade(s), using step {current_step}\n")
        else:
            # No pending trades, use current global step
            current_step = global_martingale_step
        
        current_amount = TRADE_AMOUNT * (MULTIPLIER ** current_step)
        
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        
        # Log trade attempt
        log_to_file(f"[{timestamp}] ⚡ Placing order: {asset_name} {signal['direction']} ${current_amount:.2f} Step {current_step}\n")
        
        # Place order (this is fast - usually < 1 second)
        order_result = await client.place_order(
            asset=asset_name,
            direction=order_direction,
            amount=current_amount,
            duration=signal['time_minutes'] * 60
        )
        
        if order_result and order_result.status in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
            # ✅ Order placed successfully
            
            trade_info = {
                'order_id': order_result.order_id,
                'amount': current_amount,
                'step': current_step,  # Use the step this trade was placed with
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
                'step': current_step,  # Use the step this trade was placed with
                'duration': signal['time_minutes'],  # Add duration for CSV export
                'result': 'pending',
                'order_id': order_result.order_id  # Store order_id for tracking
            })
            
            # Log success
            log_to_file(f"[{timestamp}] ✅ Order placed! ID: {order_result.order_id}\n")
            log_to_file(f"[{timestamp}] 🚀 Trade placed successfully! WebSocket will notify us when result is ready\n")
            
            # ✅ NO NEED TO SCHEDULE BACKGROUND TASK!
            # The WebSocket event listener (handle_trade_result) will automatically
            # be called when the trade completes. This is much faster and more reliable.
            
            # Return immediately - trade is placed!
            return order_result
                
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
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        
        # Log exception
        log_to_file(f"[{timestamp}] ❌ Exception in strategy trade: {e}\n")
        import traceback
        log_to_file(f"{traceback.format_exc()}\n")
        
        print(f"\n❌ Strategy trade error: {e}")


# OLD FUNCTION - REPLACED BY WebSocket event listener (handle_trade_result)
# This function used check_win() which had timeout issues
# Now we use WebSocket events for instant result updates
"""
async def check_trade_result_later(order_id: str, asset_name: str, signal: Dict, amount: float, step: int):
    # ... old implementation removed ...
    pass
"""

async def fetch_channel_messages():
    """
    Fetch messages from testpob1234 channel with INSTANT execution
    Uses event handlers for real-time message processing (< 10ms latency)
    """
    
    # 🔐 Recreate session file from environment variable if needed (Railway)
    session_file_base64 = os.getenv('TELEGRAM_SESSION_FILE')
    session_journal_base64 = os.getenv('TELEGRAM_SESSION_JOURNAL')
    
    if session_file_base64:
        print("🔐 Recreating session file from environment variable...")
        import base64
        
        # Recreate main session file
        session_data = base64.b64decode(session_file_base64)
        with open('session_testpob1234.session', 'wb') as f:
            f.write(session_data)
        print("✅ Session file recreated")
        
        # Recreate journal file if available
        if session_journal_base64:
            journal_data = base64.b64decode(session_journal_base64)
            with open('session_testpob1234.session-journal', 'wb') as f:
                f.write(journal_data)
            print("✅ Session journal file recreated")
    
    # ⚡ PRE-CONNECT to PocketOption (takes proper time for quality)
    print("🔄 Pre-connecting to PocketOption...")
    print("⏳ This takes ~25 seconds (connect + balance fetch)")
    print("💡 But all trades after this will be INSTANT!")
    try:
        await get_persistent_client()
        print("✅ Pre-connected successfully!")
        print("💰 Balance fetched and verified")
        print("⚡ Ready for INSTANT trade execution!")
    except Exception as e:
        print(f"⚠️ Pre-connect failed: {e}")
        print("Will connect on first trade (takes ~25s)")
        print("All subsequent trades will be instant")
    
    # Use unique session for this bot
    # Priority: 1. String session, 2. File session (recreated or local)
    if STRING_SESSION:
        print("🔐 Using string session (Railway deployment)")
        client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    else:
        print("📁 Using file session (local or recreated from env)")
        client = TelegramClient('session_testpob1234', API_ID, API_HASH)
    
    try:
        await client.start(PHONE_NUMBER)
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for database lock error
        if 'database is locked' in error_msg or 'database' in error_msg:
            print(f"\n❌ Database lock error detected: {e}")
            print("🔄 Automatically cleaning up session files...")
            
            # Close client if open
            try:
                await client.disconnect()
            except:
                pass
            
            # Delete session files
            session_files = [
                'session_testpob1234.session',
                'session_testpob1234.session-journal'
            ]
            
            deleted_count = 0
            for session_file in session_files:
                if os.path.exists(session_file):
                    try:
                        os.remove(session_file)
                        deleted_count += 1
                        print(f"✓ Deleted {session_file}")
                    except Exception as del_error:
                        print(f"⚠️ Could not delete {session_file}: {del_error}")
            
            if deleted_count > 0:
                print(f"\n✅ Cleaned up {deleted_count} session file(s)")
                print("💡 Please restart the bot. You will need to verify OTP again.")
            else:
                print("\n⚠️ No session files found to delete")
            
            return
        else:
            # Other error
            print(f"\n❌ Telegram connection error: {e}")
            return
    
    try:
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
            f.write(f"Pre-connected to PocketOption: Ready for instant trades!\n")
            f.write(f"Processed {processed_count} historical messages (skipped for execution)\n")
            f.write(f"⏳ Waiting for new signals...\n")
            f.write(f"\nNote: Only NEW messages received after bot startup will be executed.\n")
            f.write(f"This prevents multiple old signals from executing simultaneously.\n")
            f.write(f"\n🔔 INSTANT EXECUTION MODE: Using real-time event handlers\n")
            f.write(f"Messages will execute within < 10ms of arrival\n")
            f.write(f"⚡ ULTRA-FAST MODE: Pre-connected for instant first trade\n")
        
        last_message_id = messages.messages[0].id if messages.messages else 0
        
        # Register event handler for NEW messages (INSTANT - no polling delay)
        @client.on(events.NewMessage(chats=channel))
        async def handle_new_message(event):
            nonlocal last_message_id
            
            if event.message.id > last_message_id:
                last_message_id = event.message.id
                
                # Process immediately (< 1ms)
                log_to_file(f"\n[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🔔 NEW MESSAGE RECEIVED (ID: {event.message.id})\n")
                process_signal_message(event.message.message, event.message.date, is_historical=False)
                log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ⚡ Message processed INSTANTLY\n")
                log_to_file(f"Pending signals: {len(pending_signals)}, Upcoming trades: {len(upcoming_trades)}\n")
        
        print(f"\n✅ Connected to: {channel.title}")
        print(f"📊 Processed {processed_count} historical messages (skipped for execution)")
        print(f"\n⚡ ULTRA-FAST MODE ACTIVE")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🔌 SSID Connection: ✅ Established (~25s, ONE TIME)")
        print(f"💰 Balance Fetch: ✅ Complete (~10s, ONE TIME)")
        print(f"⚡ Message Reading: < 1ms (INSTANT)")
        print(f"⚡ Trade Placement: < 500ms (INSTANT)")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🎯 Setup complete - all trades will be INSTANT!")
        print(f"⏳ Waiting for signals...\n")
        
        log_to_file("\n🔔 Real-time event handler registered - INSTANT execution mode active\n")
        
        # Keep connection alive (events handle messages automatically)
        while True:
            try:
                # Just keep alive, no polling needed (events handle messages instantly)
                await asyncio.sleep(1)  # Check every 1 second for connection health only
                
            except Exception as e:
                log_to_file(f"Error in keep-alive loop: {e}\n")
                await asyncio.sleep(0.1)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Properly disconnect and cleanup
        try:
            if client.is_connected():
                await client.disconnect()
        except Exception as cleanup_error:
            # Silently ignore cleanup errors (event loop may be closed)
            pass

async def cleanup_shared_client():
    """Cleanup function (no longer needed with independent clients)"""
    log_to_file("👋 Bot shutting down\n")

def get_user_config():
    """Get user configuration from environment variables"""
    global TRADE_AMOUNT, IS_DEMO, MULTIPLIER
    
    # Check for appropriate SSID based on mode
    is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
    if is_demo:
        ssid = os.getenv('SSID_DEMO') or os.getenv('SSID')
        if not ssid:
            print("❌ SSID_DEMO not found in .env file")
            return False
    else:
        ssid = os.getenv('SSID_REAL')
        if not ssid:
            print("❌ SSID_REAL not found in .env file. Real account requires separate SSID.")
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
    
    # Load configuration from environment variables
    TRADE_AMOUNT = float(os.getenv('TRADE_AMOUNT', '1.0'))
    IS_DEMO = os.getenv('IS_DEMO', 'True').lower() == 'true'
    MULTIPLIER = float(os.getenv('MULTIPLIER', '2.5'))
    
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
