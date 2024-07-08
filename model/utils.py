import tiktoken
from config import MODEL_NAME


def count_tokens(messages):
    """
    Uses tiktoken to count the number of tokens in the messages.

    Args:
        messages (list): The list of messages to be tokenized.

    Returns:
        int: The total number of tokens in the messages.
    """
    # Initialize the tiktoken encoding for the OpenAI model
    encoding = tiktoken.encoding_for_model(MODEL_NAME)

    total_tokens = 0
    for msg in messages:
        total_tokens += len(encoding.encode(msg.content))
    return total_tokens
