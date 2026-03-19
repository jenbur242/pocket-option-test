import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

async def extract_session():
    load_dotenv()
    client = TelegramClient('session_testpob1234', os.getenv('TELEGRAM_API_ID'), os.getenv('TELEGRAM_API_HASH'))
    await client.connect()
    if await client.is_user_authorized():
        print('SESSION:', client.session.save())
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(extract_session())
