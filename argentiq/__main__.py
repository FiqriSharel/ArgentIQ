"""Run a small Asia market probe and print quote age by city."""

import argparse
import logging
import sys
from datetime import datetime, timezone

from .collector import fetch, save
from .market import Quote, freshness


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe AODP Asia market prices")
    parser.add_argument("--items", default="T4_BAG,T5_BAG")
    parser.add_argument("--cities", default="Bridgewatch,Martlock,Caerleon")
    parser.add_argument("--qualities", default="1")
    parser.add_argument("--db", default="argentiq.sqlite3")
    parser.add_argument("--fresh-minutes", type=int, default=60)
    parser.add_argument("--aging-minutes", type=int, default=360)
    args = parser.parse_args()
    if args.fresh_minutes <= 0 or args.aging_minutes <= args.fresh_minutes:
        parser.error("aging-minutes must exceed positive fresh-minutes")
    items = [x.strip() for x in args.items.split(",") if x.strip()]
    cities = [x.strip() for x in args.cities.split(",") if x.strip()]
    try:
        qualities = [int(x) for x in args.qualities.split(",")]
    except ValueError:
        parser.error("qualities must be comma-separated integers")
    if not items or not cities or not qualities or any(q < 1 or q > 5 for q in qualities):
        parser.error("provide items, cities, and quality values 1 through 5")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    try:
        observations = fetch(items, cities, qualities)
        save(args.db, observations)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"Collection failed: {exc}", file=sys.stderr)
        return 1
    now = datetime.now(timezone.utc)
    found = {(o.item_id, o.city, o.quality): o for o in observations}
    print("Asia (AODP East) | source dates interpreted as UTC provisionally | prices are observations, not fills")
    print("Item | City | Q | Ask: instant buy | Bid: instant sell | Received UTC")
    for item in items:
        for city in cities:
            for quality in qualities:
                obs = found.get((item, city, quality))
                def describe(q: Quote) -> str:
                    status, age = freshness(q, now, args.fresh_minutes, args.aging_minutes)
                    return f"{q.price} ({status}, {age}m, {q.source_at.isoformat()})" if q.price is not None else "unavailable"
                if obs:
                    print(f"{item} | {city} | {quality} | {describe(obs.sell)} | {describe(obs.buy)} | {obs.received_at.isoformat()}")
                else:
                    print(f"{item} | {city} | {quality} | unavailable | unavailable | no row")
    print(f"Stored {len(observations)} returned rows in {args.db}; rerun to refresh. No profit recommendations are computed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
