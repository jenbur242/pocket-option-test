import asyncio
import os
from telethon.sync import TelegramClient
from dotenv import load_dotenv

async def get_channel_info():
    load_dotenv()
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    client = TelegramClient('session_testpob1234', api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        print('Not authorized!')
        return
    
    try:
        # Get channel info
        channel = await client.get_entity('t.me/Pocket_Option_Signals_Vip')
        print(f'Channel ID: {channel.id}')
        print(f'Channel Title: {channel.title}')
        print(f'Channel Username: {channel.username}')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(get_channel_info())
