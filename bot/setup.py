from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from storage.utils import save_file
from handlers.message_handlers import echo, update_command
from handlers.command_handlers import start, help_command
from config import TELEGRAM_BOT_TOKEN


def setup_telegram_bot():
    bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", help_command))
    # Handler for /upd command
    bot.add_handler(CommandHandler("upd", update_command))
    # Handler for /ask command
    bot.add_handler(CommandHandler("ask", echo))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    # Handler for receiving files
    bot.add_handler(MessageHandler(filters.Document.ALL, save_file))

    return bot