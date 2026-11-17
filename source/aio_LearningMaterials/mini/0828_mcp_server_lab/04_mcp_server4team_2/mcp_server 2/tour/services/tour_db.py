import json
import os
from typing import Any

import asyncpg
from dotenv import load_dotenv

load_dotenv()


class PostgresTourRepository:
    async def search(self, item_type: str, city: str, keyword: str | None = None,
                     max_price: int | None = None, category: str | None = None,
                     embedding: list[float] | None = None) -> list[dict[str, Any]]:
        conn = await asyncpg.connect(os.environ["DATABASE_URL"], timeout=5)
        try:
            conditions = ["metadata->>'type' = $1", "metadata->>'city' = $2"]
            values: list[Any] = [item_type, city]
            if max_price is not None:
                values.append(max_price)
                conditions.append("COALESCE((metadata->>'price')::int, 0) <= $" + str(len(values)))
            if category:
                values.append(category)
                conditions.append("metadata->>'category' = $" + str(len(values)))
            where = " AND ".join(conditions)
            if embedding:
                values.append(json.dumps(embedding))
                query = ("SELECT id, content, metadata, embedding <=> $" + str(len(values)) + "::vector AS distance "
                         "FROM tour_vectors WHERE " + where + " ORDER BY distance LIMIT 10")
            else:
                query = "SELECT id, content, metadata FROM tour_vectors WHERE " + where + " ORDER BY id LIMIT 10"
            rows = await conn.fetch(query, *values)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
