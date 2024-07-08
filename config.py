from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(override=True)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPLOAD_FOLDER = './uploaded_files/'
MODEL_NAME = "gpt-4-turbo-2024-04-09"
EMBEDDING_MODEL_NAME = "text-embedding-ada-002"
MAX_MESSAGES = 100
MAX_TOKENS = 14000