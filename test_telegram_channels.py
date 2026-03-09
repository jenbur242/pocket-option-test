"""
Test script to check if we can read messages from Telegram channel
Tests both channel username and channel ID
"""
import asyncio
import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Load environment variables
load_dotenv()

# Get credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')
STRING_SESSION = os.getenv('TELEGRAM_STRING_SESSION')

# Channel info
CHANNEL_USERNAME = 'testpob1234'
CHANNEL_ID = -1002420379150

async def test_channel_access():
    """Test accessing channel by both username and ID"""
    
    print("="*60)
    print("🔍 TESTING TELEGRAM CHANNEL ACCESS")
    print("="*60)
    
    # Connect to Telegram
    if STRING_SESSION:
        print("🔐 Using string session")
        client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    else:
        print("📁 Using file session: session_testpob1234.session")
        client = TelegramClient('session_testpob1234', API_ID, API_HASH)
    
    try:
        await client.start(PHONE_NUMBER)
        print("✅ Connected to Telegram\n")
        
        # Test 1: Access by USERNAME
        print("="*60)
        print(f"TEST 1: Accessing by USERNAME (@{CHANNEL_USERNAME})")
        print("="*60)
        
        try:
            channel_by_username = await client.get_entity(CHANNEL_USERNAME)
            print(f"✅ Channel found!")
            print(f"   Title: {channel_by_username.title}")
            print(f"   ID: {channel_by_username.id}")
            print(f"   Username: @{channel_by_username.username if channel_by_username.username else 'N/A'}")
            
            # Try to get messages
            messages = await client.get_messages(channel_by_username, limit=5)
            print(f"\n📨 Recent messages ({len(messages)}):")
            
            for i, msg in enumerate(messages, 1):
                if msg.message:
                    preview = msg.message[:50] + '...' if len(msg.message) > 50 else msg.message
                    print(f"   {i}. [{msg.date.strftime('%H:%M:%S')}] {preview}")
            
            print("\n✅ Can read messages by USERNAME")
            
        except Exception as e:
            print(f"❌ Failed to access by username: {e}")
        
        # Test 2: Access by CHANNEL ID
        print("\n" + "="*60)
        print(f"TEST 2: Accessing by CHANNEL ID ({CHANNEL_ID})")
        print("="*60)
        
        try:
            channel_by_id = await client.get_entity(CHANNEL_ID)
            print(f"✅ Channel found!")
            print(f"   Title: {channel_by_id.title}")
            print(f"   ID: {channel_by_id.id}")
            print(f"   Username: @{channel_by_id.username if channel_by_id.username else 'N/A'}")
            
            # Try to get messages
            messages = await client.get_messages(channel_by_id, limit=5)
            print(f"\n📨 Recent messages ({len(messages)}):")
            
            for i, msg in enumerate(messages, 1):
                if msg.message:
                    preview = msg.message[:50] + '...' if len(msg.message) > 50 else msg.message
                    print(f"   {i}. [{msg.date.strftime('%H:%M:%S')}] {preview}")
            
            print("\n✅ Can read messages by CHANNEL ID")
            
        except Exception as e:
            print(f"❌ Failed to access by ID: {e}")
        
        # Test 3: Compare both
        print("\n" + "="*60)
        print("TEST 3: Comparison")
        print("="*60)
        
        try:
            channel_by_username = await client.get_entity(CHANNEL_USERNAME)
            channel_by_id = await client.get_entity(CHANNEL_ID)
            
            if channel_by_username.id == channel_by_id.id:
                print("✅ Both methods access the SAME channel")
                print(f"   Channel: {channel_by_username.title}")
                print(f"   ID: {channel_by_username.id}")
            else:
                print("⚠️ WARNING: Different channels!")
                print(f"   By username: {channel_by_username.title} (ID: {channel_by_username.id})")
                print(f"   By ID: {channel_by_id.title} (ID: {channel_by_id.id})")
        except Exception as e:
            print(f"⚠️ Could not compare: {e}")
        
        # Test 4: Listen for new messages (5 seconds)
        print("\n" + "="*60)
        print("TEST 4: Listening for NEW messages (5 seconds)")
        print("="*60)
        
        try:
            channel = await client.get_entity(CHANNEL_ID)
            print(f"👂 Listening to: {channel.title}")
            print("⏳ Waiting 5 seconds for new messages...")
            
            from telethon import events
            
            new_messages = []
            
            @client.on(events.NewMessage(chats=channel))
            async def handler(event):
                new_messages.append(event.message.message)
                print(f"   🔔 NEW: {event.message.message[:50]}")
            
            # Wait 5 seconds
            await asyncio.sleep(5)
            
            if new_messages:
                print(f"\n✅ Received {len(new_messages)} new message(s)")
            else:
                print("\n⏳ No new messages in 5 seconds (this is normal)")
            
        except Exception as e:
            print(f"❌ Failed to listen: {e}")
        
        print("\n" + "="*60)
        print("✅ TESTING COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.disconnect()
        print("\n🔌 Disconnected from Telegram")

if __name__ == "__main__":
    asyncio.run(test_channel_access())
