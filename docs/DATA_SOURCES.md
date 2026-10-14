# AODP feasibility findings

Checked: **2026-10-13**. Primary sources: [AODP API documentation](https://www.albion-online-data.com/api/), [developer documentation](https://www.albion-online-data.com/developer), [AODP home page](https://www.albion-online-data.com/), [item metadata](https://github.com/ao-data/ao-bin-dumps/blob/master/formatted/items.json), and [location metadata](https://github.com/ao-data/ao-bin-dumps/blob/master/formatted/world.json).

## Confirmed API shape

- Asia uses `https://east.albion-online-data.com`. Current price observations use `/api/v2/stats/prices/{item_ids}.json?locations=...&qualities=...`. Item IDs and locations may be batched. Documentation limits the URL to 4096 characters and lists 180 requests/minute and 300 requests/5 minutes; long-running clients should accept gzip. The exact enforcement response headers were not documented.
- Item IDs use game identifiers such as `T4_BAG`; `T4_BAG@1` returned results in the live probe and represents an enchantment variant. Tier is encoded in the item ID for this example. Keep item IDs as authoritative identifiers rather than fabricating unsupported combinations. The response has a separate numeric `quality` and city string. The maintained item and world metadata files are the starting point for a full catalog. We have not validated every tier, enchantment, quality, or city mapping.
- `sell_price_min` is the lowest observed sell order, useful as a possible instant buy cost. `buy_price_max` is the highest observed buy order, useful as a possible instant sell quote. Each has its own `*_date`. These are observations, not execution guarantees or confirmed sales. The AODP client uploads orders that contributors load in game, so coverage varies by place and time.
- Zero prices with `0001-01-01T00:00:00` occurred in the live response. ArgentIQ converts those pairs to unavailable. REST timestamps in the response have **no timezone offset**. The prototype assumes UTC only to calculate provisional ages; AODP's developer page explicitly documents UTC for an example of market-history ticks, but does not explicitly state the timezone of these REST price strings. Verify that assumption before relying on ages.
- Historical endpoint: `/api/v2/stats/history/{item_ids}.json?locations=...&qualities=...&time-scale=24`. Documentation calls this **historical prices (sell orders only)** and offers 1-hour, 6-hour, and daily buckets. A live daily response contained `location`, `item_id`, `quality`, and `data` entries with `item_count`, `avg_price`, `timestamp`. The documentation does not define `item_count` precisely enough to treat it as confirmed sales volume. Label it a source aggregate, not completed sales.
- No individual completed-sale records or transaction-level REST endpoint are documented by AODP. The developer page exposes `markethistories` NATS topics, but they are feed messages, not proof of accessible individual executed trades. We found no legitimate, documented public source for transaction-level sales in this investigation. The honest alternative is historical sell-order price statistics, plus locally collected observation snapshots.
- NATS has an Asia connection and deduplicated market-order/history topics. The documentation says deduplication uses a five-minute window and new subscribers may miss earlier messages. It does not promise replay/recovery. Small-batch REST polling is sufficient for this first on-demand probe; streaming could later reduce latency for emitted observations, with REST reconciliation after disconnects. Neither guarantees complete market coverage.
- AODP provides daily database exports. A concrete public rule for how long an independent app may retain or redistribute API data was not found in the reviewed docs. Do not infer permission or a guaranteed retention period from the existence of exports; clarify this before public hosting or bulk archival.

## Live probe

On **2026-10-13 07:44 UTC**, a read-only request for `T4_BAG` at quality 1 on the Asia host returned these examples:

| City | Lowest sell order | Highest buy order | Source date as returned |
| --- | ---: | ---: | --- |
| Bridgewatch | unavailable | 2087 | buy: `2026-10-12T11:00:00` |
| Caerleon | unavailable | unavailable | sentinel dates |
| Martlock | 499999 | unavailable | sell: `2026-10-13T01:40:00` |

These are a **point-in-time API response**, not current recommendations. The Martlock ask is an example of why a single listed price cannot be treated as a realistic sale opportunity. A request for two base items plus an enchantment variant, three cities, and qualities 1 and 2 returned 18 rows and HTTP 200. Its response included no `X-RateLimit-Limit` header in that request.

The history endpoint returned 20 daily buckets for `T4_BAG`, Martlock, quality 1, from 2026-09-13 through 2026-10-02. One bucket (2026-10-02) had `item_count: 92`, `avg_price: 5513`, and `timestamp: 2026-10-02T00:00:00`. We have not established why the returned history stopped on October 2 or whether the count represents sales, observed listings, or another aggregation rule. It must not be shown as completed-sale volume.

## Open checks before later milestones

1. Confirm the timezone and update semantics of current-price `*_date` fields with AODP source code or maintainers.
2. Determine the exact meaning of history `item_count` and `avg_price`, including whether historical buckets are delayed and their retention window.
3. Verify the item metadata schema, city IDs, numeric quality labels, and supported variants for a small craftable set.
4. Measure freshness across repeated observations and establish practical refresh windows from data rather than assuming polling creates fresh quotes.
5. Clarify storage/redistribution terms before a public service; investigate legitimate transaction data only if a documented source emerges.

## One-hour freshness spot check (2026-10-13)

At 08:27 UTC, a batched Asia request for `T4_BAG`, `T4_ORE`, `T4_WOOD`, and `T4_METALBAR` across six cities at quality 1 returned 24 rows and 14 nonzero ask/bid quotes. Under the prototype's provisional UTC interpretation, **only one quote was less than 60 minutes old**: the `T4_BAG` lowest sell order in Lymhurst, source time `07:40:00`, age about 47 minutes. This is a small, time-specific sample, not a coverage guarantee.

AODP says its [client](https://www.albion-online-data.com/client) uploads only orders loaded in game and makes uploaded prices available immediately. Running the client on the Asia game server while opening the exact item and city market views is the practical way for this user to contribute fresh observations. Repeated API polling alone cannot produce source updates. The local interface therefore defaults to **Last hour only**, with older data available for inspection but hidden from that view.
