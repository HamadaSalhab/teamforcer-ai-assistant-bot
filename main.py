import nest_asyncio
from bot.setup import setup_telegram_bot

# Apply nest_asyncio to allow nested asynchronous event loops
nest_asyncio.apply()

def main():
    # Setup and initialize the Telegram bot
    bot = setup_telegram_bot()
    # Start polling for updates from Telegram
    bot.run_polling(close_loop=False)

if __name__ == "__main__":
    main()