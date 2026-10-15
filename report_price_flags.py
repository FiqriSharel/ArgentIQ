import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import sqlite3

from argentiq.profile_food_history import review_flags

database = "file:C:/ArgentIQ/food_history_cleaning_work.sqlite3?mode=ro"
output = Path(__file__).resolve().parent / ".tools" / "food_price_review_flags.csv"

markets = {
    7: "Thetford",
    1002: "Lymhurst",
    2004: "Bridgewatch",
    3005: "Caerleon",
    3008: "Martlock",
    4002: "Fort Sterling",
    5003: "Brecilien",
}

series = defaultdict(list)

with sqlite3.connect(database, uri=True) as connection:
    names = dict(
        connection.execute("SELECT item_id, display_name FROM food_items")
    )

    for item_id, location_id, timestamp, items, silver in connection.execute(
        """
        SELECT item_id, location_id, bucket_time_source,
               item_amount, silver_amount
        FROM food_history_market_6h
        ORDER BY item_id, location_id, bucket_time_source
        """
    ):
        series[(item_id, location_id)].append(
            (datetime.fromisoformat(timestamp), items, silver, 6)
        )

report_rows = []
flags_by_market = Counter()

for (item_id, location_id), observations in series.items():
    positions = {
        row[0].isoformat(sep=" "): index
        for index, row in enumerate(observations)
    }

    for timestamp, kind, flagged_price in review_flags(observations):
        index = positions[timestamp]
        previous = observations[index - 1]
        current = observations[index]
        following = observations[index + 1]

        report_rows.append({
            "market": markets[location_id],
            "location_id": location_id,
            "item_id": item_id,
            "food_name": names.get(item_id, item_id),
            "bucket_time": timestamp,
            "flag": kind,
            "previous_price": round(previous[2] / previous[1], 2),
            "flagged_price": flagged_price,
            "next_price": round(following[2] / following[1], 2),
            "item_amount": current[1],
            "silver_amount": current[2],
        })
        flags_by_market[location_id] += 1

output.parent.mkdir(exist_ok=True)

fieldnames = [
    "market", "location_id", "item_id", "food_name", "bucket_time",
    "flag", "previous_price", "flagged_price", "next_price",
    "item_amount", "silver_amount",
]

with output.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(report_rows)

print(f"Report: {output}")
print(f"Provisional price flags: {len(report_rows)}")

for location_id, name in markets.items():
    print(f"{name}: {flags_by_market[location_id]} flags")

cabbage_flags = [
    row for row in report_rows if row["item_id"] == "T5_MEAL_SOUP"
]
print(f"Cabbage Soup: {len(cabbage_flags)} flags")

for row in cabbage_flags[:20]:
    print(
        f"{row['market']} | {row['bucket_time']} | {row['flag']} | "
        f"{row['previous_price']} -> {row['flagged_price']} "
        f"-> {row['next_price']}"
    )