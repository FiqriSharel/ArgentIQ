from datetime import datetime, timedelta
from math import log
from statistics import correlation
import sqlite3

database = "file:C:/ArgentIQ/food_history_cleaning_work.sqlite3?mode=ro"

markets = {
    1002: "Lymhurst",
    2004: "Bridgewatch",
    3008: "Martlock",
}

with sqlite3.connect(database, uri=True) as connection:
    for location_id, name in markets.items():
        rows = connection.execute(
            """
            SELECT bucket_time_source, item_amount, silver_amount
            FROM food_history_market_6h
            WHERE item_id = 'T8_MEAL_STEW'
              AND location_id = ?
            ORDER BY bucket_time_source
            """,
            (location_id,),
        ).fetchall()

        log_prices = {
            datetime.fromisoformat(timestamp): log(silver / items)
            for timestamp, items, silver in rows
        }

        print(f"\n{name}: {len(log_prices)} observed buckets")

        for label, hours in (
            ("6 hours", 6),
            ("1 day", 24),
            ("7 days", 168),
        ):
            offset = timedelta(hours=hours)
            pairs = [
                (price, log_prices[timestamp + offset])
                for timestamp, price in log_prices.items()
                if timestamp + offset in log_prices
            ]

            earlier = [pair[0] for pair in pairs]
            later = [pair[1] for pair in pairs]
            value = correlation(earlier, later)

            print(
                f"  {label}: correlation={value:.3f}, "
                f"matched pairs={len(pairs)}"
            )