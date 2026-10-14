import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from argentiq.import_food_catalogue import import_catalogue


class FoodCatalogueImportTests(unittest.TestCase):
    def test_catalogue_keeps_items_without_history_and_excludes_other_items(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            database = folder / "food.sqlite3"
            metadata = folder / "items.json"
            with closing(sqlite3.connect(database)) as db:
                db.execute("CREATE TABLE food_history (item_id TEXT, bucket_time_source TEXT)")
                db.execute("INSERT INTO food_history VALUES ('T4_MEAL_STEW', '2026-04-02 00:00:00.000000')")
                db.commit()
            metadata.write_text(json.dumps([
                {"UniqueName": "T4_MEAL_STEW", "Index": 836, "LocalizedNames": {"EN-US": "Goat Stew"}},
                {"UniqueName": "T4_MEAL_STEW@1", "Index": 837, "LocalizedNames": {"EN-US": "Goat Stew"}},
                {"UniqueName": "T8_MEAL_SPECIAL_FOOD_DRAKE_EGG", "Index": 900, "LocalizedNames": {"EN-US": "Drake Egg Biscuits"}},
                {"UniqueName": "T4_BAG", "Index": 5, "LocalizedNames": {"EN-US": "Bag"}},
            ]), encoding="utf-8")
            result = import_catalogue(metadata, database)
            self.assertEqual((result["catalogue_ids"], result["history_matched_ids"], result["history_unmatched_ids"]), (3, 1, 0))
            with closing(sqlite3.connect(database)) as db:
                rows = db.execute("SELECT item_id, display_name, food_type_code, tier, enchantment FROM food_items ORDER BY item_id").fetchall()
                coverage = db.execute("SELECT item_id, history_rows_all_locations FROM food_coverage ORDER BY item_id").fetchall()
            self.assertEqual(rows, [
                ("T4_MEAL_STEW", "Goat Stew", "STEW", 4, 0),
                ("T4_MEAL_STEW@1", "Goat Stew", "STEW", 4, 1),
                ("T8_MEAL_SPECIAL_FOOD_DRAKE_EGG", "Drake Egg Biscuits", "SPECIAL", 8, 0),
            ])
            self.assertEqual(coverage, [
                ("T4_MEAL_STEW", 1),
                ("T4_MEAL_STEW@1", 0),
                ("T8_MEAL_SPECIAL_FOOD_DRAKE_EGG", 0),
            ])
            with self.assertRaisesRegex(ValueError, "already exists"):
                import_catalogue(metadata, database)


if __name__ == "__main__":
    unittest.main()
