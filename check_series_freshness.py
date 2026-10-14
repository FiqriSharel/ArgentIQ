from datetime import datetime
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

with sqlite3.connect(database, uri=True) as connection:
    rows = connection.execute(
        """
        SELECT location_id, item_id, MAX(bucket_time_source)
        FROM food_history_market_6h
        GROUP BY location_id, item_id
        """
    ).fetchall()

as_of = max(datetime.fromisoformat(last) for _, _, last in rows)
print(f"Latest bucket in the dataset: {as_of}")

for location_id, name in markets.items():
    latest_by_item = [
        datetime.fromisoformat(last)
        for market_id, _, last in rows
        if market_id == location_id
    ]

    within_2_days = sum(
        (as_of - last).total_seconds() <= 2 * 86400
        for last in latest_by_item
    )
    within_7_days = sum(
        (as_of - last).total_seconds() <= 7 * 86400
        for last in latest_by_item
    )

    print(
        f"{name}: {len(latest_by_item)} items; "
        f"{within_2_days} seen within 2 days; "
        f"{within_7_days} seen within 7 days"
    )
