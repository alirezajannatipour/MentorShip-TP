# تست بار (Locust)

این پوشه شبیه‌سازی ترافیک پلتفرم را انجام می‌دهد: سه نوع کاربر مجازی (گردش‌کننده، خریدار، ورود با رمز) که بار را پله‌پله از ۱۰ تا ۱۵۰ کاربر همزمان بالا می‌برند و زمان پاسخ، تعداد درخواست در ثانیه، خطاها و مصرف منابع را ثبت می‌کنند.

| فایل | کار |
| --- | --- |
| `seed.py` | دیتابیس تستی را پر می‌کند: ۱۰۰ هزار محصول، ۲۰۰۰ خریدار، ۵۰ غرفه |
| `locustfile.py` | سناریوی کاربرها (کدام endpointها با چه وزنی صدا زده می‌شوند) |
| `stages.py` | پله‌های بار: ۱۰ ← ۲۵ ← ۵۰ ← ۱۰۰ ← ۱۵۰ کاربر، هر پله ۶۰ ثانیه |
| `monitor.py` | CPU، RAM و کانکشن‌های دیتابیس را هر ۲ ثانیه ثبت می‌کند |
| `make_charts.py` | از خروجی‌ها چهار نمودار PNG می‌سازد |

## اجرا

**مهم:** تست بار را روی یک دیتابیس جدا (مثلاً `ecommerce_load`) اجرا کنید، نه دیتابیس اصلی. `seed.py` اگر دیتابیس کاربر داشته باشد، خودش متوقف می‌شود.

در این مراحل چهار ترمینال لازم است. همه‌ی دستورها با `uv run` نوشته شده‌اند. اگر uv ندارید، بخش «بدون uv» پایین‌تر را ببینید.

۱. نصب uv (فقط یک بار) و ابزارهای تست:

```powershell
pip install uv
uv sync --group loadtest
```

۲. دیتابیس تستی: در pgAdmin دیتابیس خالی `ecommerce_load` را بسازید.

۳. **ترمینال ۱ (سرور):** آدرس اتصال را فقط برای همین ترمینال عوض کنید (متغیر محیطی از `.env` اولویت دارد، پس `.env` اصلی دست‌نخورده می‌ماند)، جدول‌ها و داده‌ی تستی را بسازید (۱ تا ۲ دقیقه) و سرور را **بدون `--reload`** اجرا کنید:

```powershell
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/ecommerce_load"
uv run python -m src.data.migrate
uv run --group loadtest python -m loadtest.seed
uv run uvicorn src.app:app --port 8000
```

(لینوکس و مک: به‌جای خط اول `export DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/ecommerce_load`)

۴. **ترمینال ۲ (مانیتور منابع):** `DATABASE_URL` را دوباره بگذارید و قبل از شروع تست اجرایش کنید:

```powershell
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/ecommerce_load"
uv run --group loadtest python -m loadtest.monitor --out loadtest/results/resources.csv
```

۵. **ترمینال ۳ (تست بار، حدود ۵ دقیقه؛ خودش تمام می‌شود):**

```powershell
uv run --group loadtest locust -f loadtest/locustfile.py,loadtest/stages.py --host http://127.0.0.1:8000 --headless --csv loadtest/results/locust --csv-full-history --html loadtest/results/report.html
```

۶. بعد از پایان تست، در ترمینال ۱ و ۲ با Ctrl+C سرور و مانیتور را ببندید و نمودارها و جدول پله‌ها را بسازید:

```powershell
uv run --group loadtest python -m loadtest.make_charts --dir loadtest/results
uv run --group loadtest python -m loadtest.stage_summary --dir loadtest/results
```

خروجی داخل `loadtest/results/`: چهار نمودار PNG، `report.html` (گزارش خود Locust با نمودار)، `stage_summary.md` (جدول هر پله برای گزارش) و فایل‌های CSV.

برای اجرای تعاملی با رابط وب: `uv run --group loadtest locust -f loadtest/locustfile.py --host http://127.0.0.1:8000` و بعد `http://localhost:8089`.

### بدون uv (فقط pip)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-loadtest.txt
```

بعد همه‌ی دستورهای بالا را بدون `uv run --group loadtest` و بدون `uv run` بزنید (مثلاً `python -m loadtest.seed` و `locust -f ...`).

## نکته‌ها برای نتیجه‌ی درست‌تر

- برنامه‌های سنگین دیگر را ببندید. Locust، سرور API و PostgreSQL روی یک ماشین هستند و CPU را تقسیم می‌کنند؛ پس اعداد مطلق سیستم شما به تعداد هسته‌هایش بستگی دارد.
- اگر سیستم شما قوی است و تا پله‌ی آخر کند نشد، `stages.py` را عوض کنید (مثلاً ۳۰۰ و ۵۰۰ کاربر).
- هر بار اجرا، `loadtest/results/` را پاک کنید یا اسم دیگری بدهید.
- توکن‌های داخل `tokens.json` فقط برای دیتابیس تستی کار می‌کنند، داخل گیت نمی‌روند و **۲۴ ساعت** اعتبار دارند. اگر بیشتر از یک روز بعد از seed تست را اجرا کردید و درخواست‌های خریدار `401` گرفتند، فقط توکن‌ها را دوباره بسازید (داده‌ها دست نمی‌خورند):
  `uv run --group loadtest python -m loadtest.seed --tokens-only`
- مانیتور (`monitor.py`) در هر نمونه پروسه‌های API و PostgreSQL را دوباره پیدا می‌کند، پس ری‌استارت سرور وسط کار مشکلی ایجاد نمی‌کند. فایل `resources.csv` ستون‌های `app_procs` و `pg_procs` (تعداد پروسه‌های پیداشده) هم دارد؛ اگر `app_procs` صفر بود، یعنی مانیتور سرور را پیدا نکرده و ستون‌های CPU و RAM آن معتبر نیستند.

## نمودارها را چطور بخوانیم

| نمودار | چه چیزی را نشان می‌دهد |
| --- | --- |
| `01_throughput_and_users.png` | تعداد درخواست در ثانیه (RPS)، خطاها در ثانیه و تعداد کاربر همزمان. جایی که RPS دیگر با کاربرها بالا نمی‌رود، سقف ظرفیت (Throughput) است. |
| `02_response_time_percentiles.png` | P50، P95 و P99 در طول زمان. فاصله‌ی P95 و P99 از P50 نشان می‌دهد چند درصد کاربرها تجربه‌ی بدتری دارند. |
| `03_response_time_per_endpoint.png` | کدام endpointها کندترند. |
| `04_resource_utilization.png` | CPU (کل ماشین، API و PostgreSQL)، RAM و کانکشن‌های دیتابیس (باز، فعال و `idle in transaction`). |
