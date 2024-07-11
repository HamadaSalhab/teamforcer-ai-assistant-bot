# Teamforcer AI Assistant Bot

Teamforcer AI Assistant Bot is a Telegram bot designed to provide intelligent responses and maintain a knowledge base using Pinecone and LangChain. This bot supports handling text queries, updating its knowledge base with various file formats, and personalized user interactions by keeping chat histories.

## Features

- **Intelligent Responses**: Leverages OpenAI's GPT-4 and Pinecone for providing intelligent responses to user queries.
- **Knowledge Base Updates**: Supports updating the knowledge base with .docx, .pdf, .xlsx, and .csv files, as well as text messages with an '/upd' command.

## Project Structure

```plaintext
teamforcer-ai-assistant-bot/
├── bot/
│   └── setup.py
├── config.py
├── handlers/
│   ├── __init__.py
│   ├── command_handlers.py
│   ├── message_handlers.py
│   ├── utils.py
├── main.py
├── model/
│   ├── __init__.py
│   ├── chat_model.py
│   ├── embeddings.py
│   ├── utils.py
├── storage/
│   ├── __init__.py
│   ├── database.py
│   ├── trainers.py
│   ├── updaters.py
│   ├── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_handlers.py
│   ├── test_models.py
│   ├── test_storage.py
└── requirements.txt
```

## Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/teamforcer-ai-assistant-bot.git
    cd teamforcer-ai-assistant-bot
    ```

2. Create and activate a virtual environment:

    Linux/MacOS:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

    Windows:

    ```bash
    python3 -m venv venv
    venv\Scripts\activate
    ```


3. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:

    ```bash
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    PINECONE_API_KEY=your_pinecone_api_key
    OPENAI_API_KEY=your_openai_api_key
    EMBEDDING_MODEL_NAME=text-embedding-ada-002
    UPLOAD_FOLDER=./uploaded_files/
    INDEX_NAME=your_pinecone_index_name
    ```

5. Run the bot:

    ```bash
    python main.py
    ```

## Usage

- Start the bot: Send /start to the bot to initialize the conversation.
- Get help: Send /help to get information about the bot and its capabilities.
- Update the knowledge base:
  - Text: Send a message starting with /upd followed by the information.
  - File: Upload a supported file format (.docx, .pdf, .xlsx, .csv) to the bot.

## Contributing

Feel free to open issues or submit pull requests if you find any bugs or have suggestions for improvements.
