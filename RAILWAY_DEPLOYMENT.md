# Railway Deployment Guide

## 🚀 Quick Deploy to Railway

### Prerequisites
- Railway account (sign up at https://railway.app)
- Git installed
- Railway CLI (optional but recommended)

### Method 1: Deploy via Railway Dashboard (Easiest)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

2. **Connect to Railway**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect the configuration

3. **Set Environment Variables**
   In Railway dashboard, go to your project → Variables → Add:
   ```
   SSID=your_ssid_here
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_PHONE=your_phone_number
   TELEGRAM_CHANNEL=testpob1234
   TRADE_AMOUNT=1.0
   IS_DEMO=True
   MULTIPLIER=2.5
   MARTINGALE_STEP=0
   PORT=5000
   ```

4. **Deploy**
   - Railway will automatically deploy
   - Wait for deployment to complete
   - Get your public URL from Railway dashboard

### Method 2: Deploy via Railway CLI

1. **Install Railway CLI**
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Initialize Project**
   ```bash
   railway init
   ```

4. **Link to Project**
   ```bash
   railway link
   ```

5. **Set Environment Variables**
   ```bash
   railway variables set SSID="your_ssid_here"
   railway variables set TELEGRAM_API_ID="your_api_id"
   railway variables set TELEGRAM_API_HASH="your_api_hash"
   railway variables set TELEGRAM_PHONE="your_phone_number"
   railway variables set TELEGRAM_CHANNEL="testpob1234"
   railway variables set TRADE_AMOUNT="1.0"
   railway variables set IS_DEMO="True"
   railway variables set MULTIPLIER="2.5"
   railway variables set MARTINGALE_STEP="0"
   railway variables set PORT="5000"
   ```

6. **Deploy**
   ```bash
   railway up
   ```

### Method 3: One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

Click the button above and follow the prompts.

## 📋 Configuration Files

The following files have been created for Railway deployment:

- `railway.json` - Railway configuration
- `Procfile` - Process definition
- `runtime.txt` - Python version specification
- `requirements.txt` - Python dependencies

## 🔧 Important Notes

### Environment Variables
Make sure to set all required environment variables in Railway dashboard:
- `SSID` - Your PocketOption SSID (required)
- `TELEGRAM_API_ID` - Telegram API ID (required)
- `TELEGRAM_API_HASH` - Telegram API Hash (required)
- `TELEGRAM_PHONE` - Your phone number (required)
- `TELEGRAM_CHANNEL` - Telegram channel name (default: testpob1234)
- `PORT` - Port number (Railway sets this automatically)

### Session Files
- Telegram session files (`.session`) are gitignored
- You'll need to complete OTP verification after first deployment
- Use the frontend Configuration section to set up Telegram

### Database/Storage
- Trade results are stored in CSV files in `trade_results/` folder
- Railway provides ephemeral storage (files may be lost on restart)
- Consider using Railway's persistent volumes for production

### Logs
- Logs are stored in `logs/` folder
- View logs in Railway dashboard or via CLI: `railway logs`

## 🌐 Accessing Your Deployment

After deployment:
1. Railway will provide a public URL (e.g., `https://your-app.railway.app`)
2. Open the URL in your browser
3. Configure SSID and Telegram in the Configuration section
4. Start trading!

## 🔄 Updating Your Deployment

To update your deployment:

```bash
git add .
git commit -m "Update description"
git push origin main
```

Railway will automatically redeploy on push.

Or using Railway CLI:
```bash
railway up
```

## 🐛 Troubleshooting

### Deployment Fails
- Check Railway logs: `railway logs`
- Verify all environment variables are set
- Check `requirements.txt` for missing dependencies

### Can't Connect to PocketOption
- Verify SSID is valid and not expired
- Check if SSID is properly set in environment variables
- SSID expires after some time, update it regularly

### Telegram OTP Issues
- Complete OTP verification through the frontend
- Session files are not persistent on Railway (use volumes)
- May need to re-verify after each deployment

### Balance Not Showing
- Ensure SSID is configured
- Click the refresh button manually
- Check Railway logs for connection errors

## 📊 Monitoring

Monitor your deployment:
- Railway Dashboard: View metrics, logs, and deployments
- Railway CLI: `railway logs --follow`
- Frontend: Real-time status in the dashboard

## 💰 Costs

Railway offers:
- Free tier: $5 credit/month
- Hobby plan: $5/month + usage
- Pro plan: $20/month + usage

This bot should run comfortably on the free tier for testing.

## 🔒 Security

- Never commit `.env` file (already in .gitignore)
- Keep SSID and API credentials secure
- Use Railway's environment variables for sensitive data
- Regularly rotate your SSID
- Enable 2FA on your Railway account

## 📞 Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: Create an issue in your GitHub repo

## ✅ Deployment Checklist

Before deploying:
- [ ] All code committed to Git
- [ ] `requirements.txt` is up to date
- [ ] Environment variables documented
- [ ] `.gitignore` excludes sensitive files
- [ ] Railway configuration files created
- [ ] Tested locally

After deploying:
- [ ] Verify deployment succeeded
- [ ] Set all environment variables
- [ ] Configure SSID in frontend
- [ ] Complete Telegram OTP verification
- [ ] Test balance fetching
- [ ] Test trade execution
- [ ] Monitor logs for errors

## 🎉 Success!

Your Pocket Option Trading Bot is now live on Railway!

Access it at: `https://your-app.railway.app`
