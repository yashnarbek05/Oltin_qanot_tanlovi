from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, ApplicationBuilder

from bot.service import IS_SUB, error_handler, catch_subscribed, start, LANGUAGE, CONTACT, receive_number, language, \
    fullname, FULLNAME, link,LINK, my_count, get_winners, send_messagee, cancel
    
from config import BOT_TOKEN

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(BOT_TOKEN).read_timeout(300).write_timeout(300).build()


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            IS_SUB: [
                CallbackQueryHandler(catch_subscribed, pattern="^sub$")
            ],
            LANGUAGE: [CommandHandler('cancel', cancel),CallbackQueryHandler(language)],
            CONTACT: [CommandHandler('cancel', cancel),MessageHandler(filters.CONTACT, receive_number)],
            FULLNAME: [CommandHandler('cancel', cancel),MessageHandler(filters.TEXT, fullname)],
            LINK: [CommandHandler('cancel', cancel),CallbackQueryHandler(link, pattern="^link$")],
            
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    )   

    application.add_handler(CommandHandler("myscore", my_count))
    application.add_handler(CommandHandler("get_winners", get_winners))
    application.add_handler(CommandHandler("sm", send_messagee))

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == "__main__":
    main()
