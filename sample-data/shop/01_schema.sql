CREATE TABLE categories (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    price       NUMERIC(10, 2) NOT NULL
);

CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    full_name   TEXT NOT NULL,
    city        TEXT NOT NULL,
    signup_date DATE NOT NULL
);

CREATE TABLE orders (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date  DATE NOT NULL,
    status      TEXT NOT NULL,
    channel     TEXT NOT NULL
);

CREATE TABLE order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity   INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

CREATE INDEX orders_order_date_idx ON orders(order_date);
CREATE INDEX order_items_order_id_idx ON order_items(order_id);

COMMENT ON TABLE orders IS 'One row per customer order';
COMMENT ON COLUMN orders.status IS 'delivered, returned, cancelled or processing';
COMMENT ON COLUMN order_items.unit_price IS 'Price actually paid per unit, in MKD';
