# Render.com Deployment Guide

## Render.com haqida

Render - zamonaviy cloud platform:
- ✅ **Bepul tier** - 750 soat/oy
- ✅ **PostgreSQL** bepul (90 kun)
- ✅ **Auto-deploy** GitHub dan
- ✅ **SSL** bepul
- ✅ **Oson sozlash**

---

## Deployment Qadamlari

### 1️⃣ Render Account Yaratish

1. https://render.com ga o'ting
2. **"Get Started for Free"** tugmasini bosing
3. **GitHub** bilan ro'yxatdan o'ting

### 2️⃣ Blueprint Deploy (Tavsiya etiladi)

Render `render.yaml` faylini avtomatik o'qiydi va barcha servicelarni yaratadi.

1. Dashboard da **"New +"** → **"Blueprint"** ni tanlang
2. **GitHub repository** ni ulang: `ilkhmovic/ovozber`
3. **Blueprint Name**: `ovozber`
4. **Apply** tugmasini bosing

Render avtomatik yaratadi:
- ✅ Web service (Django)
- ✅ Worker service (Telegram bot)
- ✅ PostgreSQL database

### 3️⃣ Manual Deploy (Alternativ)

Agar Blueprint ishlamasa, qo'lda yarating:

#### A. PostgreSQL Database

1. **"New +"** → **"PostgreSQL"**
2. **Name**: `ovozber-db`
3. **Database**: `ovozber`
4. **User**: `ovozber`
5. **Region**: Frankfurt (yoki yaqin)
6. **Plan**: Free
7. **Create Database**

#### B. Web Service

1. **"New +"** → **"Web Service"**
2. **Connect repository**: `ilkhmovic/ovozber`
3. **Name**: `ovozber-web`
4. **Runtime**: Python 3
5. **Build Command**: `./build.sh`
6. **Start Command**: `gunicorn ovozber.wsgi:application`
7. **Plan**: Free
8. **Create Web Service**

#### C. Background Worker

1. **"New +"** → **"Background Worker"**
2. **Connect repository**: `ilkhmovic/ovozber`
3. **Name**: `ovozber-bot`
4. **Runtime**: Python 3
5. **Build Command**: `pip install -r requirements.txt`
6. **Start Command**: `cd bot && python bot.py`
7. **Plan**: Free
8. **Create Background Worker**

### 4️⃣ Environment Variables

Har bir service uchun Environment variables sozlang:

#### Web Service Variables:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.13.1` |
| `SECRET_KEY` | `<random-secret-key>` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `DATABASE_URL` | `<postgres-connection-string>` |

#### Worker Service Variables:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.13.1` |
| `BOT_TOKEN` | `8573828164:AAF...` |
| `API_BASE_URL` | `https://ovozber-web.onrender.com/api` |
| `DATABASE_URL` | `<postgres-connection-string>` |

**SECRET_KEY yaratish:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**DATABASE_URL olish:**
1. PostgreSQL service ni oching
2. **"Connections"** tabda **Internal Database URL** ni nusxalang
3. Web va Worker servicelarga qo'shing

### 5️⃣ Deploy Monitoring

1. Har bir service da **"Logs"** tabni oching
2. Build va deploy jarayonini kuzating
3. Xatolik bo'lsa, logs ni o'qing

### 6️⃣ Database Migrations

Render avtomatik `build.sh` da migrations bajaradi:
```bash
python manage.py migrate
```

Agar qo'lda bajarish kerak bo'lsa:
1. Web service → **"Shell"** tab
2. Command: `python manage.py migrate`

### 7️⃣ Superuser Yaratish

Web service Shell da:
```bash
python manage.py createsuperuser
```

Yoki Python shell orqali:
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
User.objects.create_superuser('admin', 'admin@example.com', 'password123')
```

### 8️⃣ Static Files

`build.sh` avtomatik bajaradi:
```bash
python manage.py collectstatic --noinput
```

### 9️⃣ Tekshirish

#### Django Admin:
```
https://ovozber-web.onrender.com/admin
```

#### API:
```
https://ovozber-web.onrender.com/api/regions/
https://ovozber-web.onrender.com/api/statistics/
```

#### Telegram Bot:
1. Telegram da botga `/start` yuboring
2. Ovoz berish jarayonini sinab ko'ring

---

## Render Xususiyatlari

### ✅ Bepul Tier

**Web Service:**
- 750 soat/oy
- 512 MB RAM
- Shared CPU
- Auto-sleep (15 daqiqa faoliyatsizlikdan keyin)

**PostgreSQL:**
- 1 GB storage
- 90 kun bepul
- Keyin $7/oy

**Background Worker:**
- 750 soat/oy
- 512 MB RAM

### 🔄 Auto-Deploy

Har safar GitHub ga push qilganingizda avtomatik deploy:
```bash
git add .
git commit -m "Update"
git push origin main
```

### 📊 Monitoring

**Metrics:**
- CPU usage
- Memory usage
- Response time
- Request count

**Logs:**
- Real-time logs
- Log search
- Download logs

### 🔒 Security

- ✅ Free SSL/TLS
- ✅ DDoS protection
- ✅ Auto-backups (PostgreSQL)

---

## Troubleshooting

### ❌ Build Failed

**Xatolik:** `requirements.txt` topilmadi

**Yechim:**
- Repository to'g'ri ulanganini tekshiring
- Branch `main` ekanini tekshiring

### ❌ Database Connection Error

**Xatolik:** `could not connect to server`

**Yechim:**
1. `DATABASE_URL` to'g'ri ekanini tekshiring
2. PostgreSQL service ishlab turganini tekshiring
3. Internal Database URL ishlatilganini tekshiring (External emas)

### ❌ Static Files 404

**Xatolik:** CSS/JS yuklanmayapti

**Yechim:**
1. `build.sh` bajarilganini tekshiring
2. `STATIC_ROOT` to'g'ri sozlanganini tekshiring
3. WhiteNoise middleware qo'shilganini tekshiring

### ❌ Service Sleeping

**Muammo:** Bepul tier 15 daqiqa faoliyatsizlikdan keyin uxlaydi

**Yechim:**
- Birinchi so'rov 30-60 soniya olishi mumkin
- Paid plan ga o'ting ($7/oy) auto-sleep ni o'chirish uchun
- Yoki cron job bilan ping qiling

### ❌ Bot Ishlamayapti

**Sabab 1:** Worker service to'xtatilgan
- Worker service ni restart qiling

**Sabab 2:** API_BASE_URL noto'g'ri
- Render URL ni to'g'ri kiriting

**Sabab 3:** BOT_TOKEN noto'g'ri
- Environment variables ni tekshiring

---

## Render vs Railway

| Xususiyat | Render | Railway |
|-----------|--------|---------|
| Bepul tier | 750 soat/oy | $5 credit/oy |
| PostgreSQL | 90 kun bepul | Bepul |
| Auto-sleep | Ha (15 min) | Yo'q |
| Deploy tezligi | O'rtacha | Tez |
| Logs | Yaxshi | Juda yaxshi |
| UI | Sodda | Zamonaviy |

---

## Keyingi Qadamlar

### 1. Test Ma'lumotlari

Admin panelda:
1. Kanallar qo'shing
2. Viloyatlar qo'shing
3. Tumanlar qo'shing
4. Nomzodlar qo'shing

### 2. Custom Domain (Ixtiyoriy)

1. Service Settings → **"Custom Domain"**
2. Domain qo'shing (masalan: `ovozber.uz`)
3. DNS sozlamalarini yangilang

### 3. Monitoring

**UptimeRobot** yoki **Pingdom** bilan monitoring:
- Service availability
- Response time
- Downtime alerts

### 4. Backup

PostgreSQL backup:
1. Database Settings → **"Backups"**
2. Manual backup yarating
3. Yoki avtomatik backup sozlang

---

## Render CLI (Ixtiyoriy)

```bash
# O'rnatish
npm install -g render-cli

# Login
render login

# Services ro'yxati
render services list

# Logs
render logs <service-id>

# Shell
render shell <service-id>
```

---

## Xulosa

✅ Render.com - oson va ishonchli platform
✅ Bepul tier yetarli kichik loyihalar uchun
✅ Auto-deploy GitHub dan
✅ PostgreSQL bepul (90 kun)

**Keyingi qadam:** Render.com da account yarating va Blueprint deploy qiling!

## Foydali Havolalar

- Render Dashboard: https://dashboard.render.com
- Render Docs: https://render.com/docs
- Render Status: https://status.render.com
