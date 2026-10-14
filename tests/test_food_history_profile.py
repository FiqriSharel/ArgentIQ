import unittest
from datetime import datetime, timedelta

from argentiq.profile_food_history import review_flags


class FoodHistoryProfileTests(unittest.TestCase):
    def test_flags_an_isolated_low_only_with_adjacent_buckets(self):
        start = datetime(2026, 10, 8)
        consecutive = [
            (start, 10, 50000, 6),
            (start + timedelta(hours=6), 10, 10000, 6),
            (start + timedelta(hours=12), 10, 50000, 6),
        ]
        self.assertEqual(review_flags(consecutive), [
            ('2026-10-08 06:00:00', 'isolated_low', 1000.0),
        ])

        with_gap = [consecutive[0], consecutive[1],
                    (start + timedelta(hours=18), 10, 50000, 6)]
        self.assertEqual(review_flags(with_gap), [])


if __name__ == '__main__':
    unittest.main()
