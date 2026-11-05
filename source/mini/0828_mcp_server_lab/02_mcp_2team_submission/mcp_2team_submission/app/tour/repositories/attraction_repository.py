"""관광지 PostgreSQL 조회."""

from ..database import fetch_all


ATTRACTION_COLUMNS = (
    "a.id, a.city, a.area, a.name, a.address, a.description, a.precautions"
)


def search_structured(region: str, count: int) -> list[dict]:
    return fetch_all(
        f"""
        SELECT {ATTRACTION_COLUMNS}
        FROM tourist_attractions AS a
        WHERE a.city = %s
        ORDER BY a.area, a.name
        LIMIT %s
        """,
        (region, count),
    )


def search_similar(
    region: str, query_vector: str, count: int,
    provider: str, model: str, dimension: int,
) -> list[dict]:
    return fetch_all(
        f"""
        SELECT {ATTRACTION_COLUMNS},
               1 - (d.embedding <=> %s::vector) AS similarity
        FROM tourist_attractions AS a
        JOIN tour_documents AS d
         ON d.entity_type = 'attraction' AND d.entity_id = a.id::text
         AND d.chunk_type = 'summary' AND d.chunk_index = 0
         AND d.embedding_provider = %s AND d.embedding_model = %s
         AND d.embedding_dimension = %s
        WHERE a.city = %s AND d.embedding IS NOT NULL
        ORDER BY d.embedding <=> %s::vector, a.area, a.name
        LIMIT %s
        """,
        (query_vector, provider, model, dimension, region, query_vector, count),
    )


def find_by_name(name: str) -> list[dict]:
    exact = fetch_all(
        """
        SELECT id, city, area, name, address, description
        FROM tourist_attractions
        WHERE name = %s
        ORDER BY city, area
        """,
        (name,),
    )
    if exact:
        return exact
    return fetch_all(
        """
        SELECT id, city, area, name, address, description
        FROM tourist_attractions
        WHERE name ILIKE %s
        ORDER BY city, area, name
        LIMIT 10
        """,
        (f"%{name}%",),
    )
