import csv
import pandas as pd
from storage.trainers import train_tabular_data, train_textual_data
from storage.utils import read_docx, read_pdf
from storage.database import get_index
from pinecone.data.index import Index


async def update_knowledge_base(file_path: str) -> None:
    """
    Updates the knowledge base with data from the specified file.

    Args:
        file_path (str): The path to the file containing the data.
    """
    index: Index = get_index()
    # Process the file and update the dataset
    if file_path.endswith('.xlsx') or file_path.endswith('.csv'):
        new_data = pd.read_excel(file_path) if file_path.endswith('xlsx') else pd.read_csv(file_path, sep=',',
                                                                                           quoting=csv.QUOTE_ALL,
                                                                                           quotechar='"')
        new_data.iloc[:, 1] = new_data.iloc[:, 1].astype(str)
        train_tabular_data(new_data, index)
    elif file_path.endswith('.docx'):
        texts = read_docx(file_path)
        train_textual_data(texts, index)
    elif file_path.endswith('.pdf'):
        texts = read_pdf(file_path)
        train_textual_data(texts, index)
    else:
        print("Неизвестный формат файла")
        return
