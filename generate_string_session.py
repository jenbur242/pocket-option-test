#!/usr/bin/env python3
"""
Generate String Session Token
Creates a string session token to avoid OTP authentication
"""

import asyncio
import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

async def generate_string_session():
    """Generate string session token"""
    load_dotenv()
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone_number = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone_number]):
        print("Missing required environment variables!")
        print("Need: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
        return
    
    print("String Session Generator")
    print("=" * 30)
    print(f"Phone: {phone_number}")
    print(f"API ID: {api_id}")
    
    try:
        # Create client with string session
        client = TelegramClient(StringSession(), api_id, api_hash)
        
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
        
        # Get the string session
        string_session = client.session.save()
        print(f"\nString session generated!")
        print(f"Length: {len(string_session)} characters")
        print(f"Preview: {string_session[:50]}...")
        
        # Save to file
        with open('string_session.txt', 'w') as f:
            f.write(string_session)
        print(f"\nSaved to: string_session.txt")
        
        # Show how to use it
        print(f"\n" + "=" * 50)
        print("HOW TO USE:")
        print("=" * 50)
        print("1. Copy the string session below:")
        print("-" * 50)
        print(string_session)
        print("-" * 50)
        print("\n2. Add it to your .env file:")
        print(f"TELEGRAM_STRING_SESSION={string_session}")
        print("\n3. Restart your bot - no more OTP required!")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(generate_string_session())
