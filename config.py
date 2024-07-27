from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(override=True)

# Keys & Tokens
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Pinecone configs
INDEX_NAME = os.getenv("INDEX_NAME")

UPLOAD_FOLDER = './uploaded_files/'

# OpenAI model configs
MODEL_NAME = "gpt-4-turbo-2024-04-09"
EMBEDDING_MODEL_NAME = "text-embedding-ada-002"
MAX_TOKENS = 20000

# Bot admins (have access to uploading files & getting stats)
AUTHORIZED_USERNAMES = os.getenv('AUTHORIZED_USERNAMES').split(',')

# Database configs
DATABASE_HOSTNAME = os.getenv('DATABASE_HOSTNAME')
DATABASE_PORT = os.getenv('DATABASE_PORT')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_URL = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"