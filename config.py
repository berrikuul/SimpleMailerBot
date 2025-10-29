import os
from dotenv import load_dotenv

load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_USERNAMES = [username.strip() for username in os.getenv('ADMIN_USERNAMES', '').split(',') if username.strip()]
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
GROUP_LINK = os.getenv('GROUP_LINK')

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле")

if not ADMIN_USERNAMES:
    raise ValueError("❌ ADMIN_USERNAMES не найден в .env файле")

if not GROUP_CHAT_ID:
    raise ValueError("❌ GROUP_CHAT_ID не найден в .env файле")

print(f"✅ Загружены админы: {ADMIN_USERNAMES}")