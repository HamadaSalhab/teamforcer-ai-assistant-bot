from dotenv import load_dotenv
from pypdf import PdfReader
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from tqdm.auto import tqdm
from pinecone import ServerlessSpec, Pinecone
from datasets import Dataset
import aiofiles
import asyncio
import csv
import pandas as pd
import tiktoken
import logging
import time
import os
import io
from docx import Document
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import nest_asyncio
from typing import List

nest_asyncio.apply()


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPLOAD_FOLDER = './uploaded_files/'
MODEL_NAME = "gpt-4-turbo-2024-04-09"

EMBEDDING_MODEL_NAME = "text-embedding-ada-002"

MAX_MESSAGES = 100
MAX_TOKENS = 14000  # slightly below the max token limit to be safe

# Initialize the tiktoken encoding for the OpenAI model
encoding = tiktoken.encoding_for_model(MODEL_NAME)
embeddings_model = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)
chat = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model=MODEL_NAME)
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)


def create_index(pinecone_client):
    index_name = 'teamforce-rag'
    existing_indexes = [index_info["name"]
                        for index_info in pinecone_client.list_indexes()]
    print(existing_indexes)
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


index = create_index(pinecone_client)
vectorstore = PineconeVectorStore(
    index=index, embedding=embeddings_model, text_key="text")

messages = [
    SystemMessage(content="Вы - полезный ассистент, хорошо разбирающийся в простых вопросах из разных профессиональных сфер. Ваша аудитория - обычные пользователи, имеющие небольшой контекст во всех профессиональных сферах. Стремитесь к тому, чтобы уровень чтения по Флешу составил 80 баллов или выше. Используйте активный залог и избегайте наречий. Избегайте сложных терминов и используйте простой язык. Избегайте навязчивости или чрезмерного энтузиазма, вместо этого выражайте спокойную уверенность. Отвечайте кратко и структурировано. Если у вас нет контекста про аббревиатуру, не придумывайте её расшифровку."),
    HumanMessage(content="Привет, ИИ, как ты сегодня?"),
    AIMessage(content="У меня все отлично, спасибо вам. Чем я могу вам помочь?")
]


def preprocess(knowledgebase_path='/content/KBTF1.xlsx'):
    dataframe = pd.read_excel(knowledgebase_path)
    dataframe.iloc[:, 1] = dataframe.iloc[:, 1].astype(str)
    dataset_tf = Dataset.from_pandas(dataframe)
    data = dataset_tf.to_pandas()
    return data


def augment_prompt(query: str, vectorstore: PineconeVectorStore):
    results = vectorstore.similarity_search(query, k=3)
    source_knowledge = "\n".join([x.page_content for x in results])
    augmented_prompt = f"""Using the context below, answer the query.

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

    while len(messages)>1:
        messages.pop()

    return res.content, messages


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


def preprocess_text(text):
    # Пример предварительной обработки текста
    text = text.replace('\n', ' ').strip()
    return text


def train_textual_data(data, index):
    embeddings_model = OpenAIEmbeddings(model="text-embedding-ada-002")
    processed_texts = [preprocess_text(text) for text in data]
    for i in tqdm(range(0, len(processed_texts))):
        embeds = embeddings_model.embed_documents([processed_texts[i]])
        metadata = [{'text': processed_texts[i]}]
        index.upsert(vectors=zip([str(i)], embeds, metadata))

    vectorstore = PineconeVectorStore(
        index=index, embedding=embeddings_model, text_key="text")

    return vectorstore

# Updating the vectorstore


async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = update.message.document.file_name
    print(f"Received file: {file_name}")
    if update.message.document:
        # Проверяем формат файла
        if not file_name.endswith(('.docx', '.pdf', '.xlsx', 'csv')):
            await update.message.reply_text('Пожалуйста, загрузите файл формата .docx, .pdf, .xlsx, или .csv.')
            return

        file = await update.message.document.get_file()
        file_path = os.path.join(
            UPLOAD_FOLDER, file_name)

        # Убедимся, что папка существует
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        if os.path.exists(file_path):
            if len(file_path.split(".")) > 3:
                print("Unsupported format!")
                return
            path, extension = file_path.split(".")
            path+="_copy"
            file_path = path+extension
            print(f"A similar file with the same name was found. Changing to {file_path}")

        await file.download_to_drive(file_path)

        # Проверка, что файл сохранен
        if os.path.exists(file_path):
            print(f"Файл сохранен как {file_path}")
            await update.message.reply_text(f'Файл сохранен. Обновление базы знаний...')
        else:
            print(f"Ошибка при сохранении файла {file_path}")
            await update.message.reply_text(f'Ошибка при сохранении файла {file_path}')

        # Обновляем базу знаний после загрузки файла
        await update_knowledge_base(file_path)
        await update.message.reply_text('База знаний успешно обновлена!')


def read_docx(file_path):
    doc = Document(file_path)
    full_text = ""
    for paragraph in doc.paragraphs:
        full_text += "\n" + paragraph.text
    return full_text


def read_pdf(file_path):
    reader = PdfReader(file_path)
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)
    return full_text


async def update_knowledge_base(file_path):
    global index
    # Обработка файла и обновление датасета
    if file_path.endswith('.xlsx') or file_path.endswith('.csv'):
        new_data = pd.read_excel(file_path) if file_path.endswith('xlsx') else pd.read_csv(file_path, sep=',',
                                                                                           quoting=csv.QUOTE_ALL,
                                                                                           quotechar='"')
        new_data.iloc[:, 1] = new_data.iloc[:, 1].astype(str)
        train_tabular_data(new_data, index)
    elif file_path.endswith('.docx'):
        texts = await read_docx(file_path)
        # Разбиваем текст на строки и создаем датафрейм
        train_textual_data(texts, index)
    elif file_path.endswith('.pdf'):
        texts = read_pdf(file_path)
        # Разбиваем текст на строки и создаем датафрейм
        train_textual_data(texts, index)
    else:
        print("Неизвестный формат файла")
        return


def in_group_not_tagged(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.message.chat.type in ['group', 'supergroup']:
        if f'@{context.bot.username}' not in update.message.text:
            return True
    return False



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
    # Ignore the message if the bot is in a group but not tagged
    if in_group_not_tagged(update, context):
        return

    global messages
    user_input = update.message.text
    if update.message.chat.type in ['group', 'supergroup']:
        if f'@{context.bot.username}' not in user_input:
            return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    answer, messages = get_answer(user_input, chat, vectorstore, messages)
    await update.message.reply_text(answer)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """Меня зовут ТимФорсер, я цифровой ассистент на базе искусственного интеллекта и член команды ТИМФОРС.

Я всегда готов ответить на ваши вопросы, используя коллективную базу знаний. Присоединяйтесь и делитесь своими знаниями с командой.

В одиночку можно сделать так мало – вместе можно сделать так много"""

    await update.message.reply_text(help_text)



async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Ignore the message if the bot is in a group but not tagged
    if in_group_not_tagged(update, context):
        return

        return

    global index
    user_input = update.message.text
    print("Updating with text info...")
    await update.message.reply_text('Обновление получено. Обновление базы знаний...')
    # Remove the "+" from the message before processing
    train_textual_data(user_input[1:].split("."), index)
    await update.message.reply_text('База знаний успешно обновлена!')

# Новый обработчик для сообщения "+"
async def update_plus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Проверяем, что сообщение начинается с "+"
    if update.message.text.startswith("+"):
        await update_command(update, context)

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
# Handler for /upd command
app.add_handler(CommandHandler("upd", update_command))
# Handler for /ask command
app.add_handler(CommandHandler("ask", echo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
# Обработчик для получения файлов
app.add_handler(MessageHandler(filters.Document.ALL, save_file))

app.run_polling(close_loop=False)