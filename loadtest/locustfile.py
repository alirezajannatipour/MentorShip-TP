"""سناریوی تست بار پلتفرم فروشگاهی (Locust).

سه نوع کاربر مجازی:
  BrowserUser  (وزن ۸): فقط می‌گردد و محصول می‌بیند (بدون ورود)؛ بیشتر ترافیک واقعی
  BuyerUser    (وزن ۲): سبد خرید می‌چیند و پرداخت می‌کند؛ ۳۰٪ خریدها روی ۲۰ محصول پرطرفدار
                        می‌افتد تا رقابت روی قفل ردیف‌ها دیده شود (مثل لحظه‌ی تخفیف)
  LoginUser    (وزن ۱): ورود با رمز؛ هش Argon2 عمداً CPU می‌خورد

اجرا (از ریشه‌ی پروژه):
  locust -f loadtest/locustfile.py --host http://127.0.0.1:8000            # با UI
  locust -f loadtest/locustfile.py,loadtest/stages.py --host http://127.0.0.1:8000 \
         --headless --csv loadtest/results/locust --csv-full-history \
         --html loadtest/results/report.html                                # پله‌پله و بدون UI
"""

import json
import random
import uuid
from pathlib import Path

from locust import HttpUser, between, task

DATA = json.loads((Path(__file__).parent / "tokens.json").read_text(encoding="utf-8"))
PRODUCT_MIN, PRODUCT_MAX = DATA["product_min_id"], DATA["product_max_id"]
HOT_PRODUCTS = range(PRODUCT_MIN, PRODUCT_MIN + 20)
SHOP_IDS = DATA["shop_ids"]
BUYERS = DATA["buyers"]

SEARCH_TERMS = ["گوشی", "لپتاپ", "کفش", "کتاب", "ساعت", "کیف", "هدفون", "پیراهن"]
SORTS = ["price", "-price", "-sold_count", "-created_at"]


def random_product() -> int:
    return random.randint(PRODUCT_MIN, PRODUCT_MAX)


class BrowserUser(HttpUser):
    weight = 8
    wait_time = between(1, 3)

    @task(5)
    def product_list(self):
        self.client.get(
            "/v1/products",
            params={"page": random.randint(1, 5)},
            name="GET /v1/products",
        )

    @task(3)
    def category_sorted(self):
        self.client.get(
            "/v1/products",
            params={"category_id": random.randint(1, 5), "sort": random.choice(SORTS)},
            name="GET /v1/products?category_id&sort",
        )

    @task(3)
    def search(self):
        self.client.get(
            "/v1/products",
            params={"q": random.choice(SEARCH_TERMS)},
            name="GET /v1/products?q=",
        )

    @task(5)
    def product_detail(self):
        self.client.get(f"/v1/products/{random_product()}", name="GET /v1/products/{id}")

    @task(1)
    def categories(self):
        self.client.get("/v1/categories", name="GET /v1/categories")

    @task(1)
    def shop_page(self):
        shop_id = random.choice(SHOP_IDS)
        self.client.get(f"/v1/shops/{shop_id}", name="GET /v1/shops/{id}")
        self.client.get(
            "/v1/products", params={"shop_id": shop_id}, name="GET /v1/products?shop_id="
        )


class BuyerUser(HttpUser):
    weight = 2
    wait_time = between(2, 5)

    def on_start(self):
        buyer = random.choice(BUYERS)
        self.address_id = buyer["address_id"]
        self.client.headers.update({"Authorization": f"Bearer {buyer['token']}"})

    @task(3)
    def purchase(self):
        for _ in range(random.randint(1, 3)):
            product_id = (
                random.choice(HOT_PRODUCTS) if random.random() < 0.3 else random_product()
            )
            self.client.post(
                "/v1/cart/items",
                json={"product_id": product_id, "quantity": 1},
                name="POST /v1/cart/items",
            )
        cart = self.client.get("/v1/cart", name="GET /v1/cart")
        if cart.status_code != 200:
            return
        total = cart.json()["total_price"]
        with self.client.post(
            "/v1/checkouts",
            json={
                "address_id": self.address_id,
                "receiver_name": "کاربر تست",
                "receiver_phone": "09123456789",
                "expected_total_price": total,
            },
            headers={"Idempotency-Key": str(uuid.uuid4())},
            name="POST /v1/checkouts",
            catch_response=True,
        ) as response:
            if response.status_code == 422 and "CART_EMPTY" in response.text:
                response.success()  # سبد خالی؛ خطای مورد انتظار سناریو، نه مشکل سرویس

    @task(1)
    def my_orders(self):
        self.client.get("/v1/orders", name="GET /v1/orders")

    @task(1)
    def wallet(self):
        self.client.get("/v1/wallet", name="GET /v1/wallet")


class LoginUser(HttpUser):
    weight = 1
    wait_time = between(2, 4)

    @task
    def login(self):
        buyer = random.choice(BUYERS)
        self.client.post(
            "/v1/auth/login",
            json={"email": buyer["email"], "password": DATA["password"]},
            name="POST /v1/auth/login",
        )
