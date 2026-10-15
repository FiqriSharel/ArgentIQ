import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import sqlite3

database = "file:C:/ArgentIQ/food_history_cleaning_work.sqlite3?mode=ro"
output = Path(__file__).resolve().parent / ".tools" / "food_series_runs.csv"

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
    latest_text = connection.execute(
        "SELECT MAX(bucket_time_source) FROM food_history_market_6h"
    ).fetchone()[0]

    names = dict(
        connection.execute("SELECT item_id, display_name FROM food_items")
    )

    for item_id, location_id, timestamp in connection.execute(
        """
        SELECT item_id, location_id, bucket_time_source
        FROM food_history_market_6h
        ORDER BY item_id, location_id, bucket_time_source
        """
    ):
        series[(item_id, location_id)].append(datetime.fromisoformat(timestamp))

latest = datetime.fromisoformat(latest_text)
report_rows = []

for (item_id, location_id), timestamps in series.items():
    current_run = 1
    longest_run = 1
    largest_gap = 0

    for previous, current in zip(timestamps, timestamps[1:]):
        hours_apart = (current - previous).total_seconds() / 3600

        if hours_apart == 6:
            current_run += 1
        else:
            if hours_apart > 6:
                missing = int(hours_apart / 6) - 1
                largest_gap = max(largest_gap, missing)
            current_run = 1

        longest_run = max(longest_run, current_run)

    last = timestamps[-1]
    report_rows.append({
        "market": markets[location_id],
        "item_id": item_id,
        "food_name": names.get(item_id, item_id),
        "observed_buckets": len(timestamps),
        "last_bucket": last.isoformat(sep=" "),
        "days_behind_dataset_latest": round(
            (latest - last).total_seconds() / 86400, 2
        ),
        "trailing_uninterrupted_buckets": current_run,
        "longest_uninterrupted_buckets": longest_run,
        "largest_internal_gap_buckets": largest_gap,
    })

output.parent.mkdir(exist_ok=True)

with output.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=report_rows[0].keys())
    writer.writeheader()
    writer.writerows(report_rows)

print(f"Report: {output}")
print(f"Series checked: {len(report_rows)}")
print("\nCabbage Soup:")

for row in report_rows:
    if row["item_id"] == "T5_MEAL_SOUP":
        print(
            f"{row['market']}: last={row['last_bucket'][:16]}, "
            f"trailing run={row['trailing_uninterrupted_buckets']}, "
            f"longest run={row['longest_uninterrupted_buckets']}, "
            f"largest gap={row['largest_internal_gap_buckets']}"
        )