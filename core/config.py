import os
from dotenv import load_dotenv


load_dotenv()
HUGGINGFACE_HUB_TOKEN = os.getenv('HUGGINGFACE_HUB_TOKEN')
QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')

models_list = [{'id' : 1, 'model_name' : 'IlyaGusev/saiga_llama3_8b', 'dev_level' : 'hard'},
               {'id' : 2, 'models_name' : 'distilgpt2', 'dev_level' : 'light'}]

def get_hf_token():
    return HUGGINGFACE_HUB_TOKEN

def get_qdrant_url():
    return QDRANT_URL

def get_qdrant_api_key():
    return QDRANT_API_KEY

def get_model_list():
    return models_list