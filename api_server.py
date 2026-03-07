#!/usr/bin/env python3
"""
Flask API Server for Pocket Option Trading Bot
Provides endpoints for frontend to manage SSID, start trading, and view results
"""
from flask import Flask, request, jsonify
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
    MULTIPLIER
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Global state
trading_active = False
trading_thread = None
trade_results = []  # Store all trade results

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

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
                'total_profit': 0
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

def run_trading_bot(initial_amount, is_demo, multiplier, martingale_step):
    """Run trading bot in background with custom configuration"""
    global trading_active
    
    try:
        # Update global variables in telegram.main module
        import telegram.main as trading_module
        trading_module.TRADE_AMOUNT = initial_amount
        trading_module.IS_DEMO = is_demo
        trading_module.MULTIPLIER = multiplier
        trading_module.global_martingale_step = martingale_step
        
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
        trading_active = False
    
    finally:
        loop.close()

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Pocket Option Trading API Server")
    print("=" * 60)
    print("📡 Server starting on http://localhost:5000")
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
    
    app.run(host='0.0.0.0', port=5000, debug=True)
