import sqlite3

database = "file:C:/ArgentIQ/food_history_cleaning_work.sqlite3?mode=ro"

names = {
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
        SELECT location_id,
               COUNT(*) AS history_rows,
               COUNT(DISTINCT item_id) AS food_items,
               MIN(bucket_time_source) AS first_bucket,
               MAX(bucket_time_source) AS last_bucket
        FROM food_history_market_6h
        GROUP BY location_id
        ORDER BY location_id
        """
    ).fetchall()

for location_id, count, items, first, last in rows:
    print(
        f"{names[location_id]}: {count} rows, {items} food items, "
        f"{first[:16]} to {last[:16]}"
    )

print(f"Markets: {len(rows)}")