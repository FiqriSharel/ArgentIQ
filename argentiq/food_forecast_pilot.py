"""Read-only seven-day backtests for the approved T8 Beef Stew pilots.

Weekly repetition uses the preceding 28 six-hour prices. The 24-hour median
method repeats the median of the last four prices. Persistence repeats the
last observed price. No forecast is published by this module.
"""

import argparse
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, median


ITEM_ID = 'T8_MEAL_STEW'
LOCATIONS = {1002: 'Lymhurst', 2004: 'Bridgewatch', 3008: 'Martlock'}
BUCKETS_PER_WEEK = 28
BUCKET_INTERVAL = timedelta(hours=6)
REQUIRED_IMPROVEMENT = 0.05


def is_contiguous(rows):
    return all(right[0] - left[0] == BUCKET_INTERVAL
               for left, right in zip(rows, rows[1:]))


def backtest_series(rows):
    """Evaluate non-overlapping seven-day holdouts without future leakage."""
    results = []
    for start in range(BUCKETS_PER_WEEK, len(rows) - BUCKETS_PER_WEEK + 1,
                       BUCKETS_PER_WEEK):
        window = rows[start - BUCKETS_PER_WEEK:start + BUCKETS_PER_WEEK]
        if not is_contiguous(window):
            continue
        observed = [price for _, price in window[BUCKETS_PER_WEEK:]]
        weekly = [price for _, price in window[:BUCKETS_PER_WEEK]]
        median_24h = [median(price for _, price in window[BUCKETS_PER_WEEK - 4:BUCKETS_PER_WEEK])] * BUCKETS_PER_WEEK
        persistence = [window[BUCKETS_PER_WEEK - 1][1]] * BUCKETS_PER_WEEK
        results.append({
            'origin_bucket': window[BUCKETS_PER_WEEK - 1][0].isoformat(sep=' '),
            'holdout_first_bucket': window[BUCKETS_PER_WEEK][0].isoformat(sep=' '),
            'holdout_last_bucket': window[-1][0].isoformat(sep=' '),
            'weekly_mae': mean(abs(actual - predicted)
                               for actual, predicted in zip(observed, weekly)),
            'median_24h_mae': mean(abs(actual - predicted)
                                   for actual, predicted in zip(observed, median_24h)),
            'persistence_mae': mean(abs(actual - predicted)
                                    for actual, predicted in zip(observed, persistence)),
        })
    return results


def evaluate(database):
    connection = sqlite3.connect(f'file:{database.as_posix()}?mode=ro', uri=True)
    try:
        per_city = []
        all_origins = []
        for location_id, city in LOCATIONS.items():
            source = connection.execute('''
                SELECT bucket_time_source, item_amount, silver_amount
                FROM food_history
                WHERE item_id = ? AND location_id = ? AND quality = 1
                  AND aggregation = 6
                ORDER BY bucket_time_source
            ''', (ITEM_ID, location_id))
            rows = [(datetime.fromisoformat(timestamp), silver / amount)
                    for timestamp, amount, silver in source if amount > 0]
            origins = backtest_series(rows)
            all_origins.extend(origins)
            per_city.append({
                'city': city,
                'location_id': location_id,
                'history_rows': len(rows),
                'backtest_origins': len(origins),
                'weekly_median_mae': median(row['weekly_mae'] for row in origins)
                if origins else None,
                'median_24h_median_mae': median(row['median_24h_mae'] for row in origins)
                if origins else None,
                'persistence_median_mae': median(row['persistence_mae'] for row in origins)
                if origins else None,
                'weekly_wins': sum(row['weekly_mae'] < row['persistence_mae']
                                   for row in origins),
                'median_24h_wins': sum(row['median_24h_mae'] < row['persistence_mae']
                                       for row in origins),
            })

        weekly_median = median(row['weekly_mae'] for row in all_origins) if all_origins else None
        median_24h_median = median(row['median_24h_mae'] for row in all_origins) if all_origins else None
        persistence_median = median(row['persistence_mae'] for row in all_origins) if all_origins else None
        weekly_improvement = (1 - weekly_median / persistence_median
                              if persistence_median and weekly_median is not None else None)
        median_24h_improvement = (1 - median_24h_median / persistence_median
                                  if persistence_median and median_24h_median is not None else None)
        return {
            'item_id': ITEM_ID,
            'quality': 1,
            'aggregation_hours': 6,
            'horizon_buckets': BUCKETS_PER_WEEK,
            'backtest_origins': len(all_origins),
            'cities': per_city,
            'weekly_median_mae': weekly_median,
            'median_24h_median_mae': median_24h_median,
            'persistence_median_mae': persistence_median,
            'weekly_relative_improvement': weekly_improvement,
            'median_24h_relative_improvement': median_24h_improvement,
            'required_relative_improvement': REQUIRED_IMPROVEMENT,
            'weekly_passes_gate': weekly_improvement is not None
            and weekly_improvement >= REQUIRED_IMPROVEMENT,
            'median_24h_passes_gate': median_24h_improvement is not None
            and median_24h_improvement >= REQUIRED_IMPROVEMENT,
        }
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path,
                        default=Path('food_history_2026-10-13.sqlite3'))
    args = parser.parse_args()
    print(json.dumps(evaluate(args.database), indent=2))


if __name__ == '__main__':
    main()
