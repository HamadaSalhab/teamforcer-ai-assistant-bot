import tiktoken
from config import MAX_TOKENS, MODEL_NAME


def exceeds_model_tokens_limit(text: str) -> bool:
    """
    Uses tiktoken to count the number of tokens in the messages.

    Args:
        text (string): The text to be tokenized.

    Returns:
        bool: True if the given text exceeds the token limit, False otherise.
    """
    # Initialize the tiktoken encoding for the OpenAI model
    encoding = tiktoken.encoding_for_model(MODEL_NAME)

    total_tokens = len(encoding.encode(text))
    return total_tokens > MAX_TOKENS
