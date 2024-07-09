from pypdf import PdfReader
import os
from docx import Document
from config import UPLOAD_FOLDER


def get_received_file_path(filename: str):
    os.path.join(UPLOAD_FOLDER, filename)

    # Ensure the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if os.path.exists(file_path):
        file_path = change_duplicate_filename(file_path)
        print(f"A similar file with the same name was found. Changing to {
            file_path}")


def change_duplicate_filename(file_path: str):
    if len(file_path.split(".")) > 3:
        raise Exception("Unsupported file format!")
    splits = file_path.split(".")
    path, extension = ".".join(splits[:-1]), splits[-1]
    path += "_copy"
    file_path = path + "." + extension


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
