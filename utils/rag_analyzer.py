

from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from core.config import get_qdrant_url, get_qdrant_api_key
from utils.embedding import embed_text


class RAGAnalyzer:
    """
    RAG Analyzer с использованием Qdrant для семантического поиска по контексту.
    """

    def __init__(self, collection_name: str = "presentation_rules"):
        self.collection_name = collection_name
        self.client: QdrantClient | None = None
        self.initialized: bool = False

    def initialize(self):
        api_url = get_qdrant_url()
        api_token = get_qdrant_api_key()

        if not api_url or not api_token:
            raise ValueError("Не заданы QDRANT_API_URL или QDRANT_API_TOKEN")

        self.client = QdrantClient(url=api_url, api_key=api_token)

        if not self.client.collection_exists(self.collection_name):
            vector_params = VectorParams(size=384, distance=Distance.COSINE)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=vector_params
            )

        self.initialized = True

    def add_documents(self, docs: List[str], ids: List[int] | None = None):
        if not self.initialized or self.client is None:
            raise RuntimeError("RAGAnalyzer не инициализирован")

        points: List[PointStruct] = []
        for idx, doc in enumerate(docs):
            vec = embed_text(doc)
            point_id = ids[idx] if ids else None
            points.append(PointStruct(id=point_id, vector=vec, payload={"text": doc}))

        self.client.upsert(collection_name=self.collection_name, points=points)

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Семантический поиск по коллекции.
        Возвращает top_k наиболее релевантных документов.
        """
        if not self.initialized or not self.client:
            raise RuntimeError("RAGAnalyzer не инициализирован")

        vec = embed_text(query_text)

        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=vec,
            limit=top_k
        )

        return [
            {"text": point.payload.get("text", ""), "score": point.score}
            for point in search_result.points
        ]

rag_analyzer = RAGAnalyzer()
