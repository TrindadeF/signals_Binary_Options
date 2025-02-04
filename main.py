import asyncio
import logging
from telegram_handler import TelegramHandler
from iq_handler import IQHandler
from telethon import TelegramClient
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

API_ID = int(os.getenv("API_ID_TELEGRAM"))
API_HASH = os.getenv("API_HASH_TELEGRAM")
SESSION_NAME = os.getenv("SESSION_NAME")

async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    iq_handler = IQHandler()
    

    if not await iq_handler.connect():
        logger.error("❌ Não foi possível iniciar conexão com IQ Option")
        await client.disconnect()
        return

    telegram_handler = TelegramHandler(client, iq_handler)

    try:
        logger.info("🚀 Iniciando bot...")
        await telegram_handler.start()
    except KeyboardInterrupt:
        logger.warning("❌ Bot interrompido pelo usuário")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
