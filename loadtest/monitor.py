"""مصرف منابع را هر چند ثانیه نمونه‌گیری می‌کند (CPU، RAM، کانکشن‌های دیتابیس).

همزمان با تست اجرا شود:
    python -m loadtest.monitor --out loadtest/results/resources.csv
با Ctrl+C متوقف می‌شود.
"""

import argparse
import csv
import time
from pathlib import Path

import psutil
import psycopg

from src.config import settings


def is_match(proc: psutil.Process, match: str) -> bool:
    try:
        name = (proc.name() or "").lower()
        cmdline = " ".join(proc.cmdline() or []).lower()
    except psutil.Error:
        return False
    if match == "postgres":
        return name.startswith("postgres")
    # سرور API: uvicorn (مستقیم یا از طریق uv run)؛ خود مانیتور و Locust را نمی‌شماریم
    return "uvicorn" in cmdline and "monitor" not in cmdline and "locust" not in cmdline


class ProcessGroup:
    """گروهی از پروسه‌ها که در هر نمونه دوباره پیدا می‌شوند.

    PostgreSQL به‌ازای هر کانکشن یک پروسه‌ی جدید می‌سازد و سرور ممکن است بعد از
    مانیتور ری‌استارت شود؛ پس فهرست پروسه‌ها نباید فقط یک بار در شروع ساخته شود.
    Processهای قبلی نگه داشته می‌شوند تا cpu_percent درست محاسبه شود.
    """

    def __init__(self, match: str) -> None:
        self.match = match
        self.known: dict[int, psutil.Process] = {}

    def sample(self) -> tuple[float, float, int]:
        alive: dict[int, psutil.Process] = {}
        for proc in psutil.process_iter():
            if proc.pid in self.known:
                alive[proc.pid] = self.known[proc.pid]
            elif is_match(proc, self.match):
                proc.cpu_percent(interval=None)  # شروع بازه‌ی اندازه‌گیری برای پروسه‌ی جدید
                alive[proc.pid] = proc
        self.known = alive
        cpu = rss = 0.0
        for proc in alive.values():
            try:
                cpu += proc.cpu_percent(interval=None)
                rss += proc.memory_info().rss
            except psutil.Error:
                pass
        return cpu, rss / 1024 / 1024, len(alive)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="loadtest/results/resources.csv")
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(settings.database_url, autocommit=True) as conn, out.open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["timestamp", "system_cpu", "app_cpu", "app_rss_mb", "pg_cpu", "pg_rss_mb",
             "db_connections", "db_active", "db_idle_in_tx", "app_procs", "pg_procs"]
        )
        psutil.cpu_percent(interval=None)
        app_group, pg_group = ProcessGroup("uvicorn"), ProcessGroup("postgres")
        app_group.sample(), pg_group.sample()  # نمونه‌ی اول فقط مرجع است
        print("monitoring... Ctrl+C to stop")
        try:
            while True:
                time.sleep(args.interval)
                app_cpu, app_rss, app_n = app_group.sample()
                pg_cpu, pg_rss, pg_n = pg_group.sample()
                conns, active, idle_tx = conn.execute(
                    """
                    SELECT count(*),
                           count(*) FILTER (WHERE state = 'active'),
                           count(*) FILTER (WHERE state = 'idle in transaction')
                    FROM pg_stat_activity
                    WHERE datname = current_database() AND pid <> pg_backend_pid()
                    """
                ).fetchone()
                writer.writerow(
                    [round(time.time(), 1), psutil.cpu_percent(interval=None),
                     round(app_cpu, 1), round(app_rss, 1), round(pg_cpu, 1),
                     round(pg_rss, 1), conns, active, idle_tx, app_n, pg_n]
                )
                fh.flush()
        except KeyboardInterrupt:
            print("stopped")


if __name__ == "__main__":
    main()
