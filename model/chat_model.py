from typing import List
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from config import MODEL_NAME, OPENAI_API_KEY


def augment_prompt(query: str, vectorstore: PineconeVectorStore):
    results = vectorstore.similarity_search(query, k=3)
    source_knowledge = "\n".join([x.page_content for x in results])
    augmented_prompt = f"""Using the context below, answer the query.

    Context:
    {source_knowledge}

    Query: {query}"""
    return augmented_prompt


def get_answer(query: str, chat, vectorstore, messages: List[str]):
    augmented_prompt = augment_prompt(query, vectorstore)
    messages.append(HumanMessage(content=augmented_prompt))

    # while count_tokens(messages) > MAX_TOKENS:
    #     # Remove the oldest human-AI message pair
    #     if len(messages) > 3:  # Keep the initial SystemMessage and at least one exchange
    #         messages.pop(1)
    #         messages.pop(1)
    #     else:
    #         break

    res = chat.invoke(messages)
    # messages.append(res)

    while len(messages) > 1:
        messages.pop()

    return res.content, messages

def get_chat_model():
    return ChatOpenAI(openai_api_key=OPENAI_API_KEY, model=MODEL_NAME)
