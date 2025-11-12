import tempfile
import pymupdf
from pdf2image import convert_from_path
import os

POPPLER_PATH = r"D:\poppler\Library\bin"

def save_temp_pdf(upload_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(upload_file.file.read())
        return tmp.name

def extract_text(pdf_path):
    text = ""
    try:
        doc = pymupdf.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text

def pdf_to_images(pdf_path):
    try:
        # Указываем явный путь тулзы poppler, без docker-контейнера
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)

        #При использовании docker-контейнера, тулза автоматически подключается
        # images = convert_from_path(pdf_path)
        return images
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []