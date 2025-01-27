from telethon import TelegramClient
from dotenv import load_dotenv
import os

load_dotenv()

API_ID = int(os.getenv("API_ID_TELEGRAM"))
API_HASH = os.getenv("API_HASH_TELEGRAM")
SESSION_NAME = os.getenv("SESSION_NAME")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
async def list_groups():
    async for dialog in client.iter_dialogs():
        if dialog.is_group:  
            username = getattr(dialog.entity, "username", "N/A")  
            print(f"Nome: {dialog.name} | ID: {dialog.id} | Username: {username}")

if __name__ == "__main__":
    print("Listando os grupos...")
    with client:
        client.loop.run_until_complete(list_groups())
