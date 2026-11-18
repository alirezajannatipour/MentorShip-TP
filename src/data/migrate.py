"""اجرای فایل‌های SQL داخل migrations/ به ترتیب نام؛ هر فایل فقط یک بار اجرا می‌شود.

اجرا:  python -m src.data.migrate
"""

from pathlib import Path

import psycopg

from src.config import settings

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def run() -> None:
    with psycopg.connect(settings.database_url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename   TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        applied = {
            row[0] for row in conn.execute("SELECT filename FROM schema_migrations")
        }
        count = 0
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                continue
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,)
            )
            print(f"applied {path.name}")
            count += 1
        if count == 0:
            print("nothing to apply")


if __name__ == "__main__":
    run()
