from typing import List
from sqlalchemy.orm import Session
from langchain.schema import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from config import MODEL_NAME, OPENAI_API_KEY
from storage.sqlalchemy_database import get_chat_history
from .utils import exceeds_model_tokens_limit
from langchain_core.messages.base import BaseMessage


def augment_prompt(query: str, vectorstore: PineconeVectorStore) -> str:
    """
    Augments the user query with relevant context from the vector store.

    Args:
        query (str): The user query.
        vectorstore (PineconeVectorStore): The vector store containing relevant context.

    Returns:
        str: The augmented prompt containing the context and the user query.
    """
    results = vectorstore.similarity_search(query, k=3)
    source_knowledge = "\n".join([x.page_content for x in results])
    augmented_prompt = f"""Using the context below, and the previous chat history, answer the query.

    Context:
    {source_knowledge}

    Query: {query}"""
    return augmented_prompt


def get_answer(query: str, chat: ChatOpenAI, vectorstore: PineconeVectorStore, messages: List[BaseMessage], user_id: int, group_id: int, db: Session) -> str:
    """
    Generates an answer to the user query using the chat model and vector store.

    Args:
        query (str): The user query.
        chat: The chat model instance.
        vectorstore (PineconeVectorStore): The vector store containing relevant context.
        messages (List[str]): The list of previous messages.

    Returns:
        str: The generated answer.
        List[str]: The updated list of messages.
    """
    chat_history = get_chat_history(db, user_id, group_id)

    # Add all chat history to messages
    for message in chat_history:
        messages.append(AIMessage(content=message.content)
                        if message.is_bot else HumanMessage(content=message.content))

    # Augment prompt with vector store data
    augmented_prompt = augment_prompt(query, vectorstore)

    messages.append(HumanMessage(content=augmented_prompt))

    while exceeds_model_tokens_limit("".join(message.content for message in messages)):
        # Remove the oldest human-AI message pair
        if len(messages) > 4:  # Keep the initial SystemMessage and at least one exchange
            messages.pop(3)
            messages.pop(3)
        else:
            # Only occurs when the first human-AI message pair + first augmented prompt exceed token limit
            return "Произошла ошибка.\n(Код ошибки: 0x310).\n\nПожалуйста, сообщите об этом разработчику бота @hamadasalhab"

    # Generate response using the chat model
    res = chat.invoke(messages)

    return res.content


def get_chat_model() -> ChatOpenAI:
    """
    Initializes and returns a ChatOpenAI model instance.

    Returns:
        ChatOpenAI: The initialized chat model instance.
    """
    return ChatOpenAI(openai_api_key=OPENAI_API_KEY, model=MODEL_NAME)
