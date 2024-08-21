import os
from langchain_openai import ChatOpenAI
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from model.chat_model import get_answer, get_chat_model
from storage.database import get_index, get_base_messages, get_vectorstore
from storage.trainers import train_textual_data
from storage.updaters import update_knowledge_base
from storage.utils import get_received_file_path, save_update_text
from .utils import NOT_AUTHORIZED_MESSAGE, in_group_not_tagged, is_authorized
import logging
from storage.sqlalchemy_database import get_db, save_message, get_chat_history
from langchain_core.messages.base import BaseMessage
from typing import List
from pinecone.data.index import Index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for echoing messages. Processes user input and generates a response.

    Args:s
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    index: Index = get_index()
    vectorstore = get_vectorstore(index)
    chat: ChatOpenAI = get_chat_model()
    messages: List[BaseMessage] = get_base_messages()

    # Ignore the message if the bot is in a group but not tagged
    if in_group_not_tagged(update, context):
        return

    user_input = update.message.text

    db = next(get_db())

    user_id = update.message.from_user.id
    group_id = update.message.chat.id if update.message.chat.type in [
        'group', 'supergroup'] else None
    is_group = update.message.chat.type in ['group', 'supergroup']

    save_message(db, user_id, group_id, False, user_input, is_group)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    answer = get_answer(user_input, chat, vectorstore,
                        messages, user_id, group_id, db)
    save_message(db, user_id, group_id, True, answer, is_group)
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

    user_input = update.message.text
    username = update.message.chat.username

    if len(user_input.split()) < 2:
        await update.message.reply_text('Пожалуйста, предоставьте текст после команды /upd.')
        return

    index: Index = get_index()
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

    if not is_authorized(update.message.from_user.username):
        await update.message.reply_text(NOT_AUTHORIZED_MESSAGE)
        return

    file_name = update.message.document.file_name
    # Get file extension without the dot
    file_type = os.path.splitext(file_name)[1][1:]
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
            db = next(get_db())
            user_id = update.message.from_user.id
            group_id = update.message.chat.id if update.message.chat.type in [
                'group', 'supergroup'] else None
            is_group = update.message.chat.type in ['group', 'supergroup']
            print(f"filename {file_name}")
            print(f"filetype {file_type}")
            save_message(db, user_id, group_id, is_bot=False, message_content=f"File uploaded: {file_name}",
                         is_group=is_group, file_name=file_name, file_type=file_type)

            await update.message.reply_text(f'Файл сохранен. Обновление базы знаний...')
        else:
            print(f"Ошибка при сохранении файла {file_path}")
            await update.message.reply_text(f'Ошибка при сохранении файла {file_path}')

        # Update the knowledge base after file upload
        await update_knowledge_base(file_path)
        await update.message.reply_text('База знаний успешно обновлена!')


async def get_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /history command. Retrieves and displays chat history.

    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    # Ignore the message if the bot is in a group but not tagged
    if in_group_not_tagged(update, context):
        return

    db = next(get_db())

    user_id = update.message.from_user.id
    group_id = update.message.chat.id if update.message.chat.type in [
        'group', 'supergroup'] else None

    try:
        if group_id:
            history = get_chat_history(db, group_id=group_id)
            context_text = f"group {group_id}"
        else:
            history = get_chat_history(db, user_id=user_id)
            context_text = f"user {user_id}"

        if not history:
            await update.message.reply_text(f"No chat history found for {context_text}.")
            return

        history_text = f"Chat history for {context_text}:\n\n"
        for msg in history:
            sender = "Bot" if msg.is_bot else "User"
            history_text += f"{sender}: {msg.message_content}\n"

        # If the message is too long, split it into multiple messages
        if len(history_text) > 4096:
            for i in range(0, len(history_text), 4096):
                await update.message.reply_text(history_text[i:i+4096])
        else:
            await update.message.reply_text(history_text)

    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        await update.message.reply_text("An error occurred while retrieving chat history.")
    finally:
        db.close()
