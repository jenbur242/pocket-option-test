# Pocket Option Trading Bot API Documentation

## Overview
This API provides endpoints for managing SSID, configuring Telegram, starting/stopping trading, and viewing trade results.

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Health Check
**GET** `/health`

Check if the API server is running.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-03-07T10:30:00.000Z"
}
```

---

### 2. Set SSID
**POST** `/ssid`

Save the PocketOption SSID for trading.

**Request Body:**
```json
{
  "ssid": "42[\"auth\",{\"session\":\"...\",\"isDemo\":true}]"
}
```

**Response:**
```json
{
  "success": true,
  "message": "SSID saved successfully"
}
```

**Error Response:**
```json
{
  "error": "Invalid SSID format"
}
```

---

### 3. Configure Telegram
**POST** `/telegram/otp`

Configure Telegram credentials for receiving trading signals.

**Request Body:**
```json
{
  "phone": "+1234567890",
  "api_id": "12345678",
  "api_hash": "abcdef1234567890abcdef1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Telegram credentials saved. OTP will be sent when trading starts."
}
```

---

### 4. Start Trading
**POST** `/trading/start`

Start the trading bot with specified configuration.

**Request Body:**
```json
{
  "initial_amount": 1.0,
  "is_demo": true,
  "multiplier": 2.5,
  "martingale_step": 0
}
```

**Parameters:**
- `initial_amount` (required): Base trade amount in dollars (must be > 0)
- `is_demo` (required): Use demo account (true) or real account (false)
- `multiplier` (required): Martingale multiplier (must be >= 1.1)
- `martingale_step` (required): Starting martingale step (0-10)
  - 0 = Start fresh with initial amount
  - 1 = Start at step 1 (initial_amount × multiplier)
  - 2 = Start at step 2 (initial_amount × multiplier²)
  - etc.

**Current Trade Amount Calculation:**
```
current_trade_amount = initial_amount × (multiplier ^ martingale_step)
```

**Examples:**
- Initial: $1.00, Multiplier: 2.5, Step: 0 → Trade: $1.00
- Initial: $1.00, Multiplier: 2.5, Step: 1 → Trade: $2.50
- Initial: $1.00, Multiplier: 2.5, Step: 2 → Trade: $6.25
- Initial: $1.00, Multiplier: 2.5, Step: 3 → Trade: $15.63

**Response:**
```json
{
  "success": true,
  "message": "Trading started successfully",
  "config": {
    "initial_amount": 1.0,
    "is_demo": true,
    "multiplier": 2.5,
    "martingale_step": 0,
    "current_trade_amount": 1.0
  }
}
```

**Error Responses:**
```json
{
  "error": "SSID not configured. Please set SSID first."
}
```
```json
{
  "error": "Initial amount must be greater than 0"
}
```
```json
{
  "error": "Multiplier must be at least 1.1"
}
```
```json
{
  "error": "Martingale step must be between 0 and 10"
}
```

---

### 5. Stop Trading
**POST** `/trading/stop`

Stop the trading bot.

**Response:**
```json
{
  "success": true,
  "message": "Trading stopped successfully"
}
```

---

### 6. Get Trading Status
**GET** `/trading/status`

Get current trading status and configuration.

**Response:**
```json
{
  "active": true,
  "config": {
    "trade_amount": 1.0,
    "is_demo": true,
    "multiplier": 2.5,
    "global_step": 0
  },
  "upcoming_trades": 2,
  "past_trades": 15
}
```

---

### 7. Get Trade Results
**GET** `/trades/results?limit=50&offset=0`

Get paginated trade results.

**Query Parameters:**
- `limit` (optional): Number of trades to return (default: 50)
- `offset` (optional): Offset for pagination (default: 0)

**Response:**
```json
{
  "total": 100,
  "limit": 50,
  "offset": 0,
  "trades": [
    {
      "time": "10:30:45",
      "asset": "EURUSD_otc",
      "direction": "BUY",
      "amount": 1.0,
      "step": 0,
      "result": "win"
    }
  ]
}
```

---

### 8. Get Upcoming Trades
**GET** `/trades/upcoming`

Get scheduled upcoming trades.

**Response:**
```json
{
  "total": 2,
  "trades": [
    {
      "asset": "EURUSD_otc",
      "direction": "BUY",
      "duration": 1,
      "execution_time": "2026-03-07T10:35:00.000Z",
      "amount": 1.0
    }
  ]
}
```

---

### 9. Get Trade Analysis
**GET** `/trades/analysis`

Get trading statistics and analysis.

**Response:**
```json
{
  "total_trades": 50,
  "wins": 35,
  "losses": 15,
  "win_rate": 70.0,
  "total_profit": 25.50,
  "current_step": 0
}
```

---

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file with:
```
SSID=your_ssid_here
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
```

### 3. Start API Server
```bash
python api_server.py
```

The server will start on `http://localhost:5000`

### 4. Open Frontend
Open `frontend.html` in your browser to access the web interface.

---

## Frontend Usage

1. **Configure SSID**: Enter your PocketOption SSID and click "Save SSID"
2. **Configure Telegram**: Enter your Telegram credentials and click "Save Telegram Config"
3. **Configure Trading**:
   - **Initial Amount**: Base trade amount (e.g., $1.00)
   - **Multiplier**: Amount multiplier after each loss (e.g., 2.5x)
   - **Martingale Step**: Starting step (0 = fresh start, 1+ = resume from step)
   - **Account Type**: Demo or Real
   - The "Current Trade Amount" updates automatically based on your inputs
4. **Start Trading**: Click "Start Trading" to begin
5. **Monitor**: View real-time statistics and trade results
6. **Stop Trading**: Click "Stop Trading" when done

### Martingale Strategy Example

With Initial Amount = $1.00 and Multiplier = 2.5:

| Step | Trade Amount | Calculation |
|------|--------------|-------------|
| 0    | $1.00        | $1.00 × 2.5⁰ |
| 1    | $2.50        | $1.00 × 2.5¹ |
| 2    | $6.25        | $1.00 × 2.5² |
| 3    | $15.63       | $1.00 × 2.5³ |
| 4    | $39.06       | $1.00 × 2.5⁴ |

- **Win**: Resets to Step 0
- **Loss**: Advances to next step
- **Starting Step**: Allows resuming from a specific step

---

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid input)
- `500`: Internal Server Error

Error responses include an `error` field with a descriptive message.

---

## Notes

- The API uses CORS to allow frontend access from any origin
- Trading runs in a background thread to avoid blocking the API
- Trade results are stored in memory and will be lost on server restart
- For production use, consider adding authentication and database storage
