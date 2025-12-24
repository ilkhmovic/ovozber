# Telegram Ovoz Berish Bot

Django va Telegram bot orqali ovoz berish tizimi.

## Xususiyatlar

- ✅ Django admin panel orqali ma'lumotlarni boshqarish
- ✅ REST API orqali bot va Django o'rtasida aloqa
- ✅ Telegram bot orqali ovoz berish
- ✅ Kanallarga obuna bo'lishni tekshirish
- ✅ Viloyat → Tuman → Nomzod ierarxiyasi
- ✅ Statistika va natijalarni ko'rish

## O'rnatish

### 1. Virtual muhitni yaratish

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows
```

### 2. Kutubxonalarni o'rnatish

```bash
pip install django djangorestframework python-telegram-bot requests pillow
```

### 3. Ma'lumotlar bazasini sozlash

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Bot tokenini sozlash

1. @BotFather ga murojaat qiling va yangi bot yarating
2. Bot tokenini oling
3. `bot/config.py` faylida `BOT_TOKEN` ni o'zgartiring yoki environment variable sifatida o'rnating:

```bash
export BOT_TOKEN="sizning_bot_tokeningiz"
```

## Ishga tushirish

### Django serverni ishga tushirish

```bash
python manage.py runserver
```

Admin panel: http://localhost:8000/admin
API: http://localhost:8000/api/

### Telegram botni ishga tushirish

Yangi terminal oching va:

```bash
cd bot
python bot.py
```

## Foydalanish

### Admin panel orqali

1. http://localhost:8000/admin ga kiring
2. Kanallar qo'shing (majburiy obuna uchun)
3. Viloyatlar qo'shing
4. Har bir viloyat uchun tumanlar qo'shing
5. Har bir tuman uchun nomzodlar qo'shing
6. Ovozlarni va statistikani ko'ring

### Telegram bot orqali

1. Botga `/start` yuboring
2. Ko'rsatilgan kanallarga obuna bo'ling
3. "Obunani tekshirish" tugmasini bosing
4. Viloyatingizni tanlang
5. Tumaningizni tanlang
6. Nomzodni tanlang va ovoz bering

## API Endpoints

- `GET /api/channels/` - Kanallar ro'yxati
- `GET /api/regions/` - Viloyatlar ro'yxati
- `GET /api/districts/` - Tumanlar ro'yxati
- `GET /api/candidates/` - Nomzodlar ro'yxati
- `POST /api/users/register/` - Foydalanuvchini ro'yxatdan o'tkazish
- `POST /api/votes/` - Ovoz berish
- `GET /api/statistics/` - Statistika

## Struktura

```
ovozber_1/
├── api/                    # Django app
│   ├── models.py          # Ma'lumotlar modellari
│   ├── admin.py           # Admin panel sozlamalari
│   ├── serializers.py     # DRF serializerlar
│   ├── views.py           # API views
│   └── urls.py            # API URLs
├── bot/                   # Telegram bot
│   ├── bot.py            # Asosiy bot kodi
│   ├── api_client.py     # API bilan aloqa
│   └── config.py         # Bot sozlamalari
├── ovozber/              # Django project
│   ├── settings.py       # Django sozlamalari
│   └── urls.py           # Asosiy URLs
└── manage.py
```

## Muhim eslatmalar

- Bir foydalanuvchi faqat bir marta ovoz berishi mumkin
- Ovoz bergandan keyin o'zgartirib bo'lmaydi
- Admin panel orqali ovozlarni o'chirish mumkin emas (faqat ko'rish)
- Barcha vaqtlar Asia/Tashkent timezone da saqlanadi

## Muammolarni hal qilish

### Bot ishlamayapti
- Bot tokenini tekshiring
- Django server ishlab turganini tekshiring
- API_BASE_URL to'g'ri sozlanganini tekshiring

### Ma'lumotlar ko'rinmayapti
- Migratsiyalarni bajardingizmi?
- Admin panelda ma'lumotlar `is_active=True` ekanini tekshiring

## Qo'shimcha imkoniyatlar

Kelajakda qo'shish mumkin:
- Haqiqiy kanal obunasini tekshirish
- Nomzodlar uchun rasm va biografiya ko'rsatish
- Real-time statistika
- Export qilish (Excel, PDF)
- Telegram Mini App integratsiyasi
