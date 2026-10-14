from collections import Counter, defaultdict
from datetime import datetime
import sqlite3

from argentiq.profile_food_history import review_flags

database = "file:C:/ArgentIQ/food_history_cleaning_work.sqlite3?mode=ro"

location_names = {
    7: "Thetford Market",
    8: "Morgana's Rest",
    320: "Willowshade Icemarsh",
    341: "Runnelvein Sink",
    344: "Willowshade Hills",
    1002: "Lymhurst Market",
    1006: "Forest Cross",
    1012: "Merlyn's Rest",
    1312: "Deadpine Forest",
    1339: "Timberslope Grove",
    1343: "Deepwood Copse",
    1359: "Rivercopse Fount",
    2004: "Bridgewatch Market",
    2308: "Drybasin Riverbed",
    2310: "Sunfang Ravine",
    2336: "Farshore Heath",
    2342: "Slakesands Mesa",
    2344: "Sunfang Wasteland",
    2347: "Dryvein Confluence",
    2348: "Sunstrand Quicksands",
    3003: "Caerleon",
    3005: "Caerleon Market",
    3008: "Martlock Market",
    3306: "Murdergulch Cross",
    3344: "Razorrock Verge",
    3345: "Razorrock Bank",
    3351: "Gravemound Knoll",
    3357: "Highstone Loch",
    4002: "Fort Sterling Market",
    4300: "Arthur's Rest",
    4318: "Iceburn Firth",
    4351: "Frostspring Volcano",
    4357: "Whitepeak Tundra",
    5003: "Brecilien Market",
}

series = defaultdict(list)
row_counts = Counter()

with sqlite3.connect(database, uri=True) as connection:
    for item_id, location_id, quality, aggregation, timestamp, items, silver in connection.execute(
        """
        SELECT item_id, location_id, quality, aggregation,
               bucket_time_source, item_amount, silver_amount
        FROM food_history
        WHERE aggregation = 6 AND quality = 1
        ORDER BY item_id, location_id, quality, aggregation, bucket_time_source
        """
    ):
        series[(item_id, location_id, quality, aggregation)].append(
            (datetime.fromisoformat(timestamp), items, silver, aggregation)
        )
        row_counts[location_id] += 1

flag_counts = Counter()
series_counts = Counter()

for (_, location_id, _, _), observations in series.items():
    series_counts[location_id] += 1
    for _, kind, _ in review_flags(observations):
        flag_counts[(location_id, kind)] += 1

print("Location | Rows | Series | Low flags | High flags | Flag rate")
for location_id in sorted(
    row_counts,
    key=lambda value: -(
        flag_counts[(value, "isolated_low")]
        + flag_counts[(value, "isolated_high")]
    ),
):
    low = flag_counts[(location_id, "isolated_low")]
    high = flag_counts[(location_id, "isolated_high")]
    rate = 100 * (low + high) / row_counts[location_id]
    name = location_names.get(location_id, f"Location {location_id}")
    print(
        f"{name} ({location_id}) | {row_counts[location_id]} | "
        f"{series_counts[location_id]} | {low} | {high} | {rate:.2f}%"
    )

print(f"\nLocations: {len(row_counts)}")
print(f"Total flags: {sum(flag_counts.values())}")