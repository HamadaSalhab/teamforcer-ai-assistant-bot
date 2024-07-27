import time
from typing import List
import pandas as pd
from tqdm import tqdm
from model.embeddings import get_embeddings_model
from pinecone.data.index import Index

# Initialize the embeddings model
embeddings_model = get_embeddings_model()


def train_tabular_data(data: pd.DataFrame, index: Index, batch_size: int =200) -> None:
    """
    Trains the vector store with tabular data by embedding and uploading the data in batches.

    Args:
        data (pd.DataFrame): The tabular data containing questions and answers.
        index: The Pinecone index to update.
        batch_size (int): The size of the data batches to process.
    """
    for i in tqdm(range(0, len(data), batch_size)):
        i_end = min(len(data), i + batch_size)
        batch = data.iloc[i:i_end]
        # Generate unique IDs using timestamp and the index within the batch
        ids = [f"vector-{int(time.time() * 1000)}-{idx}" for idx in batch.index]
        texts = batch.iloc[:, 0].values  # questions
        # Embedding the questions
        embeds = embeddings_model.embed_documents(texts)

        metadata = [{'question': x.iloc[0], 'answer': x.iloc[1],
                     'text': x.iloc[1]} for _, x in batch.iterrows()]
        index.upsert(vectors=zip(ids, embeds, metadata))

def train_textual_data(text_list: List[str], index: Index) -> None:
    """
    Trains the vector store with textual data by embedding and uploading the data.

    Args:
        text (str): The text data to embed and upload.
        index: The Pinecone index to update.
    """
    for text in tqdm(text_list, desc="Embedding textual data"):
        vector_id = f"vector-{int(time.time() * 1000)}"
        embeds = embeddings_model.embed_documents([text])
        metadata = [{'text': text}]
        index.upsert(vectors=zip([vector_id], embeds, metadata))
