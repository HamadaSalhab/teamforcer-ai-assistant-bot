import nest_asyncio
from bot.setup import setup_telegram_bot

nest_asyncio.apply()

bot = setup_telegram_bot()

bot.run_polling(close_loop=False)
