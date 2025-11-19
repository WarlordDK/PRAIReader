from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embedder = SentenceTransformer(MODEL_NAME)

def embed_text(text: str) -> List[float]:
    vec = embedder.encode(text, normalize_embeddings=True)
    return vec.tolist()

def embed_texts(texts: List[str]) -> List[List[float]]:
    vectors = embedder.encode(texts, normalize_embeddings=True)
    return vectors.tolist()
