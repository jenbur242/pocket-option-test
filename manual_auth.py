#!/usr/bin/env python3
"""
Manual OTP Authentication Script
Run this in your terminal to authenticate and get string session
"""

import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

async def manual_auth():
    load_dotenv()
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone_number = os.getenv('TELEGRAM_PHONE')
    
    print("=== MANUAL AUTHENTICATION ===")
    print(f"Phone: {phone_number}")
    print(f"API ID: {api_id}")
    
    client = TelegramClient('session_testpob1234', api_id, api_hash)
    
    try:
        await client.connect()
        print("Connected to Telegram")
        
        if not await client.is_user_authorized():
            print(f"Sending code to {phone_number}...")
            await client.send_code_request(phone_number)
            
            # Get verification code from user
            code = input("Enter verification code: ")
            
            try:
                await client.sign_in(phone_number, code)
                print("Authentication successful!")
            except Exception as e:
                if "session password needed" in str(e):
                    password = input("Enter 2FA password: ")
                    await client.sign_in(password=password)
                else:
                    raise e
        
        # Get user info
        me = await client.get_me()
        print(f"Logged in as: {me.first_name} {me.last_name or ''}")
        
        # Extract string session
        string_session = client.session.save()
        print(f"\n=== STRING SESSION TOKEN ===")
        print(string_session)
        print("=" * 50)
        
        # Save to file
        with open('string_session.txt', 'w') as f:
            f.write(string_session)
        print(f"Saved to: string_session.txt")
        
        print(f"\n=== INSTRUCTIONS ===")
        print("1. Copy the token above")
        print("2. Add to your .env file:")
        print(f"TELEGRAM_STRING_SESSION={string_session}")
        print("3. Restart your bot - no more OTP!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(manual_auth())
