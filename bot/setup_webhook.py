import os
import sys
import requests
from decouple import config

# Add the project root to sys.path to access project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_webhook():
    print("--- Telegram Webhook Setup ---")
    
    # Get configuration from .env
    token = config('BOT_TOKEN', default='')
    if not token:
        print("Error: BOT_TOKEN not found in .env file.")
        return

    # Check for domain/host
    allowed_hosts = config('ALLOWED_HOSTS', default='')
    host = ""
    
    if allowed_hosts:
        # Take the first host from ALLOWED_HOSTS (usually comma-separated list)
        host = allowed_hosts.split(',')[0].strip()
        if host == '*':
            host = ""
    
    if not host:
        print("Warning: Could not determine host from ALLOWED_HOSTS.")
        host = input("Enter your public domain (e.g., yourname.pythonanywhere.com): ").strip()
    
    if not host:
        print("Error: Host is required for webhook setup.")
        return

    # Construct the webhook URL
    # The URL pattern in api/urls.py is: path('telegram/webhook/<str:token>/', telegram_webhook, name='telegram-webhook')
    webhook_url = f"https://{host}/api/telegram/webhook/{token}/"
    
    print(f"Token: {token[:10]}...{token[-5:]}")
    print(f"Host: {host}")
    print(f"Webhook URL: {webhook_url}")
    
    confirm = input(f"\nProceed with setting webhook to {webhook_url}? (y/n): ").lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    # Set webhook
    telegram_url = f"https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}"
    
    try:
        response = requests.get(telegram_url)
        result = response.json()
        
        if result.get('ok'):
            print("\n✅ Success! Webhook has been set.")
            print(f"Result: {result.get('description', 'OK')}")
        else:
            print("\n❌ Failed to set webhook.")
            print(f"Error Code: {result.get('error_code')}")
            print(f"Description: {result.get('description')}")
            
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    setup_webhook()
