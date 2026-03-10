#!/usr/bin/env python3
"""
Telegram Session Creator
Creates a new Telegram session file for the trading bot
"""

import asyncio
import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

def load_env():
    """Load environment variables"""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone_number = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone_number]):
        print("Missing required environment variables:")
        if not api_id:
            print("   - TELEGRAM_API_ID")
        if not api_hash:
            print("   - TELEGRAM_API_HASH")
        if not phone_number:
            print("   - TELEGRAM_PHONE")
        print("\nPlease add these to your .env file")
        return None, None, None
    
    return api_id, api_hash, phone_number

async def create_session():
    """Create new Telegram session"""
    print("Telegram Session Creator")
    print("=" * 40)
    
    # Load credentials
    api_id, api_hash, phone_number = load_env()
    if not api_id:
        return
    
    print(f"Phone: {phone_number}")
    print(f"API ID: {api_id}")
    print(f"API Hash: {api_hash[:10]}...")
    
    # Create session name
    session_name = f"session_{phone_number.replace('+', '').replace(' ', '')}"
    print(f"Session file: {session_name}.session")
    
    try:
        # Create client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Connect and authorize
        print("\nConnecting to Telegram...")
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"Sending code to {phone_number}...")
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
        print(f"\nSuccessfully logged in as:")
        print(f"   Name: {me.first_name} {me.last_name or ''}")
        print(f"   Username: @{me.username}" if me.username else "   Username: None")
        print(f"   ID: {me.id}")
        
        # Create string session by creating a new StringSession client
        string_client = TelegramClient(StringSession(), api_id, api_hash)
        await string_client.start(phone_number)
        
        # Get the string session
        string_session = string_client.session.save()
        print(f"\nString session created:")
        print(f"   Length: {len(string_session)} characters")
        print(f"   Preview: {string_session[:50]}...")
        
        await string_client.disconnect()
        
        # Save string session to file
        with open(f"{session_name}_string.txt", "w") as f:
            f.write(string_session)
        print(f"String session saved to: {session_name}_string.txt")
        
        print(f"\nSession files created:")
        print(f"   Session file: {session_name}.session")
        print(f"   String session: {session_name}_string.txt")
        
        print(f"\nTo use this session:")
        print(f"   1. Copy the string session from {session_name}_string.txt")
        print(f"   2. Add it to your .env as TELEGRAM_STRING_SESSION")
        print(f"   3. Or rename {session_name}.session to session_testpob1234.session")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"Error creating session: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_session())
