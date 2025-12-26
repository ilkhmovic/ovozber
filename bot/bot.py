from pathlib import Path
import os
import logging
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, PicklePersistence
)
from bot.api_client import APIClient
from bot.config import (
    BOT_TOKEN, BOT_USERNAME, WELCOME_MESSAGE, SUBSCRIPTION_CONFIRMED, 
    VOTE_SUCCESS, ALREADY_VOTED, RUN_BOT_LOCAL, REFER_FRIENDS_MESSAGE
)

# Base directory for persistence
BASE_DIR = Path(__file__).resolve().parent.parent

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
    
    keyboard.append([
        InlineKeyboardButton("👥 Dostlarni taklif qilish", callback_data="refer_friends")
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
    
    try:
        await query.edit_message_text(SUBSCRIPTION_CONFIRMED)
    except Exception as e:
        logger.error(f"Edit message error: {e}")
        try:
            await query.message.delete()
        except:
            pass
        await query.message.chat.send_message(SUBSCRIPTION_CONFIRMED)
    
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
    
    # Add refer friends button
    keyboard.append([
        InlineKeyboardButton("👥 Dostlarni taklif qilish", callback_data="refer_friends")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "📋 Ovoz berish uchun so'rovnomani tanlang:"
    
    if update.callback_query:
        # Eski xabarni o'chirish yoki yangilash
        try:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Edit message error: {e}")
            try:
                await update.callback_query.message.delete()
            except:
                pass
            await update.callback_query.message.chat.send_message(message, reply_markup=reply_markup)
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


async def refer_friends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Dostlarni taklif qilish"""
    query = update.callback_query
    await query.answer()
    
    # Create share button with bot link
    keyboard = [
        [
            InlineKeyboardButton(
                "📤 Chatga yuborish",
                switch_inline_query=f"Ovoz berish botiga qatnashish: https://t.me/{BOT_USERNAME}?start=referred"
            )
        ],
        [
            InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_refer")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = f"""👥 Dostlarni taklif qilish

Quyidagi tugma orqali o'z dostlaringizni taklif etishingiz mumkin:

🔗 Bot havolasi: https://t.me/{BOT_USERNAME}

'📤 Chatga yuborish' tugmasini bosing va istalgan chatni tanlang."""
    
    try:
        await query.edit_message_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Edit message error: {e}")
        try:
            await query.message.delete()
        except:
            pass
        await query.message.chat.send_message(message, reply_markup=reply_markup)
    return SELECTING_POLL


async def back_to_refer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Refer menyusidan orqaga qaytish"""
    query = update.callback_query
    await query.answer()
    
    # Eski holatga qaytish
    return await show_polls(update, context)


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
        try:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Edit message error: {e}")
            try:
                await update.callback_query.message.delete()
            except:
                pass
            await update.callback_query.message.chat.send_message(message, reply_markup=reply_markup)
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
        try:
            await query.edit_message_text("⚠️ Bu viloyatda tumanlar mavjud emas.")
        except Exception as e:
            logger.error(f"Edit message error: {e}")
            try:
                await query.message.delete()
            except:
                pass
            await query.message.chat.send_message("⚠️ Bu viloyatda tumanlar mavjud emas.")
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
    message = "🏘 Tumaningizni tanlang:"
    
    try:
        await query.edit_message_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Edit message error: {e}")
        try:
            await query.message.delete()
        except:
            pass
        await query.message.chat.send_message(message, reply_markup=reply_markup)
    
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
        try:
            await query.edit_message_text("⚠️ Bu tumanda nomzodlar mavjud emas.")
        except Exception as e:
            logger.error(f"Edit message error: {e}")
            try:
                await query.message.delete()
            except:
                pass
            await query.message.chat.send_message("⚠️ Bu tumanda nomzodlar mavjud emas.")
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
    message = "👤 Nomzodni tanlang:"
    
    try:
        await query.edit_message_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Edit message error: {e}")
        try:
            await query.message.delete()
        except:
            pass
        await query.message.chat.send_message(message, reply_markup=reply_markup)
    
    return SELECTING_CANDIDATE


async def select_candidate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nomzod tanlash - ma'lumotlarini ko'rsatish"""
    query = update.callback_query
    await query.answer()
    
    candidate_id = int(query.data.split('_')[1])
    context.user_data['candidate_id'] = candidate_id
    poll_id = context.user_data.get('poll_id')
    
    if not poll_id:
        try:
            await query.edit_message_text("⚠️ Xatolik: So'rovnoma topilmadi. Qayta urinib ko'ring.")
        except Exception as e:
            logger.error(f"Edit message error: {e}")
            try:
                await query.message.delete()
            except:
                pass
            await query.message.chat.send_message("⚠️ Xatolik: So'rovnoma topilmadi. Qayta urinib ko'ring.")
        return await show_polls(update, context)
    
    # Nomzod ma'lumotlarini olish
    candidate = api.get_candidate_detail(candidate_id)
    logger.info(f"Candidate {candidate_id} details: {candidate}")
    
    if not candidate or 'full_name' not in candidate:
        logger.warning(f"Candidate details not found or empty: {candidate}")
        try:
            await query.edit_message_text("⚠️ Nomzod ma'lumotlari topilmadi.")
        except Exception as e:
            logger.error(f"Edit message error: {e}")
            try:
                await query.message.delete()
            except:
                pass
            await query.message.chat.send_message("⚠️ Nomzod ma'lumotlari topilmadi.")
        return SELECTING_CANDIDATE
    
    # Nomzod ma'lumotlarini tayyorlash
    full_name = candidate.get('full_name', 'Nomalum')
    position = candidate.get('position', '')
    biography = candidate.get('bio', candidate.get('biography', ''))  # 'bio' yoki 'biography'
    photo_url = candidate.get('photo', '')
    
    # Xabar tayyorlash
    message = f"👤 <b>{full_name}</b>"
    if position:
        message += f"\n📍 {position}"
    if biography:
        message += f"\n\n📋 Biografiya:\n{biography}"
    
    # Tugmalar
    keyboard = [
        [
            InlineKeyboardButton("✅ Ovoz berish", callback_data=f"vote_{candidate_id}"),
            InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_districts")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Rasmni download qilib yuborish (agar mavjud bo'lsa)
    if photo_url and isinstance(photo_url, str) and len(photo_url) > 5:
        try:
            photo_bytes = api.download_photo(photo_url)
            if photo_bytes:
                photo_file = BytesIO(photo_bytes)
                photo_file.name = f"candidate_{candidate_id}.jpg"
                # Eski xabarni o'chir va rasmli xabar jo'nat
                try:
                    await query.message.delete()
                except:
                    pass
                await query.message.chat.send_photo(
                    photo=photo_file,
                    caption=message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                return SELECTING_CANDIDATE
        except Exception as e:
            logger.error(f"Photo send error: {e}")
            # Rasm xato bo'lsa, faqat matn ko'rsatamiz
            pass
    
    # Agar rasm bo'lmasa yoki rasm yuborish xato bo'lsa, matnli xabar ko'rsatish
    try:
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Message edit error: {e}")
        # Agar edit xato bo'lsa, yangi xabar jo'natamiz
        try:
            await query.message.delete()
        except:
            pass
        await query.message.chat.send_message(message, parse_mode='HTML', reply_markup=reply_markup)
    
    return SELECTING_CANDIDATE


async def submit_vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ovoz berish"""
    query = update.callback_query
    await query.answer()
    
    candidate_id = int(query.data.split('_')[1])
    poll_id = context.user_data.get('poll_id')
    user = query.from_user
    
    if not poll_id:
        try:
            await query.edit_message_text("⚠️ Xatolik: So'rovnoma topilmadi.")
        except:
            await query.message.delete()
            await query.message.chat.send_message("⚠️ Xatolik: So'rovnoma topilmadi.")
        return await show_polls(update, context)
    
    # Ovoz berish
    result = api.submit_vote(user.id, poll_id, candidate_id)
    
    try:
        # Eski xabarni o'chir
        await query.message.delete()
    except:
        pass
    
    if result.get('status') == 'success':
        message = f"✅ {VOTE_SUCCESS}\n\nBoshqa so'rovnomalarda ham qatnashishingiz mumkin!"
        keyboard = [[InlineKeyboardButton("📋 Boshqa so'rovnomalar", callback_data="back_to_polls")]]
        try:
            await query.message.chat.send_message(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        except Exception as e:
            logger.error(f"Send success message failed: {e}")
            try:
                await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            except Exception as e2:
                logger.error(f"Fallback send failed: {e2}")
    else:
        # Try to extract server provided error message
        error_message = result.get('message') if isinstance(result, dict) else None
        if not error_message:
            # Many DRF validation errors come back in non_field_errors list
            non_field = result.get('non_field_errors') if isinstance(result, dict) else None
            if non_field and isinstance(non_field, list):
                error_message = non_field[0]
        if not error_message:
            error_message = 'Xatolik yuz berdi!'
        message = f"❌ {error_message}"
        # Xatolik bo'lsa ham polllarga qaytish tugmasini ko'rsatish
        keyboard = [[InlineKeyboardButton("◀️ So'rovnomalar", callback_data="back_to_polls")]]
        try:
            await query.message.chat.send_message(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        except Exception as e:
            logger.error(f"Send error message failed: {e}")
            try:
                await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            except Exception as e2:
                logger.error(f"Fallback error send failed: {e2}")
    
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
    message = "🏘 Tumaningizni tanlang:"
    
    # Try to edit, if it fails (e.g., photo message), delete and send new message
    try:
        await query.edit_message_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Edit message error: {e}")
        try:
            await query.message.delete()
        except:
            pass
        await query.message.chat.send_message(message, reply_markup=reply_markup)
    
    return SELECTING_DISTRICT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bekor qilish"""
    await update.message.reply_text("Jarayon bekor qilindi. /start ni bosing.")
    return ConversationHandler.END


def create_application() -> Application:
    """Create and return a configured Application instance (no polling started)."""
    # Persistence setup for webhook mode
    persistence = PicklePersistence(filepath=os.path.join(BASE_DIR, "bot_state.pickle"))
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .build()
    )

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(refer_friends, pattern='^refer_friends$'),
            CallbackQueryHandler(check_subscription_callback, pattern='^check_subscription$'),
            CallbackQueryHandler(select_poll, pattern='^poll_'),
            CallbackQueryHandler(select_region, pattern='^region_'),
            CallbackQueryHandler(select_district, pattern='^district_'),
            CallbackQueryHandler(select_candidate, pattern='^candidate_'),
            CallbackQueryHandler(submit_vote, pattern='^vote_'),
        ],
        states={
            CHECKING_SUBSCRIPTION: [
                CallbackQueryHandler(check_subscription_callback, pattern='^check_subscription$'),
                CallbackQueryHandler(refer_friends, pattern='^refer_friends$')
            ],
            SELECTING_POLL: [
                CallbackQueryHandler(select_poll, pattern='^poll_'),
                CallbackQueryHandler(refer_friends, pattern='^refer_friends$'),
                CallbackQueryHandler(back_to_refer, pattern='^back_to_refer$'),
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
                CallbackQueryHandler(submit_vote, pattern='^vote_'),
                CallbackQueryHandler(back_to_districts, pattern='^back_to_districts$'),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start),
            CallbackQueryHandler(back_to_polls, pattern='^back_to_polls$'),
            CallbackQueryHandler(refer_friends, pattern='^refer_friends$'),
            CallbackQueryHandler(check_subscription_callback, pattern='^check_subscription$'),
            CallbackQueryHandler(show_polls, pattern='^back_to_polls$')
        ]
    )

    application.add_handler(conv_handler)
    return application


def main() -> None:
    """Botni ishga tushirish (local polling)"""
    application = create_application()

    # Botni ishga tushirish
    logger.info("Bot ishga tushdi...")

    # Start polling only if RUN_BOT_LOCAL is enabled (prevents duplicate polling on remote deployments)
    if str(RUN_BOT_LOCAL).lower() in ('1', 'true', 'yes'):
        logger.info("Starting polling (local mode)...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    else:
        logger.info("RUN_BOT_LOCAL is disabled — not starting polling. Start the bot locally if needed.")


if __name__ == '__main__':
    main()
