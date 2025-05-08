import os
import json
from docx import Document
from PyPDF2 import PdfReader


def read_file_content(file_obj):
    """
    Reads the content of a file and returns it as a string.

    Supports various file types including:
        - .txt, .md, .csv: Reads as plain text with UTF-8 encoding.
        - .json: Parses JSON and returns a formatted string.
        - .pdf: Extracts text content using PyPDF2.
        - .docx: Extracts text content using python-docx.

    Args:
        file_obj: A file object with a 'name' attribute indicating the file path.

    Returns:
        str: The extracted content of the file, or an error message if processing fails.  Returns an empty string if the input is None.
    """
    if file_obj is None:
        return ""
    try:
        file_path = file_obj.name
        _, ext = os.path.splitext(file_path)
        ext, content = ext.lower(), ""

        if ext in ['.txt', '.md', '.csv']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                content = f"[Error reading file: {e}]"
        
        elif ext == '.json':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    content = json.dumps(data, indent=2)  
            except Exception as e:
                content = f"[Error extracting JSON content: {e}]"

        elif ext == '.pdf':
            try:
                with open(file_path, 'r') as pdf_file:
                    reader = PdfReader(pdf_file)
                    content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            except Exception as e:
                content = f"[Error extracting PDF content: {e}]"
            
        elif ext == '.docx':
            try:
                doc = Document(file_path)
                content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            except Exception as e:
                content = f"[Error extracting DOCX content: {e}]"
        else:
            content = "[Unsupported file type for simple extraction]"
        return content
    except Exception as e:
        return f"[Error processing file: {e}]"