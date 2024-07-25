import time
from langchain_pinecone import PineconeVectorStore
from pinecone import ServerlessSpec, Pinecone
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from config import PINECONE_API_KEY
from model.embeddings import get_embeddings_model
from config import INDEX_NAME


# Default messages to initialize the bot conversation
messages = [
    SystemMessage(content="Вы - полезный ассистент, хорошо разбирающийся в простых вопросах из разных профессиональных сфер. Ваша аудитория - обычные пользователи, имеющие небольшой контекст во всех профессиональных сферах. Стремитесь к тому, чтобы уровень чтения по Флешу составил 80 баллов или выше. Используйте активный залог и избегайте наречий. Избегайте сложных терминов и используйте простой язык. Избегайте навязчивости или чрезмерного энтузиазма, вместо этого выражайте спокойную уверенность. Отвечайте кратко и структурировано. Если у вас нет контекста про аббревиатуру, не придумывайте её расшифровку."),
    HumanMessage(content="Привет, ИИ, как ты сегодня?"),
    AIMessage(content="У меня все отлично, спасибо вам. Чем я могу вам помочь?")
]


def get_index():
    """
    Initializes and returns the Pinecone index. Creates the index if it doesn't exist.

    Returns:
        index: The initialized Pinecone index.
    """
    pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    existing_indexes = [index_info["name"]
                        for index_info in pinecone_client.list_indexes()]
    spec = ServerlessSpec(cloud="aws", region="us-east-1")

    if INDEX_NAME not in existing_indexes:
        pinecone_client.create_index(
            INDEX_NAME,
            dimension=1536,
            metric='dotproduct',
            spec=spec
        )
        while not pinecone_client.describe_index(INDEX_NAME).status['ready']:
            time.sleep(1)

    index = pinecone_client.Index(INDEX_NAME)
    time.sleep(1)
    index.describe_index_stats()

    return index


def get_vectorstore(index) -> PineconeVectorStore:
    """
    Initializes and returns the Pinecone vector store with the specified index.

    Args:
        index: The Pinecone index to use.

    Returns:
        PineconeVectorStore: The initialized vector store.
    """
    return PineconeVectorStore(index=index, embedding=get_embeddings_model(), text_key="text")


def get_base_messages():
    """
    Returns the default list of messages to initialize the bot conversation.

    Returns:
        list: The default messages.
    """
    return messages
