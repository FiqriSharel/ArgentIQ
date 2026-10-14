# Importing Asia prepared-meal history

No database software installation is needed. The importer uses Python's standard-library `tarfile` and `sqlite3` modules. Laragon's Python executable is available in this workspace; its MySQL/MariaDB server is not used.

The current archive is `C:\ArgentIq\db_backup_2026-10-13T02_00_24.tgz`, downloaded from the AODP East database index on 2026-10-14. The owner's earlier `C:\Users\fiqri\Downloads\db_backup_2026-10-09T02_00_59.tgz` and its imported database remain untouched. The importer streams the archive's single SQL member and reads only `market_history` rows whose exact item IDs match the prepared-meal `T<number>_MEAL_...` convention. This is an observed-history subset. It is **not** a complete, metadata-validated food catalogue, and it does not include foods absent from the source history.

From PowerShell, run this from `C:\ArgentIq` to create a **new** SQLite file:

```powershell
& 'C:\laragon\bin\python\python-3.13\python.exe' -m argentiq.import_food_history `
  --archive 'C:\ArgentIq\db_backup_2026-10-13T02_00_24.tgz' `
  --output 'C:\ArgentIq\food_history_2026-10-13.sqlite3'
```

The command refuses to overwrite an existing output. For a fresh test, choose another output filename; do not delete the current food database just to rerun it. The 2026-10-13 archive produced 200,593 rows for 157 observed item IDs in a 63,700,992-byte SQLite file. Its SHA-256 is `0afd911cec6f8fc31680f22c3fb9976e334bc5ac6bb762c531ea9e229a472244`. The original 2026-10-09 import remains in `C:\ArgentIq\food_history.sqlite3` with 194,789 rows for 155 observed IDs.

The `food_history` table stores the archive's raw `item_amount`, `silver_amount`, source timestamp, aggregation value, numeric location, and quality, plus provenance. AODP's [API documentation](https://www.albion-online-data.com/api/) describes the historical endpoint as sell-order history. Its [history service](https://github.com/ao-data/albiondata-server-rails/blob/main/app/services/market_history_service.rb) calculates `avg_price` as `silver_amount / item_amount`; ArgentIQ uses that formula for the historical chart. The original amounts remain intact. These figures are not verified completed sales, and the source timestamps have no timezone offset. `quality` is separate from enchantment, which remains part of the exact item ID.

## Catalogue from formatted item metadata

The owner-supplied `C:\Users\fiqri\Downloads\items.json` was imported separately using the standard-library JSON parser. It matches the shape of [AODP-linked formatted item metadata](https://github.com/ao-data/ao-bin-dumps/blob/master/formatted/items.json). The importer accepts exact `T<number>_MEAL_...` IDs, validates English display names, and derives tier and enchantment from each exact ID. Food type is a provisional code derived from the ID, because this formatted JSON does not include an explicit category field. It also includes the `SPECIAL` family (`Drake Egg Biscuits`).

To add the catalogue to a **newly created history database**:

```powershell
& 'C:\laragon\bin\python\python-3.13\python.exe' -m argentiq.import_food_catalogue `
  --metadata 'C:\Users\fiqri\Downloads\items.json' `
  --database 'C:\ArgentIq\food_history_2026-10-13.sqlite3'
```

The command refuses to overwrite an existing `food_items` table. It has already been run on the current database: 219 metadata-listed meal IDs, 157 with history and 62 without history in the archive. All observed history IDs matched the metadata. `food_items` stores the catalogue; `food_coverage` is a read-only view with a count and first/last bucket across **all** locations. A nonzero count is not a guarantee of regular history for a selected city.

If DB Browser for SQLite was open during the import, close and open `C:\ArgentIq\food_history_2026-10-13.sqlite3` to see the newer database. Then choose `food_items` or `food_coverage` under **Browse Data**. Filter `display_name` for a food such as `Goat Stew`; tier and enchantment remain separate columns.

Check the local database without starting Laragon's database server:

```powershell
@'
import sqlite3
db = sqlite3.connect(r'C:\ArgentIq\food_history_2026-10-13.sqlite3')
print(db.execute('PRAGMA integrity_check').fetchone()[0])
print(db.execute('SELECT COUNT(*), COUNT(DISTINCT item_id) FROM food_history').fetchone())
db.close()
'@ | & 'C:\laragon\bin\python\python-3.13\python.exe' -
```

Expected for this archive: `ok` and `(200593, 157)`. `web\.env` sets `ARGENTIQ_FOOD_DB=C:/ArgentIq/food_history_2026-10-13.sqlite3`, so the Laravel root page reads this file and displays six-hour historical prices. The former current-quote page remains at `/market`. The two approved forecast pilots failed their backtest gate; no forecast is displayed.

Run the read-only quality profile from `C:\ArgentIq`:

```powershell
& 'C:\laragon\bin\python\python-3.13\python.exe' -m argentiq.profile_food_history --database 'C:\ArgentIq\food_history_2026-10-13.sqlite3'
```

For the current archive it reports 931 item/location/quality/aggregation series, 146,572 missing buckets **within each series' first-to-last span**, and no rows with nonpositive amounts. Its provisional review rule flags an observation only when its average price is less than half or more than twice **both immediately adjacent buckets**. It flags 742 isolated lows and 358 isolated highs. These are review candidates, not confirmed errors; the script does not edit the database. The chart applies the same rule and shows flagged points while retaining every observation. See [forecast readiness](FOOD_FORECAST_READINESS.md) for the coverage analysis and proposed next decision.
