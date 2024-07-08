from pypdf import PdfReader
import os
from docx import Document
from telegram import Update
from telegram.ext import ContextTypes
from config import UPLOAD_FOLDER
from storage.updaters import update_knowledge_base


async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Saves the uploaded file to the server and updates the knowledge base.

    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    file_name = update.message.document.file_name
    print(f"Received file: {file_name}")
    if update.message.document:
        # Check file format
        if not file_name.endswith(('.docx', '.pdf', '.xlsx', 'csv')):
            await update.message.reply_text('Пожалуйста, загрузите файл формата .docx, .pdf, .xlsx, или .csv.')
            return

        file = await update.message.document.get_file()
        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        # Ensure the upload folder exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        if os.path.exists(file_path):
            if len(file_path.split(".")) > 3:
                print("Unsupported format!")
                return
            splits = file_path.split(".")
            path, extension = ".".join(splits[:-1]), splits[-1]
            path += "_copy"
            file_path = path + "." + extension
            print(f"A similar file with the same name was found. Changing to {
                  file_path}")

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


def read_docx(file_path):
    """
    Reads the content of a .docx file.

    Args:
        file_path (str): The path to the .docx file.

    Returns:
        str: The content of the .docx file.
    """
    doc = Document(file_path)
    full_text = ""
    for paragraph in doc.paragraphs:
        full_text += "\n" + paragraph.text
    return full_text


def read_pdf(file_path):
    """
    Reads the content of a .pdf file.

    Args:
        file_path (str): The path to the .pdf file.

    Returns:
        str: The content of the .pdf file.
    """
    reader = PdfReader(file_path)
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)
    return "\n".join(full_text)
