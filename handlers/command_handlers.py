from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from .utils import NOT_AUTHORIZED_MESSAGE, validate_date, get_stats_by_date, is_authorized


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


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /stats command. Sends user stats for users with admin access.
    
    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    if not is_authorized(update):
        await update.message.reply_text(NOT_AUTHORIZED_MESSAGE)
        return

    if len(context.args) < 1:
        await update.message.reply_text('Пожалуйста, укажите дату в формате ГГГГ-ММ-ДД.')
        return
    
    date = context.args[0]
    
    if not validate_date(date):
        await update.message.reply_text("Неверный формат даты. Пожалуйста, укажите дату в формате ГГГГ-ММ-ДД.")
        return
    
    stats_data = get_stats_by_date(date)

    if not stats_data:
        await update.message.reply_text(f'Нет данных за дату {date}.')
    else:
        total_users = len(stats_data)
        total_requests = sum(stat['request_count'] for stat in stats_data)
        total_files = sum(stat['file_count'] for stat in stats_data)

        formatted_response = (f"*Общая статистика за дату {date}:*\n\n"
                              f"*Всего пользователей:* `{total_users}`\n"
                              f"*Всего запросов:* `{total_requests}`\n"
                              f"*Всего файлов:* `{total_files}`\n")

        keyboard = [[InlineKeyboardButton("Показать детали", callback_data=f"show_details_{date}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(formatted_response, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def show_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for showing detailed user stats after pressing the /stats command button.
    
    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    query = update.callback_query
    date = query.data.split('_')[-1]

    stats_data = get_stats_by_date(date)

    if not stats_data:
        await query.message.reply_text(f'Нет подробной информации на дату {date}.')
    else:
        formatted_response = f"*Детальная статистика за дату {date}:*\n"
        for stat in stats_data:
            formatted_response += (f"\n*ID пользователя:* `{stat['user_id']}`\n"
                                   f"*Запросов:* `{stat['request_count']}`\n"
                                   f"*Файлов:* `{stat['file_count']}`\n")

        await query.message.reply_text(formatted_response, parse_mode=ParseMode.MARKDOWN)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    CallbackQueryHandler to handle button presses.
    
    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    query = update.callback_query
    if query.data.startswith("show_details_"):
        await show_details(update, context)