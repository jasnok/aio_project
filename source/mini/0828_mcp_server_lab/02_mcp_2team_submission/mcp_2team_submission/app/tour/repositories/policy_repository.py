"""호텔 정책 원문 및 pgvector 검색입니다."""

from ..database import fetch_all


POLICY_COLUMNS = """
p.policy_id, p.hotel_id, h.name AS hotel_name, p.policy_type, p.title,
p.content, p.effective_date::text, p.is_mock
"""


def search_structured(
    hotel_ids: list[str], question: str, top_k_per_hotel: int
) -> list[dict]:
    policy_type = "cancellation" if any(
        word in question for word in ("취소", "환불", "당일", "노쇼")
    ) else None
    return fetch_all(
        f"""
        WITH ranked AS (
            SELECT {POLICY_COLUMNS}, NULL::double precision AS similarity,
                   ROW_NUMBER() OVER (
                       PARTITION BY p.hotel_id
                       ORDER BY CASE WHEN p.policy_type = %s THEN 0 ELSE 1 END,
                                p.policy_id
                   ) AS row_number
            FROM hotel_policies AS p
            JOIN hotels AS h ON h.hotel_id = p.hotel_id
            WHERE p.hotel_id = ANY(%s::varchar[])
              AND (%s::varchar IS NULL OR p.policy_type = %s OR p.content ILIKE %s)
        )
        SELECT policy_id, hotel_id, hotel_name, policy_type, title, content,
               effective_date, is_mock, similarity
        FROM ranked
        WHERE row_number <= %s
        ORDER BY hotel_id, row_number
        """,
        (policy_type, hotel_ids, policy_type, policy_type, f"%{question}%", top_k_per_hotel),
    )


def search_similar(
    hotel_ids: list[str], query_vector: str, top_k_per_hotel: int,
    provider: str, model: str, dimension: int,
) -> list[dict]:
    return fetch_all(
        f"""
        WITH ranked AS (
            SELECT {POLICY_COLUMNS},
                   1 - (d.embedding <=> %s::vector) AS similarity,
                   ROW_NUMBER() OVER (
                       PARTITION BY p.hotel_id
                       ORDER BY d.embedding <=> %s::vector
                   ) AS row_number
            FROM hotel_policies AS p
            JOIN hotels AS h ON h.hotel_id = p.hotel_id
            JOIN tour_documents AS d
              ON d.entity_type = 'hotel_policy'
             AND d.entity_id = p.policy_id::text
             AND d.embedding_provider = %s
             AND d.embedding_model = %s
             AND d.embedding_dimension = %s
            WHERE p.hotel_id = ANY(%s::varchar[])
        )
        SELECT policy_id, hotel_id, hotel_name, policy_type, title, content,
               effective_date, is_mock, similarity
        FROM ranked
        WHERE row_number <= %s
        ORDER BY hotel_id, row_number
        """,
        (query_vector, query_vector, provider, model, dimension, hotel_ids, top_k_per_hotel),
    )
