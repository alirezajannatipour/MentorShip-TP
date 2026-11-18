# E-commerce API (FastAPI + PostgreSQL)

بک‌اند یک پلتفرم تجارت الکترونیک چندفروشنده‌ای (کلون ساده‌ی باسلام). این نسخه‌ی اول فقط حداقل خواسته‌شده را پیاده می‌کند: ثبت‌نام و ورود کاربر، ساخت غرفه، ثبت محصول و دیدن محصولات.

طراحی endpointها از روی سند طراحی RESTful API پروژه گرفته شده و مسیرها با `/v1` شروع می‌شوند.

## امکانات این نسخه

- ثبت‌نام، ورود (JWT) و دیدن پروفایل
- ساخت غرفه و دیدن غرفه‌های خودم
- لیست دسته‌بندی‌ها
- ثبت محصول توسط صاحب غرفه (با چند تصویر)
- لیست محصولات (جستجو، فیلتر بر اساس دسته و غرفه، مرتب‌سازی، صفحه‌بندی) و جزئیات یک محصول

سبد خرید، سفارش، کیف پول و نظرات هنوز پیاده نشده‌اند (فقط ستون `wallet_balance` در جدول کاربران هست).

## ساختار پروژه

```
.
├── src/
│   ├── app.py                  # ساخت اپ FastAPI، اتصال روترها و قالب خطاها
│   ├── config.py               # تنظیمات برنامه (Pydantic Settings از .env)
│   ├── errors.py               # AppError برای خطاهای قابل‌انتظار
│   ├── api/
│   │   ├── dependencies.py     # وابستگی‌ها: کانکشن دیتابیس و کاربر جاری
│   │   └── endpoints/v1/       # endpointها (auth, users, shops, categories, products)
│   ├── services/               # منطق کسب‌وکار؛ مرز ترنزکشن (commit) اینجاست
│   ├── repositories/           # کوئری‌های SQL خام؛ هر کوئری یک تابع
│   ├── schemas/                # مدل‌های Pydantic (ورودی و خروجی)
│   ├── connections/            # اتصال به PostgreSQL (pool)
│   ├── data/
│   │   ├── migrations/         # فایل‌های SQL مرتب‌شده (001_init.sql، ...)
│   │   └── migrate.py          # اجرای migrationها
│   └── utils/                  # توابع کمکی (هش رمز و JWT)
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

جریان هر درخواست: `endpoint ← service ← repository ← PostgreSQL`. endpoint فقط ورودی را می‌گیرد و خروجی را برمی‌گرداند، service منطق را اجرا می‌کند و تصمیم می‌گیرد کی commit شود، و repository فقط SQL می‌نویسد.

## راه‌اندازی

پیش‌نیاز: Python 3.11 یا بالاتر و PostgreSQL در حال اجرا.

۱. نصب پکیج‌ها (یکی از دو روش):

```bash
# روش اول: uv
uv sync

# روش دوم: pip
python -m venv .venv
.venv\Scripts\activate          # ویندوز  (لینوکس و مک: source .venv/bin/activate)
pip install -r requirements.txt
```

۲. ساخت دیتابیس: در pgAdmin یک دیتابیس خالی به نام `ecommerce_db` بسازید (یا `CREATE DATABASE ecommerce_db;`).

۳. تنظیمات: فایل `.env.example` را به `.env` کپی کنید (ویندوز: `copy .env.example .env`) و مقدارها را پر کنید:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/ecommerce_db
JWT_SECRET=یک-رشته-تصادفی-حداقل-۳۲-کاراکتری
```

توجه: این پروژه مستقیم از `psycopg` استفاده می‌کند، پس آدرس اتصال `postgresql://` است (بدون `+psycopg`). اگر رمز کاراکتر خاص دارد، URL-encode شود (مثلاً `@` ← `%40`).

۴. ساخت جدول‌ها:

```bash
python -m src.data.migrate      # با uv:  uv run python -m src.data.migrate
```

۵. اجرای سرور:

```bash
uvicorn src.app:app --reload    # با uv:  uv run uvicorn src.app:app --reload
```

مستندات تعاملی: `http://127.0.0.1:8000/docs`

## Endpointها

| متد | مسیر | دسترسی | توضیح |
| --- | --- | --- | --- |
| POST | `/v1/auth/register` | عمومی | ثبت‌نام؛ `201` همراه کاربر و توکن |
| POST | `/v1/auth/login` | عمومی | ورود با `email` یا `username` و `password` |
| GET | `/v1/users/me` | کاربر | پروفایل و موجودی کیف پول |
| GET | `/v1/users/me/shops` | کاربر | غرفه‌های من |
| POST | `/v1/shops` | کاربر | ساخت غرفه |
| GET | `/v1/shops/{shop_id}` | عمومی | اطلاعات یک غرفه |
| GET | `/v1/categories` | عمومی | لیست دسته‌بندی‌ها |
| GET | `/v1/products` | عمومی | لیست محصولات: `q`, `category_id`, `shop_id`, `sort`, `page`, `limit` |
| GET | `/v1/products/{product_id}` | عمومی | جزئیات محصول |
| POST | `/v1/products` | صاحب غرفه | ثبت محصول |

مقدارهای `sort`: `price`، `-price`، `-sold_count`، `-created_at` (پیش‌فرض). مقدار `limit` پیش‌فرض ۲۰ و حداکثر ۱۰۰ است.

قالب خطاها همه‌جا یکسان است:

```json
{ "error": { "code": "USER_ALREADY_EXISTS", "message": "..." } }
```

کدهای وضعیت: `401` توکن نبود یا نامعتبر بود، `403` مالک غرفه نیستید، `404` پیدا نشد، `409` تکراری، `422` ورودی نامعتبر (یا غرفه و دسته‌ی داخل بدنه وجود ندارد).

## نمونه‌ی استفاده

```bash
# ثبت‌نام
curl -X POST http://127.0.0.1:8000/v1/auth/register -H "Content-Type: application/json" \
  -d '{"username":"ali","email":"ali@example.com","phone_number":"09123456789","password":"password123"}'

# ساخت غرفه (توکن را از پاسخ بالا بردارید)
curl -X POST http://127.0.0.1:8000/v1/shops -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" -d '{"name":"غرفه من"}'

# ثبت محصول (shop_id از پاسخ قبلی، category_id از /v1/categories)
curl -X POST http://127.0.0.1:8000/v1/products -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"shop_id":1,"category_id":1,"title":"گوشی","price":5000000,"stock":3,"images":["https://example.com/a.jpg"]}'

# دیدن محصولات
curl "http://127.0.0.1:8000/v1/products?sort=price&limit=10"
```

## تصمیم‌های طراحی

- **SQL خام به‌جای ORM:** کوئری‌ها توی `repositories/` با `psycopg` نوشته شده‌اند و همیشه پارامتری هستند (بدون چسباندن ورودی کاربر به SQL). مقدار `sort` فقط کلید یک دیکشنری ثابت است.
- **ترنزکشن:** هر درخواست یک کانکشن از pool می‌گیرد. عملیات نوشتن در service با `commit()` نهایی می‌شود و اگر خطایی رخ دهد، rollback انجام می‌شود.
- **رمز عبور:** با Argon2 هش می‌شود. توکن JWT با امضای HS256 و انقضای ۲۴ ساعته است.
- **یکتایی:** ایمیل (به حروف کوچک ذخیره می‌شود)، شماره تلفن و نام کاربری (بدون حساسیت به حروف) در خود دیتابیس یکتا هستند، پس ثبت‌نام همزمان هم امن است.
- **قیمت:** عدد صحیح به تومان (`BIGINT`).
- **migration:** فعلاً فایل‌های SQL ساده با یک اسکریپت کوچک. جدول `schema_migrations` نگه می‌دارد کدام فایل‌ها قبلاً اجرا شده‌اند.
