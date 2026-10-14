import sqlite3

database = "file:C:/ArgentIq/food_history_cleaning_work.sqlite3?mode=ro"

with sqlite3.connect(database, uri=True) as connection:
    rows = connection.execute(
        """
        SELECT bucket_time_source,
               item_amount,
               silver_amount,
               ROUND(1.0*silver_amount / NULLIF(item_amount, 0), 2)
        FROM food_history
        WHERE item_id = ?
            AND location_id = ?
            AND quality = 1
            AND aggregation = 6
            AND bucket_time_source >= ?
            AND bucket_time_source < ?
        ORDER BY bucket_time_source
        """,
        ("T8_MEAL_STEW", 2004, "2026-10-07", "2026-10-09"),
    ).fetchall()

for timestamp, item_amount, silver_amount, average_price in rows:
    print(
        f"{timestamp[:16]} | items = {item_amount:>5} | "
        f"silver={silver_amount:>9} | average={average_price:>8}"
    )

print("\nOther locations at 2026-06-25 00:00")

with sqlite3.connect(database, uri=True) as connection:
    other_locations = connection.execute(
        """
        SELECT  location_id,
                item_amount, 
                ROUND(1.0*silver_amount / NULLIF(item_amount, 0), 2)
                
        FROM food_history
        WHERE item_id = 'T8_MEAL_STEW'
            AND quality = 1
            AND aggregation = 6
            AND bucket_time_source >= '2026-06-25 18:00'
            AND bucket_time_source < '2026-06-25 19:00'
        ORDER BY location_id
        """
    ).fetchall()

for location_id, item_amount, average_price in other_locations: 
    print(
        f"location_id={location_id:>4} | items = {item_amount:>5} | "
        f"average={average_price:>8}"
    )

from datetime import datetime
from argentiq.profile_food_history import review_flags

with sqlite3.connect(database, uri=True) as connection:
    series = connection.execute(
        """
        SELECT bucket_time_source, item_amount, silver_amount, aggregation
        FROM food_history
        WHERE item_id = 'T8_MEAL_STEW'
            AND location_id = 2004
            AND quality = 1
            AND aggregation = 6
        ORDER BY bucket_time_source
        """
    ).fetchall()

prepared = [
    (datetime.fromisoformat(timestamp), items, silver, aggregation)
    for timestamp, items, silver, aggregation in series
]
flags = review_flags(prepared)

print(f"\nBridgewatch Beef Stew: {len(flags)} review flags")
for timestamp, reason, price in flags:
    print(timestamp, reason, price)

print("\nContext around each flag:")

for flagged_timestamp, reason, _ in flags:
    flagged_time = datetime.fromisoformat(flagged_timestamp)
    index = next(
        index for index, row in enumerate(prepared)
        if row[0] == flagged_time
    )

    print(f"\n{flagged_timestamp} — {reason}")
    for timestamp, items, silver, _ in prepared[index - 1:index + 2]:
        price = round(silver / items, 2)
        print(
            f"  {timestamp:%Y-%m-%d %H:%M} | "
            f"items={items:>5} | average={price:>9}"
        )