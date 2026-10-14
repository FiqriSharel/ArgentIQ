"""Small, bounded REST collector with local latest-observation storage."""

import json
import logging
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

from .market import Observation, parse_observation


HOST = "https://east.albion-online-data.com"
LOG = logging.getLogger(__name__)


def fetch(items: list[str], cities: list[str], qualities: list[int], retries: int = 2) -> list[Observation]:
    path = "/api/v2/stats/prices/" + ",".join(quote(item, safe="@_") for item in items) + ".json"
    url = HOST + path + "?" + urlencode({"locations": ",".join(cities), "qualities": ",".join(map(str, qualities))})
    if len(url) > 4096:
        raise ValueError("AODP URL exceeds 4096 characters; use a smaller item batch")
    request = Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "ArgentIQ-feasibility/0.1"})
    def normalise(raw: bytes) -> list[Observation]:
        payload = json.loads(raw)
        received = datetime.now(timezone.utc)
        if not isinstance(payload, list):
            raise ValueError("AODP response was not a list")
        LOG.info("AODP returned %s rows", len(payload))
        observations = []
        for index, row in enumerate(payload):
            try:
                observations.append(parse_observation(row, received, set(items), set(cities), set(qualities)))
            except ValueError as exc:
                LOG.warning("Ignoring malformed row %s: %s", index, exc)
        return observations
    for attempt in range(retries + 1):
        started = time.monotonic()
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    raw = gzip.decompress(raw)
            LOG.info("AODP request completed in %.2fs", time.monotonic() - started)
            return normalise(raw)
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == retries:
                raise RuntimeError(f"AODP HTTP {exc.code}") from exc
            retry_after = exc.headers.get("Retry-After", "0") if exc.code == 429 else "0"
            delay = min(int(retry_after), 60) if retry_after.isdigit() else 0
            LOG.warning("AODP HTTP %s; retrying after at least %ss", exc.code, max(delay, 2 ** attempt))
        except (URLError, TimeoutError) as exc:
            if attempt == retries:
                raise RuntimeError(f"AODP request failed: {exc}") from exc
            delay = 0
            LOG.warning("AODP connection failed; retrying: %s", exc)
        except json.JSONDecodeError as exc:
            raise RuntimeError("AODP returned invalid JSON") from exc
        time.sleep(max(delay, 2 ** attempt))
    return []


def save(db_path: str, observations: list[Observation]) -> None:
    with closing(sqlite3.connect(db_path)) as db, db:
        db.execute("""CREATE TABLE IF NOT EXISTS latest_observations (
            item_id TEXT NOT NULL, city TEXT NOT NULL, quality INTEGER NOT NULL,
            sell_price INTEGER, sell_source_at TEXT, buy_price INTEGER, buy_source_at TEXT,
            received_at TEXT NOT NULL, PRIMARY KEY (item_id, city, quality))""")
        for obs in observations:
            db.execute("""INSERT INTO latest_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id, city, quality) DO UPDATE SET
                sell_price=excluded.sell_price, sell_source_at=excluded.sell_source_at,
                buy_price=excluded.buy_price, buy_source_at=excluded.buy_source_at,
                received_at=excluded.received_at""", (
                    obs.item_id, obs.city, obs.quality,
                    obs.sell.price, obs.sell.source_at.isoformat() if obs.sell.source_at else None,
                    obs.buy.price, obs.buy.source_at.isoformat() if obs.buy.source_at else None,
                    obs.received_at.isoformat()))
