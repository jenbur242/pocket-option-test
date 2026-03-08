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
STRING_SESSION = os.getenv('TELEGRAM_STRING_SESSION')

# Channel username
CHANNEL_USERNAME = os.getenv('TELEGRAM_CHANNEL', 'testpob1234')

# Trading configuration
TRADE_AMOUNT = float(os.getenv('TRADE_AMOUNT', '1.0'))
IS_DEMO = os.getenv('IS_DEMO', 'True').lower() == 'true'
MULTIPLIER = float(os.getenv('MULTIPLIER', '2.5'))

# Global martingale step
global_martingale_step = 0

# Track trades
past_trades = []

# Persistent client
persistent_client = None

# CSV folder
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
        
        file_exists = os.path.exists(csv_file)
        
        headers = [
            'timestamp', 'date', 'time', 'asset', 'direction', 
            'amount', 'step', 'duration', 'result', 'profit_loss',
            'balance_before', 'balance_after', 'multiplier'
        ]
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(trade_data)
        
        print(f"✅ Trade saved to CSV: {csv_file}")
        
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")

def log_message(message: str):
    """Log message to console and file"""
    print(message)
    try:
        with open('telegram/trading_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")
    except:
        pass

def map_asset_name(pair: str) -> str:
    """Map asset pair to Pocket Option format"""
    clean_pair = pair.replace(' ', '').replace('/', '').upper()
    
    if 'OTC' in pair.upper():
        if clean_pair.endswith('OTC'):
            base_name = clean_pair[:-3]
            return f"{base_name}_otc"
        else:
            return f"{clean_pair}_otc"
    else:
        return clean_pair

async def get_persistent_client():
    """Get or create persistent client"""
    global persistent_client
    
    if persistent_client and persistent_client.is_connected:
        return persistent_client
    
    # Get SSID
    if IS_DEMO:
        ssid = os.getenv('SSID_DEMO') or os.getenv('SSID')
        if not ssid:
            raise Exception("SSID_DEMO not found in .env file")
    else:
        ssid = os.getenv('SSID_REAL')
        if not ssid:
            raise Exception("SSID_REAL not found in .env file")
    
    log_message("🔌 Connecting to PocketOption...")
    
    client = AsyncPocketOptionClient(
        ssid=ssid,
        is_demo=IS_DEMO,
        persistent_connection=False,
        auto_reconnect=True,
        enable_logging=True
    )
    
    connected = await asyncio.wait_for(client.connect(), timeout=30.0)
    
    if not connected:
        raise Exception("Connection failed")
    
    await asyncio.sleep(1)
    
    try:
        balance = await asyncio.wait_for(client.get_balance(), timeout=10.0)
        log_message(f"💰 Balance: ${balance.balance:.2f} {balance.currency}")
    except Exception as e:
        log_message(f"⚠️ Balance fetch failed: {e}")
    
    log_message("✅ Connected to PocketOption!")
    
    persistent_client = client
    return client

async def check_trade_result(order_id: str, duration_minutes: int):
    """Check trade result after completion"""
    global past_trades, global_martingale_step
    
    try:
        client = await get_persistent_client()
        
        wait_time = duration_minutes * 60 + 30
        
        log_message(f"⏳ Waiting for trade {order_id} result (max {wait_time}s)...")
        
        win_result = await client.check_win(
            order_id=order_id,
            max_wait_time=wait_time
        )
        
        if win_result and win_result.get("completed"):
            result_type = win_result.get("result", "unknown")
            profit = win_result.get("profit", 0)
            
            log_message(f"✅ Result: {result_type.upper()} | Profit: ${profit:.2f}")
            
            # Update past_trades
            for trade in reversed(past_trades):
                if trade.get('order_id') == order_id:
                    trade['result'] = result_type
                    
                    # Save to CSV
                    csv_data = {
                        'timestamp': datetime.now().isoformat(),
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'asset': trade['asset'],
                        'direction': trade['direction'],
                        'amount': trade['amount'],
                        'step': trade['step'],
                        'duration': trade.get('duration', 1),
                        'result': result_type,
                        'profit_loss': profit,
                        'balance_before': '',
                        'balance_after': '',
                        'multiplier': MULTIPLIER
                    }
                    save_trade_to_csv(csv_data)
                    break
            
            # Update martingale step
            if result_type == 'win':
                global_martingale_step = 0
                past_trades[:] = [t for t in past_trades if t['result'] == 'pending']
                log_message(f"🎉 WIN! Reset martingale step to 0")
                log_message(f"💡 Ready for new asset signal")
            elif result_type == 'draw':
                past_trades[:] = [t for t in past_trades if t.get('order_id') != order_id]
                log_message(f"🔄 DRAW! No change to step {global_martingale_step}")
                log_message(f"💡 Same asset kept: {last_signal['asset']}")
            elif result_type == 'loss':
                if global_martingale_step < 8:
                    global_martingale_step += 1
                    log_message(f"❌ LOSS! Martingale step increased to {global_martingale_step}")
                    log_message(f"💡 Same asset kept: {last_signal['asset']} - waiting for next direction")
                else:
                    global_martingale_step = 0
                    log_message(f"🔄 Max steps reached, reset to 0")
                    log_message(f"💡 Same asset kept: {last_signal['asset']}")
        else:
            log_message(f"⚠️ Result timeout for order {order_id}")
            
    except Exception as e:
        log_message(f"❌ Error checking result: {e}")

async def place_trade(asset: str, direction: str, duration: int):
    """Place trade immediately - SIMPLE AND DIRECT"""
    global past_trades, global_martingale_step
    
    duration_minutes = duration  # Rename for clarity
    
    try:
        # Check if there are pending trades
        pending_count = sum(1 for trade in past_trades if trade['result'] == 'pending')
        
        if pending_count > 0:
            log_message(f"⏸️ Skipping trade - {pending_count} pending trade(s)")
            return
        
        # Get client
        client = await get_persistent_client()
        
        # Map asset name
        asset_name = map_asset_name(asset)
        
        # Calculate amount with martingale
        current_step = global_martingale_step
        current_amount = TRADE_AMOUNT * (MULTIPLIER ** current_step)
        
        # Determine direction
        order_direction = OrderDirection.CALL if direction.upper() == 'BUY' else OrderDirection.PUT
        
        log_message(f"\n{'='*60}")
        log_message(f"📊 PLACING TRADE")
        log_message(f"{'='*60}")
        log_message(f"Asset: {asset_name}")
        log_message(f"Direction: {direction.upper()}")
        log_message(f"Amount: ${current_amount:.2f}")
        log_message(f"Duration: {duration_minutes} min")
        log_message(f"Martingale Step: {current_step}")
        log_message(f"{'='*60}")
        
        # Place order - EXACT SAME AS test_trade.py
        order_result = await client.place_order(
            asset=asset_name,
            amount=current_amount,
            direction=order_direction,
            duration=duration_minutes * 60
        )
        
        if order_result and order_result.status in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
            log_message(f"✅ Order placed successfully!")
            log_message(f"   Order ID: {order_result.order_id}")
            log_message(f"   Status: {order_result.status.value}")
            log_message(f"   Placed at: {order_result.placed_at.strftime('%H:%M:%S')}")
            log_message(f"   Expires at: {order_result.expires_at.strftime('%H:%M:%S')}")
            
            # Add to past trades
            past_trades.append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'asset': asset_name,
                'direction': direction.upper(),
                'amount': current_amount,
                'step': current_step,
                'duration': duration_minutes,
                'result': 'pending',
                'order_id': order_result.order_id
            })
            
            # Check result in background
            asyncio.create_task(check_trade_result(order_result.order_id, duration_minutes))
            
        else:
            error_msg = order_result.error_message if order_result and order_result.error_message else 'Unknown error'
            log_message(f"❌ Trade failed: {error_msg}")
            
    except Exception as e:
        log_message(f"❌ Error placing trade: {e}")
        import traceback
        traceback.print_exc()

def parse_signal(message_text: str) -> Dict:
    """Parse signal from Telegram message - SIMPLE REGEX"""
    signal = {'asset': None, 'direction': None, 'duration': None}
    
    # Pattern: 📈 Pair: AUD/USD OTC
    asset_match = re.search(r'📈\s*Pair:\s*([A-Z]+/[A-Z]+(?:\s+OTC)?)', message_text, re.IGNORECASE)
    if asset_match:
        signal['asset'] = asset_match.group(1).strip()
    
    # Pattern: ⌛️ time: 1 min
    time_match = re.search(r'⌛[️]?\s*time:\s*(\d+)\s*min', message_text, re.IGNORECASE)
    if time_match:
        signal['duration'] = int(time_match.group(1))
    
    # Pattern: Buy or Sell
    direction_match = re.search(r'^(Buy|Sell)\s*$', message_text, re.IGNORECASE | re.MULTILINE)
    if direction_match:
        signal['direction'] = direction_match.group(1).upper()
    
    return signal

# Store last signal for direction matching - KEEP ASSET UNTIL WIN
last_signal = {'asset': None, 'duration': None}

async def process_message(message_text: str):
    """Process Telegram message and place trade if complete signal"""
    global last_signal
    
    signal = parse_signal(message_text)
    
    # If we got asset and duration, store it (update the asset)
    if signal['asset'] and signal['duration']:
        last_signal['asset'] = signal['asset']
        last_signal['duration'] = signal['duration']
        log_message(f"📥 Signal received: {signal['asset']} - {signal['duration']} min")
    
    # If we got direction and have stored asset/duration, place trade
    if signal['direction'] and last_signal['asset'] and last_signal['duration']:
        log_message(f"🎯 Direction received: {signal['direction']}")
        
        # Place trade immediately
        await place_trade(
            asset=last_signal['asset'],
            direction=signal['direction'],
            duration=last_signal['duration']
        )
        
        # DON'T clear last signal - keep it for martingale on same asset
        # It will only be replaced when a new asset signal comes

async def main():
    """Main function - Listen to Telegram and place trades"""
    
    # Pre-connect to PocketOption
    log_message("\n" + "="*60)
    log_message("🤖 POCKET OPTION TRADING BOT")
    log_message("="*60)
    log_message(f"Channel: {CHANNEL_USERNAME}")
    log_message(f"Account: {'DEMO' if IS_DEMO else 'REAL'}")
    log_message(f"Initial Amount: ${TRADE_AMOUNT}")
    log_message(f"Multiplier: {MULTIPLIER}x")
    log_message("="*60)
    
    try:
        await get_persistent_client()
    except Exception as e:
        log_message(f"❌ Failed to connect to PocketOption: {e}")
        return
    
    # Connect to Telegram
    if STRING_SESSION:
        log_message("🔐 Using string session")
        client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    else:
        log_message("📁 Using file session")
        client = TelegramClient('session_testpob1234', API_ID, API_HASH)
    
    try:
        await client.start(PHONE_NUMBER)
    except Exception as e:
        log_message(f"❌ Telegram connection error: {e}")
        return
    
    try:
        channel = await client.get_entity(CHANNEL_USERNAME)
        log_message(f"✅ Connected to: {channel.title}")
    except Exception as e:
        log_message(f"❌ Error finding channel: {e}")
        return
    
    # Get recent messages (don't execute, just for context)
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
    
    log_message(f"📊 Found {len(messages.messages)} recent messages")
    
    last_message_id = messages.messages[0].id if messages.messages else 0
    
    # Listen for NEW messages
    @client.on(events.NewMessage(chats=channel))
    async def handle_new_message(event):
        nonlocal last_message_id
        
        if event.message.id > last_message_id:
            last_message_id = event.message.id
            
            log_message(f"\n🔔 NEW MESSAGE: {event.message.message[:100]}")
            
            # Process message and place trade if signal is complete
            await process_message(event.message.message)
    
    log_message("\n⏳ Waiting for signals...\n")
    
    # Keep alive
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
