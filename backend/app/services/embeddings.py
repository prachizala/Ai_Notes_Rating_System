"""
Embedding generation service supporting Gemini, OpenAI, and Fake providers.
"""

import time
from typing import List
import httpx

from app.core.config import settings
from app.core.logging import logger


class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER.lower()
        self.api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        self.dim = settings.EMBEDDING_DIM

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a batch of text chunks."""
        if not texts:
            return []

        if self.provider == "fake" or settings.ENVIRONMENT == "test":
            # Generate deterministic normalized pseudo-embeddings for testing
            return [[0.01 * (i % 10) + 0.001 * (j % 5) for j in range(self.dim)] for i in range(len(texts))]

        if self.provider == "gemini":
            return self._embed_gemini(texts)
        elif self.provider == "openai":
            return self._embed_openai(texts)

        return [[0.0] * self.dim for _ in texts]

    def embed_query(self, query: str) -> List[float]:
        """Generates embedding vector for a single search query."""
        res = self.embed_texts([query])
        return res[0] if res else [0.0] * self.dim

    def _embed_gemini(self, texts: List[str]) -> List[List[float]]:
        model = settings.EMBEDDING_MODEL or "text-embedding-004"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents?key={self.api_key}"
        
        requests = [
            {"model": f"models/{model}", "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        
        for attempt in range(3):
            try:
                start = time.time()
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(url, json={"requests": requests})
                    resp.raise_for_status()
                    data = resp.json()
                    embeddings = [item["values"] for item in data.get("embeddings", [])]
                    logger.info(f"Gemini embedded {len(texts)} chunks in {round(time.time() - start, 2)}s")
                    return embeddings
            except Exception as e:
                logger.warning(f"Gemini embedding batch attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)

        # Fallback on failure
        return [[0.0] * self.dim for _ in texts]

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        url = "https://api.openai.com/v1/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": settings.EMBEDDING_MODEL or "text-embedding-3-small", "input": texts}

        for attempt in range(3):
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()["data"]
                    return [item["embedding"] for item in data]
            except Exception as e:
                logger.warning(f"OpenAI embedding batch attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)

        return [[0.0] * self.dim for _ in texts]


embedding_service = EmbeddingService()
