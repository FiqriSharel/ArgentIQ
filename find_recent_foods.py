import sqlite3

database = "file:C:/ArgentIQ/food_history_cleaning_work.sqlite3?mode=ro"

with sqlite3.connect(database, uri=True) as connection:
    latest = connection.execute(
        "SELECT MAX(bucket_time_source) FROM food_history_market_6h"
    ).fetchone()[0]

    rows = connection.execute(
        """
        WITH series AS (
            SELECT item_id, location_id,
                   MAX(bucket_time_source) AS last_bucket
            FROM food_history_market_6h
            GROUP BY item_id, location_id
        )
        SELECT s.item_id,
               COALESCE(i.display_name, s.item_id) AS food_name,
               COUNT(*) AS markets_with_history,
               SUM(
                   CASE
                       WHEN julianday(?) - julianday(s.last_bucket) <= 2
                       THEN 1 ELSE 0
                   END
               ) AS markets_recent_in_snapshot
        FROM series AS s
        LEFT JOIN food_items AS i ON i.item_id = s.item_id
        GROUP BY s.item_id, i.display_name
        ORDER BY markets_recent_in_snapshot DESC,
                 markets_with_history DESC,
                 s.item_id
        LIMIT 20
        """,
        (latest,),
    ).fetchall()

print(f"Dataset's latest bucket: {latest[:16]}")
print("Food | Markets with history | Markets seen within 2 days")

for item_id, name, all_markets, recent_markets in rows:
    print(f"{name} ({item_id}) | {all_markets} | {recent_markets}")