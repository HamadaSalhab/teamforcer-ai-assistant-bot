from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import BotCommand
from handlers.message_handlers import echo, update_command, update_with_file
from handlers.command_handlers import start, help_command
from config import TELEGRAM_BOT_TOKEN
import asyncio

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

    # Register message handlers
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    bot.add_handler(MessageHandler(filters.Document.ALL, update_with_file))

    # Set the bot commands
    asyncio.run(set_commands(bot.bot))

    return bot


async def set_commands(bot):
    """
    Устанавливает список команд бота и показывает их при вводе слеша "/"

    Аргументы:
        bot: объект типа telegram.bot
    """
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help information"),
        BotCommand("upd", "Update the bot"),
    ]
    await bot.set_my_commands(commands)