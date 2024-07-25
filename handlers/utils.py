from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from config import AUTHORIZED_USERNAMES
from storage.sqlalchemy_database import get_db, ChatHistory
from sqlalchemy import func, case

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
    try:
        # Convert the string date to a datetime object
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Invalid date format. Please use 'YYYY-MM-DD'.")

    db = next(get_db())
    user_stats = db.query(
        ChatHistory.user_id,
        func.count(ChatHistory.id).label('request_count'),
        func.sum(case((ChatHistory.file_name.isnot(None), 1), else_=0)).label('file_count')
    ).filter(
        func.date(ChatHistory.timestamp) == date_obj
    ).group_by(ChatHistory.user_id).all()
    
    # Convert the result to a list of dictionaries
    result = [
        {
            "user_id": stat.user_id,
            "request_count": stat.request_count,
            "file_count": stat.file_count
        }
        for stat in user_stats
    ]
    
    return result