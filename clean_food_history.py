import sqlite3

database = r"C:\ArgentIQ\food_history_cleaning_work.sqlite3"

exclusions = [
    ("Asia", "T8_MEAL_STEW", 2004, 1, 6, "2026-04-24 00:00:00.000000", "reviewed_isolated_high"),
    ("Asia", "T8_MEAL_STEW", 2004, 1, 6, "2026-06-25 18:00:00.000000", "reviewed_isolated_high"),
    ("Asia", "T8_MEAL_STEW", 2004, 1, 6, "2026-10-08 12:00:00.000000", "reviewed_isolated_low"),
    ("Asia", "T8_MEAL_STEW", 3008, 1, 6, "2026-04-08 00:00:00.000000", "reviewed_isolated_high"),
    ("Asia", "T8_MEAL_STEW", 3008, 1, 6, "2026-06-30 00:00:00.000000", "reviewed_isolated_high"),
    ("Asia", "T8_MEAL_STEW", 3008, 1, 6, "2026-07-30 00:00:00.000000", "reviewed_isolated_high"),
    ("Asia", "T5_MEAL_SOUP", 3005, 1, 6, "2026-06-07 18:00:00.000000", "reviewed_cluster_high"),
    ("Asia", "T5_MEAL_SOUP", 3005, 1, 6, "2026-06-08 00:00:00.000000", "reviewed_cluster_high"),
    ("Asia", "T5_MEAL_SOUP", 3005, 1, 6, "2026-06-08 06:00:00.000000", "reviewed_cluster_high"),
]

with sqlite3.connect(database) as connection:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS food_history_exclusions (
            server TEXT NOT NULL,
            item_id TEXT NOT NULL,
            location_id INTEGER NOT NULL,
            quality INTEGER NOT NULL,
            aggregation INTEGER NOT NULL,
            bucket_time_source TEXT NOT NULL,
            reason TEXT NOT NULL,
            PRIMARY KEY (
                server, item_id, location_id, quality,
                aggregation, bucket_time_source
            )
        )
        """
    )

    connection.executemany(
        """
        INSERT OR IGNORE INTO food_history_exclusions
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        exclusions,
    )

    connection.execute(
        """
        CREATE VIEW IF NOT EXISTS food_history_cleaned AS
        SELECT h.*
        FROM food_history AS h
        WHERE NOT EXISTS (
            SELECT 1
            FROM food_history_exclusions AS e
            WHERE e.server = h.server
              AND e.item_id = h.item_id
              AND e.location_id = h.location_id
              AND e.quality = h.quality
              AND e.aggregation = h.aggregation
              AND e.bucket_time_source = h.bucket_time_source
        )
        """
    )

    connection.execute(
        """
        CREATE VIEW IF NOT EXISTS food_history_market_6h AS
        SELECT *
        FROM food_history_cleaned
        WHERE server = 'Asia'
          AND quality = 1
          AND aggregation = 6
          AND location_id IN (7, 1002, 2004, 3005, 3008, 4002, 5003)
        """
    )

    for name in (
        "food_history",
        "food_history_exclusions",
        "food_history_cleaned",
        "food_history_market_6h",
    ):
        count = connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"{name}: {count}")

    print("Integrity:", connection.execute("PRAGMA integrity_check").fetchone()[0])

cities = {
    1002: "Lymhurst",
    2004: "Bridgewatch",
    3008: "Martlock",
}

with sqlite3.connect(database) as connection:
    for location_id, city in cities.items():
        counts = []

        for table in ("food_history", "food_history_cleaned"):
            count = connection.execute(
                f"""
                SELECT COUNT(*) FROM {table}
                WHERE item_id = 'T8_MEAL_STEW'
                  AND location_id = ?
                  AND quality = 1
                  AND aggregation = 6
                """,
                (location_id,),
            ).fetchone()[0]
            counts.append(count)

        print(f"{city}: original={counts[0]}, cleaned={counts[1]}")