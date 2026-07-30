"""Pagination helpers."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import Query
from sqlalchemy.orm import Query as SAQuery


def page_params(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    return {"limit": limit, "offset": offset}


def paginate(query: SAQuery, limit: int, offset: int) -> dict[str, Any]:
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def paginated_dicts(
    query: SAQuery,
    limit: int,
    offset: int,
    serializer: Callable[[Any], dict],
) -> dict:
    page = paginate(query, limit, offset)
    return {
        "items": [serializer(x) for x in page["items"]],
        "total": page["total"],
        "limit": page["limit"],
        "offset": page["offset"],
    }
