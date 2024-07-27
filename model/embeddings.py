from langchain_openai import OpenAIEmbeddings
from config import EMBEDDING_MODEL_NAME


def get_embeddings_model() -> OpenAIEmbeddings:
    """
    Initializes and returns an OpenAIEmbeddings model instance.

    Returns:
        OpenAIEmbeddings: The initialized embeddings model instance.
    """
    return OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)
