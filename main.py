import nest_asyncio
from bot.setup import setup_telegram_bot
from threading import Thread
from app import app

# Apply nest_asyncio to allow nested asynchronous event loops
nest_asyncio.apply()

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def main():
    # Setup and initialize the Telegram bot
    bot = setup_telegram_bot()

    # Start the Flask app in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Start polling for updates from Telegram
    bot.run_polling(close_loop=False)

if __name__ == "__main__":
    main()