CREATE TYPE order_status AS ENUM ('pending', 'paid', 'shipping', 'delivered', 'cancelled');
CREATE TYPE payment_method AS ENUM ('wallet', 'online_gateway');
CREATE TYPE transaction_type AS ENUM ('deposit', 'withdraw', 'purchase', 'sale', 'refund');

-- آدرس‌های کاربر؛ حذف منطقی با is_active
CREATE TABLE addresses (
    id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id        INTEGER      NOT NULL REFERENCES users (id),
    province       VARCHAR(100) NOT NULL,
    city           VARCHAR(100) NOT NULL,
    address_detail TEXT         NOT NULL,
    postal_code    VARCHAR(10),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX addresses_user_id_idx ON addresses (user_id);

-- سبد خرید (هر کاربر یکی) و آیتم‌هایش
CREATE TABLE carts (
    id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id),
    CONSTRAINT carts_user_id_key UNIQUE (user_id)
);

CREATE TABLE cart_items (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cart_id    INTEGER NOT NULL REFERENCES carts (id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products (id),
    quantity   INTEGER NOT NULL,
    CONSTRAINT cart_items_quantity_check CHECK (quantity > 0),
    CONSTRAINT cart_items_cart_product_key UNIQUE (cart_id, product_id)
);
CREATE INDEX cart_items_product_id_idx ON cart_items (product_id);

-- یک پرداخت (checkout) با snapshot آدرس و گیرنده
CREATE TABLE checkouts (
    id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id        INTEGER        NOT NULL REFERENCES users (id),
    total_price    BIGINT         NOT NULL,
    payment_method payment_method NOT NULL DEFAULT 'wallet',
    receiver_name  VARCHAR(100)   NOT NULL,
    receiver_phone VARCHAR(20)    NOT NULL,
    province       VARCHAR(100)   NOT NULL,
    city           VARCHAR(100)   NOT NULL,
    address_detail TEXT           NOT NULL,
    postal_code    VARCHAR(10),
    created_at     TIMESTAMPTZ    NOT NULL DEFAULT now(),
    CONSTRAINT checkouts_total_price_check CHECK (total_price >= 0)
);
CREATE INDEX checkouts_user_id_idx ON checkouts (user_id);

-- زیرسفارش به‌ازای هر غرفه
CREATE TABLE orders (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    checkout_id INTEGER      NOT NULL REFERENCES checkouts (id),
    shop_id     INTEGER      NOT NULL REFERENCES shops (id),
    total_price BIGINT       NOT NULL,
    status      order_status NOT NULL DEFAULT 'paid',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT orders_total_price_check CHECK (total_price >= 0)
);
CREATE INDEX orders_checkout_id_idx ON orders (checkout_id);
CREATE INDEX orders_shop_id_idx ON orders (shop_id);

CREATE TABLE order_items (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id          INTEGER NOT NULL REFERENCES orders (id),
    product_id        INTEGER NOT NULL REFERENCES products (id),
    quantity          INTEGER NOT NULL,
    price_at_purchase BIGINT  NOT NULL,
    CONSTRAINT order_items_quantity_check CHECK (quantity > 0),
    CONSTRAINT order_items_price_check CHECK (price_at_purchase >= 0)
);
CREATE INDEX order_items_order_id_idx ON order_items (order_id);
CREATE INDEX order_items_product_id_idx ON order_items (product_id);

-- تاریخچه‌ی کیف پول؛ منبع حقیقت برای موجودی
CREATE TABLE transactions (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id       INTEGER          NOT NULL REFERENCES users (id),
    amount        BIGINT           NOT NULL,
    type          transaction_type NOT NULL,
    checkout_id   INTEGER REFERENCES checkouts (id),
    order_id      INTEGER REFERENCES orders (id),
    balance_after BIGINT           NOT NULL,
    created_at    TIMESTAMPTZ      NOT NULL DEFAULT now(),
    CONSTRAINT transactions_amount_check CHECK (amount > 0),
    CONSTRAINT transactions_links_check CHECK (
        (type = 'purchase' AND checkout_id IS NOT NULL)
        OR (type IN ('sale', 'refund') AND order_id IS NOT NULL)
        OR (type IN ('deposit', 'withdraw'))
    )
);
CREATE INDEX transactions_user_id_idx ON transactions (user_id, id DESC);
CREATE INDEX transactions_checkout_id_idx ON transactions (checkout_id);
CREATE INDEX transactions_order_id_idx ON transactions (order_id);
-- هر سفارش حداکثر یک بار sale و یک بار refund می‌گیرد
CREATE UNIQUE INDEX transactions_order_once_key ON transactions (order_id, type)
    WHERE type IN ('sale', 'refund');

-- کلید Idempotency همراه هش بدنه و پاسخ ذخیره‌شده
CREATE TABLE idempotency_keys (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         INTEGER      NOT NULL REFERENCES users (id),
    key             VARCHAR(100) NOT NULL,
    request_hash    TEXT         NOT NULL,
    response_status INTEGER,
    response_body   JSONB,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT idempotency_keys_user_key UNIQUE (user_id, key)
);
