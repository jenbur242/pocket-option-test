"""
Quick Railway Setup Script

This script helps you set up Railway deployment by:
1. Generating a string session
2. Creating a .env.railway file with all variables
3. Showing you exactly what to paste into Railway
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

def create_railway_env():
    """Create .env.railway file with all required variables"""
    
    print("=" * 70)
    print("🚀 Railway Deployment Setup")
    print("=" * 70)
    print()
    print("This script will help you set up your Railway deployment.")
    print()
    print("Step 1: Generate Telegram String Session")
    print("-" * 70)
    print()
    print("Run this command:")
    print("  python generate_string_session.py")
    print()
    print("Copy the TELEGRAM_STRING_SESSION value it generates.")
    print()
    input("Press Enter when you have your string session ready...")
    print()
    
    string_session = input("Paste your TELEGRAM_STRING_SESSION here: ").strip()
    
    if not string_session:
        print("❌ No string session provided. Exiting.")
        return
    
    print()
    print("Step 2: Creating Railway Environment Variables")
    print("-" * 70)
    
    # Read current .env
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value.strip().strip("'\"")
    
    # Create Railway env file
    railway_env = f"""# Railway Environment Variables
# Copy these to Railway Dashboard > Variables

TELEGRAM_STRING_SESSION={string_session}

TELEGRAM_API_ID={env_vars.get('TELEGRAM_API_ID', '28375707')}
TELEGRAM_API_HASH={env_vars.get('TELEGRAM_API_HASH', 'cf54e727df04363575f8ee9f120be2c9')}
TELEGRAM_PHONE={env_vars.get('TELEGRAM_PHONE', '+12427272924')}
TELEGRAM_CHANNEL={env_vars.get('TELEGRAM_CHANNEL', 'testpob1234')}

SSID_DEMO={env_vars.get('SSID_DEMO', '')}
SSID_REAL={env_vars.get('SSID_REAL', '')}

TRADE_AMOUNT={env_vars.get('TRADE_AMOUNT', '1')}
IS_DEMO={env_vars.get('IS_DEMO', 'True')}
MULTIPLIER={env_vars.get('MULTIPLIER', '2.5')}
MARTINGALE_STEP={env_vars.get('MARTINGALE_STEP', '0')}

PORT=5000
"""
    
    with open('.env.railway', 'w', encoding='utf-8') as f:
        f.write(railway_env)
    
    print()
    print("✅ Created .env.railway file")
    print()
    print("=" * 70)
    print("📋 Next Steps:")
    print("=" * 70)
    print()
    print("1. Open Railway Dashboard:")
    print("   https://railway.app/dashboard")
    print()
    print("2. Go to your project > Variables tab")
    print()
    print("3. Copy variables from .env.railway file")
    print("   (The file has been created in your project folder)")
    print()
    print("4. Add each variable to Railway:")
    print("   - Click '+ New Variable'")
    print("   - Paste variable name and value")
    print("   - Repeat for all variables")
    print()
    print("5. Deploy:")
    print("   git add .")
    print("   git commit -m 'Add Railway support'")
    print("   git push")
    print()
    print("6. Check Railway logs to verify bot is running")
    print()
    print("=" * 70)
    print("✅ Setup Complete!")
    print("=" * 70)

if __name__ == '__main__':
    create_railway_env()
