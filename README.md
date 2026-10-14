# ArgentIQ

**Direction update (2026-10-14):** ArgentIQ is transitioning toward Asia-server food market history and forecasting. The root website now has a food catalogue and recorded-history chart. Two approved forecast pilots failed the agreed backtest gate, so no forecast is displayed. The former current-quote comparison prototype remains at `/market`. Read the [revised food forecasting specification](ArgentIQ_REVISED_FOOD_FORECASTING_SPEC.md) and the [transition audit and staged plan](docs/FOOD_FORECASTING_TRANSITION_AUDIT.md) before extending it. The original [project specification](ArgentIQ_PROJECT_SPEC.md) records the earlier broad market-analysis direction.

A separate food-history SQLite file can be built from an Asia backup using the [filtered import instructions](docs/FOOD_HISTORY_IMPORT.md). The current local website reads `C:\ArgentIq\food_history_2026-10-13.sqlite3`, which contains a metadata-based meal catalogue and a coverage view. The earlier `food_history.sqlite3` remains intact. The [forecast readiness report](docs/FOOD_FORECAST_READINESS.md) records the coverage, two approved pilots, and their failed gates.

ArgentIQ is an independent Albion Online market-analysis project. The current increment is a **single-user website that runs locally** and displays Asia food history. Its earlier current-quote comparison remains available. It does not yet calculate crafting profit or produce forecasts.

## Technology roles

| Technology | Current role |
| --- | --- |
| HTML, CSS | Laravel page shells and local dashboard styling |
| JavaScript, React | Food-history chart and filters; legacy quote-age display |
| Node.js | Vite build for the React interface |
| PHP, Laravel | Local web server, read-only food-history and market APIs, controlled quote refresh, Java check route |
| Python | AODP collector, filtered food-history import, read-only quality profile, SQLite storage |
| Java | Separate evidence gate: blocks missing or stale quote pairs; does not estimate profit |

SQLite stores market observations locally. There are no accounts, paid services, or public deployment requirements. Run the web server on `127.0.0.1` only. Before exposing it to other devices or the internet, add authentication and review the data-provider terms.

## Start locally on Windows

The current machine has Laragon PHP 8.3, Composer, Python 3.13, and Node.js 22. A JDK 11 or newer is needed for **Check evidence**; the page and price collection work without it. A portable Eclipse Temurin JDK 21 has been unpacked locally at `C:\ArgentIq\.tools\jdk\jdk-21.0.12.1+1`; this ignored folder will not travel with a source copy. In PowerShell:

1. Open `C:\ArgentIq`. Install PHP, Composer, Python, Node.js, and a JDK if they are not already available. [Laravel installation guidance](https://laravel.com/docs/13.x/installation) and [Eclipse Temurin](https://adoptium.net/installation/) are official starting points.
2. In `C:\ArgentIq\web`, run `composer install` and `npm install`. Copy `.env.example` to `.env` if needed, then run `php artisan key:generate` and `php artisan migrate`. The existing local `.env` is ignored by Git.
3. Set `ARGENTIQ_PYTHON` in `web\.env` to the full path of your Python executable. Set `ARGENTIQ_JAVA` to the full path of your JDK's `java.exe` if Java is not on PATH. The food page reads `C:\ArgentIq\food_history.sqlite3` by default; the current local `.env` selects the newer archive with `ARGENTIQ_FOOD_DB=C:/ArgentIq/food_history_2026-10-13.sqlite3`. Use forward slashes in Windows paths inside `.env`, for example `C:/laragon/bin/python/python-3.13/python.exe`.
4. In `C:\ArgentIq\web`, run `npm run build`, then `php artisan serve --host=127.0.0.1 --port=8000`.
5. Open `http://127.0.0.1:8000` for the food-history catalogue and chart. Select food type, food name, tier, enchantment, exact item, location, and quality. The chart reads the local SQLite file. The earlier current-quote page is at `http://127.0.0.1:8000/market`.

On the **current-quote page**, the **Last hour only** filter is on by default. It shows a row only when at least one quote has a source timestamp within 60 minutes, and hides older prices within that row. Turn it off to inspect stale observations. Including more cities can find an existing recent observation, but it cannot refresh an old market by itself.

### Getting observations under one hour

1. Get the [official AODP client](https://www.albion-online-data.com/client) from its [release page](https://github.com/ao-data/albiondata-client/releases) if you choose to contribute data.
2. Run it while playing on the **Asia** server. In Albion Online, open the market in the city you care about and load the exact item, enchantment, and quality views whose orders you need. AODP says its client uploads the market orders you actually load; simply running ArgentIQ or the client without opening those views does not populate them.
3. Refresh ArgentIQ and check **source age** for each ask and bid separately. If a quote is still missing or old, that side was not observed recently. Another city's recent quote is not a substitute for the city where you intend to trade.

ArgentIQ can poll AODP more often, but polling cannot create fresh observations when nobody has uploaded them. AODP's documented API limits are 180 requests per minute and 300 per five minutes; this personal interface uses a conservative one-minute refresh cooldown. The collector still needs network access to reach AODP.

For this workspace, `web\.env` already points to Laragon Python and the portable JDK. The local web page and saved-data API were verified. This Codex session restricts outbound network access from the long-running PHP server process, so its refresh POST could not complete here; the direct AODP request and standalone Python collection were verified. On your normal local environment, the refresh action should use the same Python collector. If it fails, check `web\storage\logs\laravel.log` and run `python -m argentiq` from the project root to isolate connectivity.

If the commands are not on PATH, use the corresponding Laragon executables. On this machine those are `C:\laragon\bin\php\php-8.3.33-Win32-vs16-x64\php.exe`, `C:\laragon\bin\composer\composer.phar`, `C:\laragon\bin\python\python-3.13\python.exe`, and `C:\laragon\bin\nodejs\node-v22\npm.cmd`. To run Composer without a global command: `& 'C:\laragon\bin\php\php-8.3.33-Win32-vs16-x64\php.exe' 'C:\laragon\bin\composer\composer.phar' install`.

## Collector and tests

The Python collector can also run without the web interface:

```powershell
cd C:\ArgentIq
python -m argentiq --items T4_BAG,T5_BAG --cities Bridgewatch,Martlock,Caerleon --qualities 1
python -m unittest discover -s tests -v
```

It upserts `argentiq.sqlite3` with separate source and retrieval timestamps. Missing values are never zero. The freshness windows are provisional and configurable with `--fresh-minutes` and `--aging-minutes`. AODP price strings lack an explicit timezone; ages currently assume UTC and the interface marks that assumption. The Java check is a separate conservative gate for future calculations; it does not assess liquidity, fees, recipes, or actual profit.

See [data-source findings](docs/DATA_SOURCES.md), the [live data plan](docs/LIVE_DATA_PLAN.md), and the [project specification](ArgentIQ_PROJECT_SPEC.md). The interface is an early market comparison, not the finished crafting finder.
