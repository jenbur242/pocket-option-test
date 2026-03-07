#!/usr/bin/env python3
"""
Flask API Server for Pocket Option Trading Bot
Provides endpoints for frontend to manage SSID, start trading, and view results
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import asyncio
import threading
from datetime import datetime
from dotenv import load_dotenv, set_key
from typing import Dict, List
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import trading modules
from telegram.main import (
    fetch_channel_messages,
    past_trades,
    upcoming_trades,
    global_martingale_step,
    TRADE_AMOUNT,
    IS_DEMO,
    MULTIPLIER,
    update_trading_config
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Global state
trading_active = False
trading_thread = None
trade_results = []  # Store all trade results
temp_phone_code_hash = None  # Temporary storage for OTP verification
active_client = None  # Store active PocketOption client
client_balance = {'demo': 0, 'real': 0}  # Cache balance

@app.route('/', methods=['GET'])
def index():
    """Serve the frontend HTML"""
    try:
        return send_file('frontend.html')
    except Exception as e:
        return jsonify({
            'error': 'Frontend file not found',
            'message': str(e),
            'api_info': {
                'message': 'Pocket Option Trading API',
                'version': '1.0.0',
                'endpoints': {
                    'health': 'GET /api/health',
                    'ssid': 'POST /api/ssid',
                    'telegram': 'POST /api/telegram/otp',
                    'start_trading': 'POST /api/trading/start',
                    'stop_trading': 'POST /api/trading/stop',
                    'status': 'GET /api/trading/status',
                    'results': 'GET /api/trades/results',
                    'upcoming': 'GET /api/trades/upcoming',
                    'analysis': 'GET /api/trades/analysis'
                }
            }
        }), 404

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """
    Get current configuration from .env file
    Returns SSID status and Telegram config (without sensitive values)
    """
    try:
        ssid = os.getenv('SSID')
        telegram_api_id = os.getenv('TELEGRAM_API_ID')
        telegram_api_hash = os.getenv('TELEGRAM_API_HASH')
        telegram_phone = os.getenv('TELEGRAM_PHONE')
        telegram_channel = os.getenv('TELEGRAM_CHANNEL', 'testpob1234')
        
        # Mask SSID for display (show first 20 and last 10 characters)
        masked_ssid = None
        if ssid and len(ssid) > 30:
            masked_ssid = ssid[:20] + '...' + ssid[-10:]
        elif ssid:
            masked_ssid = ssid[:10] + '...'
        
        return jsonify({
            'ssid_configured': bool(ssid),
            'ssid_preview': masked_ssid,
            'telegram_configured': bool(telegram_api_id and telegram_api_hash and telegram_phone),
            'telegram': {
                'api_id': telegram_api_id if telegram_api_id else None,
                'api_hash': '***' + telegram_api_hash[-4:] if telegram_api_hash and len(telegram_api_hash) > 4 else None,
                'phone': telegram_phone if telegram_phone else None,
                'channel': telegram_channel
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ssid', methods=['POST'])
def set_ssid():
    """
    Set SSID for trading
    Body: { "ssid": "42[\"auth\",{...}]" }
    """
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        
        if not ssid:
            return jsonify({'error': 'SSID is required'}), 400
        
        # Basic validation
        if not ssid.startswith('42["auth"'):
            return jsonify({'error': 'Invalid SSID format'}), 400
        
        # Save to .env file
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        set_key(env_path, 'SSID', ssid)
        
        # Reload environment
        load_dotenv(override=True)
        
        return jsonify({
            'success': True,
            'message': 'SSID saved successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/telegram/check-session', methods=['GET'])
def check_telegram_session():
    """
    Check if Telegram session exists
    """
    try:
        # Check if session file exists
        session_file = 'session_testpob1234.session'
        session_exists = os.path.exists(session_file)
        
        # Check if credentials are configured
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        credentials_configured = bool(api_id and api_hash and phone)
        
        return jsonify({
            'session_exists': session_exists,
            'credentials_configured': credentials_configured,
            'needs_otp': credentials_configured and not session_exists,
            'phone': phone if phone else None
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/telegram/send-code', methods=['POST'])
def send_telegram_code():
    """
    Send OTP code to phone number
    """
    try:
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        if not all([api_id, api_hash, phone]):
            return jsonify({'error': 'Telegram credentials not configured in .env'}), 400
        
        # Import Telethon
        from telethon.sync import TelegramClient
        
        # Create client and send code
        client = TelegramClient('session_testpob1234', api_id, api_hash)
        
        async def send_code():
            await client.connect()
            if not await client.is_user_authorized():
                result = await client.send_code_request(phone)
                await client.disconnect()
                return result.phone_code_hash
            else:
                await client.disconnect()
                return None
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        phone_code_hash = loop.run_until_complete(send_code())
        loop.close()
        
        if phone_code_hash:
            # Store phone_code_hash temporarily (in production, use Redis or database)
            global temp_phone_code_hash
            temp_phone_code_hash = phone_code_hash
            
            return jsonify({
                'success': True,
                'message': f'OTP code sent to {phone}',
                'phone': phone
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Already authorized',
                'session_exists': True
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/telegram/verify-otp', methods=['POST'])
def verify_telegram_otp():
    """
    Verify OTP code and create session
    Body: { "code": "12345" }
    """
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'error': 'OTP code is required'}), 400
        
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        if not all([api_id, api_hash, phone]):
            return jsonify({'error': 'Telegram credentials not configured'}), 400
        
        # Get stored phone_code_hash
        global temp_phone_code_hash
        if not temp_phone_code_hash:
            return jsonify({'error': 'Please request OTP code first'}), 400
        
        # Import Telethon
        from telethon.sync import TelegramClient
        
        # Create client and verify code
        client = TelegramClient('session_testpob1234', api_id, api_hash)
        
        async def verify_code():
            await client.connect()
            try:
                await client.sign_in(phone, code, phone_code_hash=temp_phone_code_hash)
                await client.disconnect()
                return True
            except Exception as e:
                await client.disconnect()
                raise e
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(verify_code())
        loop.close()
        
        # Clear temp hash
        temp_phone_code_hash = None
        
        return jsonify({
            'success': True,
            'message': 'Telegram session created successfully!',
            'session_exists': True
        })
    
    except Exception as e:
        return jsonify({'error': f'OTP verification failed: {str(e)}'}), 500

@app.route('/api/telegram/otp', methods=['POST'])
def send_otp():
    """
    Handle Telegram OTP if needed
    Body: { "phone": "+1234567890", "api_id": "...", "api_hash": "..." }
    """
    try:
        data = request.get_json()
        phone = data.get('phone')
        api_id = data.get('api_id')
        api_hash = data.get('api_hash')
        
        if not all([phone, api_id, api_hash]):
            return jsonify({'error': 'Phone, API ID, and API Hash are required'}), 400
        
        # Save to .env
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        set_key(env_path, 'TELEGRAM_PHONE', phone)
        set_key(env_path, 'TELEGRAM_API_ID', api_id)
        set_key(env_path, 'TELEGRAM_API_HASH', api_hash)
        
        load_dotenv(override=True)
        
        return jsonify({
            'success': True,
            'message': 'Telegram credentials saved. OTP will be sent when trading starts.'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/csv/list', methods=['GET'])
def list_csv_files():
    """
    List all CSV files in trade_results folder
    """
    try:
        csv_folder = 'trade_results'
        if not os.path.exists(csv_folder):
            return jsonify({'files': []})
        
        files = []
        for filename in os.listdir(csv_folder):
            if filename.endswith('.csv'):
                filepath = os.path.join(csv_folder, filename)
                file_stats = os.stat(filepath)
                
                files.append({
                    'filename': filename,
                    'date': filename.replace('trades_', '').replace('.csv', ''),
                    'size': file_stats.st_size,
                    'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    'path': filepath
                })
        
        # Sort by date descending
        files.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({'files': files, 'total': len(files)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/csv/read/<filename>', methods=['GET'])
def read_csv_file(filename):
    """
    Read specific CSV file and return data
    """
    try:
        import csv
        
        csv_folder = 'trade_results'
        filepath = os.path.join(csv_folder, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        trades = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append(row)
        
        # Calculate statistics
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.get('result') == 'win')
        losses = sum(1 for t in trades if t.get('result') == 'loss')
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        total_profit = sum(float(t.get('profit_loss', 0)) for t in trades if t.get('profit_loss'))
        
        return jsonify({
            'filename': filename,
            'trades': trades,
            'statistics': {
                'total_trades': total_trades,
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 2),
                'total_profit': round(total_profit, 2)
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/csv/download/<filename>', methods=['GET'])
def download_csv_file(filename):
    """
    Download CSV file
    """
    try:
        csv_folder = 'trade_results'
        filepath = os.path.join(csv_folder, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/telegram', methods=['GET'])
def test_telegram_connection():
    """
    Test Telegram connection and channel access
    """
    try:
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        channel = os.getenv('TELEGRAM_CHANNEL', 'testpob1234')
        
        if not all([api_id, api_hash, phone]):
            return jsonify({'error': 'Telegram credentials not configured'}), 400
        
        from telethon.sync import TelegramClient
        
        async def test_connection():
            client = TelegramClient('session_testpob1234', api_id, api_hash)
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.disconnect()
                return {'error': 'Not authorized. Please complete OTP verification first.'}
            
            try:
                # Get channel entity
                channel_entity = await client.get_entity(channel)
                
                # Get recent messages
                messages = await client.get_messages(channel_entity, limit=5)
                
                message_list = []
                for msg in messages:
                    if msg.message:
                        message_list.append({
                            'id': msg.id,
                            'date': msg.date.isoformat(),
                            'text': msg.message[:100] + '...' if len(msg.message) > 100 else msg.message
                        })
                
                await client.disconnect()
                
                return {
                    'success': True,
                    'channel': channel_entity.title,
                    'channel_id': channel_entity.id,
                    'recent_messages': message_list,
                    'message': f'Successfully connected to {channel_entity.title}'
                }
                
            except Exception as e:
                await client.disconnect()
                return {'error': f'Failed to access channel: {str(e)}'}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_connection())
        loop.close()
        
        if 'error' in result:
            return jsonify(result), 400
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/start', methods=['POST'])
def start_trading():
    """
    Start trading bot
    Body: { 
        "initial_amount": 1.0, 
        "is_demo": true, 
        "multiplier": 2.5,
        "martingale_step": 0
    }
    """
    global trading_active, trading_thread
    
    try:
        if trading_active:
            return jsonify({'error': 'Trading is already active'}), 400
        
        data = request.get_json()
        
        # Update trading config
        initial_amount = data.get('initial_amount', 1.0)
        is_demo = data.get('is_demo', True)
        multiplier = data.get('multiplier', 2.5)
        martingale_step = data.get('martingale_step', 0)
        
        # Validate inputs
        if initial_amount <= 0:
            return jsonify({'error': 'Initial amount must be greater than 0'}), 400
        
        if multiplier < 1.1:
            return jsonify({'error': 'Multiplier must be at least 1.1'}), 400
        
        if martingale_step < 0 or martingale_step > 10:
            return jsonify({'error': 'Martingale step must be between 0 and 10'}), 400
        
        # Validate SSID exists
        ssid = os.getenv('SSID')
        if not ssid:
            return jsonify({'error': 'SSID not configured. Please set SSID first.'}), 400
        
        # Validate Telegram credentials
        if not all([os.getenv('TELEGRAM_API_ID'), os.getenv('TELEGRAM_API_HASH'), os.getenv('TELEGRAM_PHONE')]):
            return jsonify({'error': 'Telegram credentials not configured'}), 400
        
        # Save config to environment for trading bot to use
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        set_key(env_path, 'TRADE_AMOUNT', str(initial_amount))
        set_key(env_path, 'IS_DEMO', str(is_demo))
        set_key(env_path, 'MULTIPLIER', str(multiplier))
        set_key(env_path, 'MARTINGALE_STEP', str(martingale_step))
        
        # Reload environment
        load_dotenv(override=True)
        
        # Start trading in background thread
        trading_active = True
        trading_thread = threading.Thread(
            target=run_trading_bot, 
            args=(initial_amount, is_demo, multiplier, martingale_step),
            daemon=True
        )
        trading_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Trading started successfully',
            'config': {
                'initial_amount': initial_amount,
                'is_demo': is_demo,
                'multiplier': multiplier,
                'martingale_step': martingale_step,
                'current_trade_amount': initial_amount * (multiplier ** martingale_step)
            }
        })
    
    except Exception as e:
        trading_active = False
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    """Stop trading bot"""
    global trading_active
    
    try:
        if not trading_active:
            return jsonify({'error': 'Trading is not active'}), 400
        
        trading_active = False
        
        return jsonify({
            'success': True,
            'message': 'Trading stopped successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/status', methods=['GET'])
def get_trading_status():
    """Get current trading status"""
    try:
        return jsonify({
            'active': trading_active,
            'config': {
                'trade_amount': TRADE_AMOUNT,
                'is_demo': IS_DEMO,
                'multiplier': MULTIPLIER,
                'global_step': global_martingale_step
            },
            'upcoming_trades': len(upcoming_trades),
            'past_trades': len(past_trades)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/results', methods=['GET'])
def get_trade_results():
    """
    Get trade results with pagination
    Query params: ?limit=50&offset=0
    """
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Get trades from past_trades
        total = len(past_trades)
        trades = past_trades[offset:offset + limit]
        
        return jsonify({
            'total': total,
            'limit': limit,
            'offset': offset,
            'trades': trades
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/upcoming', methods=['GET'])
def get_upcoming_trades():
    """Get upcoming scheduled trades"""
    try:
        trades_data = []
        for trade in upcoming_trades:
            signal = trade['signal']
            execution_time = trade['execution_time']
            
            trades_data.append({
                'asset': signal['pair'],
                'direction': signal['direction'],
                'duration': signal['time_minutes'],
                'execution_time': execution_time.isoformat(),
                'amount': TRADE_AMOUNT * (MULTIPLIER ** global_martingale_step)
            })
        
        return jsonify({
            'total': len(trades_data),
            'trades': trades_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/analysis', methods=['GET'])
def get_trade_analysis():
    """Get trade analysis and statistics"""
    try:
        if not past_trades:
            return jsonify({
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_profit': 0,
                'current_step': global_martingale_step
            })
        
        wins = sum(1 for t in past_trades if t.get('result') == 'win')
        losses = sum(1 for t in past_trades if t.get('result') == 'loss')
        total = len(past_trades)
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # Calculate profit (simplified)
        total_profit = 0
        for trade in past_trades:
            if trade.get('result') == 'win':
                total_profit += trade.get('amount', 0) * 0.8  # Assuming 80% payout
            elif trade.get('result') == 'loss':
                total_profit -= trade.get('amount', 0)
        
        return jsonify({
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate, 2),
            'total_profit': round(total_profit, 2),
            'current_step': global_martingale_step
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/balance', methods=['GET'])
def get_balance():
    """Get current account balance from PocketOption"""
    try:
        global client_balance
        
        # Check if SSID is configured
        ssid = os.getenv('SSID')
        if not ssid:
            return jsonify({
                'demo_balance': 0,
                'real_balance': 0,
                'currency': 'USD',
                'error': 'SSID not configured. Please configure SSID in Configuration section first.'
            }), 400
        
        print("🔄 Fetching balance from PocketOption...")
        
        # Import client
        from pocketoptionapi_async import AsyncPocketOptionClient
        
        async def fetch_both_balances():
            results = {'demo': 0, 'real': 0, 'currency': 'USD'}
            
            # Fetch Demo Balance
            try:
                print("📊 Connecting to Demo account...")
                demo_client = AsyncPocketOptionClient(ssid=ssid, is_demo=True)
                await asyncio.wait_for(demo_client.connect(), timeout=15.0)
                demo_balance = await asyncio.wait_for(demo_client.get_balance(), timeout=10.0)
                results['demo'] = demo_balance.balance
                results['currency'] = demo_balance.currency
                print(f"✅ Demo Balance: ${demo_balance.balance:.2f}")
                await demo_client.disconnect()
            except asyncio.TimeoutError:
                print("⏱️ Demo balance fetch timeout")
            except Exception as e:
                print(f"❌ Error fetching demo balance: {e}")
            
            # Fetch Real Balance
            try:
                print("💰 Connecting to Real account...")
                real_client = AsyncPocketOptionClient(ssid=ssid, is_demo=False)
                await asyncio.wait_for(real_client.connect(), timeout=15.0)
                real_balance = await asyncio.wait_for(real_client.get_balance(), timeout=10.0)
                results['real'] = real_balance.balance
                print(f"✅ Real Balance: ${real_balance.balance:.2f}")
                await real_client.disconnect()
            except asyncio.TimeoutError:
                print("⏱️ Real balance fetch timeout")
            except Exception as e:
                print(f"❌ Error fetching real balance: {e}")
            
            return results
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(fetch_both_balances())
        loop.close()
        
        # Update cache
        client_balance['demo'] = result['demo']
        client_balance['real'] = result['real']
        
        print(f"💾 Balance cached - Demo: ${result['demo']:.2f}, Real: ${result['real']:.2f}")
        
        return jsonify({
            'demo_balance': result['demo'],
            'real_balance': result['real'],
            'currency': result['currency'],
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"❌ Balance fetch error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'demo_balance': client_balance.get('demo', 0),
            'real_balance': client_balance.get('real', 0),
            'currency': 'USD',
            'error': str(e),
            'cached': True
        }), 500

def run_trading_bot(initial_amount, is_demo, multiplier, martingale_step):
    """Run trading bot in background with custom configuration"""
    global trading_active
    
    try:
        # Update trading configuration in telegram.main module
        import telegram.main as trading_module
        trading_module.update_trading_config(
            initial_amount=initial_amount,
            is_demo=is_demo,
            multiplier=multiplier,
            martingale_step=martingale_step
        )
        
        print(f"🚀 Starting trading bot with config:")
        print(f"   Initial Amount: ${initial_amount}")
        print(f"   Account Type: {'DEMO' if is_demo else 'REAL'}")
        print(f"   Multiplier: {multiplier}x")
        print(f"   Starting Martingale Step: {martingale_step}")
        print(f"   Current Trade Amount: ${initial_amount * (multiplier ** martingale_step):.2f}")
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run trading bot
        loop.run_until_complete(fetch_channel_messages())
    
    except Exception as e:
        print(f"Trading bot error: {e}")
        import traceback
        traceback.print_exc()
        trading_active = False
    
    finally:
        loop.close()

if __name__ == '__main__':
    # Get port from environment variable (Railway) or default to 5000
    port = int(os.getenv('PORT', 5000))
    
    print("=" * 60)
    print("🚀 Pocket Option Trading API Server")
    print("=" * 60)
    print(f"📡 Server starting on port {port}")
    print(f"🌐 Frontend available at http://localhost:{port}")
    print("=" * 60)
    print("📚 API Endpoints:")
    print("   POST /api/ssid - Set SSID")
    print("   POST /api/telegram/otp - Configure Telegram")
    print("   POST /api/trading/start - Start trading")
    print("   POST /api/trading/stop - Stop trading")
    print("   GET  /api/trading/status - Get status")
    print("   GET  /api/trades/results - Get trade results")
    print("   GET  /api/trades/upcoming - Get upcoming trades")
    print("   GET  /api/trades/analysis - Get trade analysis")
    print("=" * 60)
    print("💡 Quick Start:")
    print(f"   1. Open http://localhost:{port} in your browser")
    print("   2. Configure SSID and Telegram credentials")
    print("   3. Set trading parameters and click Start Trading")
    print("=" * 60)
    
    # Disable debug mode in production
    is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None
    app.run(host='0.0.0.0', port=port, debug=not is_production)
