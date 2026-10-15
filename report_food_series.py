import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
import sqlite3

database = "file:C:/ArgentIQ/food_history_cleaning_work.sqlite3?mode=ro"
output = Path(__file__).resolve().parent / ".tools" / "food_series_coverage_report.csv"

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
    latest_text = connection.execute(
        "SELECT MAX(bucket_time_source) FROM food_history_market_6h"
    ).fetchone()[0]

    series = connection.execute(
        """
        SELECT h.item_id,
               COALESCE(f.display_name, h.item_id),
               h.location_id,
               COUNT(*) AS history_rows,
               COUNT(DISTINCT h.bucket_time_source) AS observed_buckets,
               MIN(h.bucket_time_source) AS first_bucket,
               MAX(h.bucket_time_source) AS last_bucket,
               SUM(
                   CASE
                       WHEN h.item_amount <= 0 OR h.silver_amount <= 0
                       THEN 1 ELSE 0
                   END
               ) AS nonpositive_rows
        FROM food_history_market_6h AS h
        LEFT JOIN food_items AS f ON f.item_id = h.item_id
        GROUP BY h.item_id, f.display_name, h.location_id
        ORDER BY h.location_id, h.item_id
        """
    ).fetchall()

latest = datetime.fromisoformat(latest_text)
summary = {market_id: Counter() for market_id in markets}
report_rows = []

for item_id, food_name, market_id, count, observed, first_text, last_text, invalid in series:
    first = datetime.fromisoformat(first_text)
    last = datetime.fromisoformat(last_text)

    expected = int((last - first).total_seconds() // (6 * 60 * 60)) + 1
    missing = expected - observed
    days_since_last = (latest - last).total_seconds() / (24 * 60 * 60)

    report_rows.append({
        "market": markets[market_id],
        "location_id": market_id,
        "item_id": item_id,
        "food_name": food_name,
        "history_rows": count,
        "observed_buckets": observed,
        "expected_buckets_between_first_and_last": expected,
        "missing_buckets_between_first_and_last": missing,
        "first_bucket": first_text,
        "last_bucket": last_text,
        "days_behind_dataset_latest": round(days_since_last, 2),
        "nonpositive_rows": invalid,
    })

    summary[market_id]["series"] += 1
    summary[market_id]["series_with_gaps"] += missing > 0
    summary[market_id]["missing_buckets"] += missing
    summary[market_id]["seen_within_2_days"] += days_since_last <= 2
    summary[market_id]["nonpositive_rows"] += invalid

output.parent.mkdir(exist_ok=True)

with output.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=report_rows[0].keys())
    writer.writeheader()
    writer.writerows(report_rows)

print(f"Dataset's latest bucket: {latest_text[:16]}")
print(f"Report: {output}")
print(f"Total food-market series: {len(report_rows)}")

for market_id, name in markets.items():
    counts = summary[market_id]
    print(
        f"{name}: {counts['series']} series, "
        f"{counts['series_with_gaps']} with internal gaps, "
        f"{counts['missing_buckets']} missing buckets, "
        f"{counts['seen_within_2_days']} seen within 2 days, "
        f"{counts['nonpositive_rows']} nonpositive rows"
    )