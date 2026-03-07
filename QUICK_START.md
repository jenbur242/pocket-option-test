# Quick Start Guide - Pocket Option Trading Bot

## 🚀 Setup (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Get Your SSID from PocketOption
1. Open PocketOption in your browser
2. Press `F12` to open Developer Tools
3. Go to **Network** tab
4. Filter by **WS** (WebSocket)
5. Look for a message starting with `42["auth",{`
6. Copy the entire message (it's your SSID)

Example SSID format:
```
42["auth",{"session":"abc123...","isDemo":true}]
```

### Step 3: Get Telegram Credentials
1. Go to https://my.telegram.org/auth
2. Login with your phone number
3. Go to **API Development Tools**
4. Create an app to get:
   - **API ID** (numbers like: 12345678)
   - **API Hash** (string like: abcdef1234567890)

### Step 4: Start the API Server
```bash
python api_server.py
```

You should see:
```
🚀 Pocket Option Trading API Server
📡 Server starting on http://localhost:5000
```

### Step 5: Open the Frontend
Open `frontend.html` in your browser (just double-click it)

---

## 🎮 Using the Bot

### 1. Configure SSID
- Paste your SSID in the first field
- Click **Save SSID**
- You should see: ✅ "SSID saved successfully!"

### 2. Configure Telegram
- Enter your phone number (with country code, e.g., +1234567890)
- Enter your API ID
- Enter your API Hash
- Click **Save Telegram Config**

### 3. Configure Trading Parameters

#### Initial Amount
- Base trade amount (e.g., $1.00)
- This is what you'll trade on Step 0

#### Multiplier
- How much to multiply after each loss
- Common values: 2.0, 2.5, 3.0
- Example: 2.5x means each loss multiplies by 2.5

#### Martingale Step
- **0** = Start fresh (recommended)
- **1+** = Resume from a specific step
- Use this if you want to continue a sequence

#### Account Type
- **Demo** = Practice with fake money (recommended for testing)
- **Real** = Trade with real money

### 4. Understanding the Preview

The bot shows you the next 5 steps:

Example with Initial=$1.00, Multiplier=2.5, Step=0:
```
→ Step 0: $1.00   ← You start here
  Step 1: $2.50   ← If you lose
  Step 2: $6.25   ← If you lose again
  Step 3: $15.63  ← If you lose again
  Step 4: $39.06  ← If you lose again
```

### 5. Start Trading
- Click **▶️ Start Trading**
- Status will change to "Active"
- The bot will:
  1. Connect to Telegram channel
  2. Wait for trading signals
  3. Execute trades automatically
  4. Update results in real-time

### 6. Monitor Results
- **Statistics Card**: Shows wins, losses, win rate, profit
- **Recent Trades Table**: Shows last 10 trades with results
- Everything updates every 2 seconds automatically

### 7. Stop Trading
- Click **⏹️ Stop Trading** when done
- Status will change to "Inactive"

---

## 📊 Understanding Martingale Strategy

### How It Works
1. **Start**: Trade with initial amount (e.g., $1.00)
2. **Win**: Reset to Step 0, trade $1.00 again
3. **Loss**: Move to next step, trade $2.50 (1.00 × 2.5)
4. **Loss again**: Move to Step 2, trade $6.25 (2.50 × 2.5)
5. **Win**: Reset to Step 0, trade $1.00 again

### Example Sequence
```
Trade 1: $1.00  → LOSS  → Total: -$1.00
Trade 2: $2.50  → LOSS  → Total: -$3.50
Trade 3: $6.25  → WIN   → Total: +$1.75 (profit!)
Trade 4: $1.00  → (reset to Step 0)
```

### Risk Management
- Higher multiplier = faster recovery but higher risk
- Lower multiplier = slower recovery but lower risk
- Always test with DEMO account first!

---

## 🔧 Troubleshooting

### "SSID not configured"
- Make sure you saved the SSID first
- Check that SSID starts with `42["auth"`

### "Telegram credentials not configured"
- Save all 3 Telegram fields (phone, API ID, API Hash)
- Phone must include country code (+1234567890)

### "Trading is already active"
- Stop the current trading session first
- Click "Stop Trading" button

### No trades executing
- Check that Telegram channel is sending signals
- Verify you're connected to the correct channel
- Check the console/terminal for error messages

### Connection timeout
- SSID may be expired (they expire after ~24 hours)
- Get a fresh SSID from PocketOption
- Save the new SSID and try again

---

## 💡 Tips

1. **Always test with DEMO first** - Get comfortable with the bot before using real money
2. **Start with small amounts** - Use $1-5 initial amount when starting
3. **Monitor regularly** - Check the statistics and results frequently
4. **Set limits** - Decide your max loss before starting
5. **Keep SSID fresh** - Update SSID daily for best results

---

## 📞 Support

If you encounter issues:
1. Check the terminal/console for error messages
2. Verify all credentials are correct
3. Make sure the API server is running
4. Try restarting the API server

---

## ⚠️ Disclaimer

This bot is for educational purposes. Trading involves risk. Always:
- Test thoroughly with demo account
- Never trade more than you can afford to lose
- Understand the risks of martingale strategy
- Use at your own risk
