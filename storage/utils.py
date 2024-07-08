from pypdf import PdfReader
import os
from docx import Document
from telegram import Update
from telegram.ext import ContextTypes
from config import UPLOAD_FOLDER


async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = update.message.document.file_name
    print(f"Received file: {file_name}")
    if update.message.document:
        # Проверяем формат файла
        if not file_name.endswith(('.docx', '.pdf', '.xlsx', 'csv')):
            await update.message.reply_text('Пожалуйста, загрузите файл формата .docx, .pdf, .xlsx, или .csv.')
            return

        file = await update.message.document.get_file()
        file_path = os.path.join(
            UPLOAD_FOLDER, file_name)

        # Убедимся, что папка существует
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

        # Проверка, что файл сохранен
        if os.path.exists(file_path):
            print(f"Файл сохранен как {file_path}")
            await update.message.reply_text(f'Файл сохранен. Обновление базы знаний...')
        else:
            print(f"Ошибка при сохранении файла {file_path}")
            await update.message.reply_text(f'Ошибка при сохранении файла {file_path}')

        # Обновляем базу знаний после загрузки файла
        await update_knowledge_base(file_path)
        await update.message.reply_text('База знаний успешно обновлена!')


def read_docx(file_path):
    doc = Document(file_path)
    full_text = ""
    for paragraph in doc.paragraphs:
        full_text += "\n" + paragraph.text
    return full_text


def read_pdf(file_path):
    reader = PdfReader(file_path)
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)
    return "\n".join(full_text)
