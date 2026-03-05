from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler, CallbackContext,
)


import traceback, time

from telegram.error import BadRequest, TelegramError



from config import REQUESTED_CHANNELS, ADMINS, BANNED

from sheet.service import get_count, add_user, is_registreted, update_count, get_winnerss 

IS_SUB = 0
LANGUAGE = 1
CONTACT = 2
FULLNAME = 3
LINK = 4

async def start(update, context):
    clear_datas(context)

    user_id = update.effective_user.id

    text = update.message.text.split(" ")
    invited_by = text[1] if len(text) == 2 else ""

    context.user_data["invited_by"] = invited_by
    
    if await is_registreted(user_id) or user_id in BANNED:

        await update.message.reply_text("Siz allaqachon ko'nkursda ishtirok etmoqdasiz.\nUshbu buyruqni berish orqali to'plagan ballingizni ko'rishingiz mumkin /myscore!")

        clear_datas(context)
        return ConversationHandler.END


    is_sub = await check_user_in_channels(user_id, context)

    if not is_sub:
        await send_subscribe_message(user_id, context)
        return IS_SUB

    await update.message.reply_text("Xush kelibsiz! 🎉")

    if invited_by: 
        await update_count(invited_by)

    keyboard = [
            [InlineKeyboardButton("English🇺🇸", callback_data="en")],
            [InlineKeyboardButton("O'zbek🇺🇿", callback_data="uz")],
            [InlineKeyboardButton("Русский🇷🇺", callback_data="ru")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Tilni tanlang:", reply_markup=reply_markup)

    return LANGUAGE



async def check_user_in_channels(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for channel in REQUESTED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except BadRequest:
            return False

    return True


async def send_subscribe_message(user_id, context):
    keyboard = []

    for channel in REQUESTED_CHANNELS:
        keyboard.append([
            InlineKeyboardButton(
                text=channel,
                url=f"https://t.me/{channel}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("Ezgu_uz", url="https://www.instagram.com/volunteers_uz")
    ])

    keyboard.append([
        InlineKeyboardButton("Obuna bo'ldim ✅", callback_data="sub")
    ])

    await context.bot.send_message(
        chat_id=user_id,
        text="Majburiy kanallarga obuna bo'ling:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def catch_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    is_subscribed = await check_user_in_channels(user_id, context)

    if is_subscribed:
        await query.edit_message_text("✅ Obuna tasdiqlandi. Davom etishingiz mumkin.")
        if context.user_data.get("invited_by"): 
            await update_count(context.user_data.get("invited_by"))
        keyboard = [
            [InlineKeyboardButton("English🇺🇸", callback_data="en")],
            [InlineKeyboardButton("O'zbek🇺🇿", callback_data="uz")],
            [InlineKeyboardButton("Русский🇷🇺", callback_data="ru")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text("Tilni tanlang:", reply_markup=reply_markup)

        return LANGUAGE
    else:
        await query.answer("❌ Hali barcha kanallarga obuna bo‘lmadingiz", show_alert=True)
        await query.edit_message_text("❌ Hali barcha kanallarga obuna bo‘lmadingiz")
        await send_subscribe_message(user_id, context)
        return IS_SUB
    

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query

    
    messages = {
        'en': f"Hello, {query.from_user.first_name}! Share your number:",
        'ru': f"Здравствуйте, {query.from_user.first_name}! Поделитесь своим номером:",
        'uz': f"Assalomu alaykum, {query.from_user.first_name}! Raqamingizni ulashing:"
    }

    keyboard = [[KeyboardButton("📞 Share Your Number", request_contact=True)]]
    reply_markup1 = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    
    await query.message.reply_text(text = messages.get(query.data, 'uz'), reply_markup=reply_markup1)
    
    context.user_data['language'] = query.data

    return CONTACT


async def receive_number(update: Update, context: CallbackContext) -> None:
    contact = update.message.contact


    messages = {
        'en': f"Enter your first and last name to participate in the contest!",
        'ru': f"Введите свое имя и фамилию, чтобы принять участие в конкурсе!",
        'uz': f"Tanlovda qatnashish uchun ism va familiyangizni kiriting!"
    }
    
    
    context.user_data["contact"] = contact.phone_number
    
    await update.message.reply_text(messages.get(context.user_data.get('language'), messages.get('uz')), reply_markup=ReplyKeyboardRemove())

    return FULLNAME


async def fullname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_fullname = update.message.text

    result = all(char.isalpha() or char == ' ' or not char.isnumeric() for char in user_fullname)

    if not result:
        messages = {
            'uz': f"Siz to'liq ismingizni noto'g'ri kiritdingiz, \"{user_fullname}\"😕, \nqayta yuboring...",
            'ru': f"Вы неправильно ввели свое полное имя: \"{user_fullname}\"😕, \nотправьте еще раз...",
            'en': f"You have entered your full name incorrectly: \"{user_fullname}\"😕, \nsend again..."
        }
        await update.message.reply_text(messages.get(context.user_data.get('language'), messages.get('uz')))
        return FULLNAME

    await add_user(user_id, context.user_data.get("contact"), user_fullname)

    keyboard = []

    keyboard.append([
        InlineKeyboardButton("Create Link🔗", callback_data="link")
    ])

    messages = {
        'uz': (
            "🎉 *“Oltin Qanot” volontyorlari Respublika tanloviga xush kelibsiz!* 🎉\n\n"
            "Ushbu tanlovda ishtirok etish uchun bot orqali sizga berilgan maxsus havola yordamida "
            "do‘stlaringizni taklif qiling va g‘oliblar safidan joy oling!\n\n"
            "🏆 *G‘oliblar quyidagicha taqdirlanadi:*\n\n"
            "💎 *1-o‘rin:*\n"
            "— *“YIL FAOLI”* nomli statuetka\n"
            "— Diplom va Tavsiyanoma xati\n"
            "— Humo Arenada bo‘lib o‘tadigan konsert uchun chipta\n"
            "— Tashakkurnoma\n\n"
            "🥇 *2–10-o‘rinlar:*\n"
            "— Diplom va Sertifikat\n"
            "— Humo Arenada bo‘lib o‘tadigan konsert uchun chiptalar\n"
            "— Tashakkurnoma\n"
            "— Barcha oflayn loyihalarda tashkilotchilik va koordinatorlik imkoniyati\n"
            "— 1 oylik loyihalarda bepul ishtirok etish\n"
            "— Tasdiqlovchi bejik hamda xayriya loyihalarida ishtirok etish imkoniyati (bayonnoma beriladi)\n\n"
            "🥈 *11–20-o‘rinlar:*\n"
            "— Diplom\n"
            "— Kitoblar\n"
            "— Sertifikatlar\n\n"
            "🥉 *21–40-o‘rinlar:*\n"
            "— Sertifikatlar\n\n"
            "👇 *Quyidagi tugmani bosing va o‘z taklifnomangizni do‘stlaringizga yuboring*"
        ),

        'ru': (
            "🎉 *Добро пожаловать на Республиканский конкурс волонтёров “Oltin Qanot”!* 🎉\n\n"
            "Чтобы принять участие, пригласите своих друзей с помощью специальной ссылки, "
            "предоставленной этим ботом, и займите место среди победителей.\n\n"
            "🏆 *Победители будут награждены следующим образом:*\n\n"
            "💎 *1 место:*\n"
            "— Статуэтка *«АКТИВИСТ ГОДА»*\n"
            "— Диплом и рекомендательное письмо\n"
            "— Билет на концерт в Humo Arena\n"
            "— Благодарственное письмо\n\n"
            "🥇 *2–10 места:*\n"
            "— Диплом и сертификат\n"
            "— Билеты на концерт в Humo Arena\n"
            "— Благодарственное письмо\n"
            "— Возможность быть организатором и координатором во всех офлайн-проектах\n"
            "— Бесплатное участие в проектах в течение 1 месяца\n"
            "— Подтверждающий бейдж и участие в благотворительных проектах (выдается протокол)\n\n"
            "🥈 *11–20 места:*\n"
            "— Диплом\n"
            "— Книги\n"
            "— Сертификаты\n\n"
            "🥉 *21–40 места:*\n"
            "— Сертификаты\n\n"
            "👇 *Нажмите кнопку ниже и отправьте приглашение своим друзьям*"
        ),

        'en': (
            "🎉 *Welcome to the “Oltin Qanot” Volunteers National Contest!* 🎉\n\n"
            "To participate, invite your friends using the special link provided through this bot "
            "and secure your place among the winners.\n\n"
            "🏆 *Winners will be rewarded as follows:*\n\n"
            "💎 *1st place:*\n"
            "— *“ACTIVIST OF THE YEAR”* statuette\n"
            "— Diploma and Letter of Recommendation\n"
            "— Ticket to the concert at Humo Arena\n"
            "— Letter of Appreciation\n\n"
            "🥇 *2nd–10th places:*\n"
            "— Diploma and Certificate\n"
            "— Concert tickets at Humo Arena\n"
            "— Letter of Appreciation\n"
            "— Opportunity to act as organizer or coordinator in all offline projects\n"
            "— Free participation in projects for 1 month\n"
            "— Verified badge and participation in charity projects (official record provided)\n\n"
            "🥈 *11th–20th places:*\n"
            "— Diploma\n"
            "— Books\n"
            "— Certificates\n\n"
            "🥉 *21st–40th places:*\n"
            "— Certificates\n\n"
            "👇 *Click the button below and send your invitation to your friends*"
        )
    }
    
    await update.message.reply_text(messages.get(context.user_data.get('language'), messages.get('uz')),
                                     reply_markup=InlineKeyboardMarkup(keyboard),
                                     parse_mode="Markdown")
    
    return LINK


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_user = await context.bot.get_me()
    user_id = update.effective_user.id
    
    # Botning fotosini olish
    photos = await context.bot.get_user_profile_photos(bot_user.id)

    file_id = photos.photos[0][-1].file_id


    messages = {
            'uz': (
    "🎉 *Do‘stim!* 🎉\n\n"
    "Sen ham shu tanlovga qatnash! 🏆\n"
    "Juda koʻp sovgʻalar va ajoyib imkoniyatlar seni kutmoqda ✨🎁\n\n"
    f"👇 *Ushbu linkni bos va kanallarga azo bo‘lish orqali tanlovda ishtirok et:* \nhttps://t.me/Oltinqanottanlovibot?start={user_id}"
),
            'ru': (
    "🎉 *Привет, друг!* 🎉\n\n"
    "Прими участие в этом конкурсе! 🏆\n"
    "Тебя ждёт много подарков и крутых возможностей ✨🎁\n\n"
    f"👇 *Нажми на эту ссылку и подпишись на каналы, чтобы участвовать в конкурсе:* \nhttps://t.me/Oltinqanottanlovibot?start={user_id}"
),
            'en': (
    "🎉 *Hey friend!* 🎉\n\n"
    "Join this contest too! 🏆\n"
    "Lots of amazing gifts and opportunities are waiting for you ✨🎁\n\n"
    f"👇 *Click this link and subscribe to the channels to participate in the contest:* \nhttps://t.me/Oltinqanottanlovibot?start={user_id}"
)
        }

    
    await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=file_id,
            caption=messages.get(context.user_data.get('language'), messages.get('uz')),
            parse_mode="Markdown"
        )
    
    messages = {
            'uz': "Ushbu buyruqni berish orqali to'plagan ballingizni ko'rishingiz mumkin /myscore!",
            'ru': "Вы можете отобразить накопленные баллы, выполнив команду /myscore!",
            'en': "You can show your accumulated points by issuing this command /myscore!"
    }

    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.get(context.user_data.get('language'), messages.get('uz')))

    clear_datas(context)
    return ConversationHandler.END


async def my_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Sizning to'plagan ballingiz: {await get_count(update.effective_user.id)}")
    clear_datas(context)
    return ConversationHandler.END


async def get_winners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMINS:

        winners = await get_winnerss()

        t = 1

        for w in winners:
            text = (
                f"🏆 {t}) <b>G‘olib</b>\n\n"
                f"👤 <b>Ism:</b> {w[2]}\n"
                f"📞 <b>Telefon:</b> +{w[1]}\n"
                f"➕ <b>Qo‘shganlar odamlari soni:</b> {w[3]}\n"
                f"🆔 <b>Telegram ID:</b> {w[0]}"
            )
            
            await context.bot.send_message(chat_id=update.effective_user.id, text= text, parse_mode="HTML")
            t = t + 1
        
    clear_datas(context)
    return ConversationHandler.END


async def get_winners_for_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    winners = await get_winnerss()

    t = 1
    text = "📌 *Tanlovimiz g'oliblari* 🥳\n\n"
    for w in winners:
        text = text + (
            f"{t}) 👤: {w[2]} 🅱️: {w[3]}\n"
        )
            
        t = t + 1
    await context.bot.send_message(chat_id=update.effective_user.id, text= text, parse_mode="Markdown")
        
    clear_datas(context)
    return ConversationHandler.END

async def send_messagee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMINS[0]:
    
        text = update.message.text

        words = text.split(" ", 2)

        try:
            await context.bot.send_message(chat_id=words[1], text=words[2])
            await context.bot.send_message(chat_id=update.effective_user.id, text="Yuborildi✅")
        except TelegramError as e:
            await context.bot.send_message(chat_id=update.effective_user.id, text="Yuborilmadi ❌\n" + e.message)
        
    else:
        await context.bot.send_message(chat_id=update.effective_user.id, text="Bu buyruq siz uchun emas🙈😊")
    
    clear_datas(context)
    return ConversationHandler.END



def clear_datas(context):
    context.chat_data.clear()
    context.user_data.clear()



async def error_handler(update: Update, context: CallbackContext):
    # NoneType chat_id xatosini e’tiborsiz qoldirish
    if context.error and "'NoneType' object has no attribute 'chat_id'" in str(context.error):
        return

    # To‘liq traceback olish
    tb = "".join(
        traceback.format_exception(
            type(context.error),
            context.error,
            context.error.__traceback__
        )
    )

    error_text = (
        "🚨 *Botda xatolik yuz berdi!*\n\n"
        f"*Xato turi:* `{type(context.error).__name__}`\n\n"
        f"*Xato matni:*\n`{context.error}`\n\n"
        f"*Qayerda (traceback):*\n```{tb}```"
    )

    await context.bot.send_message(
        chat_id=ADMINS[0],
        text=error_text,
        parse_mode="Markdown"
    )

    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext):
    messages = {
        'uz': 'Bekor qilindi!',
        'ru': 'Отменено!',
        'en': 'Cancelled!'
    }
    await update.message.reply_text(messages.get(context.user_data.get('language'), messages.get('uz')))
    clear_datas(context)
    return ConversationHandler.END


