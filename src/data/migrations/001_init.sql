CREATE TABLE users (
    id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username       VARCHAR(50)  NOT NULL,
    email          VARCHAR(255) NOT NULL,
    phone_number   VARCHAR(20)  NOT NULL,
    password_hash  TEXT         NOT NULL,
    wallet_balance BIGINT       NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT users_phone_number_key UNIQUE (phone_number),
    CONSTRAINT users_wallet_balance_check CHECK (wallet_balance >= 0)
);
-- نام کاربری بدون حساسیت به حروف بزرگ و کوچک یکتاست
CREATE UNIQUE INDEX users_username_lower_key ON users (lower(username));

CREATE TABLE shops (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id    INTEGER      NOT NULL REFERENCES users (id),
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    logo_url    TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX shops_owner_id_idx ON shops (owner_id);

CREATE TABLE categories (
    id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES categories (id)
);

CREATE TABLE products (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shop_id     INTEGER      NOT NULL REFERENCES shops (id),
    category_id INTEGER      NOT NULL REFERENCES categories (id),
    title       VARCHAR(150) NOT NULL,
    description TEXT,
    price       BIGINT       NOT NULL,
    stock       INTEGER      NOT NULL DEFAULT 0,
    sold_count  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT products_price_check CHECK (price >= 0),
    CONSTRAINT products_stock_check CHECK (stock >= 0)
);
CREATE INDEX products_shop_id_idx ON products (shop_id);
CREATE INDEX products_category_price_idx ON products (category_id, price);
CREATE INDEX products_price_idx ON products (price);

CREATE TABLE product_images (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    image_url  TEXT    NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX product_images_product_id_idx ON product_images (product_id);

INSERT INTO categories (name) VALUES
    ('موبایل'),
    ('لوازم خانگی'),
    ('پوشاک'),
    ('کتاب'),
    ('ورزش');
