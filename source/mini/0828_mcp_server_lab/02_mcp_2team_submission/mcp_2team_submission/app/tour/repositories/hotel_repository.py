"""호텔 PostgreSQL 조회."""

from ..database import fetch_all


HOTEL_COLUMNS = """
h.hotel_id, h.name, h.city, h.district, h.address, h.price, h.rating,
h.review_count, h.hotel_grade, h.room_type, h.breakfast_included,
h.parking, h.wifi, h.pool, h.description
"""


def search_structured(region: str, max_price: int | None, count: int) -> list[dict]:
    return fetch_all(
        f"""
        SELECT {HOTEL_COLUMNS}
        FROM hotels AS h
        WHERE h.city = %s
          AND (%s::integer IS NULL OR h.price <= %s::integer)
        ORDER BY h.price, h.rating DESC, h.review_count DESC, h.name
        LIMIT %s
        """,
        (region, max_price, max_price, count),
    )


def search_similar(
    region: str, max_price: int | None, query_vector: str, count: int,
    provider: str, model: str, dimension: int,
) -> list[dict]:
    return fetch_all(
        f"""
        SELECT {HOTEL_COLUMNS},
               1 - (d.embedding <=> %s::vector) AS similarity
        FROM hotels AS h
        JOIN tour_documents AS d
         ON d.entity_type = 'hotel' AND d.entity_id = h.hotel_id
         AND d.chunk_type = 'summary' AND d.chunk_index = 0
         AND d.embedding_provider = %s AND d.embedding_model = %s
         AND d.embedding_dimension = %s
        WHERE h.city = %s
          AND (%s::integer IS NULL OR h.price <= %s::integer)
          AND d.embedding IS NOT NULL
        ORDER BY d.embedding <=> %s::vector, h.price, h.rating DESC
        LIMIT %s
        """,
        (query_vector, provider, model, dimension, region, max_price, max_price, query_vector, count),
    )


def find_near_attraction(
    city: str,
    area: str,
    max_price: int | None,
    count: int,
    query_vector: str | None = None,
    embedding_identity: tuple[str, str, int] | None = None,
) -> list[dict]:
    similarity_select = ""
    document_join = ""
    similarity_order = ""
    if query_vector:
        if embedding_identity is None:
            raise ValueError("벡터 검색에는 embedding_identity가 필요합니다.")
        provider, model, dimension = embedding_identity
        similarity_select = ", 1 - (d.embedding <=> %s::vector) AS similarity"
        document_join = """
        JOIN tour_documents AS d
          ON d.entity_type = 'hotel' AND d.entity_id = h.hotel_id
         AND d.chunk_type = 'summary' AND d.chunk_index = 0
         AND d.embedding IS NOT NULL
         AND d.embedding_provider = %s AND d.embedding_model = %s
         AND d.embedding_dimension = %s
        """
        similarity_order = "d.embedding <=> %s::vector,"
        params = (area, query_vector, provider, model, dimension, city, max_price, max_price, area, query_vector, count)
    else:
        params = (area, city, max_price, max_price, area, count)

    return fetch_all(
        f"""
        SELECT {HOTEL_COLUMNS},
               CASE WHEN h.district = %s THEN 'same_area' ELSE 'same_city' END
                   AS proximity_level
               {similarity_select}
        FROM hotels AS h
        {document_join}
        WHERE h.city = %s
          AND (%s::integer IS NULL OR h.price <= %s::integer)
        ORDER BY CASE WHEN h.district = %s THEN 0 ELSE 1 END,
                 {similarity_order} h.price, h.rating DESC, h.review_count DESC
        LIMIT %s
        """,
        params,
    )
