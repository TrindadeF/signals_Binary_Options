import asyncio
from telegram_handler import TelegramHandler
from iq_handler import IQHandler
from telethon import TelegramClient
from dotenv import load_dotenv
import os

load_dotenv()

API_ID = int(os.getenv("API_ID_TELEGRAM"))
API_HASH = os.getenv("API_HASH_TELEGRAM")
SESSION_NAME = os.getenv("SESSION_NAME")

async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    iq_handler = IQHandler()
    telegram_handler = TelegramHandler(client, iq_handler)

    print("Iniciando bot...")
    await telegram_handler.start()

if __name__ == "__main__":
    asyncio.run(main())