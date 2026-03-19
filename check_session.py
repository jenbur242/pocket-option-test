import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

async def check_and_extract():
    load_dotenv()
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone_number = os.getenv('TELEGRAM_PHONE')
    
    print("Checking session file...")
    print(f"API ID: {api_id}")
    print(f"Phone: {phone_number}")
    
    client = TelegramClient('session_testpob1234', api_id, api_hash)
    
    try:
        await client.connect()
        print("✅ Connected to Telegram")
        
        if await client.is_user_authorized():
            print("✅ Session is authorized")
            
            # Get user info
            me = await client.get_me()
            print(f"User: {me.first_name} {me.last_name or ''}")
            print(f"Username: @{me.username}" if me.username else "No username")
            
            # Extract string session
            string_session = client.session.save()
            print(f"\nSTRING SESSION TOKEN:")
            print("=" * 50)
            print(string_session)
            print("=" * 50)
            
            # Save to file
            with open('string_session.txt', 'w') as f:
                f.write(string_session)
            print(f"\nSaved to: string_session.txt")
            
            print(f"\nAdd this to your .env file:")
            print(f"TELEGRAM_STRING_SESSION={string_session}")
            
        else:
            print("❌ Session is NOT authorized")
            print("Need to authenticate first!")
            
            # Try to authenticate
            print(f"\nTrying to authenticate with {phone_number}...")
            await client.send_code_request(phone_number)
            code = input("Enter verification code: ")
            
            try:
                await client.sign_in(phone_number, code)
                print("✅ Authentication successful!")
                
                # Now extract
                string_session = client.session.save()
                print(f"\nSTRING SESSION TOKEN:")
                print("=" * 50)
                print(string_session)
                print("=" * 50)
                
                with open('string_session.txt', 'w') as f:
                    f.write(string_session)
                print(f"\nSaved to: string_session.txt")
                
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_and_extract())
