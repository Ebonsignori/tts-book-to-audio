import os
from ebooklib import epub, ITEM_DOCUMENT
from mobi import Mobi
import PyPDF2
import html2text
from bs4 import BeautifulSoup

def extract_text(file_path):
    """
    Extracts text from epub, mobi, pdf, or plaintext files.
    If the file has no extension, attempts to determine if it's plaintext.

    Parameters:
        file_path (str): Path to the input file.

    Returns:
        str: Extracted text content.

    Raises:
        ValueError: If the file type is unsupported or if there's an error during extraction.
    """
    if not os.path.isfile(file_path):
        raise ValueError(f"The file {file_path} does not exist.")

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # Function to read plaintext files
    def read_plaintext(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try reading with a different encoding if UTF-8 fails
            try:
                with open(path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Error reading plaintext file with UTF-8 or Latin-1 encoding: {e}")
        except Exception as e:
            raise ValueError(f"Error reading plaintext file: {e}")

    if ext == '.txt':
        # Plaintext file
        return read_plaintext(file_path)

    elif ext == '.epub':
        # EPUB file
        try:
            book = epub.read_epub(file_path)
            texts = []
            for item in book.get_items_of_type(ITEM_DOCUMENT):
                soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                texts.append(soup.get_text())
            return '\n'.join(texts)
        except Exception as e:
            raise ValueError(f"Error reading EPUB file: {e}")

    elif ext == '.mobi':
        reader = None
        try:
            reader = Mobi(file_path)
            output = reader.read()  # bytearray containing the decoded MOBI file
            reader.close()
            decoded_text = output.decode('utf-8', errors='replace')  # Decode with UTF-8, replacing errors
            # Parse the HTML and extract the text
            text = html2text.html2text(decoded_text)
            # soup = BeautifulSoup(decoded_text, 'html.parser')
            # text = soup.get_text()
            if not text.strip():
                raise ValueError("No text extracted from MOBI file.")
            return text
        except Exception as e:
            raise ValueError(f"Error reading MOBI file: {e}")
        finally:
            if reader:
                reader.close()

    elif ext == '.pdf':
        # PDF file
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                texts = []
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        texts.append(page_text)
                return '\n'.join(texts)
        except Exception as e:
            raise ValueError(f"Error reading PDF file: {e}")

    else:
        # Handle files without an extension or with unsupported extensions
        # Attempt to read as plaintext
        try:
            return read_plaintext(file_path)
        except ValueError:
            # If reading as plaintext fails, raise an error
            raise ValueError(f"Unsupported or unrecognized file type for file: {file_path}")
