import csv
from collections import defaultdict
from pathlib import Path

source = Path(__file__).resolve().parent / ".tools" / "batch_price_review_candidates.csv"

groups = defaultdict(list)

with source.open(newline="", encoding="utf-8-sig") as file:
    for row in csv.DictReader(file):
        if row["already_reviewed_and_excluded"].lower() == "true":
            continue

        local_ratio = float(row["price"]) / float(row["nearby_market_median"])
        peer_ratio = float(row["price"]) / float(row["other_markets_median"])

        if row["flag"] == "high":
            strength = min(local_ratio, peer_ratio)
        else:
            strength = min(1 / local_ratio, 1 / peer_ratio)

        groups[(row["market"], row["flag"])].append((strength, row))

print("Closest-to-threshold new candidate in each market and direction:")

for market, flag in sorted(groups):
    strength, row = min(groups[(market, flag)], key=lambda entry: entry[0])
    print(
        f"{market} | {flag} | {row['item_id']} | "
        f"{row['bucket_time'][:16]} | "
        f"price={row['price']} | "
        f"local median={row['nearby_market_median']} | "
        f"other markets={row['other_markets_median']} | "
        f"items={row['item_amount']} | "
        f"strength={strength:.2f}x"
    )