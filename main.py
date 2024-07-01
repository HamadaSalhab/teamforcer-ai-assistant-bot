from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from datasets import Dataset
from pinecone import ServerlessSpec, Pinecone
from tqdm.auto import tqdm
import pandas as pd
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import os
import time
from dotenv import load_dotenv
import logging
import tiktoken

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MAX_MESSAGES = 100
MAX_TOKENS = 14000  # slightly below the max token limit to be safe

# Initialize the tiktoken encoding for the OpenAI model
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Hi AI, how are you today?"),
    AIMessage(content="I'm great thank you. How can I help you?")
]

def preprocess(knowledgebase_path='./knowledge-base/KBTF1.xlsx'):
    dataframe = pd.read_excel(knowledgebase_path)
    dataframe['Answer'] = dataframe['Answer'].astype(str)
    dataset_tf = Dataset.from_pandas(dataframe)
    data = dataset_tf.to_pandas()
    return data


def augment_prompt(query: str, vectorstore):
    results = vectorstore.similarity_search(query, k=3)
    source_knowledge = "\n".join([x.page_content for x in results])
    augmented_prompt = f"""Using the contexts below, answer the query.

    Context:
    {source_knowledge}

    Query: {query}"""
    return augmented_prompt


def count_tokens(messages):
    """Use tiktoken to count the number of tokens in the messages."""
    total_tokens = 0
    for msg in messages:
        total_tokens += len(encoding.encode(msg.content))
    return total_tokens


def get_answer(query: str, chat, vectorstore, messages):
    augmented_prompt = augment_prompt(query, vectorstore)
    messages.append(HumanMessage(content=augmented_prompt))

    while count_tokens(messages) > MAX_TOKENS:
        # Remove the oldest human-AI message pair
        if len(messages) > 3:  # Keep the initial SystemMessage and at least one exchange
            messages.pop(1)
            messages.pop(1)
        else:
            break

    res = chat.invoke(messages)
    messages.append(res)

    return res.content, messages


def train(model, data, index, batch_size=200):
    embeddings_model = OpenAIEmbeddings(model="text-embedding-ada-002")
    for i in tqdm(range(0, len(data), batch_size)):
        i_end = min(len(data), i + batch_size)
        batch = data.iloc[i:i_end]
        ids = [f"{index}" for index in batch.index]
        texts = batch['Question'].values
        embeds = embeddings_model.embed_documents(texts)
        metadata = [{'question': x['Question'], 'answer': x['Answer'],
                     'text': x['Answer']} for _, x in batch.iterrows()]
        index.upsert(vectors=zip(ids, embeds, metadata))

    vectorstore = PineconeVectorStore(
        index=index, embedding=embeddings_model, text_key="text")

    return model, vectorstore


def create_index(pinecone_client):
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    button_start = KeyboardButton('/start')
    button_help = KeyboardButton('/help')
    keyboard = ReplyKeyboardMarkup(
        [[button_start, button_help]], resize_keyboard=True)
    await update.message.reply_text(
        'Привет! Я ТимФорсер. Чем могу помочь?',
        reply_markup=keyboard
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global messages
    user_input = update.message.text
    answer, messages = get_answer(user_input, chat, vectorstore, messages)
    await update.message.reply_text(answer)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """Меня зовут ТимФорсер, я цифровой ассистент на базе искусственного интеллекта и член команды ТИМФОРС. Я всегда готов ответить на ваши вопросы, используя коллективную базу знаний. Присоединяйтесь и делитесь своими знаниями с командой.

В одиночку можно сделать так мало – вместе можно сделать так много"""

    await update.message.reply_text(help_text)




def main():
    global chat, vectorstore, messages

    chat = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model='gpt-3.5-turbo'
    )

    data = preprocess()
    pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    index = create_index(pinecone_client)
    chat, vectorstore = train(chat, data, index)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app.run_polling(close_loop=False)


if __name__ == '__main__':
    main()
