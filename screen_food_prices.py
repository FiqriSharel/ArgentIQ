import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
import sqlite3

database = "file:C:/ArgentIQ/food_history_cleaning_work.sqlite3?mode=ro"
output = Path(__file__).resolve().parent / ".tools" / "batch_price_review_candidates.csv"

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
prices_by_time = defaultdict(list)

with sqlite3.connect(database, uri=True) as connection:
    names = dict(
        connection.execute("SELECT item_id, display_name FROM food_items")
    )

    reviewed = set(connection.execute(
        """
        SELECT item_id, location_id, bucket_time_source
        FROM food_history_exclusions
        WHERE server = 'Asia' AND quality = 1 AND aggregation = 6
        """
    ))

    for item_id, location_id, timestamp, items, silver in connection.execute(
        """
        SELECT item_id, location_id, bucket_time_source,
               item_amount, silver_amount
        FROM food_history
        WHERE server = 'Asia'
          AND quality = 1
          AND aggregation = 6
          AND location_id IN (7, 1002, 2004, 3005, 3008, 4002, 5003)
          AND item_amount > 0
          AND silver_amount > 0
        ORDER BY item_id, location_id, bucket_time_source
        """
    ):
        price = silver / items
        row = (datetime.fromisoformat(timestamp), timestamp, items, price)
        series[(item_id, location_id)].append(row)
        prices_by_time[(item_id, timestamp)].append((location_id, price))

candidates = []
candidate_keys = set()

for (item_id, location_id), observations in series.items():
    for index, (bucket_time, timestamp, items, price) in enumerate(observations):
        nearby = [
            observations[position][3]
            for position in range(
                max(0, index - 4),
                min(len(observations), index + 5),
            )
            if position != index
            and abs(
                (observations[position][0] - bucket_time).total_seconds()
            ) <= 24 * 60 * 60
        ]

        peers = [
            peer_price
            for peer_location, peer_price in prices_by_time[(item_id, timestamp)]
            if peer_location != location_id
        ]

        if len(nearby) < 4 or len(peers) < 3:
            continue

        local_median = median(nearby)
        peer_median = median(peers)
        local_ratio = price / local_median
        peer_ratio = price / peer_median

        if local_ratio >= 3 and peer_ratio >= 3:
            flag = "high"
        elif local_ratio <= 1 / 3 and peer_ratio <= 1 / 3:
            flag = "low"
        else:
            continue

        key = (item_id, location_id, timestamp)
        candidate_keys.add(key)

        candidates.append({
            "market": markets[location_id],
            "item_id": item_id,
            "food_name": names.get(item_id, item_id),
            "bucket_time": timestamp,
            "flag": flag,
            "price": round(price, 2),
            "nearby_market_median": round(local_median, 2),
            "other_markets_median": round(peer_median, 2),
            "local_ratio": round(local_ratio, 2),
            "peer_ratio": round(peer_ratio, 2),
            "item_amount": items,
            "already_reviewed_and_excluded": key in reviewed,
        })

output.parent.mkdir(exist_ok=True)

with output.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=[
        "market", "item_id", "food_name", "bucket_time", "flag",
        "price", "nearby_market_median", "other_markets_median",
        "local_ratio", "peer_ratio", "item_amount",
        "already_reviewed_and_excluded",
    ])
    writer.writeheader()
    writer.writerows(candidates)

print(f"Report: {output}")
print(f"Batch review candidates: {len(candidates)}")
print(f"Previously reviewed exclusions detected: {len(reviewed & candidate_keys)} of {len(reviewed)}")
print(f"New candidates: {len(candidate_keys - reviewed)}")

for item_id, location_id, timestamp in sorted(reviewed - candidate_keys):
    print(f"Reviewed exclusion missed by rule: {item_id}, {markets[location_id]}, {timestamp}")

cabbage = [row for row in candidates if row["item_id"] == "T5_MEAL_SOUP"]
print(f"Cabbage Soup candidates: {len(cabbage)}")