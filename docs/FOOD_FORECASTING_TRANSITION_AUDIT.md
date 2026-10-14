# Food forecasting transition audit

Checked: 2026-10-14. This audit records the **starting repository state before the food-history implementation**. For the current imported database, website, and approved pilot result, read the [forecast readiness report](FOOD_FORECAST_READINESS.md) and [import notes](FOOD_HISTORY_IMPORT.md). The [revised specification](../ArgentIQ_REVISED_FOOD_FORECASTING_SPEC.md) sets the new direction; the [original specification](../ArgentIQ_PROJECT_SPEC.md) describes the earlier, broader market-analysis goal.

## What exists now

| Concern | Verified repository state | Use in the revised project |
| --- | --- | --- |
| Local website | Laravel serves `/`; React 19 and Vite render a current-price comparison table. There is no charting library or historical chart. | Retain the page shell and adapt the interface after data and catalogue contracts are established. |
| Market API | `GET /market-data` reads the Python-owned SQLite file; `POST /refresh` runs the collector with a 60-second cooldown; `POST /evidence` calls Java. | Keep current quotes available while adding separate history queries later. |
| Python collector | Requests AODP Asia `/api/v2/stats/prices`, validates returned item, city, and quality against the request, converts sentinel/zero quotes to missing, and records separate source and retrieval times. | Reuse request, validation, and source-handling patterns; history needs its own parser and storage. |
| Market database | `argentiq.sqlite3` has one `latest_observations` table keyed by `(item_id, city, quality)`. Its 12 rows are six cities each for `T4_BAG` and `T5_BAG`. Repeated collection upserts and overwrites prior values. | It cannot answer historical food queries or measure food coverage. Add history storage separately after validating the source payload. |
| Laravel database | `web/database/database.sqlite` contains framework tables, not market history. | Keep its responsibility separate from the Python-owned market database for now. |
| Java | `EvidenceGate.java` checks whether a current ask/bid pair is present and recent. It does not forecast or estimate profit. | Preserve it for the existing comparison feature; assess its future role separately. |
| Tests | Four Python unit tests cover quote parsing, freshness, invalid rows, and upsert behavior. Five Laravel tests passed with ten assertions. The Vite production build passed. | Add catalogue and history tests when those features are implemented. Current tests do not establish food or history behavior. |

The current UI searches saved item IDs and cities. It has no food names, food-type/food/tier/enchantment filters, validated variant metadata, or historical series. Its `quality` field is a separate AODP dimension; it must not be treated as enchantment. The page's one-hour freshness filter is for latest quotes and does not define historical coverage or forecast eligibility.

`C:\ArgentIq` has no `.git` directory in this workspace, so this audit cannot establish which files differ from the GitHub repository or an earlier commit.

## Source findings and limits

- [AODP API documentation](https://www.albion-online-data.com/api/) names the Asia host `east.albion-online-data.com` and documents `/api/v2/stats/history/{item_ids}.json` as **historical prices (sell orders only)**. It supports `time-scale` values 1, 6, and 24 for hourly, six-hour, and daily buckets, and accepts date ranges. It documents a 4096-character URL limit and 180 requests/minute and 300 requests/five minutes limits.
- [AODP developer documentation](https://www.albion-online-data.com/developer) lists Asia NATS `markethistories` topics and warns that new subscribers may miss previous messages. It also lists daily table dumps. The [Asia export index](https://www.albion-online-data.com/database-east/) currently exposes dated backup archives and monthly `market_history_*.sql.gz` files. The listing establishes that bulk files exist; it does not establish their schema, completeness, permitted use, or current coverage.
- [AODP's site](https://www.albion-online-data.com/) states that its client uploads only market orders loaded in game. This limits the coverage of contributed current quotes. The documented history endpoint and exports are promising sources, but their presence alone cannot establish usable data for every food variant.
- Existing [data-source notes](DATA_SOURCES.md) record a prior live response with `item_count`, `avg_price`, and `timestamp` buckets for a bag. The source documentation calls these sell-order history, not completed transactions. The precise meaning of `item_count` and `avg_price`, the bucket update delay, timezone handling, and retention depth still need verification.
- The live Asia food-history API request could not be read in this environment. The earlier shared link also mistakenly encoded query separators; that link should not be used to judge endpoint availability.

### Bounded check of an Asia backup supplied by the owner

The owner downloaded `db_backup_2026-10-09T02_00_59.tgz` from the Asia export index. This audit inspected it as a compressed stream without extracting or importing it. It contains a 747,299,708-byte MariaDB SQL dump with `market_history`, `market_orders`, `market_orders_expired`, and `market_stats` tables. The `market_history` schema includes `item_amount`, `silver_amount`, `item_id`, numeric `location`, `quality`, `timestamp`, and `aggregation`, with a uniqueness key on item, quality, location, timestamp, and aggregation. Its field semantics still need confirmation against the source code or maintainers.

Rows found in `market_history` for four exact item IDs in this **single 2026-10-09 snapshot**:

| Item ID | Rows | Earliest bucket | Latest bucket |
| --- | ---: | --- | --- |
| `T4_MEAL_STEW` | 2,797 | 2026-04-01 | 2026-10-03 |
| `T4_MEAL_SANDWICH` | 1,742 | 2026-04-01 | 2026-10-03 |
| `T4_MEAL_STEW@1` | 17 | 2026-04-01 | 2026-10-07 |
| `T4_MEAL_SANDWICH@1` | 22 | 2026-04-01 | 2026-10-03 |

These 4,578 rows span seven numeric location IDs and quality 1. The `aggregation` field is 6 for 4,576 rows and 1 for two rows. The backup proves some historical food data exists, while showing that coverage can differ sharply by variant. It does **not** establish regular coverage for any one city, completeness between the first and last bucket, older history availability, current API availability, or forecast suitability. It is a source snapshot, not a catalogue of every valid food.

## Minimum path forward

1. Review the imported 219-entry prepared-meal catalogue against the maintained AODP-linked [item metadata](https://github.com/ao-data/ao-bin-dumps/blob/master/formatted/items.json) and the intended food scope. Confirm the provisional food-type mapping and check for any valid foods outside the `MEAL` IDs. Keep catalogue membership separate from history availability; do not infer unsupported variants from a naming pattern.
2. Extend the supplied-backup coverage analysis by exact item, location, quality, and bucket; map numeric locations with verified metadata. When API access is available, compare a small REST response with the export. Record missing buckets and response fields. No further bulk download is needed for this first check.
3. Agree on the historical price statistic and city/quality scope to display. AODP's documented history is sell-order aggregation; never label it completed sales. Document how the statistic and timestamps are interpreted.
4. Build on the isolated history import and storage with a validated, range-bounded query for the website. Preserve source, server, exact item ID, location, quality, bucket time, aggregation scale, and retrieval time. Keep the current latest-quote table and endpoints functioning.
5. Add catalogue search and dependent filters, then a history-only chart with honest empty, stale, and coverage states. Keep distinct item/variant/city/quality series separate. Add a forecast display contract after the data shape is known, without generating values.
6. Discuss forecasting candidates, horizon, minimum history, and evaluation only after the coverage report. No method is selected by this audit.

## Decisions needed after the coverage probe

- Which AODP sell-order statistic and aggregation scale should be the prediction target?
- Should the first chart focus on one city and one variant, with comparison as an optional view?
- What history depth and missing-bucket rate are acceptable for the first supported foods?
- What precise role, if any, should the current-price comparison and Java evidence check have in the food-focused interface?

The existing website functionality is preserved. No forecasting model, generated forecast, or new software dependency was added.

## Food-only local storage decision (owner direction, 2026-10-14)

The owner wants the project database to hold food information only. A separate SQLite file now contains an **observed prepared-meal history subset** imported from the downloaded MariaDB `.tgz`. The importer accepts only item IDs matching the `T<number>_MEAL_...` form in `market_history`; it excludes other items, market orders, gold prices, and framework tables. This prefix is an import boundary, **not a verified complete food catalogue**. Item metadata must still confirm which entries count as food and which variants exist, including valid foods with no observations.

Current and planned tables:

- `food_history` (implemented): server, exact item ID, numeric source location, quality, source bucket timestamp, aggregation value, raw `item_amount` and `silver_amount`, archive hash, and import time. A unique key on server/item/location/quality/bucket/aggregation prevents duplicates. The source fields remain raw until their meanings and the displayed price calculation are verified.
- `import_runs` (implemented): archive identity/checksum, compressed size, import time, and accepted row and observed ID counts.
- `food_items` (implemented): exact metadata item ID, English display name, item-ID-derived food type, tier, enchantment, and metadata provenance. One row per metadata-listed meal variant, independent of market availability.
- `catalogue_imports` and `food_coverage` (implemented): metadata import provenance and a read-only view of catalogue entries with history row counts and first/last bucket across all locations.

The existing `argentiq.sqlite3` latest-quote database and Java check belong to the current prototype. They remain intact; decide how to retire or retain them without losing data accidentally. Laravel is not yet wired to the food database. Laragon can provide PHP and related local tools, but its MySQL/MariaDB server is not required for this design.

The history importer is `argentiq/import_food_history.py`, and the current output is `food_history.sqlite3`. It read the Asia archive as a stream and imported 194,789 rows for 155 observed meal item IDs. The catalogue importer is `argentiq/import_food_catalogue.py`; it read the owner-supplied formatted `items.json` and added 219 metadata-listed meal variants. All 155 observed IDs matched metadata; 64 metadata IDs had no history in this snapshot. SQLite `PRAGMA integrity_check` returned `ok`; no non-meal history IDs were found. Source bucket timestamps run from 2026-04-01 to 2026-10-08 in this snapshot. See [import instructions](FOOD_HISTORY_IMPORT.md). The output file is a local data artifact, not a forecasting dataset approved for model training. The food-type code is derived from item IDs, because formatted metadata provides IDs and names but no explicit type field.
