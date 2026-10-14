# ArgentIQ

## Project Brief, Product Requirements, and Technical Direction

**Project name:** ArgentIQ\
**Project type:** Albion Online market-analysis web application\
**Initial game server:** Asia\
**Primary objective:** Help the player identify what to craft, where to
buy required materials, where to craft, and where/how to sell for the
highest realistic net profit.\
**Future objective:** Add market-value forecasting after the core
market-analysis system is reliable.\
**Status:** Data-source feasibility probe and local interface prototype\
**Audience:** Codex and any developer helping implement the project

### 2026-10-13 scope and technology update

ArgentIQ is initially a **single-user, local-first website** for its
owner. It must run on the owner's Windows machine and provide a browser
interface at a loopback address. Public hosting, accounts, and
multi-user features are not required for this phase. The interface must
show real saved observations, source and retrieval timestamps, freshness,
missing values, and collection errors. A page refresh alone does not make
upstream data fresh.

The required technology set is **HTML, CSS, JavaScript, React, Node.js,
PHP, Laravel, Python, and Java**. Give each technology a clear role:
Laravel/PHP serves the local website and its API; React/JavaScript renders
the interface using HTML and CSS; Node.js builds the frontend; Python
collects and validates AODP data in SQLite; Java handles a separate,
testable evidence or calculation rule. Do not require a Java process for
the page to load or hide a missing Java runtime. Keep data boundaries
explicit so this technology requirement does not produce duplicate
market collection or conflicting financial formulas.

The first local interface is a market-observation comparison, not the
finished crafting finder. It may offer manual collection with a rate
limit. Later work can add scheduled collection and crafting calculations
after data semantics and game rules are verified. Keep the server bound
to localhost by default; revisit authentication before any network or
public exposure.

------------------------------------------------------------------------

## 1. Project Overview

ArgentIQ is an independent market-analysis website for Albion Online. It
should bring market prices, item variations, historical market
information, and crafting/trading calculations into one clear interface.

The main motivation is to create a useful alternative to complex
spreadsheets and paid market-analysis tools. ArgentIQ should prioritise
usability, transparency, and dependable calculations. The goal is not
simply to show the highest listed price. It is to estimate which action
is most likely to produce the best **realistic net profit after costs**,
while making the age and limitations of the underlying data visible.

The first release should focus on a practical decision-making workflow:

1.  Select or discover an item worth crafting.
2.  Compare its price across cities, tiers, enchantment levels, and item
    qualities.
3.  Inspect available price history and, if a legitimate data source
    supports it, completed-sale history.
4.  Estimate the cost of sourcing the recipe's materials from suitable
    cities.
5.  Estimate crafting costs, resource returns, taxes, and other relevant
    expenses.
6.  Compare possible crafting and selling locations.
7.  Rank opportunities using net profit and other useful metrics.
8.  Show the data timestamps, assumptions, and uncertainty behind each
    result.

The system should initially target the **Asia server**, but the
architecture should not hard-code the server in a way that prevents
adding Europe or Americas later.

## 2. Why This Project Matters

### 2.1 Reduce dependence on paid tools

Some existing Albion Online market tools limit advanced calculations or
convenience features to subscribers. ArgentIQ should rely on publicly
available data sources and open-source software wherever practical,
keeping recurring costs low.

"Free" should be treated as a design goal, not an unconditional promise.
Data providers, hosting, storage, domain registration, and usage limits
can change. The project should be useful locally at no hosting cost
during development and should avoid paid dependencies unless there is a
clear reason.

### 2.2 Turn market data into decisions

A list of prices is not enough. The useful question is:

> Given current market information, item variations, material
> requirements, crafting conditions, fees, and likely selling prices,
> which available crafting or trading option has the best expected net
> return?

ArgentIQ should turn raw observations into explainable recommendations.
Users must be able to inspect the assumptions behind a result rather
than trusting a mysterious "profit" number.

### 2.3 Make a complex spreadsheet easier to use

The user has access to a spreadsheet created by the Albion Online
content creator Goldenium. It is a reference for the type of
functionality desired, but the spreadsheet is considered too difficult
to navigate.

Reference spreadsheet:
https://docs.google.com/spreadsheets/d/1b8RwAtuiX9LPzP3cLVJ-E2UY5NAlQcaXK2PPwq6Y8dk/edit?usp=sharing

Use this as inspiration for the problem domain and workflow, not as
something to copy wholesale. ArgentIQ should have its own
implementation, interface, calculations, and code. Do not reproduce
proprietary spreadsheet content, formulas, branding, or protected assets
without permission.

**Reference-inspection limitation:** At the time this brief was
prepared, the accessible extraction exposed the spreadsheet's "Main
Settings" content, including the selected Asia region, but did not
expose enough of the other sheets and formulas to verify the complete
workbook. Do not assume any unseen tab, formula, or feature. If more
detailed comparison is needed, ask the user to export and provide a copy
or screenshots of the relevant tabs.

### 2.4 Make data freshness visible and meaningful

Close-to-real-time data is a core requirement, not a cosmetic
enhancement. Albion's markets can change quickly. If a buy price is
stale, an apparent crafting profit or city arbitrage opportunity may no
longer exist when the user acts on it.

The application should therefore: - Fetch and process updates as
frequently as the chosen data source and usage limits reasonably
permit. - Prefer event-driven or streaming updates where practical,
while retaining a sensible REST polling fallback. - Store the source's
update timestamp and the time ArgentIQ received the record. - Display
data age for every relevant price or price group. - Mark stale or
missing values explicitly. - Avoid presenting a recommendation as
reliable if its key inputs are too old. - Recalculate opportunities when
relevant input prices change. - Never claim that prices are "live"
merely because the website refreshed. - Explain that an upstream
community data feed may not contain every order or update from every
city.

The objective is **near-real-time when the source has fresh
observations**, with honest reporting when it does not. ArgentIQ cannot
manufacture missing upstream data by polling more often.

------------------------------------------------------------------------

## 3. Critical Data-Source Reality: Prices Versus Completed Sales

This distinction must be resolved early, because it affects what
ArgentIQ can truthfully promise.

### 3.1 Market price and order observations

The Albion Online Data Project (AODP) is a community-maintained source
that collects market observations contributed by players and makes
market-price data available through an API. Its coverage and freshness
depend on contributions. It should not be treated as a guaranteed,
complete official exchange feed.

Useful starting points: - AODP website:
https://www.albion-online-data.com/ - API documentation:
https://www.albion-online-data.com/api - Developer documentation:
https://www.albion-online-data.com/developer

Use the official documentation to confirm the currently supported
endpoints, parameters, regions, limits, fields, and stream behaviour
before implementation. Do not rely on remembered endpoint details
without checking them.

A price endpoint may provide the latest observed buy/sell prices and
timestamps. Historical price-statistics endpoints may provide aggregate
values over time. These are useful, but they are not automatically the
same as a record of each completed transaction.

### 3.2 The user's requested "past sales data"

The user would like to select an item and inspect its real in-game past
sales data. ArgentIQ must distinguish these concepts:

1.  **Current order-book/price observations:** observed buy and sell
    order prices.
2.  **Historical price statistics:** aggregated or sampled price
    information over time, depending on the endpoint.
3.  **Completed transaction history:** individual sales that actually
    occurred, ideally including transaction time, price, quantity, city,
    item variation, and possibly order type.

Do not label price observations or price averages as "completed sales"
unless the source explicitly confirms they represent completed
transactions.

Before promising transaction-level history, investigate whether an
accessible, permitted data source actually provides it for Albion
Online. Check AODP documentation, available public endpoints, and
relevant terms. Do not assume the official game API exposes it, and do
not build an undocumented scraper that violates site/game rules.

If reliable completed-sale records are not publicly available, implement
the best available alternative and label it accurately, such as
**historical observed prices** or **historical price statistics**.
Clearly explain the limitation in the interface. Keep the data-source
layer modular so a legitimate transaction-history source could be added
later.

### 3.3 Data-source acceptance checklist

Before building the full UI, make a small proof of concept that answers:

-   Which API endpoint serves current price observations?
-   Which endpoints serve historical statistics, and what exactly do
    their records mean?
-   Does any permitted source provide individual completed transactions?
-   Which server/region identifiers are supported?
-   Which timestamps are included, and what timezone/format do they use?
-   How are item quality and enchantment represented?
-   What are the request limits and expected update cadence?
-   What are the rules for caching, retaining, and redistributing
    collected data?
-   What happens when an item/city/quality combination has no recent
    observation?
-   Can a stream be resumed or recovered after a disconnect?

Document findings in `docs/DATA_SOURCES.md` with links and a date last
verified.

------------------------------------------------------------------------

## 4. Scope

### 4.1 MVP: required features

The first version should focus on finding crafting and market
opportunities.

#### A. Item search and item variations

Users should be able to search by item name and/or game item ID. The
system should handle relevant variations of an item:

-   **Tier:** the item's tier, such as T4, T5, T6, and so on, for tiers
    that exist for that item.
-   **Enchantment:** the item's supported enchantment level, commonly
    represented with the game's enchantment suffix conventions.
-   **Quality:** the item's supported quality values, such as Normal,
    Good, Outstanding, Excellent, and Masterpiece where applicable.
-   **City:** market city/market location.
-   **Server/region:** initially Asia.

Represent item variations as structured fields rather than relying only
on display-name string matching. Use authoritative or maintained item
metadata where available. Do not assume every item supports every
possible combination.

The UI should make it easy to compare variations without overwhelming
the user. Provide filters and sortable tables, with sensible defaults
and an option to expand advanced filters.

#### B. Cross-city price comparison

For the selected item variation, show relevant cities side by side,
including as available:

-   Lowest observed sell-order price (useful when buying from existing
    sell orders).
-   Highest observed buy-order price (useful when selling directly to
    existing buy orders).
-   Relevant order/quote fields exposed by the source.
-   Source timestamp and ArgentIQ retrieval timestamp.
-   Data freshness status.
-   Data missing/stale warnings.

Do not conflate a buy order with a sell order. Explain the player's
perspective in labels and tooltips: - A **sell order** is an offer
listed by another player to sell the item; buying immediately from it
generally costs the seller's ask price. - A **buy order** is an offer
listed by another player to buy the item; selling immediately into it
generally receives the buyer's bid price.

Actual market mechanics and fees must be confirmed against current game
behaviour and represented accurately.

#### C. Historical chart

For each selected item variation, show the historical data the source
genuinely provides. The chart should allow users to: - Select a time
range when supported. - See the data type (observed prices, price
statistics, or completed transactions). - Inspect timestamps and
values. - Identify gaps and stale periods. - Avoid misleading
interpolation over missing data.

If both buy-side and sell-side historical series are available, allow
users to toggle them. If only aggregated historical statistics are
available, clearly label them as such.

#### D. Crafting opportunity finder

The core screen should answer: **What should I craft, where should I buy
the inputs, where should I craft it, and where should I sell it?**

At a minimum, support: - Choosing a target item or browsing candidate
craftable items. - Loading its recipe and material quantities from a
verified recipe dataset. - Estimating material cost using selected
source cities and appropriate buy/sell-order assumptions. - Comparing
different cities for sourcing inputs. - Selecting or configuring the
crafting city/station and relevant crafting assumptions. - Accounting
for resource return rate (RRR) where applicable. - Supporting focus and
non-focus scenarios where applicable. - Including crafting station fees,
market fees/taxes, and other relevant costs as configurable and
documented inputs. - Comparing alternative selling cities and selling
strategies. - Showing estimated net profit per craft/batch, profit
margin, return on input cost, capital required, and price/data
freshness. - Ranking candidates by a user-selected metric. - Showing a
breakdown of every cost and revenue input. - Warning if the recipe, fee,
price, or return-rate data is incomplete or stale.

Do not hard-code a single RRR, tax, fee, focus bonus, or city bonus into
the calculations. Make game rules and user-specific assumptions
configurable and verify them. The calculation should explain whether it
assumes instant purchase/sale or placing orders and waiting.

#### E. Data freshness and collection status

Include a compact status area showing: - Server selected. - Last
successful collection time. - Last successful update for the selected
item/market where available. - API errors or throttling. - Number of
stale/missing price records in the current view. - Whether live-stream
collection is connected, if implemented.

#### F. Settings

Provide configuration for: - Server/region. - Relevant cities. - Refresh
behaviour within source limits. - Staleness thresholds. - Market fee/tax
assumptions. - Crafting location, focus, and return-rate assumptions. -
Profit-ranking preference. - Data retention settings if needed.

### 4.2 Explicitly out of scope for the MVP

Do **not** implement these before the market analyser is working and
tested:

-   Machine-learning price forecasting.
-   Sales-volume or demand forecasting.
-   Automated in-game buying/selling or botting.
-   Automated interaction with the game client.
-   User accounts, social features, or public leaderboards unless later
    requested.
-   Complex portfolio optimisation.
-   Paid data-provider integration by default.
-   Claims that recommendations guarantee profit.

### 4.3 Later phase: price/sales prediction

After the market analyser is reliable, consider forecasting the
near-future market value of selected items so users can plan materials
and crafting in advance.

This is a later phase only. Do not build predictive modelling into the
MVP or let it delay the core work.

Potential future work: - Build a clean historical dataset first. -
Define the target precisely, e.g. future observed sell price, buy price,
or a defined price statistic at a fixed horizon. - Compare simple
baselines before complex models. - Include prediction
intervals/uncertainty and data-coverage warnings. - Backtest using
chronological splits to prevent future data leaking into training. -
Evaluate errors across item categories, tiers, enchantments, qualities,
and cities. - Track whether forecasts beat a naive baseline. - Label
forecasts as estimates, not guarantees.

------------------------------------------------------------------------

## 5. Core Business Logic

### 5.1 Net profit, not just price difference

ArgentIQ should optimise realistic estimated net profit rather than
simply selecting the city with the highest listed price.

A simplified model is:

``` text
Expected net profit =
    expected net sale proceeds
  - effective material cost
  - crafting station fee
  - other crafting costs
  - market listing/sale fees and taxes
  - transport or other user-entered costs
  + value of resources returned by crafting
```

The implementation must verify the current in-game rules and avoid
double-counting costs or returns. The exact equation will depend on
whether the user buys via existing sell orders or buy orders, sells into
existing buy orders or lists sell orders, and whether returned resources
are sold, reused, or assigned a value.

Show at least: - Gross revenue. - Expected sale fees/taxes. - Net sale
proceeds. - Material cost before resource returns. - Estimated
resource-return value or effective material-cost reduction. - Crafting
fees. - Additional costs. - Net profit. - Profit margin. - Return on
cost. - Required capital. - Estimated break-even price. - Input-data age
and confidence/warning state.

Document the definitions of profit margin and return on cost to avoid
ambiguous percentages.

### 5.2 Buying and selling strategies

Do not assume that every quoted price can be achieved instantly.

At minimum, distinguish: - **Instant buy:** use an available sell order
as the purchase quote, if observed. - **Buy order:** use an appropriate
buy-order assumption, with an explicit note that execution is not
guaranteed. - **Instant sell:** use an available buy order as the sale
quote, if observed. - **Sell order:** use a sell-order quote or
user-defined expected sale price, with an explicit note that execution
time and sale are not guaranteed.

A profitable spreadsheet calculation is not the same as a guaranteed
fill. Where transaction volume or liquidity data is unavailable, say so
rather than inventing it.

### 5.3 City routing and crafting location

The system should evaluate different roles for cities: - Material
sourcing city/cities. - Crafting city. - Finished-item selling city.

These do not need to be the same city. If the user can source materials
from multiple cities, ArgentIQ may later optimise a shopping basket
across cities. For the first version, a transparent comparison of
practical alternatives is more important than a sophisticated route
optimiser.

Transport costs and risk may be optional user-entered values. Do not
assume transport is free if the user wants a realistic net-profit
calculation.

### 5.4 Opportunity ranking

Offer several ranking modes rather than one opaque "best item" score: -
Highest estimated net profit per craft. - Highest profit margin. -
Highest return on cost. - Lowest capital requirement. - Best
freshness/coverage among profitable options. - Best estimated profit for
a user-entered crafting budget.

Avoid recommending an option based on a single extreme or stale quote
without warning.

------------------------------------------------------------------------

## 6. Data Architecture and Storage

Keep the data ingestion layer separate from the business logic and
frontend so that data sources can be replaced or expanded later.

### 6.1 Suggested initial architecture

A practical starting architecture is:

-   **Frontend:** React with JavaScript, rendered as HTML and styled with
    CSS. Node.js and Vite build its assets for Laravel.
-   **Web backend:** Laravel/PHP serves the local interface and API and
    coordinates bounded collection requests.
-   **Collector:** Python owns AODP request parsing, validation, and
    normalised market writes. FastAPI is not required while Laravel is
    the only local web backend.
-   **Java module:** A narrow, testable evidence gate initially; extend
    it into calculations only after rules and inputs are verified.
-   **Database:** PostgreSQL for a durable deployment; SQLite is
    acceptable for an early local prototype.
-   **Background collection:** a Python worker or scheduled process.
-   **Charts:** a maintained charting library compatible with the chosen
    frontend.
-   **Market provider:** AODP initially, after checking current API
    documentation.
-   **Item and recipe metadata:** a versioned, validated data source
    kept separate from observed market prices.

Do not add Redis, message brokers, container orchestration, or other
infrastructure unless the actual workload requires them. Keep the first
implementation understandable and inexpensive.

### 6.2 Suggested data entities

Names are conceptual and can be adapted during implementation.

**Item metadata** - item_id - display_name - category - supported
tiers/variations if known - recipe/metadata source - metadata version or
last verified time

**Market observation** - item_id - tier - enchantment - quality - city -
server/region - buy-order price and any relevant quantity/metadata the
source provides - sell-order price and any relevant quantity/metadata
the source provides - source timestamp - received_at timestamp -
source/provider - raw payload or a safely retained subset where
permitted

**Historical statistic** - item variation identifiers - city and
server - statistic type - period or observation timestamp - value and
units - source timestamp and provenance

**Completed transaction** (only if a legitimate source is verified) -
transaction/source record ID where provided - item variation
identifiers - city/server - transaction timestamp - unit price -
quantity - source/provenance - confidence and validation fields if
needed

Do not populate the completed-transaction table with price snapshots. If
no legitimate transaction feed exists, keep this feature unavailable or
represent historical statistics in their own table.

**Recipe** - crafted item variation/rules - ingredient item IDs -
ingredient quantities - crafting output quantity - recipe source and
version - applicable crafting assumptions

**Calculation configuration** - fee/tax rules and effective dates -
city/station bonuses where verified - resource return rate assumptions -
focus assumptions - user-selected buy/sell strategy - extra cost
assumptions

**Opportunity result** - calculation timestamp - item variation - source
and destination choices - assumptions/configuration version - cost and
revenue breakdown - estimated net profit and related metrics - freshness
status for each key input

### 6.3 Data provenance

Every price must be traceable to its source and timestamp. Keep raw
upstream responses only when permitted and useful. The normalised schema
should not assume all providers use the same fields.

Separate: - `source_timestamp`: timestamp associated with the source
observation. - `received_at`: when ArgentIQ retrieved the observation. -
`calculated_at`: when an opportunity was computed.

This separation is essential for freshness checks, debugging, and future
model training.

------------------------------------------------------------------------

## 7. Near-Real-Time Collection Strategy

Near-real-time freshness is a product requirement and should influence
the architecture from the beginning.

### 7.1 Initial implementation

Start with a small, well-tested collector: 1. Fetch a small selection of
item variations across a few cities. 2. Validate the response and
timestamps. 3. Normalise the records. 4. Upsert the latest observation
and optionally append a historical snapshot. 5. Log success, errors,
latency, and rate-limit responses. 6. Recalculate affected
opportunities. 7. Expose data freshness through the backend API.

Do not request every possible item variation across every city on every
cycle by default. Use batching, caching, bounded retries, and a refresh
strategy appropriate to the source limits.

### 7.2 REST polling and streaming

Begin with REST polling because it is easier to reason about and test.
Review the current AODP documentation for streaming options, including
NATS if currently supported, before deciding whether a stream is
beneficial.

A future stream-based design should handle: - Reconnection and
backoff. - Duplicate and out-of-order observations. - Missing messages
and recovery. - Data validation. - Retention and compaction. -
Monitoring and health checks.

A stream is not automatically more complete than REST data. It can
reduce update latency for observations that are actually emitted, but it
cannot guarantee all markets are represented.

### 7.3 Freshness policy

Define configurable freshness thresholds. Do not silently hard-code one
universal threshold for every item and endpoint. A possible initial
policy, subject to measurement, is: - **Fresh:** observation within the
target freshness window. - **Aging:** observation is older than the
target but still within a tolerated window. - **Stale:** observation is
too old for a confident recommendation. - **Unavailable:** no valid
observation exists.

The interface should show exact age/timestamp as well as the label. Do
not show a green "live" status if only the website itself is updating.

The collector should prioritise selected/watchlisted items and items
relevant to current opportunity calculations, within the provider's
limits.

------------------------------------------------------------------------

## 8. User Experience and Main Screens

Keep the experience clearer than a large multi-tab spreadsheet.

### 8.1 Dashboard

Show: - Current server. - Collection status and latest successful
update. - High-level market freshness. - Top current opportunities, with
caveats. - Quick access to item search and the crafting finder.

### 8.2 Item Market page

A user selects an item and sees: - Item name and variation selectors. -
Tier, enchantment, quality, city, and server. - Current buy/sell quotes
by city. - Update timestamps and freshness indicators. - Historical
chart with clearly identified data type. - Completed sales only if a
verified source supplies real transaction records. - A concise
comparison of best available buy and sell choices.

### 8.3 Crafting Finder page

Allow the user to: - Select an item or browse craftable items. -
Configure the number of crafts/batches. - Choose focus and crafting
assumptions. - Compare sourcing, crafting, and selling cities. - Select
instant orders versus order-placement assumptions. - Filter by tier,
enchantment, quality, category, profit, margin, and capital. - Sort
opportunities. - Open an opportunity to inspect every calculation input.

### 8.4 Opportunity detail

A result should be explainable with a breakdown, not merely a profit
number. Show: - Recipe and required quantities. - Source city and price
for each ingredient. - Whether each ingredient quote is a buy or sell
order. - Resource return calculation and assumptions. - Crafting city
and fee assumptions. - Finished-item sale city and price assumption. -
Fees/taxes. - Estimated profit and margin. - Timestamps/freshness for
all important observations. - Warnings for missing or stale data.

### 8.5 Visual design

Use a clear, modern, data-dense but readable dashboard. Tables should
support sorting, filtering, and column visibility. Use colour sparingly
and never rely on colour alone to communicate stale or missing data.
Ensure the site works on common desktop screen sizes first; mobile
support can follow without blocking the core use case.

------------------------------------------------------------------------

## 9. Reliability, Testing, and Guardrails

The application should be financially useful as a decision-support tool,
not make unsupported guarantees.

### Required safeguards

-   No fabricated prices, recipes, completed transactions, or
    timestamps.
-   No treating missing values as zero.
-   No using stale prices without warning.
-   No confusing buy orders and sell orders.
-   No claiming historical price averages are completed sales.
-   No guaranteeing a trade will execute at a quoted price.
-   No hidden fee assumptions.
-   No unverified crafting rules.
-   No over-polling or ignoring API rate limits.
-   No dependency on paid services for the core local prototype.

### Test coverage

-   API response parsing and validation.
-   Missing, malformed, stale, and out-of-order data.
-   Item variation mapping for tier/enchantment/quality.
-   Price comparison across cities.
-   Buy-order versus sell-order semantics.
-   Recipe ingredient quantities and output quantities.
-   Resource-return calculation.
-   Crafting fee and market fee calculations.
-   Profit, margin, return-on-cost, and break-even calculations.
-   Handling of missing recipe inputs.
-   Freshness propagation into opportunity rankings.
-   Regression tests with hand-calculated examples.
-   Frontend behaviour when data is unavailable.

Use deterministic unit tests for all financial calculations. Keep the
profit calculation engine independent from UI components and external
API calls.

------------------------------------------------------------------------

## 10. Suggested Repository Layout

Adapt this to the chosen framework, but keep responsibilities separated.

``` text
ArgentIQ/
├── README.md
├── PROJECT_SPEC.md
├── .env.example
├── .gitignore
├── docs/
│   ├── DATA_SOURCES.md
│   ├── DATA_MODEL.md
│   ├── PROFIT_CALCULATIONS.md
│   └── ROADMAP.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── data_sources/
│   │   ├── ingestion/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── calculations/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── features/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json
├── data/
│   ├── item_metadata/
│   └── recipes/
└── scripts/
    ├── check_data_source.py
    └── seed_metadata.py
```

This is a suggested target layout, not a requirement to create every
folder immediately. Build only what the current milestone needs.

------------------------------------------------------------------------

## 11. Implementation Milestones

### Milestone 0: Validate data feasibility

-   Read the current AODP API and developer documentation.
-   Verify current Asia-server endpoints and item ID conventions.
-   Test a small set of item variations across several cities.
-   Record timestamps, missing data, and observed freshness over time.
-   Investigate whether a legitimate source provides completed
    transaction records.
-   Document rate limits, terms, and data limitations.
-   Do not build forecasting yet.

**Exit condition:** We understand which current prices and historical
data can actually be obtained and what "sales history" can truthfully
mean.

### Milestone 1: Minimal data collector

-   Build a small Python collector.
-   Validate and normalise results.
-   Save observations to SQLite initially.
-   Add logging, error handling, caching, and basic retry/backoff.
-   Store source timestamps and retrieval timestamps.

**Exit condition:** Repeated runs collect valid data without duplicating
or corrupting records.

### Milestone 2: Market comparison

-   Add a Laravel endpoint for item price comparison and a local React
    interface using HTML, CSS, and JavaScript.
-   Build item variation selectors.
-   Show city comparison tables.
-   Show source timestamps and freshness states.
-   Add a historical chart for the history the source actually provides.

**Exit condition:** A user can select a variation and inspect its
available market observations across cities.

### Milestone 3: Recipes and profit engine

-   Source and validate recipe metadata.
-   Implement deterministic calculation functions.
-   Add tests using manually verified examples.
-   Support transparent crafting, return-rate, fee, and sale
    assumptions.

**Exit condition:** The system produces explainable and tested estimates
for a small set of recipes.

### Milestone 4: Crafting opportunity finder

-   Evaluate candidate items.
-   Compare material sourcing, crafting, and selling cities.
-   Rank opportunities by configurable metrics.
-   Flag stale or incomplete inputs.
-   Display a detailed calculation breakdown.

**Exit condition:** The user can make a practical, informed crafting
decision from one workflow.

### Milestone 5: Reliability and usability

-   Improve performance and query efficiency.
-   Add watchlists and configurable refresh behaviour if useful.
-   Test missing data and upstream outages.
-   Improve layout and usability based on actual use.
-   Deploy only if public access is desired.

### Later milestone: Prediction

Only after sufficient reliable history has been collected and the market
analyser is validated, design and evaluate a forecasting feature
separately.

------------------------------------------------------------------------

## 12. Instructions for Codex

Treat this file as the product specification and source of truth for the
initial scope.

When beginning work:

1.  Inspect the existing repository before creating or overwriting
    files.
2.  If the repository is empty, establish a small, clear project
    skeleton.
3.  Do not try to implement every milestone in one pass.
4.  Start with **Milestone 0: Validate data feasibility** and then
    implement a small working vertical slice.
5.  Verify current API documentation and endpoints rather than guessing.
6.  Clearly distinguish observed market prices, historical statistics,
    and completed transactions.
7.  Prioritise data freshness, provenance, correct item variation
    handling, and tested profit calculations.
8.  Keep the implementation free or low-cost by default and avoid adding
    paid services without asking.
9.  Do not implement predictive modelling in the MVP.
10. Before making major architectural decisions, explain the trade-offs
    and choose the simplest option that meets the current requirements.
11. Maintain a concise README with setup instructions and update the
    documentation as assumptions are verified.
12. Never claim the application is real-time, accurate, or profitable
    without evidence from testing.

### Definition of MVP success

The MVP is successful when ArgentIQ can: - Retrieve and persist valid
market observations for selected Asia-server item variations. - Display
price comparisons across cities, tier, enchantment, and quality where
the source supports them. - Clearly communicate the age and limitations
of the data. - Show genuine historical data with correct labels. -
Calculate and compare crafting opportunities using explicit, tested
assumptions. - Recommend a sourcing/crafting/selling option based on
estimated net profit, while making uncertainty and missing data
visible. - Run locally without requiring a paid subscription for its
core functionality.

------------------------------------------------------------------------

## 13. Naming and Independence

The product name is **ArgentIQ**. Use this name consistently in the UI,
documentation, and repository metadata.

ArgentIQ is intended to be an independent community tool, not an
official Albion Online product. Do not imply endorsement by Sandbox
Interactive or by the creators of third-party tools used as inspiration.
Respect game, data-provider, and source-project terms, and attribute
data sources where required.

------------------------------------------------------------------------

## 14. Key Principle

**ArgentIQ should optimise decisions, not just display prices.**

The quality of its recommendations depends on three things working
together: 1. Market observations that are as fresh and complete as the
source permits. 2. Correct, transparent calculations that account for
real costs and game mechanics. 3. An interface that explains the
evidence and warns when the evidence is weak.

When those foundations are reliable, prediction and other advanced
analytics can be added later.
