import time
from langchain_pinecone import PineconeVectorStore
from pinecone import ServerlessSpec, Pinecone
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from config import PINECONE_API_KEY
from model.embeddings import get_embeddings_model

messages = [
    SystemMessage(content="Вы - полезный ассистент, хорошо разбирающийся в простых вопросах из разных профессиональных сфер. Ваша аудитория - обычные пользователи, имеющие небольшой контекст во всех профессиональных сферах. Стремитесь к тому, чтобы уровень чтения по Флешу составил 80 баллов или выше. Используйте активный залог и избегайте наречий. Избегайте сложных терминов и используйте простой язык. Избегайте навязчивости или чрезмерного энтузиазма, вместо этого выражайте спокойную уверенность. Отвечайте кратко и структурировано. Если у вас нет контекста про аббревиатуру, не придумывайте её расшифровку."),
    HumanMessage(content="Привет, ИИ, как ты сегодня?"),
    AIMessage(content="У меня все отлично, спасибо вам. Чем я могу вам помочь?")
]


def get_index():
    pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    index_name = 'teamforce-rag'
    existing_indexes = [index_info["name"]
                        for index_info in pinecone_client.list_indexes()]
    spec = ServerlessSpec(cloud="aws", region="us-east-1")

    if index_name not in existing_indexes:
        pinecone_client.create_index(
            index_name,
            dimension=1536,
            metric='dotproduct',
            spec=spec
        )
        while not pinecone_client.describe_index(index_name).status['ready']:
            time.sleep(1)

    index = pinecone_client.Index(index_name)
    time.sleep(1)
    index.describe_index_stats()

    return index


def get_vectorstore(index):
    return PineconeVectorStore(
        index=index, embedding=get_embeddings_model(), text_key="text")


def get_messages():
    return messages
