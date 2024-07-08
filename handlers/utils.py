from telegram import Update
from telegram.ext import ContextTypes


def in_group_not_tagged(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.message.chat.type in ['group', 'supergroup']:
        if f'@{context.bot.username}' not in update.message.text:
            return True
    return False
