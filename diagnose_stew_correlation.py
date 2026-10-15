import csv
from datetime import datetime, timedelta
from math import log
from pathlib import Path
from statistics import correlation
import sqlite3

folder = Path(__file__).resolve().parent
database = "file:C:/ArgentIQ/food_history_cleaning_work.sqlite3?mode=ro"
candidate_file = folder / ".tools" / "batch_price_review_candidates.csv"

flagged_times = set()

with candidate_file.open(newline="", encoding="utf-8-sig") as file:
    for row in csv.DictReader(file):
        if (
            row["item_id"] == "T8_MEAL_STEW"
            and row["market"] == "Martlock"
            and row["already_reviewed_and_excluded"].lower() == "false"
        ):
            flagged_times.add(datetime.fromisoformat(row["bucket_time"]))

with sqlite3.connect(database, uri=True) as connection:
    rows = connection.execute(
        """
        SELECT bucket_time_source, item_amount, silver_amount
        FROM food_history_market_6h
        WHERE item_id = 'T8_MEAL_STEW'
          AND location_id = 3008
        ORDER BY bucket_time_source
        """
    ).fetchall()

all_prices = {
    datetime.fromisoformat(timestamp): log(silver / items)
    for timestamp, items, silver in rows
}
without_candidates = {
    timestamp: price
    for timestamp, price in all_prices.items()
    if timestamp not in flagged_times
}

print(f"Martlock candidate timestamps temporarily omitted: {len(flagged_times)}")
for timestamp in sorted(flagged_times):
    print(f"  {timestamp}")

for label, prices in (
    ("All cleaned observations", all_prices),
    ("Temporarily omitting candidates", without_candidates),
):
    print(f"\n{label}: {len(prices)} buckets")

    for name, hours in (("6 hours", 6), ("1 day", 24), ("7 days", 168)):
        offset = timedelta(hours=hours)
        pairs = [
            (price, prices[timestamp + offset])
            for timestamp, price in prices.items()
            if timestamp + offset in prices
        ]

        value = correlation(
            [earlier for earlier, _ in pairs],
            [later for _, later in pairs],
        )
        print(f"  {name}: correlation={value:.3f}, pairs={len(pairs)}")