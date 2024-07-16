import os
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from model.chat_model import get_answer, get_chat_model
from storage.database import get_index, get_messages, get_vectorstore
from storage.trainers import train_textual_data
from storage.updaters import update_knowledge_base
from storage.utils import get_received_file_path, save_update_text
from .utils import NOT_AUTHORIZED_MESSAGE, in_group_not_tagged, is_authorized
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

    if not is_authorized(update):
        await update.message.reply_text(NOT_AUTHORIZED_MESSAGE)
        return

    # Ignore the message if the bot is in a group but not tagged
    if in_group_not_tagged(update, context):
        return

    index = get_index()
    user_input = update.message.text
    username = update.message.chat.username
    print("Updating with text info...")
    await update.message.reply_text('Обновление получено. Обновление базы знаний...')
    update_text = user_input[4:]
    save_update_text(username=username, text=update_text)
    train_textual_data(update_text, index)
    await update.message.reply_text('База знаний успешно обновлена!')


async def update_with_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Saves the uploaded file to the server and updates the knowledge base.

    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """

    if not is_authorized(update):
        await update.message.reply_text(NOT_AUTHORIZED_MESSAGE)
        return

    file_name = update.message.document.file_name
    print(f"Received file: {file_name}")
    if update.message.document:
        # Check file format
        if not file_name.endswith(('.docx', '.pdf', '.xlsx', 'csv')):
            await update.message.reply_text('Пожалуйста, загрузите файл формата .docx, .pdf, .xlsx, или .csv.')
            return

        file = await update.message.document.get_file()
        file_path = get_received_file_path(file_name)

        await file.download_to_drive(file_path)

        # Check if the file was saved
        if os.path.exists(file_path):
            print(f"Файл сохранен как {file_path}")
            await update.message.reply_text(f'Файл сохранен. Обновление базы знаний...')
        else:
            print(f"Ошибка при сохранении файла {file_path}")
            await update.message.reply_text(f'Ошибка при сохранении файла {file_path}')

        # Update the knowledge base after file upload
        await update_knowledge_base(file_path)
        await update.message.reply_text('База знаний успешно обновлена!')
