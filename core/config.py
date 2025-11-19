import os
from dotenv import load_dotenv


load_dotenv()
HUGGINGFACE_HUB_TOKEN = os.getenv('HUGGINGFACE_HUB_TOKEN')
QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')

def get_hf_token():
    return HUGGINGFACE_HUB_TOKEN

def get_qdrant_url():
    return QDRANT_URL

def get_qdrant_api_key():
    return QDRANT_API_KEY