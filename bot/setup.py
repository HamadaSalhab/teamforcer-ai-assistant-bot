from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from storage.utils import save_file
from handlers.message_handlers import echo, update_command
from handlers.command_handlers import start, help_command
from config import TELEGRAM_BOT_TOKEN


def setup_telegram_bot():
    """
    Setup and initialize the Telegram bot with the specified token and handlers.

    Returns:
        bot: The initialized Telegram bot application.
    """
    # Create a new application instance for the bot
    bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", help_command))
    bot.add_handler(CommandHandler("upd", update_command))
    bot.add_handler(CommandHandler("ask", echo))

    # Register message handlers
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    bot.add_handler(MessageHandler(filters.Document.ALL, save_file))

    return bot
