"""نمودارهای نتیجه‌ی تست بار را از فایل‌های CSV می‌سازد.

    python -m loadtest.make_charts --dir loadtest/results

ورودی‌ها (داخل --dir): locust_stats.csv، locust_stats_history.csv و (اختیاری) resources.csv
خروجی: چهار فایل PNG همان‌جا
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PCT_COLORS = {"50%": "#2e7d32", "95%": "#ef6c00", "99%": "#c62828"}


def load_history(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["Name"] == "Aggregated"].copy()
    for col in df.columns:
        if col not in ("Type", "Name"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["t"] = df["Timestamp"] - df["Timestamp"].min()
    return df


def stage_lines(ax, stage_ends: list[float]) -> None:
    for end in stage_ends:
        ax.axvline(end, color="#bdbdbd", linestyle=":", linewidth=1)


def chart_throughput(hist: pd.DataFrame, out: Path, stage_ends) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(hist["t"], hist["Requests/s"], color="#1565c0", label="Requests/s (RPS)")
    ax.plot(hist["t"], hist["Failures/s"], color="#c62828", label="Failures/s")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("requests per second")
    stage_lines(ax, stage_ends)
    ax2 = ax.twinx()
    ax2.plot(hist["t"], hist["User Count"], color="#757575", linestyle="--", label="Users")
    ax2.set_ylabel("concurrent users")
    lines = ax.get_legend_handles_labels()
    lines2 = ax2.get_legend_handles_labels()
    ax.legend(lines[0] + lines2[0], lines[1] + lines2[1], loc="upper left")
    ax.set_title("Throughput and failures vs. concurrent users")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def chart_percentiles(hist: pd.DataFrame, out: Path, stage_ends) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for col, color in PCT_COLORS.items():
        ax.plot(hist["t"], hist[col], color=color, label=f"P{col[:-1]}")
    ax.set_yscale("log")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("response time (ms, log scale)")
    stage_lines(ax, stage_ends)
    ax2 = ax.twinx()
    ax2.plot(hist["t"], hist["User Count"], color="#757575", linestyle="--", label="Users")
    ax2.set_ylabel("concurrent users")
    lines = ax.get_legend_handles_labels()
    lines2 = ax2.get_legend_handles_labels()
    ax.legend(lines[0] + lines2[0], lines[1] + lines2[1], loc="upper left")
    ax.set_title("Response time percentiles (all endpoints)")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def chart_endpoints(stats_path: Path, out: Path) -> None:
    df = pd.read_csv(stats_path)
    df = df[df["Name"] != "Aggregated"].copy()
    df = df.sort_values("95%")
    y = range(len(df))
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(df) + 2))
    height = 0.27
    for i, (col, color) in enumerate(PCT_COLORS.items()):
        ax.barh([v + (i - 1) * height for v in y], df[col], height=height,
                color=color, label=f"P{col[:-1]}")
    ax.set_yticks(list(y))
    ax.set_yticklabels(df["Name"])
    ax.set_xscale("log")
    ax.set_xlabel("response time (ms, log scale)")
    ax.legend(loc="lower right")
    ax.set_title("Response time per endpoint (whole run)")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def chart_resources(res_path: Path, hist: pd.DataFrame, out: Path, stage_ends) -> None:
    res = pd.read_csv(res_path)
    res["t"] = res["timestamp"] - hist["Timestamp"].min()
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(res["t"], res["system_cpu"], color="#424242", label="whole machine")
    axes[0].plot(res["t"], res["app_cpu"], color="#1565c0", label="API (uvicorn)")
    axes[0].plot(res["t"], res["pg_cpu"], color="#ef6c00", label="PostgreSQL")
    axes[0].set_ylabel("CPU % (100 = one core)")
    axes[0].legend(loc="upper left")
    axes[0].set_title("Resource utilization during the test")
    axes[1].plot(res["t"], res["app_rss_mb"], color="#1565c0", label="API RAM")
    axes[1].plot(res["t"], res["pg_rss_mb"], color="#ef6c00", label="PostgreSQL RAM (sum, includes shared)")
    axes[1].set_ylabel("RAM (MB)")
    axes[1].legend(loc="upper left")
    axes[2].plot(res["t"], res["db_connections"], color="#6a1b9a", label="open connections")
    axes[2].plot(res["t"], res["db_active"], color="#c62828", label="active (running a query)")
    axes[2].plot(res["t"], res["db_idle_in_tx"], color="#00838f", label="idle in transaction")
    axes[2].set_ylabel("DB connections")
    axes[2].set_xlabel("time (s)")
    axes[2].legend(loc="upper left")
    for ax in axes:
        stage_lines(ax, stage_ends)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="loadtest/results")
    args = parser.parse_args()
    d = Path(args.dir)

    hist = load_history(d / "locust_stats_history.csv")
    # پایان هر پله را از جایی که تعداد کاربر تغییر می‌کند حدس می‌زنیم
    changes = hist["User Count"].ne(hist["User Count"].shift()).fillna(False)
    stage_ends = [t for t in hist.loc[changes, "t"].tolist()[1:]]

    chart_throughput(hist, d / "01_throughput_and_users.png", stage_ends)
    chart_percentiles(hist, d / "02_response_time_percentiles.png", stage_ends)
    chart_endpoints(d / "locust_stats.csv", d / "03_response_time_per_endpoint.png")
    if (d / "resources.csv").exists():
        chart_resources(d / "resources.csv", hist, d / "04_resource_utilization.png", stage_ends)
    print("charts written to", d)


if __name__ == "__main__":
    main()
