import re
import os
from tiktoken import get_encoding

# Initialize the GPT-3 encoder
ENCODER = get_encoding("gpt2")


def count_tokens(text: str) -> int:
    """Counts the number of tokens in a given text using tiktoken."""
    return len(ENCODER.encode(text))


def split_into_sentences(text: str) -> list:
    """Splits a block of text into sentences using regex."""
    sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s')
    sentences = sentence_endings.split(text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def extract_character_tags(text: str) -> list:
    """Extracts character tags from processed text."""
    regex = re.compile(r'<([a-z_]+)-(f|m)>')
    matches = regex.findall(text)
    return [{"name": name, "gender": gender} for name, gender in matches]


def clean_markdown_code_blocks(text: str) -> str:
    """Removes wrapping Markdown code block delimiters like ``` or ```markdown."""
    # ^\s*```(?:markdown)?\s*\n? => Matches the opening ``` with optional 'markdown' specifier and optional whitespace/newline
    # (.*?) => Non-greedy capture of the code block content
    # \s*```$ => Matches the closing ``` with optional whitespace before the end
    code_block_regex = re.compile(
        r'^\s*```(?:markdown)?\s*\n?(.*?)\s*```$',
        re.DOTALL | re.IGNORECASE  # Added re.IGNORECASE to handle 'Markdown', 'MARKDOWN', etc.
    )
    
    match = code_block_regex.match(text)
    if match:
        return match.group(1).strip()
    return text

def clean_json_code_blocks(text: str) -> str:
    """Removes wrapping JSON code block delimiters like ``` or ```json."""
    # ^\s*```(?:json)?\s*\n? => Matches the opening ``` with optional 'json' specifier and optional whitespace/newline
    # (.*?) => Non-greedy capture of the code block content
    # \s*```$ => Matches the closing ``` with optional whitespace before the end
    json_code_block_regex = re.compile(
        r'^\s*```(?:json)?\s*\n?(.*?)\s*```$',
        re.DOTALL | re.IGNORECASE  # Added re.IGNORECASE to handle 'Json', 'JSON', etc.
    )
    
    match = json_code_block_regex.match(text)
    if match:
        return match.group(1).strip()
    return text

def split_text_into_chunks(text: str, max_length: int) -> list:
    """Splits a long text into smaller chunks without breaking words."""
    words = text.split()
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = word
            else:
                # If a single word exceeds max_length, split the word
                split_word = split_long_word(word, max_length)
                chunks.extend(split_word[:-1])
                current_chunk = split_word[-1]
        else:
            current_chunk += " " + word

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def split_long_word(word: str, max_length: int) -> list:
    """Splits a long word into smaller parts."""
    return [word[i:i + max_length] for i in range(0, len(word), max_length)]
  
def remove_suffix(file_name: str) -> str:
    # Split the file name into the name and extension
    name, extension = os.path.splitext(file_name)
    # Return the name part only, effectively removing the suffix
    return name
