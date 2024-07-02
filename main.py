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
from docx import Document as DocxDocument
from pypdf import PdfReader
import csv

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
index = create_index(pinecone_client)
vectorstore = PineconeVectorStore(
    index=index, embedding=embeddings_model, text_key="text")

messages = [
    SystemMessage(content="Вы - полезный ассистент, хорошо разбирающийся в простых вопросах из разных профессиональных сфер. Ваша аудитория - обычные пользователи, имеющие небольшой контекст во всех профессиональных сферах. Стремитесь к тому, чтобы уровень чтения по Флешу составил 80 баллов или выше. Используйте активный залог и избегайте наречий. Избегайте сложных терминов и используйте простой язык. Избегайте навязчивости или чрезмерного энтузиазма, вместо этого выражайте спокойную уверенность. Отвечайте кратко и структурировано."),
    HumanMessage(content="Привет, ИИ, как ты сегодня?"),
    AIMessage(content="У меня все отлично, спасибо вам. Чем я могу вам помочь?")
]

def preprocess(knowledgebase_path='./knowledge-base/KBTF1.xlsx'):
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

def train_textual_data(texts, index, ids):

    embeddings_list = []
    for text in texts:
        res = embeddings_model.embed_documents(text)
        # embeddings_list.append(res['data'][0]['embedding'])
        embeddings_list.append(res)

    index.upsert(vectors=[(id, embedding)
                 for id, embedding in zip(ids, embeddings_list)])

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
    if user_input.startswith("/upd"):
        train_textual_data(user_input[4:].split("."), index, ["text-from-message"])
    else: 
        answer, messages = get_answer(user_input, chat, vectorstore, messages)
        await update.message.reply_text(answer)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """Меня зовут ТимФорсер, я цифровой ассистент на базе искусственного интеллекта и член команды ТИМФОРС. Я всегда готов ответить на ваши вопросы, используя коллективную базу знаний. Присоединяйтесь и делитесь своими знаниями с командой.

В одиночку можно сделать так мало – вместе можно сделать так много"""

    await update.message.reply_text(help_text)


# Updating the vectorstore
async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        # Проверяем формат файла
        if not update.message.document.file_name.endswith(('.docx', '.pdf', '.xlsx', 'csv')):
            await update.message.reply_text('Пожалуйста, загрузите файл формата .docx, .pdf, .xlsx, или .csv.')
            return

        file = await update.message.document.get_file()
        file_path = os.path.join(
            UPLOAD_FOLDER, update.message.document.file_name)

        # Убедимся, что папка существует
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        await file.download_to_drive(file_path)

        # Проверка, что файл сохранен
        if os.path.exists(file_path):
            print(f"Файл сохранен как {file_path}")
            await update.message.reply_text(f'Файл сохранен. Обновление базы знаний...')
        else:
            print(f"Ошибка при сохранении файла {file_path}")
            await update.message.reply_text(f'Ошибка при сохранении файла {file_path}')

        # Обновляем базу знаний после загрузки файла
        update_knowledge_base(file_path)
        await update.message.reply_text('База знаний успешно обновлена!')


def read_docx(file_path):
    doc = DocxDocument(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return full_text


def read_pdf(file_path):
    reader = PdfReader(file_path)
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)
    return full_text


def update_knowledge_base(file_path):
    global index
    # Обработка файла и обновление датасета
    if file_path.endswith(('.xlsx', 'csv')):
        new_data = pd.read_excel(file_path) if file_path.endswith(
            'xlsx') else pd.read_csv(file_path, sep=',',
                                     quoting=csv.QUOTE_ALL,
                                     quotechar='"')

        new_data.iloc[:, 1] = new_data.iloc[:, 1].astype(str)

        train_tabular_data(new_data, index)

    elif file_path.endswith('.docx'):
        texts = read_docx(file_path)
        # Разбиваем текст на строки и создаем датафрейм
        train_textual_data(texts, index, [file_path])
    elif file_path.endswith('.pdf'):
        texts = read_pdf(file_path)
        # Разбиваем текст на строки и создаем датафрейм
        train_textual_data(texts, index, [file_path])
    else:
        print("Неизвестный формат файла")
        return

    print(f"Новые данные: {new_data}")  # Дополнительный вывод для отладки


app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
# Обработчик для получения файлов
app.add_handler(MessageHandler(filters.Document.ALL, save_file))

app.run_polling(close_loop=False)