# Pocket Option Trading Bot

Automated trading bot for Pocket Option with Telegram signal integration and Flask API.

## Features

- 🤖 Automated trading based on Telegram signals
- 📊 Martingale strategy with customizable parameters
- 🌐 Flask API server with REST endpoints
- 💻 Beautiful web interface for bot management
- 📈 Real-time trade monitoring and statistics
- 🔄 Support for Demo and Real accounts

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the API server:
```bash
python api_server.py
```

3. Open `frontend.html` in your browser

4. Configure SSID, Telegram credentials, and start trading!

## Documentation

- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [Quick Start Guide](QUICK_START.md) - Detailed setup instructions

## API Endpoints

- `POST /api/ssid` - Save SSID configuration
- `POST /api/telegram/otp` - Configure Telegram credentials
- `POST /api/trading/start` - Start trading bot
- `POST /api/trading/stop` - Stop trading bot
- `GET /api/trading/status` - Get current status
- `GET /api/trades/results` - Get trade history
- `GET /api/trades/upcoming` - Get scheduled trades
- `GET /api/trades/analysis` - Get statistics

## Configuration

The bot accepts the following parameters:

- **Initial Amount**: Base trade amount (e.g., $1.00)
- **Multiplier**: Amount multiplier after each loss (e.g., 2.5x)
- **Martingale Step**: Starting step (0 = fresh start, 1+ = resume)
- **Account Type**: Demo or Real

## Martingale Strategy

The bot uses a martingale strategy where:
- **Win**: Reset to Step 0
- **Loss**: Advance to next step with multiplied amount

Example with Initial=$1.00, Multiplier=2.5:
- Step 0: $1.00
- Step 1: $2.50
- Step 2: $6.25
- Step 3: $15.63

## Disclaimer

⚠️ This bot is for educational purposes. Trading involves risk. Always test with demo account first and never trade more than you can afford to lose.
