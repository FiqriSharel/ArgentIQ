"""Check the pilot backtest's time boundary and gap handling."""

import unittest
from datetime import datetime, timedelta

from argentiq.food_forecast_pilot import backtest_series


class FoodForecastPilotTests(unittest.TestCase):
    def test_held_out_week_is_not_used_to_form_the_forecast(self):
        start = datetime(2026, 4, 1)
        rows = [(start + timedelta(hours=6 * index), float(index % 28 + 1))
                for index in range(56)]

        result = backtest_series(rows)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['origin_bucket'], rows[27][0].isoformat(sep=' '))
        self.assertEqual(result[0]['holdout_first_bucket'], rows[28][0].isoformat(sep=' '))
        self.assertEqual(result[0]['weekly_mae'], 0)
        self.assertGreater(result[0]['persistence_mae'], 0)

    def test_missing_bucket_prevents_scoring_an_incomplete_window(self):
        start = datetime(2026, 4, 1)
        rows = [(start + timedelta(hours=6 * index), 100.0)
                for index in range(57) if index != 40]

        self.assertEqual(backtest_series(rows), [])

    def test_24_hour_median_uses_only_the_four_prices_before_origin(self):
        start = datetime(2026, 4, 1)
        rows = [(start + timedelta(hours=6 * index),
                 1000.0 if index == 27 else 10.0)
                for index in range(56)]

        result = backtest_series(rows)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['median_24h_mae'], 0)
        self.assertEqual(result[0]['persistence_mae'], 990)


if __name__ == '__main__':
    unittest.main()
