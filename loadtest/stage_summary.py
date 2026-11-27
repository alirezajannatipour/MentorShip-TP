"""خلاصه‌ی هر پله‌ی بار را به‌صورت جدول Markdown چاپ می‌کند (برای گذاشتن در گزارش).

    python -m loadtest.stage_summary --dir loadtest/results

خروجی در ترمینال چاپ می‌شود و در stage_summary.md کنار فایل‌های نتیجه هم ذخیره می‌شود.
"""

import argparse
from pathlib import Path

import pandas as pd

from loadtest.stages import StepLoad


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="loadtest/results")
    args = parser.parse_args()
    d = Path(args.dir)

    hist = pd.read_csv(d / "locust_stats_history.csv")
    hist = hist[hist["Name"] == "Aggregated"].copy()
    for col in hist.columns:
        if col not in ("Type", "Name"):
            hist[col] = pd.to_numeric(hist[col], errors="coerce")
    hist["t"] = hist["Timestamp"] - hist["Timestamp"].min()

    res = None
    if (d / "resources.csv").exists():
        res = pd.read_csv(d / "resources.csv")
        res["t"] = res["timestamp"] - hist["Timestamp"].min()

    lines = [
        "| users | RPS | P50 (ms) | P95 (ms) | P99 (ms) | failures/s | machine CPU % | DB connections (max) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    start = 0
    for end, users, _rate in StepLoad.stages:
        w = hist[(hist["t"] >= start) & (hist["t"] < end)]
        cpu = conns = "-"
        if res is not None:
            r = res[(res["t"] >= start) & (res["t"] < end)]
            if len(r):
                cpu = f"{r['system_cpu'].mean():.0f}"
                conns = f"{r['db_connections'].max():.0f}"
        lines.append(
            f"| {users} | {w['Requests/s'].mean():.1f} | {w['50%'].median():.0f} | "
            f"{w['95%'].median():.0f} | {w['99%'].median():.0f} | "
            f"{w['Failures/s'].mean():.2f} | {cpu} | {conns} |"
        )
        start = end

    total = int(hist["Total Request Count"].max())
    failed = int(hist["Total Failure Count"].max())
    lines.append("")
    lines.append(f"total requests: {total}, failures: {failed} ({failed / total * 100:.2f}%)")
    text = "\n".join(lines)
    print(text)
    (d / "stage_summary.md").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
