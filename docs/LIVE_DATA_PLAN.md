# Live market data plan

Checked: **2026-10-13**. This plan is for ArgentIQ's single-user, local Asia-server interface. "Live" means a recently observed market order delivered promptly; it does not mean every order in every city is known.

## What comparable tools disclose

[Albion Analyser](https://albionanalyser.com/) says its free data comes from the shared [Albion Online Data Project (AODP)](https://www.albion-online-data.com/) feed, while its premium data comes from the user's own private market scans. Its public description does not establish the exact mechanism used by its desktop app. The Free/Premium feature table alone is not evidence of complete, continuously fresh coverage.

AODP's [client](https://www.albion-online-data.com/client) runs alongside Albion Online, observes the market orders a player loads in game, and uploads them. AODP says uploaded prices become available immediately. An open market view can therefore supply a fresh observation for the viewed item and city; it cannot supply unvisited markets. Data age and delivery latency are separate: a fast connection can deliver an old observation quickly.

## Build path

1. **Use contributed scans now.** Run the official AODP client while playing on Asia, open the exact city/item/variant/quality market views of interest, then refresh ArgentIQ. Keep the existing separate source timestamps for ask and bid, and show missing or older-than-one-hour sides as unavailable in the default filter. This remains shared community data.
2. **Add a stream bridge for lower latency.** A small Python process subscribes to the documented Asia NATS `marketorders.deduped` topic, validates and normalizes messages, and writes observations to the local SQLite store. The Laravel API reads that store; React can poll it briefly or use server-sent events to redraw changed rows. Record the AODP event time and local receipt time separately. Accept only newer observations for a given item, city, quality, and order side. Make reconnects safe and run a bounded REST reconciliation on startup and after a disconnect, because [AODP's developer documentation](https://www.albion-online-data.com/developer) does not promise stream replay. Confirm the message schema and timestamp semantics with a real Asia message before committing to the parser. The documented Asia NATS port `24222` was reachable from this development session, but a successful subscription and message payload have not been verified.
3. **Evaluate personal private scans.** To offer a feature comparable to Albion Analyser's disclosed private scans, first verify a supported local output path and relevant game/client terms. A user-run companion could then pass the market views observed on this PC into ArgentIQ's local store without publishing them. Mark each row's origin as `private_scan` or `community_aodp`; do not mix their timestamps or imply a private scan covers markets the user has not viewed. Do not claim this feature is implemented until local capture, provenance, and disconnect behavior are tested.

The current [AODP REST API](https://www.albion-online-data.com/api/) remains useful for initial snapshots and recovery. More frequent REST polling changes how soon ArgentIQ sees an upload; it cannot make a stale quote fresh. Its hourly history buckets are aggregates of historical sell-order data, not a substitute for current orders or proof of completed trades.

## Acceptance checks for the next increment

- A known market view on Asia produces an observed message or an updated REST quote, with its exact source time and city visible in ArgentIQ.
- A stream event updates only its matching item, city, quality, and side; an older event cannot overwrite a newer one.
- A restart or disconnect resumes safely, reconciles selected items through bounded REST calls, and indicates when the stream is disconnected.
- The interface distinguishes **observed at** from **received at**, shows the data origin, and hides quotes older than 60 minutes in the default view.
- An empty or old market remains clearly unavailable; no claim is made about completed sales, all-city coverage, or guaranteed execution.

## Current status

ArgentIQ currently has REST collection and a local Laravel/React interface with a one-hour source-age filter. It does **not** yet have a NATS subscriber or a private scan companion. See [DATA_SOURCES.md](DATA_SOURCES.md) for the source investigation and unresolved timestamp assumptions.
