"""دیتابیس تستی را با حجم واقعی‌تر پر می‌کند (کاربر، غرفه، محصول، عکس، آدرس، کیف پول).

حتماً روی یک دیتابیس جدا اجرا کنید (مثلاً ecommerce_load)، نه دیتابیس اصلی:

    1) DATABASE_URL را در .env روی دیتابیس تستی بگذارید
    2) python -m src.data.migrate
    3) python -m loadtest.seed

خروجی: loadtest/tokens.json (توکن خریدارها برای Locust؛ داخل گیت نمی‌رود)
"""

import argparse
import json
import sys
from pathlib import Path

import psycopg

from src.config import settings
from src.utils.security import create_access_token, hash_password

TOKENS_FILE = Path(__file__).parent / "tokens.json"
PASSWORD = "password123"


def load_ids(conn):
    buyers = conn.execute(
        """
        SELECT u.id, u.email, a.id AS address_id
        FROM users u JOIN addresses a ON a.user_id = u.id
        WHERE u.username LIKE 'lt_buyer%' ORDER BY u.id
        """
    ).fetchall()
    min_id, max_id = conn.execute("SELECT min(id), max(id) FROM products").fetchone()
    shop_ids = [r[0] for r in conn.execute("SELECT id FROM shops ORDER BY id")]
    return buyers, min_id, max_id, shop_ids


def write_tokens(buyers, min_id, max_id, shop_ids) -> None:
    TOKENS_FILE.write_text(
        json.dumps(
            {
                "password": PASSWORD,
                "product_min_id": min_id,
                "product_max_id": max_id,
                "shop_ids": shop_ids,
                "buyers": [
                    {
                        "user_id": uid,
                        "email": email,
                        "address_id": address_id,
                        "token": create_access_token(uid),
                    }
                    for uid, email, address_id in buyers
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--products", type=int, default=100_000)
    parser.add_argument("--buyers", type=int, default=2_000)
    parser.add_argument("--sellers", type=int, default=50)
    parser.add_argument(
        "--tokens-only",
        action="store_true",
        help="فقط tokens.json را دوباره بسازد (توکن‌ها ۲۴ ساعت اعتبار دارند؛ داده‌ها دست نمی‌خورند)",
    )
    args = parser.parse_args()

    if args.tokens_only:
        with psycopg.connect(settings.database_url) as conn:
            buyers, min_id, max_id, shop_ids = load_ids(conn)
        if not buyers:
            sys.exit("دیتابیس خریدار تستی ندارد؛ اول بدون --tokens-only اجرا کنید.")
        write_tokens(buyers, min_id, max_id, shop_ids)
        print(f"tokens refreshed for {len(buyers)} buyers -> {TOKENS_FILE}")
        return

    with psycopg.connect(settings.database_url) as conn:
        db_name = conn.execute("SELECT current_database()").fetchone()[0]
        users = conn.execute("SELECT count(*) FROM users").fetchone()[0]
        if users > 0:
            sys.exit(
                f"دیتابیس «{db_name}» از قبل کاربر دارد ({users}). برای جلوگیری از "
                "خراب شدن داده‌ی واقعی، seed فقط روی دیتابیس خالی اجرا می‌شود."
            )
        print(f"seeding database: {db_name}")

        password_hash = hash_password(PASSWORD)  # یک بار؛ همه‌ی کاربران یک رمز دارند

        conn.execute(
            """
            INSERT INTO users (username, email, phone_number, password_hash)
            SELECT 'lt_seller' || g, 'lt_seller' || g || '@loadtest.example',
                   '0912' || lpad(g::text, 7, '0'), %s
            FROM generate_series(1, %s) g
            """,
            (password_hash, args.sellers),
        )
        conn.execute(
            """
            INSERT INTO users (username, email, phone_number, password_hash, wallet_balance)
            SELECT 'lt_buyer' || g, 'lt_buyer' || g || '@loadtest.example',
                   '0913' || lpad(g::text, 7, '0'), %s, 1000000000
            FROM generate_series(1, %s) g
            """,
            (password_hash, args.buyers),
        )
        conn.execute(
            """
            INSERT INTO transactions (user_id, amount, type, balance_after)
            SELECT id, 1000000000, 'deposit', 1000000000
            FROM users WHERE username LIKE 'lt_buyer%'
            """
        )
        conn.execute(
            """
            INSERT INTO shops (owner_id, name, description)
            SELECT id, 'غرفه تست ' || id, 'غرفه‌ی ساختگی برای تست بار'
            FROM users WHERE username LIKE 'lt_seller%'
            """
        )
        print("users, shops: done")

        conn.execute(
            """
            WITH sh AS (SELECT array_agg(id ORDER BY id) AS ids FROM shops)
            INSERT INTO products
                (shop_id, category_id, title, description, price, stock, sold_count, created_at)
            SELECT sh.ids[1 + g %% cardinality(sh.ids)],
                   1 + g %% 5,
                   (ARRAY['گوشی','لپتاپ','کفش','کتاب','ساعت','کیف','هدفون','پیراهن','قابلمه','تلویزیون'])[1 + g %% 10]
                     || ' ' ||
                   (ARRAY['مدل الف','مدل ب','پرو','مینی','اسپرت','کلاسیک'])[1 + (g / 10) %% 6]
                     || ' ' || g,
                   'توضیحات محصول شماره ' || g,
                   50000 + (g * 37) %% 5000000,
                   1000000,
                   (g * 7919) %% 500,
                   now() - random() * interval '365 days'
            FROM sh, generate_series(1, %s) g
            """,
            (args.products,),
        )
        conn.execute(
            """
            INSERT INTO product_images (product_id, image_url, sort_order)
            SELECT id, 'https://cdn.example.com/p/' || id || '.jpg', 0 FROM products
            """
        )
        conn.execute(
            """
            INSERT INTO product_images (product_id, image_url, sort_order)
            SELECT id, 'https://cdn.example.com/p/' || id || '_2.jpg', 1
            FROM products WHERE id % 3 = 0
            """
        )
        print("products, images: done")

        conn.execute(
            """
            INSERT INTO addresses (user_id, province, city, address_detail, postal_code)
            SELECT id, 'تهران', 'تهران', 'خیابان تست، پلاک ' || id, '1234567890'
            FROM users WHERE username LIKE 'lt_buyer%'
            """
        )
        conn.commit()
        conn.execute("ANALYZE")  # آمار جدول‌ها برای planner

        buyers, min_id, max_id, shop_ids = load_ids(conn)
    write_tokens(buyers, min_id, max_id, shop_ids)
    print(
        f"done: {args.products} products, {len(buyers)} buyers, {len(shop_ids)} shops "
        f"-> {TOKENS_FILE}"
    )


if __name__ == "__main__":
    main()
