from telegram import Update
from telegram.ext import ContextTypes
from config import AUTHORIZED_USERNAMES

NOT_AUTHORIZED_MESSAGE = 'Извините. Вам не разрешено обновлять базу знаний.'


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
