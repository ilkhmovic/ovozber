# Bot konfiguratsiyasi
import os
from decouple import config

# Telegram Bot Token (@BotFather dan olinadi)
# TEST TOKEN (Local Environment) — for security prefer setting BOT_TOKEN via env variable
BOT_TOKEN = config('BOT_TOKEN', default='')

# Bot username (e.g., 'ovozberbot', without @)
BOT_USERNAME = config('BOT_USERNAME', default='ovozberbot')

# Run bot only in local/dev environment when this is set to '1' or 'true'. Set to '0' in production to prevent polling.
RUN_BOT_LOCAL = config('RUN_BOT_LOCAL', default='1')

# Django API URL
API_BASE_URL = config('API_BASE_URL', default='http://localhost:8000/api')

# Bot sozlamalasri
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

REFER_FRIENDS_MESSAGE = """
👥 Dostlarni taklif qilish

Bu havola orqali o'z dostlaringizni taklif etishingiz mumkin:

🔗 [Bot havolasini ulashing](https://t.me/{BOT_USERNAME}?start=referred)

Yoki quyidagi tugma orqali:
"""
