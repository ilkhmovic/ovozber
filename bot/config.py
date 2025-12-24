# Bot konfiguratsiyasi
import os

# Telegram Bot Token (@BotFather dan olinadi)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8573828164:AAFccyUo3yCnUh8VKntYwRJTj35kxJk9HxQ')

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
