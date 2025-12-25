"""Minimal webhook Application instance for processing Telegram updates inside Django."""
from bot.bot import create_application

# Create a single application instance for webhook usage
application = create_application()

# Expose bot for convenience
bot = application.bot
