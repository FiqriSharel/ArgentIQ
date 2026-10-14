# Food forecast readiness, 2026-10-14

This is the data evidence and decision record for the first forecast pilots. The owner approved seven-day weekly repetition, then a 24-hour median method, on 2026-10-14. Both backtests failed the agreed 5% improvement gate, so no forecast is published.

## Verified data

- Source: AODP East database archive `db_backup_2026-10-13T02_00_24.tgz`, imported into `C:\ArgentIq\food_history_2026-10-13.sqlite3`. The archive SHA-256 recorded during import is `0afd911cec6f8fc31680f22c3fb9976e334bc5ac6bb762c531ea9e229a472244`.
- SQLite integrity check: `ok`. There are 200,593 food-history rows for 157 exact meal IDs. The metadata catalogue has 219 meal IDs, so 62 have no rows in this snapshot.
- Of the history rows, 197,083 are six-hour aggregates and 3,510 are one-hour aggregates. Every imported row has quality 1. Six-hour data covers 804 distinct item/location series, and spans source timestamps from 2026-04-01 00:00 to 2026-10-12 18:00 overall. Source timestamps have no timezone offset.
- Across all aggregations, the read-only profile finds 931 series and 146,572 missing bucket positions **inside each series' own first-to-last span**. It finds no rows with nonpositive item or silver amounts. Its price screen flags 742 isolated lows and 358 isolated highs for review; these are not confirmed errors and no values were removed.
- The six-hour series have very uneven size: minimum 1 row, median 146, 75th percentile 408, maximum 780. Among series with at least 100 rows, 59 have a last observation within one day of the snapshot's latest six-hour bucket, and 119 within seven days. These counts are exploratory coverage descriptions, **not** eligibility rules.
- `T8_MEAL_STEW`, quality 1, has 775 six-hour buckets in Bridgewatch (location 2004), 773 in Lymhurst (1002), and 780 in Martlock (3008). Each series has no missing bucket between its first and last recorded timestamps. The Martlock series ends at 2026-10-12 18:00, while Bridgewatch ends at 2026-10-11 12:00. Their different end times matter: a forecast from the last observed point is not a current live quote.
- In contrast, `T4_MEAL_STEW` in Bridgewatch has 368 rows and 315 missing six-hour positions within its observed span. Its last source bucket is 2026-09-18 12:00. A successful pilot on T8 Beef Stew cannot justify forecasting every catalogue entry.

The source history API describes [sell-order history](https://www.albion-online-data.com/api/). Its [history service](https://github.com/ao-data/albiondata-server-rails/blob/main/app/services/market_history_service.rb) calculates average price as `silver_amount / item_amount`. This is an aggregate sell-order statistic, not a verified completed-sale price.

## Reproduce the main checks

Open `C:\ArgentIq\food_history_2026-10-13.sqlite3` in DB Browser for SQLite and run:

```sql
PRAGMA integrity_check;

SELECT aggregation, quality, COUNT(*) AS rows,
       COUNT(DISTINCT item_id) AS item_ids,
       MIN(bucket_time_source) AS first_bucket,
       MAX(bucket_time_source) AS last_bucket
FROM food_history
GROUP BY aggregation, quality
ORDER BY aggregation, quality;

SELECT location_id, COUNT(*) AS rows,
       MIN(bucket_time_source) AS first_bucket,
       MAX(bucket_time_source) AS last_bucket
FROM food_history
WHERE item_id = 'T8_MEAL_STEW' AND quality = 1 AND aggregation = 6
GROUP BY location_id
ORDER BY rows DESC;
```

The full read-only profile can be rerun from PowerShell in `C:\ArgentIq`:

```powershell
& 'C:\laragon\bin\python\python-3.13\python.exe' -m argentiq.profile_food_history --database 'C:\ArgentIq\food_history_2026-10-13.sqlite3'
```

## Approved first forecast experiment and result

The owner selected **seven days** as the initial horizon and approved the following first pilot:

1. **Target:** the six-hour `silver_amount / item_amount` price for one exact item ID, city, and quality 1. Seven days means 28 future six-hour points. Keep the raw amounts and source timestamps; do not treat flagged prices as confirmed errors.
2. **First method:** a transparent weekly seasonal baseline: repeat the last complete 28-bucket week into the next 28 buckets. Compare it with a simple persistence baseline that repeats the last observed price. Use T8 Beef Stew in Martlock, Bridgewatch, and Lymhurst as the initial pilot, because these three series are continuous across the available span. Later items need their own coverage review.
3. **Backtest:** use time-ordered rolling origins on past dates. At each origin, use only earlier observations, forecast the next 28 buckets, then compare with the actual 28 held-out buckets. Require complete input and holdout windows for this first pilot; do not fill gaps with invented prices. Report error per city and origin using mean absolute error (MAE), plus the median across origins. Keep both methods' outputs so the comparison is auditable.
4. **Proposed acceptance rule:** the weekly method's median MAE across pilot origins should be at least 5% lower than persistence's median MAE. If it does not pass, do not present it as a reliable forecast; review another method with the owner. Regardless of the score, label any displayed forecast as a projection from its last source bucket, and show that bucket's exact timestamp. Do not claim profitability or accuracy for other foods based on the pilot.
5. **Display:** when a method passes evaluation, keep historical values solid and future values dotted. Reuse the final historical point only as the dotted line's display anchor; the model's 28 predicted values begin at future bucket times. No uncertainty band is proposed for this deterministic baseline.

The read-only implementation is `argentiq/food_forecast_pilot.py`. Reproduce the result from PowerShell:

```powershell
& 'C:\laragon\bin\python\python-3.13\python.exe' -m argentiq.food_forecast_pilot --database 'C:\ArgentIq\food_history_2026-10-13.sqlite3'
```

There are 26 complete, non-overlapping seven-day holdouts per city, 78 in total. The pooled median MAE is **244.18 silver** for weekly repetition and **183.53 silver** for persistence. Weekly repetition wins only 12 of 78 holdouts. Its relative improvement is **-33.05%**, versus the required **+5%**. It fails in each pilot city as well: Lymhurst 294.74 versus 205.83, Bridgewatch 185.40 versus 91.39, and Martlock 251.43 versus 190.39 (weekly versus persistence median MAE). The pilot therefore **fails the release gate**. These are backtest results, not a claim that persistence is an approved or reliable production forecast.

The weekly approach is cheap and easy to audit, but it assumes the latest week's pattern repeats and cannot react to sudden market changes. Another method needs a separate owner decision and evaluation. No dotted forecast line has been published.

## Approved 24-hour median pilot and result

After the weekly method failed, the owner approved a second pilot: take the median of the **last four six-hour prices** available at each forecast origin and repeat that value for the following 28 six-hour buckets. The same 78 complete, time-ordered holdouts, three T8 Beef Stew cities, persistence comparison, MAE metric, and 5% pooled median improvement gate were retained. The method uses no future values at its origin. The same read-only `argentiq.food_forecast_pilot` command above reproduces both pilots.

The 24-hour median method's pooled median MAE is **178.45 silver per item**, versus **183.53** for persistence. Its relative improvement is **2.77%**, below the required **5%**. It wins 39 of 78 individual holdouts. City median MAE is 215.00 versus 205.83 in Lymhurst, 101.89 versus 91.39 in Bridgewatch, and 199.59 versus 190.39 in Martlock (24-hour median versus persistence). The pooled result is slightly better, but none of the three city medians beats persistence. This pilot also **fails the release gate**. The history page still has no forecast line.
