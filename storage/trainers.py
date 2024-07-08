import pandas as pd
import tqdm
from model.embeddings import get_embeddings_model

embeddings_model = get_embeddings_model()

def train_tabular_data(data: pd.DataFrame, index, batch_size=200):
    for i in tqdm(range(0, len(data), batch_size)):
        i_end = min(len(data), i + batch_size)
        batch = data.iloc[i:i_end]
        ids = [f"{index}" for index in batch.index]
        texts = batch.iloc[:, 0].values  # questions
        # embedding of the questions
        embeds = embeddings_model.embed_documents(texts)

        metadata = [{'question': x.iloc[0], 'answer': x.iloc[1],
                     'text': x.iloc[1]} for _, x in batch.iterrows()]
        index.upsert(vectors=zip(ids, embeds, metadata))


def train_textual_data(text: str, index):
    embeds = embeddings_model.embed_documents([text])
    metadata = [{'text': text}]
    index.upsert(vectors=zip([str(0)], embeds, metadata))
