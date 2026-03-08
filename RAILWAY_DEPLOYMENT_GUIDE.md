# 🚀 Railway Deployment Guide

## Why Trades Don't Work on Railway (But Work Locally)

The issue is that **Railway doesn't have your Telegram session file**. When you run locally, the bot uses `session_testpob1234.session` which contains your authenticated Telegram session. This file doesn't get uploaded to Railway, so the bot can't connect to Telegram to receive trade signals.

## Solution: Use String Session

Instead of a file, we'll convert your Telegram session to a string that can be stored as an environment variable on Railway.

---

## Step 1: Generate String Session (Run Locally)

1. **Run the generator script:**
   ```bash
   python generate_string_session.py
   ```

2. **Enter OTP code** when prompted (you'll receive it via Telegram)

3. **Copy the output** - it will look like:
   ```
   TELEGRAM_STRING_SESSION=1BVtsOKcBu6T8QHw...very_long_string...xYz123
   ```

---

## Step 2: Add to Railway Environment Variables

1. Go to your Railway dashboard: https://railway.app/dashboard
2. Click on your project
3. Go to **Variables** tab
4. Click **+ New Variable**
5. Add these variables:

### Required Variables:

```bash
# Telegram String Session (from Step 1)
TELEGRAM_STRING_SESSION=<paste_your_string_session_here>

# Telegram Credentials
TELEGRAM_API_ID=28375707
TELEGRAM_API_HASH=cf54e727df04363575f8ee9f120be2c9
TELEGRAM_PHONE=+12427272924
TELEGRAM_CHANNEL=testpob1234

# PocketOption SSIDs
SSID_DEMO=42["auth",{"session":"8kmju1f41cibg1vg5pihe37d7u","isDemo":1,"uid":116040367,"platform":2,"isFastHistory":true,"isOptimized":true}]

SSID_REAL=42["auth",{"session":"a:4:{s:10:\"session_id\";s:32:\"2a8f01f1efeca20cc174c1b75eb6156a\";s:10:\"ip_address\";s:14:\"172.86.107.247\";s:10:\"user_agent\";s:111:\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36\";s:13:\"last_activity\";i:1772807404;}3fed45de8f1ed072a8cabf7a07571f05","isDemo":0,"uid":116040367,"platform":2,"isFastHistory":true,"isOptimized":true}]

# Trading Configuration
TRADE_AMOUNT=1
IS_DEMO=True
MULTIPLIER=2.5
MARTINGALE_STEP=0

# Port (Railway sets this automatically)
PORT=5000
```

---

## Step 3: Deploy

1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Add string session support for Railway"
   git push
   ```

2. **Railway will auto-deploy** when you push

3. **Check logs** in Railway dashboard to verify:
   - ✅ "Using string session (Railway deployment)"
   - ✅ "Connected to: Test"
   - ✅ "Pre-connected to PocketOption"
   - ✅ "Waiting for signals..."

---

## Step 4: Test

1. Open your Railway URL: https://web-production-db4ea.up.railway.app/
2. The bot should auto-start in DEMO mode
3. Send a test signal to your Telegram channel
4. Check logs - you should see:
   - 🔔 NEW MESSAGE RECEIVED
   - 📥 Trade signal received
   - ✅ Order placed!

---

## Troubleshooting

### Issue: "TELEGRAM_STRING_SESSION not found"
**Solution:** Make sure you added the variable in Railway dashboard and redeployed

### Issue: "Invalid string session"
**Solution:** Regenerate the string session using `generate_string_session.py`

### Issue: "Balance data not available"
**Solution:** This is normal - the bot will still place trades. Balance fetch is non-critical.

### Issue: "SSID expired"
**Solution:** 
1. Get new SSID from PocketOption (F12 > Network > look for WebSocket connection)
2. Update `SSID_DEMO` or `SSID_REAL` in Railway variables
3. Redeploy

---

## How It Works

### Local Development:
- Uses file session: `session_testpob1234.session`
- Session persists between runs
- Need to verify OTP only once

### Railway Deployment:
- Uses string session from environment variable
- No files needed
- Session stored securely in Railway variables
- Works across deployments and restarts

---

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` file to GitHub
- Never share your string session publicly
- Keep your Railway variables private
- Regenerate sessions if compromised

---

## Quick Checklist

- [ ] Generated string session locally
- [ ] Added `TELEGRAM_STRING_SESSION` to Railway
- [ ] Added all other environment variables
- [ ] Pushed code to GitHub
- [ ] Railway deployed successfully
- [ ] Checked logs for "Using string session"
- [ ] Bot auto-started in DEMO mode
- [ ] Tested with a signal from Telegram

---

## Support

If trades still don't work after following this guide:

1. Check Railway logs for errors
2. Verify all environment variables are set correctly
3. Make sure SSID is not expired
4. Test locally first to ensure code works
5. Check that Telegram channel is accessible

---

**Last Updated:** March 8, 2026
