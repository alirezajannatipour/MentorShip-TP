from collections.abc import Iterator
from contextlib import contextmanager

import anyio
import psycopg
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


# سقف تعداد درخواست‌هایی که همزمان کانکشن می‌گیرند یا نگه می‌دارند؛ برابر اندازه‌ی pool.
# بدون این سقف، وقتی همه‌ی threadها منتظر کانکشن باشند و کانکشن‌ها دست درخواست‌هایی باشند که
# منتظر thread هستند، سرویس deadlock می‌شود (در تست بار دیده شد).
# درخواست‌های اضافه بدون گرفتن thread در صف async منتظر می‌مانند.
_slots: anyio.Semaphore | None = None


def open_pool() -> None:
    global _slots
    pool.open(wait=True, timeout=10)
    _slots = anyio.Semaphore(settings.db_pool_max_size)  # داخل event loop ساخته می‌شود


def close_pool() -> None:
    pool.close()


def get_slots() -> anyio.Semaphore:
    if _slots is None:
        raise RuntimeError("pool is not open; was the app lifespan started?")
    return _slots


@contextmanager
def transaction(conn: psycopg.Connection) -> Iterator[None]:
    """همه‌ی کارهای داخل بلوک یک ترنزکشن‌اند: موفق ← commit، خطا ← rollback."""
    try:
        yield
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
