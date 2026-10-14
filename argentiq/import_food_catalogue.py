"""Add metadata-listed prepared meals to the food-only SQLite database."""

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


MEAL_ID = re.compile(r"^T(?P<tier>[0-9]+)_MEAL_(?P<type>[A-Z]+)(?:_[A-Z0-9_]+)?(?:@(?P<enchantment>[0-9]+))?$")
FOOD_TYPES = {
    "GRILLEDFISH", "SEAWEEDSALAD", "SOUP", "SALAD", "OMELETTE",
    "PIE", "ROAST", "STEW", "SANDWICH", "SPECIAL",
}


def read_catalogue(path: Path) -> tuple[list[tuple], str]:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        raw = source.read()
    digest.update(raw)
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Expected a list of formatted item metadata")

    meals = []
    seen = set()
    for entry in data:
        if not isinstance(entry, dict):
            continue
        item_id = entry.get("UniqueName")
        if not isinstance(item_id, str) or "_MEAL_" not in item_id:
            continue
        match = MEAL_ID.fullmatch(item_id)
        if not match or match.group("type") not in FOOD_TYPES:
            raise ValueError(f"Unrecognised meal item ID: {item_id!r}")
        if item_id in seen:
            raise ValueError(f"Duplicate meal item ID: {item_id}")
        seen.add(item_id)
        names = entry.get("LocalizedNames") or {}
        name = names.get("EN-US") if isinstance(names, dict) else None
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Missing English name for {item_id}")
        index = entry.get("Index")
        if not isinstance(index, (str, int)):
            raise ValueError(f"Missing metadata index for {item_id}")
        meals.append((
            item_id, item_id.split("@", 1)[0], name.strip(),
            match.group("type"), int(match.group("tier")),
            int(match.group("enchantment") or 0), str(index),
        ))
    if not meals:
        raise ValueError("No prepared-meal entries found in metadata")
    return meals, digest.hexdigest()


def import_catalogue(metadata_path: Path, database_path: Path) -> dict:
    if not metadata_path.is_file() or not database_path.is_file():
        raise FileNotFoundError("Metadata JSON and food SQLite database must both exist")
    meals, sha256 = read_catalogue(metadata_path)
    imported_at = datetime.now(timezone.utc).isoformat()
    db = sqlite3.connect(database_path)
    try:
        present = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='food_history'").fetchone()
        if not present:
            raise ValueError("Target database has no food_history table")
        if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='food_items'").fetchone():
            raise ValueError("food_items already exists; this importer will not overwrite it")
        db.execute("BEGIN")
        db.execute("""CREATE TABLE food_items (
            item_id TEXT PRIMARY KEY,
            base_item_id TEXT NOT NULL,
            display_name TEXT NOT NULL,
            food_type_code TEXT NOT NULL,
            tier INTEGER NOT NULL,
            enchantment INTEGER NOT NULL,
            metadata_index TEXT NOT NULL,
            metadata_sha256 TEXT NOT NULL,
            imported_at_utc TEXT NOT NULL
        )""")
        db.execute("CREATE INDEX food_items_search ON food_items (food_type_code, display_name, tier, enchantment)")
        db.execute("""CREATE TABLE catalogue_imports (
            metadata_sha256 TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            imported_at_utc TEXT NOT NULL,
            item_count INTEGER NOT NULL
        )""")
        db.executemany("INSERT INTO food_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       [(*meal, sha256, imported_at) for meal in meals])
        db.execute("INSERT INTO catalogue_imports VALUES (?, ?, ?, ?)",
                   (sha256, metadata_path.name, imported_at, len(meals)))
        db.execute("""CREATE VIEW food_coverage AS
            SELECT f.item_id, f.display_name, f.food_type_code, f.tier, f.enchantment,
                   COUNT(h.item_id) AS history_rows_all_locations,
                   MIN(h.bucket_time_source) AS first_history_bucket,
                   MAX(h.bucket_time_source) AS last_history_bucket
            FROM food_items f LEFT JOIN food_history h ON h.item_id = f.item_id
            GROUP BY f.item_id""")
        matched = db.execute("""SELECT COUNT(DISTINCT h.item_id)
            FROM food_history h LEFT JOIN food_items f ON f.item_id = h.item_id
            WHERE f.item_id IS NOT NULL""").fetchone()[0]
        unmatched = db.execute("""SELECT COUNT(DISTINCT h.item_id)
            FROM food_history h LEFT JOIN food_items f ON f.item_id = h.item_id
            WHERE f.item_id IS NULL""").fetchone()[0]
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return {"catalogue_ids": len(meals), "history_matched_ids": matched,
            "history_unmatched_ids": unmatched, "metadata_sha256": sha256}


def main() -> int:
    parser = argparse.ArgumentParser(description="Add prepared-meal metadata to an existing food-history SQLite file")
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = import_catalogue(args.metadata, args.database)
    except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as error:
        print(f"Catalogue import failed: {error}", file=sys.stderr)
        return 1
    print(f"Imported {result['catalogue_ids']} metadata-listed meal IDs")
    print(f"History IDs matched: {result['history_matched_ids']}; unmatched: {result['history_unmatched_ids']}")
    print("Metadata SHA-256:", result["metadata_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
