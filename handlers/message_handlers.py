from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from model.chat_model import get_answer, get_chat_model
from storage.database import get_index, get_messages, get_vectorstore
from storage.trainers import train_textual_data
from .utils import in_group_not_tagged
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for echoing messages. Processes user input and generates a response.
    
    Args:s
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    index = get_index()
    vectorstore = get_vectorstore(index)
    chat = get_chat_model()
    messages = get_messages()

    # Ignore the message if the bot is in a group but not tagged
    if in_group_not_tagged(update, context):
        return

    user_input = update.message.text
    if update.message.chat.type in ['group', 'supergroup']:
        if f'@{context.bot.username}' not in user_input:
            return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    answer, messages = get_answer(user_input, chat, vectorstore, messages)
    await update.message.reply_text(answer)


async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /upd command. Updates the knowledge base with new information.
    
    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    # Ignore the message if the bot is in a group but not tagged
    if in_group_not_tagged(update, context):
        return

    index = get_index()
    user_input = update.message.text
    print("Updating with text info...")
    await update.message.reply_text('Обновление получено. Обновление базы знаний...')
    train_textual_data(user_input[1:], index)
    await update.message.reply_text('База знаний успешно обновлена!')


async def update_plus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for messages starting with "+". Updates the knowledge base with new information.
    
    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    # Проверяем, что сообщение начинается с "+"
    if update.message.text.startswith("+"):
        await update_command(update, context)
