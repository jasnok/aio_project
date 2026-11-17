"""호텔·관광지·호텔 정책을 선택한 Provider로 임베딩하여 적재합니다."""

import sys
from pathlib import Path

from psycopg.types.json import Jsonb


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tour.database import get_connection  # noqa: E402
from app.tour.rag import create_content_hash, get_embedding_provider, vector_literal  # noqa: E402
from app.tour.rag.document_builder import (  # noqa: E402
    build_attraction_content,
    build_hotel_content,
    build_hotel_policy_content,
)


QUERIES = {
    "hotel": """
        SELECT hotel_id, name, city, district, address, price, rating,
               review_count, hotel_grade, room_type, breakfast_included,
               parking, wifi, pool, description
        FROM hotels ORDER BY hotel_id
    """,
    "attraction": """
        SELECT id, city, area, name, address, description, precautions
        FROM tourist_attractions ORDER BY id
    """,
    "hotel_policy": """
        SELECT p.policy_id, p.hotel_id, h.name AS hotel_name, p.policy_type,
               p.title, p.content, p.effective_date, p.is_mock
        FROM hotel_policies AS p
        JOIN hotels AS h ON h.hotel_id = p.hotel_id
        ORDER BY p.hotel_id, p.policy_type
    """,
}

EXISTING_QUERY = """
SELECT content_hash, embedding_dimension
FROM tour_documents
WHERE entity_type = %s AND entity_id = %s AND chunk_type = %s AND chunk_index = 0
  AND embedding_provider = %s AND embedding_model = %s
"""

UPSERT_QUERY = """
INSERT INTO tour_documents (
    entity_type, entity_id, chunk_type, chunk_index, content, metadata,
    embedding_provider, embedding_model, embedding_dimension, embedding, content_hash
)
VALUES (%s, %s, %s, 0, %s, %s, %s, %s, %s, %s::vector, %s)
ON CONFLICT (
    entity_type, entity_id, chunk_type, chunk_index,
    embedding_provider, embedding_model
)
DO UPDATE SET
    content = EXCLUDED.content,
    metadata = EXCLUDED.metadata,
    embedding_dimension = EXCLUDED.embedding_dimension,
    embedding = EXCLUDED.embedding,
    content_hash = EXCLUDED.content_hash,
    updated_at = CURRENT_TIMESTAMP
"""


def identity(entity_type: str, row: dict) -> tuple[str, str]:
    if entity_type == "hotel":
        return str(row["hotel_id"]), "summary"
    if entity_type == "attraction":
        return str(row["id"]), "summary"
    return str(row["policy_id"]), str(row["policy_type"])


def metadata(entity_type: str, row: dict) -> dict:
    if entity_type == "hotel":
        return {"city": row["city"], "district": row.get("district"), "price": row["price"]}
    if entity_type == "attraction":
        return {"city": row["city"], "area": row["area"], "name": row["name"]}
    return {
        "hotel_id": row["hotel_id"],
        "hotel_name": row["hotel_name"],
        "policy_type": row["policy_type"],
        "is_mock": row["is_mock"],
    }


def sync_rows(entity_type: str, rows: list[dict], builder, provider) -> dict:
    stats = {"success": 0, "skipped": 0, "failed": 0}
    with get_connection() as connection:
        for row in rows:
            entity_id, chunk_type = identity(entity_type, row)
            try:
                content = builder(row)
                content_hash = create_content_hash(content)
                with connection.cursor() as cursor:
                    cursor.execute(
                        EXISTING_QUERY,
                        (entity_type, entity_id, chunk_type, provider.name, provider.model),
                    )
                    existing = cursor.fetchone()
                if existing and existing["content_hash"] == content_hash:
                    stats["skipped"] += 1
                    continue

                embedding_values = provider.embed(content)
                with connection.cursor() as cursor:
                    cursor.execute(
                        UPSERT_QUERY,
                        (
                            entity_type, entity_id, chunk_type, content,
                            Jsonb(metadata(entity_type, row)), provider.name,
                            provider.model, len(embedding_values),
                            vector_literal(embedding_values), content_hash,
                        ),
                    )
                connection.commit()
                stats["success"] += 1
            except Exception as error:
                connection.rollback()
                stats["failed"] += 1
                print(f"[{entity_type}:{entity_id}] 실패: {error}")
    return stats


def main() -> None:
    provider = get_embedding_provider()
    print(f"Embedding Provider: {provider.name}, model={provider.model}")
    with get_connection() as connection, connection.cursor() as cursor:
        rows_by_type = {}
        for entity_type, query in QUERIES.items():
            cursor.execute(query)
            rows_by_type[entity_type] = cursor.fetchall()

    builders = {
        "hotel": build_hotel_content,
        "attraction": build_attraction_content,
        "hotel_policy": build_hotel_policy_content,
    }
    for entity_type in ("hotel", "attraction", "hotel_policy"):
        stats = sync_rows(
            entity_type, rows_by_type[entity_type], builders[entity_type], provider
        )
        print(f"{entity_type}: {stats}")


if __name__ == "__main__":
    main()
