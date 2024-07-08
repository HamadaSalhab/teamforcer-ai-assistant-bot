from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    button_start = KeyboardButton('/start')
    button_help = KeyboardButton('/help')
    keyboard = ReplyKeyboardMarkup(
        [[button_start, button_help]], resize_keyboard=True)
    await update.message.reply_text(
        'Привет! Я ТимФорсер. Чем могу помочь?',
        reply_markup=keyboard
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """Меня зовут ТимФорсер, я цифровой ассистент на базе искусственного интеллекта и член команды ТИМФОРС.
"
Я всегда готов ответить на ваши вопросы, используя коллективную базу знаний. Присоединяйтесь и делитесь своими знаниями с командой.

В одиночку можно сделать так мало – вместе можно сделать так много"""

    await update.message.reply_text(help_text)
