import os
from dotenv import load_dotenv


load_dotenv()
HUGGINGFACE_HUB_TOKEN = os.getenv('HUGGINGFACE_HUB_TOKEN')

def get_hf_token():
    return HUGGINGFACE_HUB_TOKEN