"""Read-only coverage and price review report for imported food history."""

import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


def review_flags(rows):
    """Flag isolated prices that differ sharply from both adjacent buckets.

    This is a review screen, not a rule for deleting or replacing observations.
    Rows are (timestamp, item_amount, silver_amount, aggregation) in time order.
    """
    flags = []
    for index in range(1, len(rows) - 1):
        previous, current, following = rows[index - 1:index + 2]
        interval = timedelta(hours=current[3])
        if (current[3] not in (1, 6, 24)
                or current[0] - previous[0] != interval
                or following[0] - current[0] != interval):
            continue
        if any(row[1] <= 0 for row in (previous, current, following)):
            continue
        prices = [row[2] / row[1] for row in (previous, current, following)]
        if prices[1] < min(prices[0], prices[2]) / 2:
            flags.append((current[0].isoformat(sep=' '), 'isolated_low', round(prices[1], 2)))
        elif prices[1] > max(prices[0], prices[2]) * 2:
            flags.append((current[0].isoformat(sep=' '), 'isolated_high', round(prices[1], 2)))
    return flags


def profile(database: Path) -> dict:
    connection = sqlite3.connect(f'file:{database.as_posix()}?mode=ro', uri=True)
    try:
        catalogue_items = connection.execute('SELECT COUNT(*) FROM food_items').fetchone()[0]
        rows = connection.execute('''
            SELECT item_id, location_id, quality, aggregation, bucket_time_source,
                   item_amount, silver_amount
            FROM food_history
            ORDER BY item_id, location_id, quality, aggregation, bucket_time_source
        ''')
        series_count = 0
        missing_buckets = 0
        invalid_amount_rows = 0
        flag_counts = Counter()
        examples = []
        current_key = None
        series_rows = []
        observed_items = set()
        total_rows = 0

        def finish_series():
            nonlocal series_count, missing_buckets
            if not series_rows:
                return
            series_count += 1
            interval_hours = current_key[3]
            if interval_hours in (1, 6, 24):
                span = series_rows[-1][0] - series_rows[0][0]
                missing_buckets += max(0, round(span.total_seconds() / (interval_hours * 3600)) + 1 - len(series_rows))
            for timestamp, kind, price in review_flags(series_rows):
                flag_counts[kind] += 1
                if len(examples) < 20:
                    examples.append({'item_id': current_key[0], 'location_id': current_key[1],
                                     'quality': current_key[2], 'aggregation': interval_hours,
                                     'bucket_time_source': timestamp, 'kind': kind,
                                     'average_price': price})

        for item_id, location_id, quality, aggregation, timestamp, item_amount, silver_amount in rows:
            key = (item_id, location_id, quality, aggregation)
            if key != current_key:
                finish_series()
                series_rows = []
                current_key = key
            series_rows.append((datetime.fromisoformat(timestamp), item_amount, silver_amount, aggregation))
            observed_items.add(item_id)
            total_rows += 1
            if item_amount <= 0 or silver_amount <= 0:
                invalid_amount_rows += 1
        finish_series()
        return {'catalogue_items': catalogue_items, 'observed_items': len(observed_items),
                'history_rows': total_rows, 'series': series_count,
                'internal_missing_buckets': missing_buckets,
                'nonpositive_amount_rows': invalid_amount_rows,
                'provisional_review_flags': dict(flag_counts), 'flag_examples': examples}
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path('food_history.sqlite3'))
    args = parser.parse_args()
    print(json.dumps(profile(args.database), indent=2))


if __name__ == '__main__':
    main()
