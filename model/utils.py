import tiktoken
from config import MODEL_NAME


def count_tokens(messages):
    # Initialize the tiktoken encoding for the OpenAI model
    encoding = tiktoken.encoding_for_model(MODEL_NAME)

    """Use tiktoken to count the number of tokens in the messages."""
    total_tokens = 0
    for msg in messages:
        total_tokens += len(encoding.encode(msg.content))
    return total_tokens
