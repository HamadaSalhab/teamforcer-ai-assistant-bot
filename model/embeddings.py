from langchain_openai import OpenAIEmbeddings
from config import EMBEDDING_MODEL_NAME


def get_embeddings_model():
    return OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)
