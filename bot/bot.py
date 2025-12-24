#!/usr/bin/env python3
"""
Telegram Ovoz Berish Boti
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)
from api_client import APIClient
from config import BOT_TOKEN, WELCOME_MESSAGE, SUBSCRIPTION_CONFIRMED, VOTE_SUCCESS, ALREADY_VOTED

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API klient
api = APIClient()

# Conversation states
CHECKING_SUBSCRIPTION, SELECTING_POLL, SELECTING_REGION, SELECTING_DISTRICT, SELECTING_CANDIDATE = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start komandasi - botni boshlash"""
    user = update.effective_user
    
    # Foydalanuvchini ro'yxatdan o'tkazish
    api.register_user(
        telegram_id=user.id,
        username=user.username or '',
        full_name=user.full_name
    )
    
    # Obuna holatini tekshirish (pollsiz)
    status = api.check_subscription(user.id)
    
    if status.get('is_subscribed'):
        # Agar obuna bo'lgan bo'lsa, so'rovnomalarni ko'rsatish
        return await show_polls(update, context)
    
    # Kanallarni ko'rsatish
    channels = api.get_channels()
    
    if not channels:
        # Kanal yo'q bo'lsa ham so'rovnomalarni ko'rsatish
        return await show_polls(update, context)
    
    message = WELCOME_MESSAGE
    keyboard = []
    
    for channel in channels:
        channel_username = channel['channel_username']
        if not channel_username.startswith('@'):
            channel_username = f"@{channel_username}"
        
        keyboard.append([
            InlineKeyboardButton(
                f"📢 {channel['title']}", 
                url=f"https://t.me/{channel_username.replace('@', '')}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subscription")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)
    
    return CHECKING_SUBSCRIPTION


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Obunani tekshirish"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Obunani tasdiqlash
    result = api.mark_subscribed(user.id)
    
    await query.edit_message_text(SUBSCRIPTION_CONFIRMED)
    
    # So'rovnomalarni ko'rsatish
    return await show_polls(update, context)


async def show_polls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """So'rovnomalarni ko'rsatish"""
    polls = api.get_polls()
    
    if not polls:
        message = "⚠️ Hozircha faol so'rovnomalar mavjud emas."
        if update.callback_query:
            await update.callback_query.message.reply_text(message)
        else:
            await update.message.reply_text(message)
        return ConversationHandler.END
    
    keyboard = []
    for poll in polls:
        status_icon = "🟢" if poll['is_open'] else "🔴"
        keyboard.append([
            InlineKeyboardButton(
                f"{status_icon} {poll['title']}", 
                callback_data=f"poll_{poll['id']}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "📋 Ovoz berish uchun so'rovnomani tanlang:"
    
    if update.callback_query:
        # Eski xabarni o'chirish yoki yangilash
        try:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
        except Exception:
             await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)
    
    return SELECTING_POLL


async def select_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """So'rovnoma tanlash"""
    query = update.callback_query
    await query.answer()
    
    poll_id = int(query.data.split('_')[1])
    context.user_data['poll_id'] = poll_id
    user = query.from_user
    
    # Poll holatini va user ovoz berganini tekshirish
    status = api.check_subscription(user.id, poll_id)
    
    if status.get('has_voted_in_poll'):
        await query.message.reply_text("⚠️ Siz bu so'rovnomada allaqachon ovoz bergansiz.")
        # Qaytib polls ro'yxatiga
        return await show_polls(update, context)
        
    # Viloyatlarni ko'rsatish (poll_id bilan)
    return await show_regions(update, context, poll_id)


async def show_regions(update: Update, context: ContextTypes.DEFAULT_TYPE, poll_id: int = None) -> int:
    """Viloyatlarni ko'rsatish"""
    if not poll_id:
        poll_id = context.user_data.get('poll_id')
        
    regions = api.get_regions(poll_id)
    
    if not regions:
        message = "⚠️ Bu so'rovnoma uchun viloyatlar mavjud emas."
        if update.callback_query:
            await update.callback_query.message.reply_text(message)
        else:
            await update.message.reply_text(message)
        return await show_polls(update, context) # Qaytish
    
    keyboard = []
    for region in regions:
        keyboard.append([
            InlineKeyboardButton(
                f"📍 {region['name']}", 
                callback_data=f"region_{region['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("◀️ So'rovnomalar", callback_data="back_to_polls")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "🗺 Viloyatingizni tanlang:"
    
    if update.callback_query:
        await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)
    
    return SELECTING_REGION


async def select_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Viloyat tanlash"""
    query = update.callback_query
    await query.answer()
    
    region_id = int(query.data.split('_')[1])
    context.user_data['region_id'] = region_id
    
    # Tumanlarni olish
    districts = api.get_districts_by_region(region_id)
    
    if not districts:
        await query.edit_message_text("⚠️ Bu viloyatda tumanlar mavjud emas.")
        return SELECTING_REGION # Viloyat tanlashda qolish
    
    keyboard = []
    for district in districts:
        keyboard.append([
            InlineKeyboardButton(
                f"🏘 {district['name']}", 
                callback_data=f"district_{district['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_regions")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🏘 Tumaningizni tanlang:", reply_markup=reply_markup)
    
    return SELECTING_DISTRICT


async def select_district(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tuman tanlash"""
    query = update.callback_query
    await query.answer()
    
    district_id = int(query.data.split('_')[1])
    context.user_data['district_id'] = district_id
    
    # Nomzodlarni olish
    candidates = api.get_candidates_by_district(district_id)
    
    if not candidates:
        await query.edit_message_text("⚠️ Bu tumanda nomzodlar mavjud emas.")
        return SELECTING_DISTRICT
    
    keyboard = []
    for candidate in candidates:
        keyboard.append([
            InlineKeyboardButton(
                f"👤 {candidate['full_name']}" + (f" - {candidate['position']}" if candidate.get('position') else ""),
                callback_data=f"candidate_{candidate['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_districts")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("👤 Nomzodni tanlang:", reply_markup=reply_markup)
    
    return SELECTING_CANDIDATE


async def select_candidate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nomzod tanlash va ovoz berish"""
    query = update.callback_query
    await query.answer()
    
    candidate_id = int(query.data.split('_')[1])
    poll_id = context.user_data.get('poll_id')
    user = query.from_user
    
    if not poll_id:
        await query.edit_message_text("⚠️ Xatolik: So'rovnoma topilmadi. Qayta urinib ko'ring.")
        return await show_polls(update, context)

    # Ovoz berish
    result = api.submit_vote(user.id, poll_id, candidate_id)
    
    if result.get('status') == 'success':
        await query.edit_message_text(f"{VOTE_SUCCESS}\n\nBoshqa so'rovnomalarda ham qatnashishingiz mumkin!")
        # Yana pollsga qaytish uchun tugma qo'shish mumkin
        keyboard = [[InlineKeyboardButton("📋 Boshqa so'rovnomalar", callback_data="back_to_polls")]]
        await query.message.reply_text("Boshqa so'rovnomalar:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        error_message = result.get('message', 'Xatolik yuz berdi!')
        await query.edit_message_text(f"❌ {error_message}")
        
        # Xatolik bo'lsa ham polllarga qaytish tugmasini ko'rsatish
        keyboard = [[InlineKeyboardButton("◀️ So'rovnomalar", callback_data="back_to_polls")]]
        await query.message.reply_text("Ortga qaytish:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    return SELECTING_POLL # Qayta poll tanlash rejimiga o'tadi


async def back_to_polls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Polllarga qaytish"""
    query = update.callback_query
    await query.answer()
    return await show_polls(update, context)


async def back_to_regions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Viloyatlarga qaytish"""
    query = update.callback_query
    await query.answer()
    poll_id = context.user_data.get('poll_id')
    return await show_regions(update, context, poll_id)


async def back_to_districts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tumanlarga qaytish"""
    query = update.callback_query
    await query.answer()
    
    region_id = context.user_data.get('region_id')
    if not region_id:
        # Agar region ID yo'qolgan bo'lsa, viloyatlarga qaytamiz
        poll_id = context.user_data.get('poll_id')
        return await show_regions(update, context, poll_id)
    
    # Tumanlarni olish
    districts = api.get_districts_by_region(region_id)
    
    keyboard = []
    for district in districts:
        keyboard.append([
            InlineKeyboardButton(
                f"🏘 {district['name']}", 
                callback_data=f"district_{district['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_regions")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🏘 Tumaningizni tanlang:", reply_markup=reply_markup)
    
    return SELECTING_DISTRICT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bekor qilish"""
    await update.message.reply_text("Jarayon bekor qilindi. /start ni bosing.")
    return ConversationHandler.END


def main() -> None:
    """Botni ishga tushirish"""
    # Application yaratish
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHECKING_SUBSCRIPTION: [
                CallbackQueryHandler(check_subscription_callback, pattern='^check_subscription$')
            ],
            SELECTING_POLL: [
                CallbackQueryHandler(select_poll, pattern='^poll_'),
                CallbackQueryHandler(back_to_polls, pattern='^back_to_polls$')
            ],
            SELECTING_REGION: [
                CallbackQueryHandler(select_region, pattern='^region_'),
                CallbackQueryHandler(back_to_polls, pattern='^back_to_polls$'),
                CallbackQueryHandler(show_polls, pattern='^back_to_polls$')
            ],
            SELECTING_DISTRICT: [
                CallbackQueryHandler(select_district, pattern='^district_'),
                CallbackQueryHandler(back_to_regions, pattern='^back_to_regions$'),
            ],
            SELECTING_CANDIDATE: [
                CallbackQueryHandler(select_candidate, pattern='^candidate_'),
                CallbackQueryHandler(back_to_districts, pattern='^back_to_districts$'),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start),
            CallbackQueryHandler(back_to_polls, pattern='^back_to_polls$')
        ],
        per_message=True,
    )
    
    application.add_handler(conv_handler)
    
    # Botni ishga tushirish
    logger.info("Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
