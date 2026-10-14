from datetime import datetime
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
        SELECT location_id,
               COUNT(*) AS rows,
               COUNT(DISTINCT bucket_time_source) AS observed_buckets,
               MIN(bucket_time_source) AS first_bucket,
               MAX(bucket_time_source) AS last_bucket
        FROM food_history_market_6h
        WHERE item_id = 'T8_MEAL_STEW'
        GROUP BY location_id
        """
    ).fetchall()

results = {row[0]: row[1:] for row in rows}

for location_id, name in markets.items():
    if location_id not in results:
        print(f"{name}: no T8 Beef Stew history")
        continue

    count, observed, first, last = results[location_id]
    start = datetime.fromisoformat(first)
    end = datetime.fromisoformat(last)
    expected = int((end - start).total_seconds() / (6 * 60 * 60)) + 1
    missing = expected - observed

    print(
        f"{name}: rows={count}, observed={observed}, "
        f"expected={expected}, missing={missing}, "
        f"first={first[:16]}, last={last[:16]}"
    )
