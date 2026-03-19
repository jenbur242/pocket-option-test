#!/usr/bin/env python3
"""
Manual String Session Instructions
Shows how to generate and use string session
"""

import os
from dotenv import load_dotenv

def show_instructions():
    """Show step-by-step instructions"""
    load_dotenv()
    
    print("TELEGRAM STRING SESSION SETUP")
    print("=" * 50)
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone_number = os.getenv('TELEGRAM_PHONE')
    
    print(f"Your Phone: {phone_number}")
    print(f"API ID: {api_id}")
    print(f"API Hash: {api_hash[:10]}...")
    
    print("\n" + "=" * 50)
    print("STEP 1: RUN THIS COMMAND MANUALLY")
    print("=" * 50)
    print("Open a new terminal and run:")
    print("python -c \"")
    print("import asyncio")
    print("from telethon.sync import TelegramClient")
    print("from telethon.sessions import StringSession")
    print("from dotenv import load_dotenv")
    print("import os")
    print("")
    print("async def gen():")
    print("    load_dotenv()")
    print("    client = TelegramClient(StringSession(), '" + str(api_id) + "', '" + api_hash[:20] + "...')")
    print("    await client.connect()")
    print("    if not await client.is_user_authorized():")
    print("        await client.send_code_request('" + phone_number + "')")
    print("        code = input('Enter code: ')")
    print("        await client.sign_in('" + phone_number + "', code)")
    print("    print('SESSION:', client.session.save())")
    print("    await client.disconnect()")
    print("")
    print("asyncio.run(gen())")
    print("\"")
    
    print("\n" + "=" * 50)
    print("STEP 2: COPY THE SESSION TOKEN")
    print("=" * 50)
    print("1. Enter the verification code when prompted")
    print("2. Copy the SESSION token that appears")
    print("3. Add it to your .env file:")
    print("TELEGRAM_STRING_SESSION=your_token_here")
    
    print("\n" + "=" * 50)
    print("STEP 3: RESTART YOUR BOT")
    print("=" * 50)
    print("The bot will now use string session (no OTP!)")
    
    print("\n" + "=" * 50)
    print("ALTERNATIVE: Use existing session file")
    print("=" * 50)
    print("If you have a working .session file, run:")
    print("python -c \"")
    print("from telethon.sync import TelegramClient")
    print("from telethon.sessions import StringSession")
    print("from dotenv import load_dotenv")
    print("import os")
    print("")
    print("load_dotenv()")
    print("client = TelegramClient('session_testpob1234', os.getenv('TELEGRAM_API_ID'), os.getenv('TELEGRAM_API_HASH'))")
    print("client.connect()")
    print("if client.is_user_authorized():")
    print("    print('SESSION:', client.session.save())")
    print("client.disconnect()")
    print("\"")

if __name__ == "__main__":
    show_instructions()
