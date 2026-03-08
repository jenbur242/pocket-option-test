# 🔧 Railway Deployment Fix Guide

## ✅ Changes Made

I've fixed two critical issues for Railway deployment:

### 1. Dynamic PORT Configuration
**File**: `api_server.py`
- Changed from hardcoded `port=5000` to `port = int(os.getenv('PORT', 5000))`
- Railway assigns a dynamic PORT, not 5000
- App now reads PORT from environment variable

### 2. Relative API URLs
**File**: `frontend.html`
- Changed from `const API_BASE = 'http://localhost:5000/api'`
- To: `const API_BASE = window.location.origin + '/api'`
- Frontend now uses the same domain as the page (works on Railway)

## 🚀 Deployment Status

**Your Railway URL**: `https://web-production-db4ea.up.railway.app`

**Current Status**: Getting 502 error (Application failed to respond)

## 🔍 How to Check Railway Logs

Since Railway CLI isn't installed, use the web dashboard:

1. **Go to Railway Dashboard**
   - Visit: https://railway.app/dashboard
   - Sign in with GitHub

2. **Find Your Project**
   - Look for "pocket-option-test" or similar name
   - Click on it

3. **View Deployment Logs**
   - Click on the "Deployments" tab
   - Click on the latest deployment
   - Click "View Logs" button
   - Look for error messages

## 🐛 Common Issues & Solutions

### Issue 1: Missing Environment Variables
**Symptoms**: App crashes on startup, logs show "SSID not found" or similar

**Solution**:
1. Go to your Railway project
2. Click "Variables" tab
3. Add these required variables:
   ```
   PORT=5000
   SSID=42["auth",{"session":"your_session_here"}]
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_PHONE=+1234567890
   TELEGRAM_CHANNEL=testpob1234
   TRADE_AMOUNT=1.0
   IS_DEMO=True
   MULTIPLIER=2.5
   MARTINGALE_STEP=0
   ```

**Note**: SSID and Telegram credentials are optional for initial deployment. The app will start without them, but trading won't work until configured.

### Issue 2: Python Dependencies Failed
**Symptoms**: Logs show "ModuleNotFoundError" or "pip install failed"

**Solution**:
1. Check `requirements.txt` is in root directory
2. Verify all packages are available on PyPI
3. Railway should auto-detect Python and install dependencies

### Issue 3: Build Failed
**Symptoms**: Deployment shows "Build Failed" status

**Solution**:
1. Check Railway build logs
2. Verify `runtime.txt` specifies `python-3.11`
3. Ensure `Procfile` has: `web: python api_server.py`

### Issue 4: App Starts But Crashes
**Symptoms**: Logs show app starting then immediately stopping

**Solution**:
1. Check for Python syntax errors in logs
2. Verify all imports are available
3. Check if Flask is binding to correct host/port

## 📋 Checklist for Successful Deployment

- [ ] Code pushed to GitHub (✅ Done)
- [ ] Railway project created and linked to GitHub repo
- [ ] Environment variables set (at minimum, can be empty initially)
- [ ] Build completed successfully
- [ ] App starts without crashing
- [ ] Health check endpoint responds: `/api/health`
- [ ] Frontend loads at root URL: `/`

## 🔧 Manual Deployment Steps

If automatic deployment isn't working:

### Step 1: Check Railway Project Settings
1. Go to Railway dashboard
2. Click on your project
3. Click "Settings" tab
4. Verify:
   - **Root Directory**: `/` (or leave empty)
   - **Build Command**: (leave empty, auto-detected)
   - **Start Command**: `python api_server.py`

### Step 2: Trigger Manual Redeploy
1. Go to "Deployments" tab
2. Click "Deploy" button (top right)
3. Select "Redeploy" from dropdown
4. Wait for build to complete (2-3 minutes)

### Step 3: Check Logs
1. Click on the new deployment
2. Click "View Logs"
3. Look for:
   - ✅ "Server starting on port XXXX"
   - ✅ "Running on http://0.0.0.0:XXXX"
   - ❌ Any error messages or stack traces

## 🎯 Expected Log Output

When working correctly, you should see:

```
====================================================================
🚀 Pocket Option Trading API Server
====================================================================
📡 Server starting on port 8080
🌐 Frontend available at http://localhost:8080
====================================================================
📚 API Endpoints:
   POST /api/ssid - Set SSID
   POST /api/telegram/otp - Configure Telegram
   POST /api/trading/start - Start trading
   POST /api/trading/stop - Stop trading
   GET  /api/trading/status - Get status
   GET  /api/trades/results - Get trade results
   GET  /api/trades/upcoming - Get upcoming trades
   GET  /api/trades/analysis - Get trade analysis
====================================================================
 * Serving Flask app 'api_server'
 * Running on http://0.0.0.0:8080
```

## 🧪 Testing After Deployment

Once deployed successfully:

### Test 1: Health Check
```bash
curl https://web-production-db4ea.up.railway.app/api/health
```
Expected: `{"status":"ok","timestamp":"..."}`

### Test 2: Frontend
Open in browser: `https://web-production-db4ea.up.railway.app`
Expected: Deep Space UI loads

### Test 3: Configuration
1. Go to Configuration section
2. Try to save SSID (should work even without valid SSID)
3. Check if Telegram section appears

## 💡 Pro Tips

1. **Don't Set SSID in Environment Variables Initially**
   - Let the app start first
   - Configure SSID through the web UI
   - This makes debugging easier

2. **Check Railway Metrics**
   - Go to "Metrics" tab in Railway
   - See CPU, Memory, Network usage
   - If all zeros, app isn't running

3. **Use Railway's Built-in Domain**
   - Don't add custom domain until app works
   - Railway provides: `*.up.railway.app`
   - Custom domains can be added later

4. **Enable Railway's Auto-Deploy**
   - Settings → Enable "Auto Deploy"
   - Every GitHub push triggers new deployment
   - Great for continuous updates

## 🆘 Still Not Working?

### Option 1: Check Railway Status
Visit: https://status.railway.app
(Railway might be having issues)

### Option 2: Create New Railway Project
Sometimes starting fresh helps:
1. Delete current Railway project
2. Create new project
3. Link to GitHub repo again
4. Let Railway auto-detect and deploy

### Option 3: Use Railway Template
I can create a Railway template button:
1. Click: [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/jenbur242/pocket-option-test)
2. Railway will clone and deploy automatically

## 📞 Get Help

If you share the Railway logs with me, I can help debug further. Look for:
- Error messages
- Stack traces
- "ModuleNotFoundError"
- "Connection refused"
- Any red text in logs

## ✅ Next Steps

1. **Check Railway Dashboard** - View logs to see what's failing
2. **Set Environment Variables** - Add at least empty values for required vars
3. **Trigger Redeploy** - After setting variables
4. **Test Health Endpoint** - `curl https://your-url/api/health`
5. **Open Frontend** - Visit your Railway URL in browser

---

**The code is ready and pushed to GitHub. Railway should auto-deploy within 2-3 minutes of the push.**

**Your deployment URL**: https://web-production-db4ea.up.railway.app

Check the Railway dashboard for logs and status!
