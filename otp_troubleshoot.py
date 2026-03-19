#!/usr/bin/env python3
"""
OTP Troubleshooting Script
Helps diagnose and fix OTP issues
"""

import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

async def troubleshoot_otp():
    load_dotenv()
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone_number = os.getenv('TELEGRAM_PHONE')
    
    print("=== OTP TROUBLESHOOTING ===")
    print(f"Phone: {phone_number}")
    print(f"API ID: {api_id}")
    print(f"API Hash: {api_hash[:10]}...")
    
    # Check phone number format
    print(f"\n--- Phone Number Check ---")
    if phone_number.startswith('+'):
        print("✓ Phone number has + prefix")
    else:
        print("✗ Phone number missing + prefix")
        print("  Should be: +" + phone_number)
    
    # Check if phone number looks valid
    digits = ''.join(filter(str.isdigit, phone_number))
    if len(digits) >= 10:
        print(f"✓ Phone number has {len(digits)} digits")
    else:
        print(f"✗ Phone number has only {len(digits)} digits")
    
    client = TelegramClient('session_testpob1234', api_id, api_hash)
    
    try:
        await client.connect()
        print("\n✓ Connected to Telegram successfully")
        
        # Check if already authorized
        if await client.is_user_authorized():
            print("✓ Already authorized - no OTP needed!")
            await get_string_token(client)
            return
        
        print("\n--- Requesting OTP ---")
        print(f"Sending code to {phone_number}...")
        
        try:
            await client.send_code_request(phone_number)
            print("✓ Code request sent successfully")
        except Exception as e:
            print(f"✗ Code request failed: {e}")
            
            # Common issues
            if "phone number" in str(e).lower():
                print("\nPossible issues:")
                print("1. Phone number is incorrect")
                print("2. Phone number not registered on Telegram")
                print("3. API credentials are wrong")
            elif "api" in str(e).lower():
                print("\nPossible issues:")
                print("1. API ID/Hash are incorrect")
                print("2. API app was deleted")
                print("3. Need to create new API app at https://my.telegram.org/apps")
            
            return
        
        print(f"\n--- OTP Instructions ---")
        print("1. Check your Telegram app on your phone")
        print("2. Look for a message from Telegram")
        print("3. If not received, try these:")
        print("   - Wait 2-3 minutes (sometimes delayed)")
        print("   - Check if phone number is correct")
        print("   - Try different Telegram account")
        
        # Try to get code
        code = input("\nEnter verification code (or 'wait' to wait longer): ").strip()
        
        if code.lower() == 'wait':
            print("Waiting 30 seconds...")
            await asyncio.sleep(30)
            code = input("Enter verification code now: ").strip()
        
        if code:
            try:
                await client.sign_in(phone_number, code)
                print("✓ Authentication successful!")
                await get_string_token(client)
            except Exception as e:
                print(f"✗ Sign in failed: {e}")
                
    except Exception as e:
        print(f"Connection error: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Verify API credentials")
        print("3. Try different phone number")
    
    finally:
        await client.disconnect()

async def get_string_token(client):
    """Extract and save string session token"""
    try:
        me = await client.get_me()
        print(f"Logged in as: {me.first_name} {me.last_name or ''}")
        
        string_session = client.session.save()
        print(f"\n=== STRING SESSION TOKEN ===")
        print(string_session)
        print("=" * 60)
        
        with open('string_session.txt', 'w') as f:
            f.write(string_session)
        print(f"Saved to: string_session.txt")
        
        print(f"\nAdd to .env: TELEGRAM_STRING_SESSION={string_session}")
        
    except Exception as e:
        print(f"Error getting token: {e}")

if __name__ == "__main__":
    asyncio.run(troubleshoot_otp())
