"""Import observed Asia prepared-meal history from an AODP SQL backup.

The archive is streamed: the MariaDB dump is never extracted or imported whole.
This is an observed-history subset, not a complete food catalogue.
"""

import argparse
import hashlib
import re
import sqlite3
import sys
import tarfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


INSERT_PREFIX = b"INSERT INTO `market_history` VALUES "
ITEM_ID = rb"T[0-9]+_MEAL_[A-Z0-9_]+(?:@[0-9]+)?"
ITEM_REFERENCE = re.compile(rb"'(" + ITEM_ID + rb")'")
HISTORY_ROW = re.compile(
    rb"\((\d+),(\d+),(\d+),'(" + ITEM_ID + rb")',(\d+),(\d+),"
    rb"'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6})',(\d+)\)"
)


def archive_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def iter_food_rows(archive_path: Path):
    """Yield exact meal-ID rows only from the East market_history INSERTs."""
    with tarfile.open(archive_path, "r:gz") as archive:
        members = [member for member in archive if member.isfile()]
        if len(members) != 1 or not members[0].name.endswith(".sql"):
            raise ValueError("Expected one SQL dump inside the archive")
        source = archive.extractfile(members[0])
        if source is None:
            raise ValueError("Could not read SQL dump")
        first = source.read(1024)
        if b"Database: albion-east" not in first:
            raise ValueError("This is not an Albion East/Asia database dump")
        source.seek(0)
        in_history = False
        found_history = False
        for line in source:
            if line.startswith(b"-- Table structure for table `market_history`"):
                in_history = True
                found_history = True
            elif in_history and line.startswith(b"-- Table structure for table `"):
                break
            if not in_history or not line.startswith(INSERT_PREFIX):
                continue
            references = ITEM_REFERENCE.findall(line)
            if not references:
                continue
            matches = list(HISTORY_ROW.finditer(line))
            if len(matches) != len(references):
                raise ValueError("A food history row did not match the expected SQL schema")
            for match in matches:
                row_id, item_amount, silver_amount, item_id, location, quality, timestamp, aggregation = match.groups()
                if item_amount == b"0" or quality == b"0" or aggregation == b"0":
                    raise ValueError("A food history row has an invalid amount, quality, or aggregation")
                yield (
                    item_id.decode("ascii"), int(location), int(quality),
                    timestamp.decode("ascii"), int(aggregation),
                    int(item_amount), int(silver_amount),
                )
        if not found_history:
            raise ValueError("No market_history table found in the dump")


def import_archive(archive_path: Path, output_path: Path) -> dict:
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)
    if output_path.exists():
        raise FileExistsError(f"Output already exists: {output_path}")
    if not output_path.parent.is_dir():
        raise FileNotFoundError(output_path.parent)

    sha256 = archive_hash(archive_path)
    imported_at = datetime.now(timezone.utc).isoformat()
    counts = Counter()
    db = sqlite3.connect(output_path)
    try:
        db.execute("BEGIN")
        db.executescript("""
            CREATE TABLE food_history (
                server TEXT NOT NULL DEFAULT 'Asia' CHECK (server = 'Asia'),
                item_id TEXT NOT NULL,
                location_id INTEGER NOT NULL,
                quality INTEGER NOT NULL,
                bucket_time_source TEXT NOT NULL,
                aggregation INTEGER NOT NULL,
                item_amount INTEGER NOT NULL,
                silver_amount INTEGER NOT NULL,
                source_sha256 TEXT NOT NULL,
                imported_at_utc TEXT NOT NULL,
                PRIMARY KEY (server, item_id, location_id, quality,
                             bucket_time_source, aggregation)
            );
            CREATE INDEX food_history_range ON food_history
                (item_id, location_id, quality, bucket_time_source);
            CREATE TABLE import_runs (
                source_sha256 TEXT PRIMARY KEY,
                archive_name TEXT NOT NULL,
                compressed_bytes INTEGER NOT NULL,
                imported_at_utc TEXT NOT NULL,
                history_rows INTEGER NOT NULL,
                observed_item_ids INTEGER NOT NULL
            );
        """)
        sql = """INSERT INTO food_history
            (item_id, location_id, quality, bucket_time_source, aggregation,
             item_amount, silver_amount, source_sha256, imported_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        batch = []
        for row in iter_food_rows(archive_path):
            counts[row[0]] += 1
            batch.append((*row, sha256, imported_at))
            if len(batch) >= 1000:
                db.executemany(sql, batch)
                batch.clear()
        if batch:
            db.executemany(sql, batch)
        if not counts:
            raise ValueError("No prepared-meal history rows found")
        db.execute("INSERT INTO import_runs VALUES (?, ?, ?, ?, ?, ?)", (
            sha256, archive_path.name, archive_path.stat().st_size,
            imported_at, sum(counts.values()), len(counts),
        ))
        db.commit()
    except Exception:
        db.rollback()
        db.close()
        output_path.unlink(missing_ok=True)
        raise
    else:
        db.close()
    return {"rows": sum(counts.values()), "item_ids": len(counts), "sha256": sha256}


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Asia prepared-meal history into a food-only SQLite file")
    parser.add_argument("--archive", required=True, type=Path, help="AODP East db_backup_*.tgz")
    parser.add_argument("--output", required=True, type=Path, help="New SQLite file; must not already exist")
    args = parser.parse_args()
    try:
        result = import_archive(args.archive, args.output)
    except (OSError, ValueError, tarfile.TarError, sqlite3.Error) as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 1
    print(f"Imported {result['rows']} meal-history rows for {result['item_ids']} observed item IDs into {args.output}")
    print("Source SHA-256:", result["sha256"])
    print("Food catalogue and price-field semantics still require separate verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
