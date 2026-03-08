"""
Generate Telegram String Session for Railway Deployment

Run this locally to generate a string session that can be used as an environment variable.
This allows the bot to work on Railway without needing the session file.
"""

import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')

async def generate_session():
    """Generate string session"""
    print("=" * 60)
    print("🔐 Telegram String Session Generator")
    print("=" * 60)
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"🔑 API ID: {API_ID}")
    print()
    
    # Create client with StringSession
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    await client.start(phone=PHONE_NUMBER)
    
    # Get the string session
    string_session = client.session.save()
    
    print()
    print("=" * 60)
    print("✅ String Session Generated Successfully!")
    print("=" * 60)
    print()
    print("📋 Add this to your Railway environment variables:")
    print()
    print(f"TELEGRAM_STRING_SESSION={string_session}")
    print()
    print("=" * 60)
    print("💡 Instructions:")
    print("1. Copy the TELEGRAM_STRING_SESSION value above")
    print("2. Go to Railway dashboard > Your project > Variables")
    print("3. Add new variable: TELEGRAM_STRING_SESSION")
    print("4. Paste the value")
    print("5. Redeploy your app")
    print("=" * 60)
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(generate_session())
