import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from argentiq.collector import save
from argentiq.market import freshness, parse_observation


class MarketTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 13, 7, 0, tzinfo=timezone.utc)
        self.row = {"item_id": "T4_BAG", "city": "Martlock", "quality": 1,
                    "sell_price_min": 5000, "sell_price_min_date": "2026-10-13T06:30:00",
                    "buy_price_max": 0, "buy_price_max_date": "0001-01-01T00:00:00"}

    def parse(self):
        return parse_observation(self.row, self.now, {"T4_BAG"}, {"Martlock"}, {1})

    def test_missing_buy_is_not_zero(self):
        obs = self.parse()
        self.assertIsNone(obs.buy.price)
        self.assertIsNone(obs.buy.source_at)
        self.assertEqual(obs.sell.source_at.tzinfo, timezone.utc)

    def test_freshness_boundaries(self):
        obs = self.parse()
        self.assertEqual(freshness(obs.sell, self.now, 60, 360), ("fresh", 30))
        self.assertEqual(freshness(obs.sell, self.now + timedelta(minutes=30), 60, 360)[0], "aging")
        self.assertEqual(freshness(obs.sell, self.now + timedelta(hours=2), 60, 360)[0], "aging")
        self.assertEqual(freshness(obs.sell, self.now + timedelta(hours=7), 60, 360)[0], "stale")
        self.assertEqual(freshness(obs.buy, self.now, 60, 360), ("unavailable", None))

    def test_malformed_and_unexpected_rows(self):
        self.row["sell_price_min"] = -5
        with self.assertRaises(ValueError):
            self.parse()
        self.row["sell_price_min"] = 5000
        self.row["city"] = "Unknown"
        with self.assertRaises(ValueError):
            self.parse()

    def test_repeated_save_upserts(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "test.sqlite3")
            save(path, [self.parse()])
            save(path, [self.parse()])
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM latest_observations").fetchone()[0], 1)
                self.assertIsNone(db.execute("SELECT buy_price FROM latest_observations").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
