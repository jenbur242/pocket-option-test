"""
Generate String Session for Railway Deployment

This script converts your local session file to a string session
that can be stored as an environment variable on Railway.
"""

import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')

print("=" * 70)
print("🔐 String Session Generator for Railway")
print("=" * 70)
print()

if not all([API_ID, API_HASH, PHONE]):
    print("❌ Error: Missing Telegram credentials in .env file")
    print("   Please ensure TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE are set")
    exit(1)

print(f"📱 Phone: {PHONE}")
print(f"🔑 API ID: {API_ID}")
print()

# Check if session file exists
session_file = 'session_testpob1234.session'
if os.path.exists(session_file):
    print(f"✅ Found existing session file: {session_file}")
    print("   Converting to string session...")
    print()
    
    # Load existing session and convert to string
    with TelegramClient('session_testpob1234', API_ID, API_HASH) as client:
        string_session = StringSession.save(client.session)
        
        print("=" * 70)
        print("✅ STRING SESSION GENERATED!")
        print("=" * 70)
        print()
        print("Add this to your Railway environment variables:")
        print()
        print("Variable Name: TELEGRAM_STRING_SESSION")
        print("Variable Value:")
        print("-" * 70)
        print(string_session)
        print("-" * 70)
        print()
        print("=" * 70)
        print("📋 Next Steps:")
        print("=" * 70)
        print()
        print("1. Go to Railway Dashboard > Your Project > Variables")
        print("2. Click '+ New Variable'")
        print("3. Name: TELEGRAM_STRING_SESSION")
        print("4. Value: (paste the string above)")
        print("5. Click 'Add'")
        print("6. Redeploy your app")
        print()
        print("The bot will use the string session instead of session files!")
        print("=" * 70)
else:
    print(f"❌ Session file not found: {session_file}")
    print()
    print("Creating new session...")
    print("You will receive an OTP code on your phone.")
    print()
    
    with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        client.start(phone=PHONE)
        string_session = client.session.save()
        
        print()
        print("=" * 70)
        print("✅ NEW STRING SESSION CREATED!")
        print("=" * 70)
        print()
        print("Add this to your Railway environment variables:")
        print()
        print("Variable Name: TELEGRAM_STRING_SESSION")
        print("Variable Value:")
        print("-" * 70)
        print(string_session)
        print("-" * 70)
        print()
        print("=" * 70)
        print("📋 Next Steps:")
        print("=" * 70)
        print()
        print("1. Go to Railway Dashboard > Your Project > Variables")
        print("2. Click '+ New Variable'")
        print("3. Name: TELEGRAM_STRING_SESSION")
        print("4. Value: (paste the string above)")
        print("5. Click 'Add'")
        print("6. Deploy your app")
        print()
        print("The bot will use the string session instead of session files!")
        print("=" * 70)
