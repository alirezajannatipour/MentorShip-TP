import math


def build_pagination(total: int, page: int, limit: int) -> dict[str, int]:
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total / limit),
    }
