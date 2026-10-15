import sqlite3

database = "file:C:/ArgentIQ/food_history_cleaning_work.sqlite3?mode=ro"

markets = {
    7: "Thetford",
    1002: "Lymhurst",
    2004: "Bridgewatch",
    3005: "Caerleon",
    3008: "Martlock",
    4002: "Fort Sterling",
    5003: "Brecilien",
}

with sqlite3.connect(database, uri=True) as connection:
    rows = connection.execute(
        """
        SELECT bucket_time_source,
               location_id,
               item_amount,
               ROUND(1.0 * silver_amount / NULLIF(item_amount, 0), 2)
        FROM food_history_market_6h
        WHERE item_id = 'T5_MEAL_SOUP'
          AND bucket_time_source >= '2026-06-07 12:00'
          AND bucket_time_source < '2026-06-08 18:00'
        ORDER BY bucket_time_source, location_id
        """
    ).fetchall()

for timestamp, location_id, items, price in rows:
    print(
        f"{timestamp[:16]} | {markets[location_id]:<13} | "
        f"items={items:>5} | average={price:>12}"
    )