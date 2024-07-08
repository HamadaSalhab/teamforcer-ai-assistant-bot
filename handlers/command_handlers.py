from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /start command. Initializes the bot with a welcome message and a keyboard.
    
    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    button_start = KeyboardButton('/start')
    button_help = KeyboardButton('/help')
    keyboard = ReplyKeyboardMarkup(
        [[button_start, button_help]], resize_keyboard=True)
    await update.message.reply_text(
        'Привет! Я ТимФорсер. Чем могу помочь?',
        reply_markup=keyboard
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /help command. Sends a help message describing the bot's purpose.
    
    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    help_text = """Меня зовут ТимФорсер, я цифровой ассистент на базе искусственного интеллекта и член команды ТИМФОРС.
"
Я всегда готов ответить на ваши вопросы, используя коллективную базу знаний. Присоединяйтесь и делитесь своими знаниями с командой.

В одиночку можно сделать так мало – вместе можно сделать так много"""

    await update.message.reply_text(help_text)
