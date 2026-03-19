#!/usr/bin/env python3
"""
Robust Authentication Script
Handles invalid codes and provides retry options
"""

import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

async def robust_auth():
    load_dotenv()
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone_number = os.getenv('TELEGRAM_PHONE')
    
    print("=== ROBUST AUTHENTICATION ===")
    print(f"Phone: {phone_number}")
    print(f"API ID: {api_id}")
    
    client = TelegramClient('session_testpob1234', api_id, api_hash)
    
    try:
        await client.connect()
        print("Connected to Telegram")
        
        # Check if already authorized
        if await client.is_user_authorized():
            print("Already authorized!")
            await get_string_token(client)
            return
        
        # Try authentication with retry
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                print(f"\n--- Attempt {attempt + 1}/{max_attempts} ---")
                
                # Request new code each attempt
                await client.send_code_request(phone_number)
                print(f"Code sent to {phone_number}")
                
                # Get code from user
                code = input("Enter verification code (or 'resend' for new code): ").strip()
                
                if code.lower() == 'resend':
                    print("Requesting new code...")
                    await client.send_code_request(phone_number)
                    code = input("Enter new verification code: ").strip()
                
                # Try to sign in
                await client.sign_in(phone_number, code)
                print("Authentication successful!")
                await get_string_token(client)
                return
                
            except Exception as e:
                error_msg = str(e)
                print(f"Error: {error_msg}")
                
                if "invalid" in error_msg.lower():
                    print("Invalid code - please check the code from Telegram")
                    if attempt < max_attempts - 1:
                        print("Try again with the correct code")
                        continue
                    else:
                        print("Max attempts reached")
                        break
                elif "flood" in error_msg.lower():
                    print("Too many requests - please wait a few minutes")
                    break
                elif "password needed" in error_msg.lower():
                    password = input("Enter 2FA password: ")
                    await client.sign_in(password=password)
                    print("Authentication successful!")
                    await get_string_token(client)
                    return
                else:
                    print(f"Unexpected error: {e}")
                    break
        
        print("\nAuthentication failed. Options:")
        print("1. Wait 5 minutes and try again")
        print("2. Check if you're receiving the correct code")
        print("3. Make sure your phone number is correct")
        
    except Exception as e:
        print(f"Connection error: {e}")
    
    finally:
        await client.disconnect()

async def get_string_token(client):
    """Extract and save string session token"""
    try:
        # Get user info
        me = await client.get_me()
        print(f"Logged in as: {me.first_name} {me.last_name or ''}")
        
        # Extract string session
        string_session = client.session.save()
        print(f"\n=== STRING SESSION TOKEN ===")
        print(string_session)
        print("=" * 60)
        
        # Save to file
        with open('string_session.txt', 'w') as f:
            f.write(string_session)
        print(f"Saved to: string_session.txt")
        
        print(f"\n=== NEXT STEPS ===")
        print("1. Copy the token above")
        print("2. Add to your .env file:")
        print(f"TELEGRAM_STRING_SESSION={string_session}")
        print("3. Restart your bot - no more OTP!")
        
    except Exception as e:
        print(f"Error getting token: {e}")

if __name__ == "__main__":
    asyncio.run(robust_auth())
