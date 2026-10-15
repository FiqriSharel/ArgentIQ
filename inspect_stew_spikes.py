from datetime import datetime, timedelta
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

spikes = [
    datetime(2026, 4, 8, 0),
    datetime(2026, 6, 30, 0),
    datetime(2026, 7, 30, 0),
]

def sql_time(value):
    return value.strftime("%Y-%m-%d %H:%M:%S.%f")

with sqlite3.connect(database, uri=True) as connection:
    for spike in spikes:
        print(f"\n=== {spike} ===")

        print("Martlock before, during, and after:")
        local_rows = connection.execute(
            """
            SELECT bucket_time_source, item_amount,
                   ROUND(1.0 * silver_amount / item_amount, 2)
            FROM food_history_market_6h
            WHERE item_id = 'T8_MEAL_STEW'
              AND location_id = 3008
              AND bucket_time_source >= ?
              AND bucket_time_source <= ?
            ORDER BY bucket_time_source
            """,
            (
                sql_time(spike - timedelta(hours=6)),
                sql_time(spike + timedelta(hours=6)),
            ),
        ).fetchall()

        for timestamp, items, price in local_rows:
            print(f"  {timestamp[:16]} | items={items:>5} | price={price:>10}")

        print("All markets at the spike time:")
        market_rows = connection.execute(
            """
            SELECT location_id, item_amount,
                   ROUND(1.0 * silver_amount / item_amount, 2)
            FROM food_history_market_6h
            WHERE item_id = 'T8_MEAL_STEW'
              AND bucket_time_source = ?
            ORDER BY location_id
            """,
            (sql_time(spike),),
        ).fetchall()

        for location_id, items, price in market_rows:
            print(
                f"  {markets[location_id]:<13} | "
                f"items={items:>5} | price={price:>10}"
            )