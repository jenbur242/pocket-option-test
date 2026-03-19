#!/usr/bin/env python3
"""
Quick Telegram Session Fix
Regenerates the session file to fix OTP issues
"""

import asyncio
import os
from telethon.sync import TelegramClient
from dotenv import load_dotenv

async def fix_session():
    """Fix Telegram session by regenerating it"""
    load_dotenv()
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone_number = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone_number]):
        print("Missing required environment variables!")
        return
    
    print("Telegram Session Fix")
    print("=" * 30)
    print(f"Phone: {phone_number}")
    print(f"API ID: {api_id}")
    
    # Remove old session file if it exists
    session_file = 'session_testpob1234.session'
    if os.path.exists(session_file):
        os.remove(session_file)
        print(f"Removed old session file: {session_file}")
    
    try:
        # Create new client
        client = TelegramClient('session_testpob1234', api_id, api_hash)
        
        print("\nConnecting to Telegram...")
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"Sending verification code to {phone_number}...")
            await client.send_code_request(phone_number)
            
            # Get verification code
            code = input("\nEnter verification code: ")
            
            try:
                await client.sign_in(phone_number, code)
            except Exception as e:
                if "session password needed" in str(e):
                    password = input("Enter 2FA password: ")
                    await client.sign_in(password=password)
                else:
                    raise e
        
        # Get user info
        me = await client.get_me()
        print(f"\nSuccessfully logged in as: {me.first_name} {me.last_name or ''}")
        print(f"Username: @{me.username}" if me.username else "Username: None")
        print(f"User ID: {me.id}")
        
        # Test channel access
        print("\nTesting channel access...")
        try:
            # Test channels
            test_channels = [
                'testpob1234',
                'Pocket_Option_Signals_Vip'
            ]
            
            for channel_username in test_channels:
                try:
                    channel = await client.get_entity(channel_username)
                    print(f"✅ Connected to: {channel.title}")
                except Exception as e:
                    print(f"❌ Failed to connect to @{channel_username}: {e}")
        except Exception as e:
            print(f"Channel test error: {e}")
        
        await client.disconnect()
        print(f"\n✅ Session fixed successfully!")
        print(f"New session file created: {session_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_session())
