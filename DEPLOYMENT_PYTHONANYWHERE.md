
# Ovozber Botini PythonAnywhere-ga Joylash Bo'yicha Qo'llanma

Ushbu qo'llanma Ovozber Django loyihasini va Telegram botini PythonAnywhere-ga joylash (deploy qilish) jarayonini tushuntiradi.

## 1. Talablar (Prerequisites)

-   PythonAnywhere akkaunti.
-   Loyihangiz kodi PythonAnywhere-ga yuklangan bo'lishi kerak (Git yoki ZIP orqali).
-   Telegram Bot Token (@BotFather dan olingan).

## 2. Muhitni Tayyorlash (Environment Setup)

1.  PythonAnywhere saytida **Console** (Terminal) bo'limini oching.
2.  **Virtual muhit (venv) yarating**:
    ```bash
    mkvirtualenv --python=/usr/bin/python3.10 myenv
    ```
    *(Eslatma: Agar kerak bo'lsa python versiyasini o'zgartiring, 3.10 tavsiya etiladi)*

3.  **Kutubxonalarni o'rnating**:
    `requirements.txt` fayli joylashgan papkaga kiring:
    ```bash
    cd ~/ovozber_1  # Papka nomini o'zingiznikiga moslang
    pip install -r requirements.txt
    ```

## 3. Loyiha Sozlamalari

1.  **Environment O'zgaruvchilar**:
    Loyiha asosiy papkasida `.env` faylini yarating (`~/ovozber_1/.env`).
    
    ```bash
    nano .env
    ```
    
    Quyidagi tarkibni qo'shing (O'zgaruvchilarni o'zingizga moslang):
    ```env
    DEBUG=False
    SECRET_KEY=sizning-maxfiy-kalitingiz
    ALLOWED_HOSTS=ovozber1234.pythonanywhere.com
    BOT_TOKEN=8573828164:AAG5EkPnpqinh_q8BCbUxCrcRn8SUuKz-IY
    BOT_USERNAME=bot_username_kuchukchasiz
    RUN_BOT_LOCAL=0
    DATABASE_URL=sqlite:////home/sizning_username/ovozber_1/db.sqlite3
    ```
    *`sizning_username` o'rniga PythonAnywhere usernameingizni yozing.*

2.  **Statik fayllarni yig'ish**:
    ```bash
    python manage.py collectstatic
    ```

3.  **Bazani migratsiya qilish**:
    ```bash
    python manage.py migrate
    ```

## 4. Web App Sozlamalari (PythonAnywhere saytida)

1.  **Web** bo'limiga o'ting.
2.  **Yangi web app qo'shing**:
    -   **Manual configuration** ni tanlang (chunki biz custom virtualenv ishlatyapmiz).
    -   **Python 3.10** ni tanlang (virtualenv versiyasi bilan bir xil bo'lsin).
3.  **Virtualenv**:
    -   Yo'lni kiriting: `/home/sizning_username/.virtualenvs/myenv`
4.  **Code (Kod)**:
    -   **Source code**: `/home/sizning_username/ovozber_1`
    -   **Working directory**: `/home/sizning_username/ovozber_1`
5.  **WSGI Konfiguratsiya Fayli**:
    -   WSGI faylini tahrirlash havolasini bosing.
    -   Tarkibini quyidagiga almashtiring:

    ```python
    import os
    import sys
    from pathlib import Path

    # Loyiha papkasini yo'lga qo'shish
    path = '/home/sizning_username/ovozber_1'  # O'ZGARTIRING
    if path not in sys.path:
        sys.path.append(path)

    # .env faylini yuklash
    from decouple import config
    
    # Django sozlamalarini ko'rsatish
    os.environ['DJANGO_SETTINGS_MODULE'] = 'ovozber.settings'
    
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    ```
    *`sizning_username` ni o'z usernameingizga almashtirishni unutmang.*

## 5. Webhookni O'rnatish

Web ilova ishga tushgandan so'ng (Web tabida "Reload" tugmasini bosing), Telegramga yangilanishlarni sizning saytingizga yuborishni buyurish kerak.

Ushbu oddiy skriptni PythonAnywhere konsolida (yoki tokenga ega bo'lsangiz o'z kompyuteringizda) yuriting:

```python
import requests

TOKEN = "8573828164:AAG5EkPnpqinh_q8BCbUxCrcRn8SUuKz-IY"
HOST = "ovozber1234.pythonanywhere.com"
URL = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://{HOST}/api/telegram/webhook/{TOKEN}/"

print(requests.get(URL).json())
```

Agar muvaffaqiyatli bo'lsa, `{'ok': True, 'result': True, ...}` javobini ko'rasiz.

## 6. Webhookni Qayta Sozlash (Reset)

Agar webhook xato ishlayotgan bo'lsa yoki tokenni o'zgartirsangiz, uni o'chirib qayta yoqish kerak:

```python
import requests

TOKEN = "8573828164:AAG5EkPnpqinh_q8BCbUxCrcRn8SUuKz-IY"
HOST = "ovozber1234.pythonanywhere.com"

# 1. Eski webhookni o'chirish
delete_url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
print("Delete:", requests.get(delete_url).json())

# 2. Yangi webhookni o'rnatish
set_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://{HOST}/api/telegram/webhook/{TOKEN}/"
print("Set:", requests.get(set_url).json())
```

## 7. Muammolarni Hal Qilish

-   **Loglarni tekshirish**: Web tabidagi **Server log** va **Error log** fayllarini tekshiring.
-   **Statik fayllar**: `STATIC_ROOT` sozlanganligiga va `collectstatic` qilinganligiga ishonch hosil qiling. Web tabida "Static files" bo'limida `/static/` -> `/home/sizning_username/ovozber_1/staticfiles` yo'naltirilgan bo'lishi kerak.
