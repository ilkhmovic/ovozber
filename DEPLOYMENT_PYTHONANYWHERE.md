
# Deploying Ovozber Bot on PythonAnywhere

This guide describes how to deploy the Ovozber Django project and Telegram bot to PythonAnywhere.

## 1. Prerequisites

-   A PythonAnywhere account.
-   Your project code uploaded to PythonAnywhere (via Git or ZIP).
-   A Telegram Bot Token (from @BotFather).

## 2. Environment Setup

1.  **Open a Console** on PythonAnywhere.
2.  **Create a Virtual Environment**:
    ```bash
    mkvirtualenv --python=/usr/bin/python3.10 myenv
    ```
    *(Note: Adjust python version if needed, 3.10 is recommended)*

3.  **Install Dependencies**:
    Navigate to your project folder where `requirements.txt` is located:
    ```bash
    cd ~/ovozber_1  # Adjust path as necessary
    pip install -r requirements.txt
    ```

## 3. Project Configuration

1.  **Environment Variables**:
    Create a `.env` file in your project root (`~/ovozber_1/.env`).
    
    ```bash
    nano .env
    ```
    
    Add the following content (Adjust values):
    ```env
    DEBUG=False
    SECRET_KEY=your-secure-secret-key
    ALLOWED_HOSTS=ovozber1234.pythonanywhere.com
    BOT_TOKEN=8573828164:AAG5EkPnpqinh_q8BCbUxCrcRn8SUuKz-IY
    BOT_USERNAME=your_bot_username_without_at
    RUN_BOT_LOCAL=0
    DATABASE_URL=sqlite:////home/yourusername/ovozber_1/db.sqlite3
    ```
    *Replace `yourusername` with your PythonAnywhere username.*

2.  **Collect Static Files**:
    ```bash
    python manage.py collectstatic
    ```

3.  **Migrate Database**:
    ```bash
    python manage.py migrate
    ```

## 4. Web App Configuration (on PythonAnywhere Dashboard)

1.  Go to the **Web** tab.
2.  **Add a new web app**:
    -   Select **Manual configuration** (since we are using a custom virtualenv).
    -   Select **Python 3.10** (matching your virtualenv).
3.  **Virtualenv**:
    -   Enter the path: `/home/yourusername/.virtualenvs/myenv`
4.  **Code**:
    -   **Source code**: `/home/yourusername/ovozber_1`
    -   **Working directory**: `/home/yourusername/ovozber_1`
5.  **WSGI Configuration File**:
    -   Click the link to edit the WSGI file.
    -   Replace the contents with:

    ```python
    import os
    import sys
    from pathlib import Path

    # Expand the path to include the project directory
    path = '/home/yourusername/ovozber_1'  # CHANGE THIS
    if path not in sys.path:
        sys.path.append(path)

    # Load .env file
    from decouple import config
    # You might need to manually load .env if python-decouple doesn't find it automatically in WSGI 
    # Or just rely on os.environ if set otherwise. 
    # Better approach for PA:
    
    os.environ['DJANGO_SETTINGS_MODULE'] = 'ovozber.settings'
    
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    ```
    *Make sure to change `yourusername`.*

## 5. Setting the Webhook

Once the web app is running (click "Reload" on the Web tab), you need to tell Telegram to send updates to your URL.

Run this simple script in your PythonAnywhere console (or local terminal if you have the token):

```python
import requests

TOKEN = "8573828164:AAG5EkPnpqinh_q8BCbUxCrcRn8SUuKz-IY"
HOST = "ovozber1234.pythonanywhere.com"
URL = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://{HOST}/api/telegram/webhook/{TOKEN}/"

print(requests.get(URL).json())
```

If successful, you should see `{'ok': True, 'result': True, ...}`.

## 6. Troubleshooting

-   **Check Logs**: Look at the **Server log** and **Error log** on the Web tab.
-   **Static Files**: Ensure `STATIC_ROOT` is set and you've run `collectstatic`. mapping `/static/` -> `/home/yourusername/ovozber_1/staticfiles` in the Web tab "Static files" section is also good practice.
