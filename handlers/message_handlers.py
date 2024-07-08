from pinecone import Pinecone
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from config import PINECONE_API_KEY
from model.chat_model import get_answer, get_chat_model
from storage.database import get_index, get_messages, get_vectorstore
from storage.trainers import train_textual_data
from .utils import in_group_not_tagged
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    # Проверяем, что сообщение начинается с "+"
    if update.message.text.startswith("+"):
        await update_command(update, context)
