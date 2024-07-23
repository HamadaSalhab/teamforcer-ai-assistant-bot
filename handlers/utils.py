from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from config import AUTHORIZED_USERNAMES
import requests

NOT_AUTHORIZED_MESSAGE = 'Извините. Вам не разрешено использовать эту команду.'


def in_group_not_tagged(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Checks if the bot is mentioned in a group or supergroup message and not tagged (used to ignore the message).

    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.

    Returns:
        bool: True if the bot is not tagged in a group message, False otherwise.
    """
    if update.message.chat.type in ['group', 'supergroup']:
        if f'@{context.bot.username}' not in update.message.text:
            return True
    return False


def is_authorized(update: Update):
    username = update.message.from_user.username

    return username in AUTHORIZED_USERNAMES


def validate_date(date_text: str) -> bool:
    """
    Checks if input date format is valid.

    Args:
        date_text: string date text
    
    Returns:
        bool: True if the date is valid and in format YYYY-MM-DD, False otherwise.
    """
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def get_stats_by_date(date: str):
    """
    Returns fetched user stats data. 

    Args:
        date_text: string date text.
    
    Returns:
        json: reponse json that contains all fetched information.
    """
    url = f'http://127.0.0.1:5000/user_stats_by_date?date={date}'
    response = requests.get(url)
    if response.status_code == 200:
        stats_data = response.json()

    return stats_data