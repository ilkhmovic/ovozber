# Bot konfiguratsiyasi
import os

# Telegram Bot Token (@BotFather dan olinadi)
# TEST TOKEN (Local Environment) — for security prefer setting BOT_TOKEN via env variable
BOT_TOKEN = os.getenv('BOT_TOKEN', '8338934458:AAFWEe8mGJ-vMKxPactZQURr170m7ALVn9E')

# Run bot only in local/dev environment when this is set to '1' or 'true'. Set to '0' in production to prevent polling.
RUN_BOT_LOCAL = os.getenv('RUN_BOT_LOCAL', '1')

# Django API URL
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api')

# Bot sozlamalari
WELCOME_MESSAGE = """
🗳 Assalomu alaykum!

Ovoz berish tizimiga xush kelibsiz!

Davom etish uchun quyidagi kanallarga obuna bo'lishingiz kerak:
"""

SUBSCRIPTION_CONFIRMED = """
✅ Obuna tasdiqlandi!

Endi siz ovoz berishingiz mumkin. Quyidagi tugmalardan birini tanlang:
"""

VOTE_SUCCESS = """
✅ Ovozingiz muvaffaqiyatli qabul qilindi!

Ishtirok etganingiz uchun rahmat! 🎉
"""

ALREADY_VOTED = """
⚠️ Siz bu so'rovnomada allaqachon ovoz bergansiz!

Siz boshqa faol so'rovnomalarda qatnashishingiz mumkin.
"""
