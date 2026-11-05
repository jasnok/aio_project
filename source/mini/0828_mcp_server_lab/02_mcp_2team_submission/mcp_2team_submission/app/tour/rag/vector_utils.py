"""검색 문서 해시와 pgvector 문자열 변환 함수입니다."""

import hashlib


def create_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"
