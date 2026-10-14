import io
import sqlite3
import tarfile
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from argentiq.import_food_history import import_archive


class FoodHistoryImportTests(unittest.TestCase):
    def archive(self, folder: Path, database: str = "albion-east") -> Path:
        sql = (
            f"-- Database: {database}\n"
            "-- Table structure for table `market_history`\n"
            "INSERT INTO `market_history` VALUES "
            "(1,4,3708,'T4_MEAL_SANDWICH',5003,1,'2026-04-02 00:00:00.000000',6),"
            "(2,1,5000,'T4_BAG',5003,1,'2026-04-02 00:00:00.000000',6),"
            "(3,2,2400,'T4_MEAL_STEW@1',5003,1,'2026-04-02 06:00:00.000000',6);\n"
            "-- Table structure for table `market_orders`\n"
            "INSERT INTO `market_orders` VALUES (4,'T4_MEAL_STEW');\n"
        ).encode()
        path = folder / "backup.tgz"
        with tarfile.open(path, "w:gz") as archive:
            member = tarfile.TarInfo("backup.sql")
            member.size = len(sql)
            archive.addfile(member, io.BytesIO(sql))
        return path

    def test_imports_only_meal_history_and_keeps_raw_source_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            output = folder / "food.sqlite3"
            result = import_archive(self.archive(folder), output)
            self.assertEqual((result["rows"], result["item_ids"]), (2, 2))
            with closing(sqlite3.connect(output)) as db:
                rows = db.execute("SELECT item_id, location_id, quality, bucket_time_source, aggregation, item_amount, silver_amount FROM food_history ORDER BY item_id").fetchall()
                self.assertEqual(rows, [
                    ("T4_MEAL_SANDWICH", 5003, 1, "2026-04-02 00:00:00.000000", 6, 4, 3708),
                    ("T4_MEAL_STEW@1", 5003, 1, "2026-04-02 06:00:00.000000", 6, 2, 2400),
                ])
                self.assertEqual(db.execute("SELECT history_rows, observed_item_ids FROM import_runs").fetchone(), (2, 2))
            with self.assertRaises(FileExistsError):
                import_archive(folder / "backup.tgz", output)

    def test_rejects_wrong_region_without_leaving_database(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            output = folder / "food.sqlite3"
            with self.assertRaisesRegex(ValueError, "East/Asia"):
                import_archive(self.archive(folder, "albion-west"), output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
