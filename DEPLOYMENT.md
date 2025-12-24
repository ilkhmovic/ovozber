# Railway Deployment Guide

## Qadamlar

### 1. Railway Account Yaratish

1. https://railway.app ga o'ting
2. GitHub bilan ro'yxatdan o'ting
3. Dashboard ga kiring

### 2. Yangi Project Yaratish

1. "New Project" tugmasini bosing
2. "Deploy from GitHub repo" ni tanlang
3. `ilkhmovic/ovozber` repository ni tanlang
4. Railway avtomatik deploy qilishni boshlaydi

### 3. PostgreSQL Database Qo'shish

1. Project dashboardda "New" tugmasini bosing
2. "Database" → "Add PostgreSQL" ni tanlang
3. Railway avtomatik `DATABASE_URL` environment variable yaratadi

### 4. Environment Variables Sozlash

Project Settings → Variables bo'limida quyidagilarni qo'shing:

```
SECRET_KEY=<yangi-random-secret-key>
DEBUG=False
ALLOWED_HOSTS=.railway.app
BOT_TOKEN=<telegram-bot-tokeningiz>
```

**SECRET_KEY yaratish:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Deploy Settings

Railway avtomatik `Procfile` ni topadi va ikkita service yaratadi:
- **web**: Django server (gunicorn)
- **worker**: Telegram bot

### 6. Migrations Ishga Tushirish

Deploy tugagandan keyin:

1. Project Settings → "Deploy" tab
2. "Run Command" tugmasini bosing
3. Quyidagi commandni kiriting:
```bash
python manage.py migrate
```

### 7. Superuser Yaratish

1. Railway CLI o'rnating:
```bash
npm i -g @railway/cli
```

2. Login qiling:
```bash
railway login
```

3. Project ga ulaning:
```bash
railway link
```

4. Superuser yarating:
```bash
railway run python manage.py createsuperuser
```

### 8. Static Files Yig'ish

```bash
railway run python manage.py collectstatic --noinput
```

### 9. Bot Tokenini Yangilash

`bot/config.py` da API_BASE_URL ni Railway URL ga o'zgartiring:

```python
API_BASE_URL = os.getenv('API_BASE_URL', 'https://your-app.railway.app/api')
```

### 10. Tekshirish

1. **Django Admin**: `https://your-app.railway.app/admin`
2. **API**: `https://your-app.railway.app/api/`
3. **Bot**: Telegram da botga `/start` yuboring

## Muhim Eslatmalar

### Railway Bepul Tier

- $5 credit har oyda
- 500 soat execution time
- PostgreSQL 1GB storage
- Yetarli kichik loyihalar uchun

### Monitoring

Railway dashboardda:
- Deployment logs
- Resource usage
- Database metrics

### Troubleshooting

**Deploy muvaffaqiyatsiz bo'lsa:**
1. Build logs ni tekshiring
2. Environment variables to'g'ri sozlanganini tekshiring
3. `requirements.txt` da barcha dependencies borligini tekshiring

**Bot ishlamasa:**
1. Worker logs ni tekshiring
2. BOT_TOKEN to'g'ri ekanini tekshiring
3. API_BASE_URL to'g'ri Railway URL ekanini tekshiring

**Database xatoliklari:**
1. Migrations bajarilganini tekshiring
2. DATABASE_URL avtomatik sozlanganini tekshiring

## Custom Domain (Ixtiyoriy)

1. Project Settings → Domains
2. "Custom Domain" qo'shing
3. DNS sozlamalarini yangilang

## Backup

PostgreSQL backup:
```bash
railway run pg_dump $DATABASE_URL > backup.sql
```

## Yangilash

Har safar GitHub ga push qilganingizda Railway avtomatik deploy qiladi:

```bash
git add .
git commit -m "Update"
git push origin main
```

## Qo'shimcha Resurslar

- Railway Docs: https://docs.railway.app
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/
- Telegram Bot API: https://core.telegram.org/bots/api
