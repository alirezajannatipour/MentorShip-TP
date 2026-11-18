from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from src.config import settings

# هر ردیف به‌صورت dict برمی‌گردد. pool در lifespan برنامه باز و بسته می‌شود.
pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=settings.db_pool_min_size,
    max_size=settings.db_pool_max_size,
    kwargs={"row_factory": dict_row},
    open=False,
)


def open_pool() -> None:
    pool.open(wait=True, timeout=10)


def close_pool() -> None:
    pool.close()
