import asyncio
import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timedelta
from dotenv import load_dotenv

async def monitor_channel():
    """Monitor messages from the new channel to see signal format"""
    load_dotenv()
    
    API_ID = os.getenv('TELEGRAM_API_ID')
    API_HASH = os.getenv('TELEGRAM_API_HASH')
    PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')
    STRING_SESSION = os.getenv('TELEGRAM_STRING_SESSION')
    
    # Connect to Telegram
    if STRING_SESSION:
        print("Using string session")
        client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    else:
        print("Using file session: session_testpob1234.session")
        client = TelegramClient('session_testpob1234', API_ID, API_HASH)
    
    try:
        await client.start(PHONE_NUMBER)
        print("Connected to Telegram successfully!")
        
        # Get the channel
        try:
            channel = await client.get_entity('Pocket_Option_Signals_Vip')
            print(f"\nChannel Info:")
            print(f"Name: {channel.title}")
            print(f"ID: {channel.id}")
            print(f"Username: @{channel.username}")
        except Exception as e:
            print(f"Error getting channel: {e}")
            return
        
        # Get recent messages from last 2 hours
        recent_time = datetime.now() - timedelta(hours=2)
        print(f"\nGetting messages from last 2 hours...")
        
        messages = await client.get_messages(
            channel,
            limit=50,
            offset_date=recent_time
        )
        
        print(f"\nFound {len(messages)} recent messages:")
        print("=" * 80)
        
        for i, msg in enumerate(messages[:10]):  # Show first 10 messages
            if msg.message:
                print(f"\n--- Message {i+1} ---")
                print(f"Time: {msg.date.strftime('%H:%M:%S')}")
                print(f"Message: {msg.message[:200]}{'...' if len(msg.message) > 200 else ''}")
                print("-" * 40)
        
        # Listen for new messages
        print(f"\nListening for new messages... (Press Ctrl+C to stop)")
        
        @client.on(events.NewMessage(chats=channel))
        async def handler(event):
            print(f"\n{'='*60}")
            print(f"NEW MESSAGE at {event.message.date.strftime('%H:%M:%S')}")
            print(f"Content: {event.message.message}")
            print(f"{'='*60}")
            
            # Try to parse as signal
            message_text = event.message.message
            if message_text:
                print("\n--- Signal Analysis ---")
                
                # Look for asset patterns
                import re
                asset_patterns = [
                    r'Pair[:\s]*([A-Z]+/[A-Z]+(?:\s+OTC)?)',
                    r'([A-Z]+/[A-Z]+(?:\s+OTC)?)',
                    r'Asset[:\s]*([A-Z]+/[A-Z]+(?:\s+OTC)?)'
                ]
                
                for pattern in asset_patterns:
                    match = re.search(pattern, message_text, re.IGNORECASE)
                    if match:
                        print(f"Asset found: {match.group(1)}")
                        break
                
                # Look for direction
                if re.search(r'buy|call|up', message_text, re.IGNORECASE):
                    print("Direction: BUY/CALL")
                elif re.search(r'sell|put|down', message_text, re.IGNORECASE):
                    print("Direction: SELL/PUT")
                
                # Look for time/duration
                time_match = re.search(r'(\d+)\s*min', message_text, re.IGNORECASE)
                if time_match:
                    print(f"Duration: {time_match.group(1)} minutes")
                
                print("--- End Analysis ---")
        
        # Keep running
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()

if __name__ == "__main__":
    from telethon import events
    asyncio.run(monitor_channel())
