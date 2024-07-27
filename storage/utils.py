from typing import List
from pypdf import PdfReader
import os
from docx import Document
from config import UPLOAD_FOLDER
from datetime import datetime

def save_update_text(username: str, text: str) -> bool:
    try:
        timestamp = datetime.now().strftime("%d-%m-%Y_%H%M%S")

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        filename = f"{UPLOAD_FOLDER}/{username}_at_{timestamp}"
        with open(f"{filename}", "w") as text_file:
            text_file.write(text)
            return True
    except Exception as e:
        print(f"Error occured while saving text file from /upd command: {e}")
        return False

def get_received_file_path(filename: str) -> str:
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Ensure the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if os.path.exists(file_path):
        file_path = change_duplicate_filename(file_path)
        print(f"A similar file with the same name was found. Changing to {file_path}")
        
    return file_path


def change_duplicate_filename(file_path: str) -> str:
    if len(file_path.split(".")) > 3:
        raise Exception("Unsupported file format!")
    splits = file_path.split(".")
    path, extension = ".".join(splits[:-1]), splits[-1]
    path += "_copy"
    file_path = path + "." + extension

    return file_path


def read_docx(file_path: str) -> List[str]:
    """
    Reads the content of a .docx file.

    Args:
        file_path (str): The path to the .docx file.

    Returns:
        str: The content of the .docx file.
    """
    doc = Document(file_path)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return full_text


def read_pdf(file_path: str) -> List[str]:
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
    return full_text
