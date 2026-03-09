"""
Test if bot can read messages from the second channel
David Cooper | Private signals (ID: 2420379150)
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime, timedelta

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')
STRING_SESSION = os.getenv('TELEGRAM_STRING_SESSION')

# Second channel info
CHANNEL_ID = 2420379150
CHANNEL_NAME = "David Cooper | Private signals"

async def test_second_channel():
    """Test reading messages from second channel"""
    
    print("=" * 70)
    print("🔍 Testing Second Channel Access")
    print("=" * 70)
    print(f"Channel: {CHANNEL_NAME}")
    print(f"Channel ID: {CHANNEL_ID}")
    print()
    
    # Connect to Telegram
    if STRING_SESSION:
        print("🔐 Using string session")
        client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    else:
        print("📁 Using file session")
        client = TelegramClient('session_testpob1234', API_ID, API_HASH)
    
    try:
        await client.start(PHONE)
        print("✅ Connected to Telegram")
        print()
        
        # Try to get channel by ID
        try:
            channel = await client.get_entity(CHANNEL_ID)
            print(f"✅ Found channel: {channel.title}")
            print(f"   Channel ID: {channel.id}")
            print(f"   Username: @{channel.username if channel.username else 'N/A'}")
            print(f"   Type: {type(channel).__name__}")
            print()
            
            # Get recent messages
            print("📨 Fetching recent messages...")
            recent_time = datetime.now() - timedelta(hours=24)
            
            messages = await client(GetHistoryRequest(
                peer=channel,
                limit=20,
                offset_date=recent_time,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            
            print(f"✅ Found {len(messages.messages)} messages in last 24 hours")
            print()
            
            if messages.messages:
                print("=" * 70)
                print("📋 Recent Messages:")
                print("=" * 70)
                
                for i, msg in enumerate(messages.messages[:10], 1):
                    if msg.message:
                        print(f"\n{i}. Message ID: {msg.id}")
                        print(f"   Date: {msg.date}")
                        print(f"   Text: {msg.message[:100]}...")
                        print("-" * 70)
            else:
                print("⚠️ No messages found in last 24 hours")
                print("   Try posting a test message to the channel")
            
            print()
            print("=" * 70)
            print("✅ TEST SUCCESSFUL - Bot can read from second channel!")
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ Error accessing channel: {e}")
            print()
            print("Possible reasons:")
            print("1. Bot is not a member of the channel")
            print("2. Channel ID is incorrect")
            print("3. Channel is private and bot doesn't have access")
            print()
            
            # Try to list all channels bot has access to
            print("📋 Listing all channels bot has access to:")
            print("-" * 70)
            
            async for dialog in client.iter_dialogs():
                if dialog.is_channel:
                    print(f"✓ {dialog.title}")
                    print(f"  ID: {dialog.id}")
                    print(f"  Username: @{dialog.entity.username if dialog.entity.username else 'N/A'}")
                    print()
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    finally:
        await client.disconnect()
        print("\n🔌 Disconnected")

if __name__ == '__main__':
    asyncio.run(test_second_channel())
