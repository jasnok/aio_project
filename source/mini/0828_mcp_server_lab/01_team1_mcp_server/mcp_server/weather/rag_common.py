"""RAG 공용 유틸리티 — 이 폴더 안의 MCP 서버들이 함께 씁니다."""

import os
from pathlib import Path

import httpx
import psycopg
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
PGVECTOR_TABLE = os.getenv("PGVECTOR_COLLECTION", "travel_documents")
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.35"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "embeddinggemma")


async def get_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]


def _to_vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(str(v) for v in embedding) + "]"


async def search_similar_chunks(domain: str, query: str, top_k: int = 3) -> list[dict]:
    vector_literal = _to_vector_literal(await get_embedding(query))

    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT content, metadata, 1 - (embedding <=> %s::vector) AS score
                FROM {PGVECTOR_TABLE}
                WHERE domain = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vector_literal, domain, vector_literal, top_k),
            )
            rows = await cur.fetchall()

    return [
        {"content": content, "metadata": metadata, "score": score}
        for content, metadata, score in rows
        if score >= RAG_MIN_SCORE
    ]