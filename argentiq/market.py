"""Validate and describe AODP current-price observations."""

from dataclasses import dataclass
from datetime import datetime, timezone


FIELDS = ("sell_price_min", "buy_price_max")
MISSING_DATE = "0001-01-01T00:00:00"


@dataclass(frozen=True)
class Quote:
    price: int | None
    source_at: datetime | None


@dataclass(frozen=True)
class Observation:
    item_id: str
    city: str
    quality: int
    sell: Quote  # Lowest sell order: instant purchase cost.
    buy: Quote   # Highest buy order: instant sale revenue before fees.
    received_at: datetime


def parse_quote(row: dict, field: str) -> Quote:
    price = row.get(field)
    stamp = row.get(field + "_date")
    if not isinstance(price, int) or isinstance(price, bool) or price < 0:
        raise ValueError(f"invalid {field}: {price!r}")
    if price == 0 or stamp in (None, "", MISSING_DATE):
        return Quote(None, None)
    if not isinstance(stamp, str):
        raise ValueError(f"invalid {field} timestamp")
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {field} timestamp: {stamp!r}") from exc
    # AODP's REST dates omit an offset. UTC is a provisional interpretation.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return Quote(price, parsed.astimezone(timezone.utc))


def parse_observation(row: dict, received_at: datetime, items: set[str], cities: set[str], qualities: set[int]) -> Observation:
    if not isinstance(row, dict):
        raise ValueError("price row must be an object")
    item_id, city, quality = row.get("item_id"), row.get("city"), row.get("quality")
    if item_id not in items or city not in cities or quality not in qualities:
        raise ValueError(f"unexpected item/city/quality: {item_id!r}/{city!r}/{quality!r}")
    return Observation(item_id, city, quality, parse_quote(row, "sell_price_min"), parse_quote(row, "buy_price_max"), received_at)


def freshness(quote: Quote, now: datetime, fresh_minutes: int, aging_minutes: int) -> tuple[str, int | None]:
    if quote.source_at is None:
        return "unavailable", None
    age = int((now - quote.source_at).total_seconds() / 60)
    if age < -5:
        return "clock anomaly", age
    if age < fresh_minutes:
        return "fresh", max(age, 0)
    if age <= aging_minutes:
        return "aging", age
    return "stale", age
