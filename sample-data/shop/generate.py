"""Generate the synthetic "online clothing shop" sample database.

Run from the repo root:  python sample-data/shop/generate.py
It writes 02_data.sql next to this file. The output is the same on every run (fixed seed).

Patterns planted on purpose, so we can later check the agents find them:
  * steady growth over time, a Nov-Dec peak and an August dip
  * jackets sell mostly in autumn and winter
  * September 2026: jacket returns roughly double  (an insight to find)
  * last week of October 2026: orders drop ~25%      (an alert to raise)
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
START = date(2024, 1, 1)
END = date(2026, 10, 31)
OUT = Path(__file__).with_name("02_data.sql")

CITIES = [
    ("Skopje", 40), ("Bitola", 9), ("Kumanovo", 9), ("Tetovo", 8), ("Prilep", 6),
    ("Ohrid", 6), ("Veles", 4), ("Shtip", 4), ("Strumica", 4), ("Gostivar", 5),
    ("Kavadarci", 3), ("Kochani", 2),
]
FIRST = ["Ana", "Marija", "Elena", "Sara", "Ivana", "Jovana", "Teodora", "Mila",
         "Stefan", "Nikola", "Aleksandar", "Marko", "David", "Filip", "Bojan", "Luka",
         "Arta", "Edona", "Besnik", "Driton", "Leonora", "Ardit", "Vesna", "Goran"]
LAST = ["Petrovski", "Stojanovska", "Nikolovski", "Georgieva", "Trajkovski",
        "Ilievska", "Dimitrovski", "Angelova", "Jovanovski", "Ristovska",
        "Krasniqi", "Shabani", "Iseni", "Ademi", "Spasovski", "Todorova"]

CATEGORIES = {
    "Jackets":     (["Winter Parka", "Denim Jacket", "Leather Jacket", "Rain Jacket",
                     "Puffer Jacket", "Wool Coat"], (2500, 7500),
                    [1.6, 1.3, 0.8, 0.5, 0.3, 0.2, 0.2, 0.3, 0.9, 1.5, 1.9, 2.0]),
    "T-shirts":    (["Basic Tee", "Graphic Tee", "Polo Shirt", "Oversized Tee",
                     "Long Sleeve Tee"], (400, 1200),
                    [0.6, 0.6, 0.9, 1.1, 1.5, 1.8, 1.8, 1.3, 1.0, 0.8, 0.7, 0.9]),
    "Jeans":       (["Slim Jeans", "Straight Jeans", "Mom Jeans", "Wide Leg Jeans"],
                    (1500, 3500), [1.0] * 12),
    "Shoes":       (["Sneakers", "Boots", "Sandals", "Loafers", "Running Shoes"],
                    (1800, 5500),
                    [1.0, 0.9, 1.0, 1.1, 1.2, 1.3, 1.2, 0.9, 1.1, 1.1, 1.2, 1.4]),
    "Dresses":     (["Summer Dress", "Evening Dress", "Shirt Dress", "Knit Dress"],
                    (1600, 4800),
                    [0.6, 0.7, 0.9, 1.1, 1.4, 1.6, 1.6, 1.2, 0.9, 0.8, 0.8, 1.3]),
    "Accessories": (["Scarf", "Beanie", "Belt", "Sunglasses", "Backpack", "Cap"],
                    (300, 2200),
                    [1.2, 1.0, 0.8, 0.8, 1.0, 1.1, 1.1, 0.9, 0.9, 1.0, 1.3, 1.8]),
}
MONTH_FACTOR = [0.9, 0.8, 0.95, 1.0, 1.0, 0.95, 0.9, 0.65, 1.0, 1.05, 1.35, 1.6]
WEEKDAY_FACTOR = [0.9, 0.95, 1.0, 1.0, 1.1, 1.2, 1.15]
CHANNELS = [("web", 55), ("mobile_app", 35), ("instagram", 10)]


def weighted(rng: random.Random, pairs):
    items, weights = zip(*pairs)
    return rng.choices(items, weights=weights, k=1)[0]


def copy_block(table: str, columns: list[str], rows: list[tuple]) -> str:
    """Postgres COPY format: much faster to load than thousands of INSERTs."""
    def fmt(v):
        return r"\N" if v is None else str(v).replace("\t", " ").replace("\n", " ")

    lines = [f"COPY {table} ({', '.join(columns)}) FROM stdin;"]
    lines += ["\t".join(fmt(v) for v in row) for row in rows]
    lines.append("\\.\n")
    return "\n".join(lines)


def main() -> None:
    rng = random.Random(SEED)

    categories, products = [], []
    pid = 0
    for cid, (cname, (names, (lo, hi), _season)) in enumerate(CATEGORIES.items(), 1):
        categories.append((cid, cname))
        for name in names:
            pid += 1
            products.append((pid, name, cid, round(rng.uniform(lo, hi) / 10) * 10))
    product_by_cat: dict[int, list[tuple]] = {}
    for p in products:
        product_by_cat.setdefault(p[2], []).append(p)
    season = {cid: CATEGORIES[name][2] for cid, name in categories}

    customers = []
    total_days = (END - START).days
    for cust_id in range(1, 3001):
        signup = START + timedelta(days=int(rng.triangular(0, total_days, total_days * 0.6)))
        customers.append((cust_id, f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                          weighted(rng, CITIES), signup.isoformat()))

    orders, items = [], []
    oid = iid = 0
    day = START
    while day <= END:
        months_in = (day.year - START.year) * 12 + day.month - 1
        growth = 1 + months_in * 0.025
        base = 14 * growth * MONTH_FACTOR[day.month - 1] * WEEKDAY_FACTOR[day.weekday()]
        if date(2026, 10, 25) <= day <= END:
            base *= 0.75
        n_orders = max(0, int(rng.gauss(base, base ** 0.5)))
        eligible = [c for c in customers if c[3] <= day.isoformat()] or customers[:50]

        for _ in range(n_orders):
            oid += 1
            cust = rng.choice(eligible)
            n_items = weighted(rng, [(1, 60), (2, 28), (3, 9), (4, 3)])
            has_jacket = False
            for _ in range(n_items):
                cat_weights = [(cid, season[cid][day.month - 1]) for cid, _ in categories]
                cid = weighted(rng, cat_weights)
                prod = rng.choice(product_by_cat[cid])
                has_jacket |= cid == 1
                iid += 1
                discount = rng.choice([1.0, 1.0, 1.0, 0.9, 0.8]) if day.month in (1, 7) else 1.0
                items.append((iid, oid, prod[0], weighted(rng, [(1, 85), (2, 12), (3, 3)]),
                              round(prod[3] * discount)))

            return_rate = 0.06
            if has_jacket:
                return_rate = 0.09
                if day.year == 2026 and day.month == 9:
                    return_rate = 0.19
            r = rng.random()
            if r < return_rate:
                status = "returned"
            elif r < return_rate + 0.03:
                status = "cancelled"
            elif (END - day).days < 4:
                status = "processing"
            else:
                status = "delivered"
            orders.append((oid, cust[0], day.isoformat(), status, weighted(rng, CHANNELS)))
        day += timedelta(days=1)

    parts = [
        copy_block("categories", ["id", "name"], categories),
        copy_block("products", ["id", "name", "category_id", "price"], products),
        copy_block("customers", ["id", "full_name", "city", "signup_date"], customers),
        copy_block("orders", ["id", "customer_id", "order_date", "status", "channel"], orders),
        copy_block("order_items",
                   ["id", "order_id", "product_id", "quantity", "unit_price"], items),
    ]
    for table in ["categories", "products", "customers", "orders", "order_items"]:
        parts.append(f"SELECT setval('{table}_id_seq', (SELECT max(id) FROM {table}));")
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {OUT.name}: {len(customers)} customers, {len(orders)} orders, "
          f"{len(items)} items")


if __name__ == "__main__":
    main()
