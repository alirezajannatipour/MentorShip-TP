# E-commerce API (FastAPI + PostgreSQL)

بک‌اند یک پلتفرم تجارت الکترونیک چندفروشنده‌ای (کلون ساده‌ی باسلام). طراحی endpointها از روی سند طراحی RESTful API پروژه گرفته شده و مسیرها با `/v1` شروع می‌شوند.

## امکانات

**قدم ۱**
- ثبت‌نام، ورود (JWT) و پروفایل
- ساخت غرفه، دیدن غرفه‌ها
- دسته‌بندی‌ها، ثبت محصول با چند تصویر
- لیست محصولات (جستجو، فیلتر، مرتب‌سازی، صفحه‌بندی) و جزئیات محصول

**قدم ۲**
- آدرس‌های کاربر
- سبد خرید
- کیف پول (شارژ و تاریخچه‌ی تراکنش‌ها)
- پرداخت (checkout) با کیف پول؛ هر خرید به یک سفارش برای هر غرفه تقسیم می‌شود
- سفارش‌های خریدار و سفارش‌های دریافتی غرفه
- تغییر وضعیت و لغو سفارش همراه با واریز به فروشنده و بازگشت وجه به خریدار

هنوز پیاده نشده: جستجوی پیشرفته، درگاه پرداخت، نظرات و امتیاز، آمار و تسویه‌ی غرفه‌دار.

## ساختار پروژه

```
.
├── src/
│   ├── app.py                  # ساخت اپ FastAPI، اتصال روترها و قالب خطاها
│   ├── config.py               # تنظیمات برنامه (Pydantic Settings از .env)
│   ├── errors.py               # AppError برای خطاهای قابل‌انتظار
│   ├── api/
│   │   ├── dependencies.py     # وابستگی‌ها: کانکشن دیتابیس، کاربر جاری، Idempotency-Key
│   │   └── endpoints/v1/       # endpointها (auth, users, shops, products, cart, wallet, ...)
│   ├── services/               # منطق کسب‌وکار؛ مرز ترنزکشن اینجاست
│   ├── repositories/           # کوئری‌های SQL خام؛ هر کوئری یک تابع
│   ├── schemas/                # مدل‌های Pydantic (ورودی و خروجی)
│   ├── connections/            # اتصال به PostgreSQL (pool) و helper ترنزکشن
│   ├── data/
│   │   ├── migrations/         # فایل‌های SQL مرتب‌شده (001_init.sql، 002_..., ...)
│   │   └── migrate.py          # اجرای migrationها
│   └── utils/                  # هش رمز، JWT، صفحه‌بندی
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

جریان هر درخواست: `endpoint ← service ← repository ← PostgreSQL`. endpoint فقط ورودی را می‌گیرد و خروجی را برمی‌گرداند، service منطق را اجرا می‌کند و مرز ترنزکشن را تعیین می‌کند، و repository فقط SQL می‌نویسد.

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

توجه: آدرس اتصال `postgresql://` است (بدون `+psycopg`). اگر رمز کاراکتر خاص دارد، URL-encode شود (مثلاً `@` ← `%40`).

۴. ساخت یا به‌روزرسانی جدول‌ها (فقط migrationهای اجرا‌نشده اعمال می‌شوند، پس روی دیتابیس قبلی هم امن است):

```bash
python -m src.data.migrate      # با uv:  uv run python -m src.data.migrate
```

۵. اجرای سرور:

```bash
uvicorn src.app:app --reload    # با uv:  uv run uvicorn src.app:app --reload
```

مستندات تعاملی: `http://127.0.0.1:8000/docs` (برای endpointهای نیازمند ورود، دکمه‌ی Authorize را بزنید و توکن را بدهید.)

## Endpointها

| متد | مسیر | دسترسی | توضیح |
| --- | --- | --- | --- |
| POST | `/v1/auth/register` | عمومی | ثبت‌نام؛ `201` همراه کاربر و توکن |
| POST | `/v1/auth/login` | عمومی | ورود با `email` یا `username` و `password` |
| GET | `/v1/users/me` | کاربر | پروفایل و موجودی کیف پول |
| GET | `/v1/users/me/shops` | کاربر | غرفه‌های من |
| POST | `/v1/shops` | کاربر | ساخت غرفه |
| GET | `/v1/shops/{shop_id}` | عمومی | اطلاعات یک غرفه |
| GET | `/v1/shops/{shop_id}/orders` | صاحب غرفه | سفارش‌های دریافتی (`status`, `page`, `limit`) |
| GET | `/v1/categories` | عمومی | لیست دسته‌بندی‌ها |
| GET | `/v1/products` | عمومی | لیست محصولات: `q`, `category_id`, `shop_id`, `sort`, `page`, `limit` |
| GET | `/v1/products/{product_id}` | عمومی | جزئیات محصول |
| POST | `/v1/products` | صاحب غرفه | ثبت محصول |
| GET / POST | `/v1/addresses` | کاربر | لیست و افزودن آدرس |
| DELETE | `/v1/addresses/{address_id}` | کاربر | حذف منطقی آدرس (`204`) |
| GET | `/v1/cart` | کاربر | سبد خرید و جمع قیمت |
| POST | `/v1/cart/items` | کاربر | افزودن محصول؛ `201` برای آیتم جدید، `200` اگر تعداد جمع شد |
| PATCH / DELETE | `/v1/cart/items/{item_id}` | کاربر | تغییر تعداد / حذف آیتم |
| GET | `/v1/wallet` | کاربر | موجودی کیف پول |
| GET | `/v1/wallet/transactions` | کاربر | تاریخچه‌ی تراکنش‌ها (`page`, `limit`) |
| POST | `/v1/wallet/transactions` | کاربر | شارژ کیف پول (هدر `Idempotency-Key` الزامی) |
| POST | `/v1/checkouts` | کاربر | پرداخت سبد با کیف پول و ساخت سفارش‌ها (هدر `Idempotency-Key` الزامی) |
| GET | `/v1/checkouts/{checkout_id}` | خریدار | جزئیات پرداخت و snapshot آدرس |
| GET | `/v1/orders` | کاربر | سفارش‌های خودم به‌عنوان خریدار (`status`, `page`, `limit`) |
| GET | `/v1/orders/{order_id}` | خریدار یا صاحب غرفه | جزئیات سفارش |
| PATCH | `/v1/orders/{order_id}` | خریدار یا فروشنده | تغییر وضعیت یا لغو |

مقدارهای `sort` محصولات: `price`، `-price`، `-sold_count`، `-created_at` (پیش‌فرض). `limit` پیش‌فرض ۲۰ و حداکثر ۱۰۰ است.

### قالب خطا

```json
{ "error": { "code": "OUT_OF_STOCK", "message": "...", "details": { "product_id": 3 } } }
```

`details` فقط وقتی هست که اطلاعات اضافه لازم باشد (مثل `current_total_price` برای `PRICE_CHANGED`).

کدهای وضعیت: `401` توکن نبود یا نامعتبر بود، `403` دسترسی ندارید، `404` پیدا نشد، `409` تعارض (تکراری، وضعیت یا قیمت یا موجودی)، `422` ورودی نامعتبر یا قاعده‌ی کسب‌وکار نقض شده (شامل شناسه‌ی غیرموجود داخل بدنه).

## جریان یک خرید

۱. ثبت‌نام دو کاربر: فروشنده و خریدار.
۲. فروشنده: ساخت غرفه (`POST /v1/shops`) و ثبت محصول با موجودی (`POST /v1/products`).
۳. خریدار: ساخت آدرس (`POST /v1/addresses`)، شارژ کیف پول (`POST /v1/wallet/transactions`)، افزودن محصول به سبد (`POST /v1/cart/items`).
۴. خریدار: پرداخت با `POST /v1/checkouts`. بدنه: `address_id`، `receiver_name`، `receiver_phone` و `expected_total_price` (جمع قیمتی که در `GET /v1/cart` دیده). هدر `Idempotency-Key` یک رشته‌ی دلخواه یکتا (مثلاً UUID) است.
۵. فروشنده: `GET /v1/shops/{id}/orders` ← `PATCH /v1/orders/{order_id}` با `{ "status": "shipping" }`.
۶. خریدار: `PATCH /v1/orders/{order_id}` با `{ "status": "delivered" }`؛ همین لحظه مبلغ سفارش به کیف پول فروشنده می‌رود.

### وضعیت سفارش

| وضعیت فعلی | وضعیت هدف | چه کسی | اثر |
| --- | --- | --- | --- |
| `paid` | `shipping` | فروشنده | — |
| `shipping` | `delivered` | خریدار (تأیید دریافت) | تراکنش `sale` به کیف پول فروشنده |
| `paid` | `cancelled` | خریدار یا فروشنده | `refund` به خریدار، برگشت موجودی |
| `shipping` | `cancelled` | فقط فروشنده | `refund` به خریدار، برگشت موجودی |

انتقال غیرمجاز `409` و نقش غیرمجاز `403` می‌دهد؛ کسی که به سفارش مربوط نیست `404` می‌گیرد.

## تصمیم‌های طراحی

<p dir="rtl">• <strong>SQL خام به‌جای ORM:</strong> کوئری‌ها توی <code>repositories/</code> با <code>psycopg</code> نوشته شده‌اند و همیشه پارامتری هستند. مقدار <code>sort</code> فقط کلید یک دیکشنری ثابت است.</p>

<p dir="rtl">• <strong>ترنزکشن:</strong> هر درخواست یک کانکشن از <code>pool</code> می‌گیرد. <code>service</code> با <code>transaction(conn)</code> یا <code>commit()</code> مرز ترنزکشن را تعیین می‌کند و با هر خطا <code>rollback</code> می‌شود.</p>

<p dir="rtl">• <strong>پرداخت اتمیک:</strong> کم کردن موجودی انبار، کسر کیف پول، ساخت سفارش‌ها، ثبت تراکنش و خالی کردن سبد همه در یک ترنزکشن‌اند. موجودی با <code>UPDATE ... WHERE stock &gt;= q</code> و کیف پول با <code>UPDATE ... WHERE wallet_balance &gt;= total</code> به‌صورت شرطی کم می‌شود، پس هیچ‌وقت منفی نمی‌شوند.</p>

<p dir="rtl">• <strong>قفل‌ها:</strong> سبد کاربر (<code>FOR UPDATE</code>) خریدهای همزمان یک کاربر را پشت‌سرهم می‌کند و دوبار کلیک با دو کلید متفاوت دوبار پول کم نمی‌کند. ردیف محصولات هم به ترتیب <code>id</code> قفل می‌شوند تا دو خریدار همزمان آخرین موجودی را با هم نخرند و <code>deadlock</code> نشود.</p>

<p dir="rtl">• <strong>Idempotency:</strong> جدول <code>idempotency_keys</code> کلید، هش بدنه و پاسخ را نگه می‌دارد. تکرار با همان کلید و بدنه همان پاسخ اول را می‌دهد، همان کلید با بدنه‌ی دیگر یا روی <code>endpoint</code> دیگر <code>409</code> می‌دهد، و دو درخواست همزمان با یک کلید پشت‌سرهم اجرا می‌شوند (دومی صبر می‌کند و پاسخ اولی را می‌گیرد). پاسخ‌های خطا ذخیره نمی‌شوند؛ تکرار بعد از خطا دوباره اجرا می‌شود.</p>

<p dir="rtl">• <strong>تاریخچه‌ی کیف پول:</strong> <code>wallet_balance</code> موجودی کش‌شده است و هر تغییرش همان لحظه یک تراکنش با <code>balance_after</code> دارد. هر سفارش حداکثر یک <code>sale</code> و یک <code>refund</code> می‌گیرد (ایندکس یکتای جزئی).</p>

<p dir="rtl">• <strong>snapshot:</strong> آدرس و گیرنده در <code>checkout</code> کپی می‌شوند و <code>price_at_purchase</code> در آیتم سفارش، پس تغییر یا حذف بعدی آدرس و قیمت روی سفارش‌های قدیمی اثر ندارد.</p>

<p dir="rtl">• <strong>حریم خصوصی:</strong> در خروجی سفارش فقط <code>snapshot</code> گیرنده دیده می‌شود؛ شناسه و ایمیل خریدار به فروشنده داده نمی‌شود.</p>

<p dir="rtl">• <strong>رمز عبور:</strong> با <code>Argon2</code> هش می‌شود. توکن <code>JWT</code> با امضای <code>HS256</code> و انقضای ۲۴ ساعته است.</p>

<p dir="rtl">• <strong>قیمت:</strong> عدد صحیح به تومان (<code>BIGINT</code>).</p>
