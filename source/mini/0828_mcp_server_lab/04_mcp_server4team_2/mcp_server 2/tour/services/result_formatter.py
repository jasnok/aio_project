def format_results(rows: list[dict]) -> dict:
    return {"items": [{"id": row["id"], "content": row["content"], "metadata": row["metadata"], **({"distance": row["distance"]} if "distance" in row else {})} for row in rows], "count": len(rows), "source": "tour-vectors"}
