# ArgentIQ
## Revised Project Specification: Albion Online Food Market Forecasting

**Status:** Requirements and scope revision  
**Initial server:** Asia  
**Initial item domain:** Food items  
**Application:** Single-user, local-first website  
**Forecasting method:** Deliberately undecided pending discussion with the project owner.

## 1. Executive Summary

ArgentIQ is changing direction.

The original project was planned as an Albion Online market-analysis tool that would collect market observations and eventually help players compare prices, calculate crafting costs, and identify profitable crafting or trading opportunities.

The project is now being redirected towards **historical market-price analysis and forecasting for Albion Online food items**.

The change is motivated by a practical limitation of the existing community data collection approach: market observations depend on data being contributed for particular items, variants, and locations. Running the data client does not guarantee fresh, complete observations for every item and city. If a player has not loaded a particular market view, relevant observations may be absent or old. Refreshing the ArgentIQ website cannot create missing upstream observations.

Rather than prioritising a broad market-analysis tool that depends on sufficiently fresh observations across many item and city combinations, the new priority is to investigate historical-data availability and build a food-focused market-history and forecasting experience.

The first domain is food because the owner wants to inspect and forecast market values across the food branch, including different food categories, individual food items, tiers, and enchantment levels where applicable.

The website should let a user filter the food catalogue and view a line chart containing historical prices and forecast prices. Historical observations use a **solid line**. Forecast values use a **dotted line**. The two lines must visually connect at the forecast boundary: the forecast line starts at the final historical price point, then continues into the future. This connection is a visual transition only; it must not imply that forecast values are observed facts.

The forecasting algorithm, model family, libraries, training strategy, and other prediction implementation decisions are deliberately left open. They will be decided through a separate discussion before implementation.

## 2. Scope Change: Original Project and Revised Project

### 2.1 Original direction

The original ArgentIQ concept focused on market analysis and crafting/trading decisions. Its intended workflow included:

1. Collect market observations from the chosen data source.
2. Compare item prices across cities and item variations.
3. Inspect historical market information.
4. Estimate material costs and crafting fees.
5. Compare crafting and selling locations.
6. Estimate realistic net profit after relevant costs.
7. Rank possible crafting or trading opportunities.
8. Display data freshness, assumptions, and limitations.

The original plan treated forecasting as a later feature, after the market analyser became reliable.

### 2.2 Why the direction is changing

The project owner found that community-contributed market observations are not necessarily comprehensive or continuously fresh for every item, item variation, and city. The data collection client may depend on players opening specific market views in the game. Leaving the client running alone does not guarantee recent data for every food item and variant.

This creates a mismatch between a broad, current-market-analysis goal and the coverage that can be reliably obtained from the available source.

The revised direction prioritises historical data and forecasting. Before committing to any forecasting method, the project must investigate whether usable historical observations are available for the food catalogue and how complete those observations are.

### 2.3 Revised direction

The revised project will:

- Focus first on Albion Online food items.
- Build or validate a catalogue of relevant food item types and variants.
- Investigate and use legitimate historical data sources where available.
- Store and display historical observations with their provenance and timestamps.
- Allow users to search and filter food items.
- Display historical prices and forecast prices in one line chart.
- Make the transition from history to forecast clear while visually connecting the two lines.
- Show missing-data and data-coverage limitations honestly.
- Keep the forecasting implementation undecided until the owner and assistant discuss the available options.

### 2.4 Features no longer at the centre of the initial scope

The following are not the focus of the revised initial release:

- Finding the most profitable item to craft.
- Optimising material sourcing across cities.
- Selecting the best crafting location.
- Calculating full crafting profitability, taxes, resource returns, and transport costs.
- Ranking crafting opportunities by net profit.
- Building a general market-analysis tool for every item category.

These ideas may be reconsidered later, but they must not displace the current food-history and forecasting goal.

## 3. Product Goal and Success Criteria

### 3.1 Product goal

Provide a local website where the user can select an Albion Online food item or group of food variants, inspect available historical market-price information, and view a forecast extending from the historical price line into a future period.

### 3.2 Catalogue coverage versus forecast coverage

ArgentIQ should aim to represent every valid food item in the chosen catalogue, but it must distinguish two forms of coverage:

- **Catalogue coverage:** the item can be found, selected, and identified, even if market history is missing.
- **Forecast coverage:** enough suitable historical observations are available to produce and evaluate a forecast under the method eventually selected.

A complete catalogue does not mean every item can immediately receive a trustworthy forecast. When data is missing or insufficient, ArgentIQ should show that status rather than inventing prices or silently substituting unrelated data.

### 3.3 Initial success criteria

The initial version should be considered successful when:

1. Users can browse, search, and filter the supported food catalogue.
2. Food type, item, tier, and enchantment filters work together coherently.
3. The website can display available historical prices for selected food variants.
4. The chart differentiates historical and predicted values by line style.
5. The forecast line starts at the final historical point and continues into the future.
6. The interface makes the history/forecast boundary understandable.
7. Each displayed series is tied to the correct item variant and supported data scope.
8. Missing or stale observations are visible.
9. The application never presents illustrative, synthetic, or missing values as genuine market observations.
10. The data and prediction pipeline can be tested separately from the interface.
11. The forecasting approach is selected only after a documented discussion and data-feasibility review.

## 4. Scope and Boundaries

### 4.1 Game and region

- Game: Albion Online.
- Initial server: Asia.
- The design should avoid unnecessarily hard-coding assumptions that would make other regions impossible to support later.
- Other servers are not required for the first release.

### 4.2 Item domain

The first item domain is food. Candidate categories include Sandwiches, Omelettes, Stews, Soups, Roasts, Salads, Pies, and other valid categories discovered during catalogue verification.

These examples are not an authoritative final list. The catalogue must be based on validated in-game item metadata or another reliable source, not only a hand-written list.

Ingredients, fish, and other food-related items should not automatically be treated as prepared food products. Their inclusion or exclusion must be resolved during catalogue definition and clearly categorised if included.

### 4.3 Item variations

The catalogue and filters should account for valid variants supported by the game and data source, including where applicable:

- Food type or category.
- Specific food identity, such as Beef Sandwich or Beef Stew.
- Tier.
- Enchantment level.
- Any other variant dimension required to uniquely identify a market item.

Do not assume every food item supports every tier or enchantment. Offer valid variants for the selected item based on verified catalogue metadata.

Quality should only be added as a filter if it is meaningful and supported for food items and the data source.

### 4.4 Local-first operation

The existing project is intended to run on the owner's Windows computer and be accessed through a local loopback address. Public hosting, user accounts, and multi-user features are not required for this phase.

Keep the application local by default. Do not expose the development server or data services to the public internet without a separate security review.

## 5. Food Selection Interface

The food market page should provide a search bar and four main dropdown filters.

### 5.1 Search bar

Purpose: quickly find a food by name.

Requirements:

- Search should match relevant food item names.
- Search should work together with dropdown filters.
- Search should narrow displayed results rather than silently discarding selected filters.
- Search should handle partial names and differences in letter case.
- Show a clear empty state when nothing matches.
- Search the validated food catalogue, not only currently loaded chart series.

Example: typing `beef` should narrow results to matching catalogue entries, subject to the other active filters.

### 5.2 Food Type dropdown

Purpose: filter food items by category.

Requirements:

- Include an all-types option.
- Drive options from the validated catalogue.
- Selecting a type should narrow choices in the Food dropdown.
- Changing the type should clear or reset a selected food if it does not belong to the new type.

### 5.3 Food dropdown

Purpose: optionally select a specific food identity.

Examples include Beef Sandwich, Pork Omelette, and Beef Stew, subject to catalogue verification.

Requirements:

- Include an all-foods option.
- Depend on the selected Food Type.
- Leaving Food set to all foods should allow the user to inspect multiple items of the selected type.
- Selecting a specific food should narrow displayed data to that food across the selected tiers and enchantments.
- If a food is incompatible with the selected type, it must not remain selected.

This filter is intentionally optional. It must be possible to inspect multiple items of the same type without selecting a single food identity.

### 5.4 Enchantment dropdown

Purpose: filter by enchantment level.

Requirements:

- Include an all-enchantments option.
- Offer only valid enchantment variants for the current selection.
- Display the game's enchantment notation clearly, such as normal `.0` and enchanted `.1`, `.2`, and `.3`, where valid.
- Do not assume all levels exist for all foods.
- When all enchantments are selected, distinguish separate variants rather than combining unlike variants into a misleading price series.

### 5.5 Tier dropdown

Purpose: filter by item tier.

Requirements:

- Include an all-tiers option.
- Offer only valid tiers for the current selection.
- Support comparing the same food across multiple tiers.
- Keep separate tier variants identifiable.
- Do not combine prices across tiers into one average or series by default.

### 5.6 Filter interaction rules

All controls should work together.

Examples:

- **Food Type = Sandwich; Food = All foods; Tier = All tiers; Enchantment = All enchantments:** inspect available sandwich items and supported variants.
- **Food Type = Sandwich; Food = Beef Sandwich; Tier = All tiers:** compare supported tiers of Beef Sandwich.
- **Food Type = All types; Food = All foods; Tier = T6; Enchantment = Normal (.0):** inspect catalogue items that validly match that combination.
- **Search = `beef`; Food Type = Sandwich:** search within the selected category and return matching sandwich items.

The website must not silently merge different food identities, tiers, or enchantments into one series. Any multi-series comparison must identify each series clearly.

### 5.7 Results states

The interface should distinguish:

- Results with historical observations and a forecast.
- Results with historical observations but no available forecast.
- Results with insufficient historical coverage.
- Results with no observations available.
- Results whose observations are too old for the configured freshness expectations, if such expectations are later defined.

Exact freshness thresholds are not decided in this document.

## 6. Historical Price and Forecast Line Chart

### 6.1 Main requirement

The central visualisation is a line chart displaying historical market prices followed by forecast prices for selected food variants.

- Historical prices: **solid line**.
- Predicted prices: **dotted line**.

Colours may also distinguish series, but colour must not be the only way users can tell history from prediction.

### 6.2 Connected transition between history and forecast

The user explicitly wants the lines to connect.

Requirements:

1. The historical line ends at the final valid historical observation.
2. The forecast line starts at that same final historical point.
3. The forecast line continues through future predicted points.
4. The historical segment remains solid.
5. The future segment remains dotted.
6. There should be no visual gap between the final historical point and the first forecast segment when a forecast is available.
7. The shared point is a chart transition, not a claim that the future is known.
8. The chart must not draw through missing historical observations as though those observations existed.

Implementation note: the display series may reuse the final historical point as the first point of the forecast segment to create a continuous connection. That shared anchor must not be stored or reported as a second historical observation or as a newly generated forecast value. The model's actual forecast output and the chart's display representation must remain conceptually distinct.

If a forecast cannot be generated, the historical line should simply end at the last observation. The chart must not fabricate a dotted extension.

### 6.3 History/forecast boundary

The chart should make the transition understandable without breaking the connected line. Possible treatments include:

- A subtle vertical divider at the forecast start time.
- A label such as `Forecast begins`.
- A marker at the shared boundary point.
- A legend explaining solid versus dotted lines.

The exact visual treatment can be chosen during interface implementation, but it must not introduce a gap.

### 6.4 Axes and values

The chart should include:

- Horizontal axis: date and time.
- Vertical axis: market-price value in silver, using a readable numeric format.
- Tooltips on data points.
- A legend.
- Clear item and variant identification.
- A selected historical time range.
- A selected forecast horizon, once supported by the eventual forecasting method.

Do not label a metric as an actual transaction price unless the source explicitly supplies completed transaction records. If the source provides aggregated historical sell-order statistics, label them accurately as historical price statistics or observed market prices.

### 6.5 Hover details

For a historical point, show the supported timestamp, price, item variant, and relevant source/data-quality information.

For a forecast point, identify it as predicted, show its forecast timestamp and predicted price, and include a forecast range or uncertainty information only if the eventual method supports it.

The interface must not imply more precision than the data or method justifies.

### 6.6 Multiple selected variants

If the user selects all foods, all tiers, or all enchantments, the system may return multiple variants. The chart must avoid clutter and ambiguity.

Requirements:

- Every series must have a readable label identifying the food and relevant tier/enchantment.
- Historical and forecast segments must be distinguishable for every series.
- A series must not accidentally connect points belonging to different items or variants.
- The interface may allow users to toggle series on or off.
- If too many series are selected to read clearly, provide a way to narrow the selection.
- Prices from different item variants must not be averaged together by default.

Whether to show multiple variants in one chart or encourage one variant at a time can be refined during UI planning. Correct series identity and readability are mandatory.

### 6.7 Time range controls

The interface should eventually let users select the historical period and forecast horizon. Candidate historical ranges include 7 days, 30 days, 90 days, or all available history. Candidate forecast horizons include 24 hours, 3 days, or 7 days.

These are candidate options, not commitments that the data source or method can support them. Final options should depend on data granularity, historical coverage, and the forecasting method selected later.

### 6.8 Uncertainty display

If the chosen method can produce a defensible prediction interval, ArgentIQ may show a shaded range around the dotted forecast line. The range must be explained and must not be described as a guarantee.

Do not invent confidence intervals if the chosen method does not provide a defensible basis for them.

## 7. Data Source and Data Quality Requirements

### 7.1 Community-contributed market data

The existing project uses the Albion Online Data Project (AODP) as a market-data source. It is community-maintained, not a guaranteed complete official feed. Coverage and freshness depend on contributed observations and supported endpoints/data products.

Verify current documentation before implementing or changing collection behaviour:

- AODP website: https://www.albion-online-data.com/
- AODP API documentation: https://www.albion-online-data.com/api
- AODP developer documentation: https://www.albion-online-data.com/developer

Do not assume undocumented endpoint behaviour, field meanings, historical depth, or coverage. Verify current API documentation, available database exports, permitted use, and rate limits before implementation.

### 7.2 Historical observations are not necessarily completed transactions

ArgentIQ must distinguish:

1. Current order or market-price observations.
2. Historical aggregated or sampled price statistics.
3. Individual completed transactions.

Do not describe an observation or aggregated statistic as a completed sale unless the source explicitly confirms that it represents a completed transaction.

The chart should forecast the same well-defined price metric actually available from the source. The target metric must be decided during data-feasibility work before modelling begins.

### 7.3 Historical-data feasibility investigation

Before selecting a forecasting approach, investigate:

- Which historical datasets and endpoints are available for the Asia server.
- Whether bulk database exports are available and suitable for local ingestion.
- How far back usable food-price observations extend.
- Which food items and variants have observations.
- The time granularity of observations.
- How missing periods and irregular timestamps are represented.
- Whether timestamps contain a timezone or require a documented assumption.
- Whether the source distinguishes buy and sell prices, and which is suitable for the intended forecast.
- Whether historical data is sufficiently consistent for meaningful evaluation.
- Practical dataset size, update frequency, rate limits, and storage requirements.
- Data-source terms and attribution requirements.

Do not conclude that every food can be forecast simply because every food can be listed in a catalogue.

### 7.4 Data provenance

For stored observations, retain the source and available timestamps needed to explain where the value came from and when it was observed or retrieved.

Where supported by the source and existing schema, preserve:

- Item identifier.
- Item variant information.
- Server or region.
- City or location, if relevant to the selected data model.
- Price-statistic type.
- Observation timestamp.
- Source retrieval timestamp.
- Source name or endpoint.
- Validation or data-quality status.

Base the final schema on verified source fields and the existing database. Do not invent unavailable metadata.

### 7.5 Missing and stale data

- A page refresh does not make old source observations fresh.
- Do not fill missing historical observations with invented values.
- Do not silently use one food variant as a substitute for another.
- Do not silently use another city's data as if it were the selected city.
- Represent missing data explicitly.
- Make old observations identifiable through timestamps or documented freshness labels.
- Do not conceal weak coverage during forecasting.
- A catalogue entry with no history should remain findable if it is in the validated catalogue, but its history/forecast status must be described accurately.

Freshness thresholds and minimum-history requirements are not set yet. They depend on data exploration and the later forecasting discussion.

## 8. Catalogue Requirements

### 8.1 Source of truth

Build the food catalogue from validated item metadata and identifiers. Do not depend solely on names typed into the frontend.

Map each supported food to the exact item identifier and variant representation required by the data source.

### 8.2 Required catalogue information

Store or derive, where available and verified:

- Canonical item identifier.
- Display name.
- Food type/category.
- Tier.
- Enchantment level.
- Any additional variant dimensions required to distinguish the market item.
- Whether the item belongs to prepared food or a separately categorised related-item group.
- The source or rule used to establish the catalogue entry.

### 8.3 Catalogue validation

Before treating the catalogue as complete:

- Validate that each entry corresponds to a real supported item.
- Check for duplicate display names with different identifiers or variants.
- Check tier and enchantment availability.
- Check category assignments.
- Separate prepared foods from ingredients or related items where necessary.
- Record unresolved items rather than guessing identifiers.

The catalogue should be able to list a valid food item even when its historical data is unavailable.

## 9. Revised Application Architecture

Retain the existing architecture and technologies where they remain useful, rather than rewriting the project solely because its scope changed.

The current project specification assigns these roles:

- **HTML and CSS:** page structure and styling.
- **React and JavaScript:** interactive frontend, filters, chart, and UI state.
- **Node.js and Vite:** frontend build tooling.
- **PHP and Laravel:** local web server, backend API, and coordination of supported operations.
- **Python:** data collection, validation, normalisation, and historical-data preparation.
- **SQLite:** local storage for observations and metadata.
- **Java:** a separate, testable evidence or rule-checking component from the original architecture.

The Java component should not be forced into the forecasting pipeline without a demonstrated requirement. Review its role against the revised goal before retaining it in a prediction-related workflow. Do not create duplicate collectors or competing calculation logic merely to use every technology.

### 9.1 Suggested logical separation

Keep these concerns separate:

1. **Catalogue layer:** validated food metadata and item variants.
2. **Data ingestion layer:** obtains historical observations from verified sources.
3. **Validation and normalisation layer:** checks fields, timestamps, item identities, and data quality.
4. **Storage layer:** stores observations and provenance locally.
5. **Historical query layer:** retrieves the requested food variant and period.
6. **Forecasting layer:** reserved for a method to be selected later.
7. **Evaluation layer:** reserved for testing forecasts against data not used to create them.
8. **Backend API:** provides catalogue, history, and eventual forecast results to the frontend.
9. **Frontend:** filters the catalogue and renders historical/forecast series.

This is a conceptual separation, not a commitment to a particular package, class, API route, or model library.

### 9.2 Local operation and performance

- Keep the application local-first for the initial phase.
- Avoid unnecessary paid services.
- Avoid loading the entire historical dataset into the browser when a backend query can return the selected range.
- Use efficient queries and indexes appropriate to the verified schema.
- Keep historical retrieval separate from forecast computation so each can be tested independently.
- Do not make the page depend on a forecasting service that has not been selected or implemented.
- Handle missing data and collection failures without crashing the whole interface.

## 10. Forecasting Implementation: Decision Pending

**This section is intentionally left unselected. No forecasting algorithm or model is approved by this document.**

The project owner wants to discuss available options before deciding how the prediction feature should be implemented.

Do not silently select or implement any of the following on the project's behalf:

- A statistical forecasting method.
- A machine-learning model.
- A deep-learning model.
- A third-party prediction API.
- A model-training framework.
- A particular feature set.
- A fixed forecast horizon.
- A minimum-history threshold.
- A confidence-interval method.
- A retraining schedule.
- A fallback model.

These are decision topics for a later discussion.

### 10.1 Work that can happen before the model decision

- Verify the source's historical-data capabilities.
- Build and validate the food catalogue.
- Inspect coverage and quality of historical food observations.
- Decide precisely what price statistic the website intends to forecast.
- Store historical observations with provenance and timestamps.
- Build the food search and filter interface.
- Build the chart using historical data.
- Define a clean interface between historical data retrieval and future forecast output.
- Prepare a reproducible data-quality report for representative food variants.

### 10.2 Work that must wait for the decision

Do not implement these until an explicit method has been chosen:

- Model-specific data transformations.
- Training and inference pipelines.
- Model-specific feature engineering.
- Model persistence or model-serving infrastructure.
- Model-specific uncertainty estimates.
- Model-specific retraining schedules.
- Forecast generation presented as a real feature.

The chart may be developed with clearly labelled mock data for interface testing, but mock values must never be confused with real market history or an actual model forecast.

### 10.3 Forecast validation requirement

Whatever method is eventually selected, its performance must be evaluated against historical observations not used to generate the corresponding forecast. Evaluation must respect time ordering; future observations must not leak into training data for a past forecast.

Metrics, baseline comparisons, validation windows, and acceptance thresholds remain undecided until the method and data characteristics have been discussed.

ArgentIQ must not claim that forecasts are accurate, reliable, or profitable without evaluation evidence.

## 11. User Workflow

1. Open ArgentIQ locally.
2. Open the food market/forecasting page.
3. Search for a food name or select a food type.
4. Optionally choose a specific food identity.
5. Select a tier and/or enchantment, or leave a filter set to all valid options.
6. Select a historical time range and, when available, a forecast horizon.
7. Inspect the chart.
8. Read the legend to distinguish solid historical prices from dotted forecast prices.
9. Hover over points to inspect supported values and timestamps.
10. Review data coverage, freshness, and missing-data notices.
11. Narrow the selection if too many variants make the chart difficult to read.

The user should not need to understand the internal collector, database, or forecasting implementation to use the page.

## 12. Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | The application shall provide a food-focused market-history and forecasting page. |
| FR-02 | The application shall provide a search bar for food names. |
| FR-03 | The application shall provide a Food Type dropdown. |
| FR-04 | The application shall provide an optional Food dropdown dependent on Food Type. |
| FR-05 | The application shall provide an Enchantment dropdown with valid options for applicable items. |
| FR-06 | The application shall provide a Tier dropdown with valid options for applicable items. |
| FR-07 | Search and dropdown filters shall work together. |
| FR-08 | The catalogue shall distinguish valid food items and variants even when history is unavailable. |
| FR-09 | The application shall display available historical market-price observations for a selected variant. |
| FR-10 | The chart shall display historical values with a solid line. |
| FR-11 | When a forecast is available, the chart shall display predicted values with a dotted line. |
| FR-12 | The dotted forecast line shall start at the final historical price point and continue into the future without a visual gap. |
| FR-13 | The interface shall clearly distinguish historical observations from forecasts. |
| FR-14 | The chart shall not invent historical values for missing observations. |
| FR-15 | The application shall identify each series by food identity and variant. |
| FR-16 | The application shall communicate missing, stale, or insufficient data. |
| FR-17 | The application shall distinguish observed price statistics from completed transactions. |
| FR-18 | The data pipeline shall preserve source provenance and available timestamps. |
| FR-19 | The historical data layer shall be usable and testable independently of the eventual forecasting method. |
| FR-20 | No forecasting algorithm shall be selected or implemented until a separate decision is made with the project owner. |

## 13. Non-Functional Requirements

### Accuracy and honesty

- Never present a prediction as a confirmed market observation.
- Never present a historical statistic as a completed sale unless supported by the source.
- Never invent missing prices or item identifiers.
- Clearly identify limitations in coverage and freshness.
- Use the same target-price definition consistently in historical and predicted series.

### Usability

- Make search and filters straightforward.
- Keep dropdown choices valid for the current selection.
- Use clear labels, a readable chart, and informative tooltips.
- Use line style as well as colour to distinguish history from prediction.
- Keep the chart understandable when multiple variants are selected.

### Maintainability

- Separate catalogue, collection, storage, history retrieval, forecasting, evaluation, and presentation responsibilities.
- Avoid duplicated business logic.
- Document assumptions and data-source semantics.
- Keep model-specific decisions isolated so they can be changed after evaluation.

### Performance

- Query only selected data ranges and variants where practical.
- Avoid sending unnecessary historical records to the browser.
- Handle catalogue searches and multi-series charts efficiently.
- Do not block the entire application if a data request fails.

### Cost

- Prefer local and free/open-source tools where practical.
- Do not add paid APIs, cloud services, or subscriptions without asking the owner first.
- Treat zero recurring cost as a goal, not an unconditional guarantee.

## 14. Testing Requirements

### Catalogue and filters

- Search by full and partial item names.
- Confirm search is case-insensitive.
- Change Food Type after selecting a specific Food and verify incompatible selections are cleared.
- Confirm only valid tiers and enchantments are offered.
- Confirm all-items and all-variants selections do not merge unrelated series.

### Historical chart

- Confirm historical values are plotted as a solid line.
- Confirm missing historical values are not fabricated.
- Confirm timestamps are ordered correctly.
- Confirm tooltips show the right item variant, timestamp, and price.
- Confirm the chart does not connect points from different variants.

### Forecast display, once a method is approved

- Confirm the forecast line is dotted.
- Confirm it begins at the final historical point with no visual gap.
- Confirm the shared anchor does not create a duplicate observation in storage or evaluation.
- Confirm no forecast line is displayed when no forecast is available.
- Confirm the chart boundary and legend distinguish observed history from future predictions.
- Confirm evaluation does not leak future observations into past forecasts.

### Data handling

- Test empty history, partial history, stale history, invalid records, and collection failures.
- Verify source and retrieval timestamps are handled consistently.
- Verify the displayed price metric matches the source's semantics.
- Verify unsupported variants are not silently substituted.

## 15. Implementation Phases

### Phase 1: Scope and data feasibility

- Review the current repository and existing database before changing files.
- Verify current AODP documentation and available historical data products.
- Investigate available Asia-server historical data and permitted bulk exports.
- Determine real coverage and granularity for representative foods.
- Validate the definition of the market-price metric to be displayed.
- Record unresolved assumptions and limitations.

**Exit condition:** There is an evidence-based account of what historical food data can and cannot be obtained.

### Phase 2: Food catalogue

- Build or validate the food catalogue.
- Map display names to correct item identifiers and supported variants.
- Verify category, tier, and enchantment relationships.
- Separate prepared foods from related items if needed.
- Add catalogue validation tests.

**Exit condition:** Users can browse valid foods and variants regardless of whether history exists.

### Phase 3: Historical data foundation

- Implement or adapt the collector/importer based on verified source capabilities.
- Normalise and validate observations.
- Store historical data and provenance locally.
- Support efficient queries by variant and time range.
- Document timestamp assumptions and data coverage.

**Exit condition:** Historical observations can be retrieved consistently for supported variants.

### Phase 4: Search, filters, and historical chart

- Build the search bar and four dropdown filters.
- Implement dependent dropdown behaviour.
- Build the historical line chart.
- Add tooltips, legends, empty states, and data-quality indicators.
- Test single-item and multi-variant selections.

**Exit condition:** The interface clearly displays genuine historical data for selected foods.

### Phase 5: Forecasting-method discussion

- Review actual historical data and its limitations.
- Discuss candidate forecasting approaches with the project owner.
- Compare options using feasibility, interpretability, complexity, cost, data needs, and validation requirements.
- Agree on a target metric, initial forecast horizon, evaluation design, and acceptance criteria.
- Record the chosen method before implementation begins.

**Exit condition:** The owner explicitly approves a forecasting approach and evaluation plan.

### Phase 6: Forecasting implementation and evaluation

**Reserved for after Phase 5.** Exact implementation tasks depend on the approved approach and must not be filled in by assumption.

The forecast feature should only be considered ready after it has been tested against appropriate historical holdout periods and its limitations are visible in the interface.

## 16. Instructions for Codex and Future Contributors

1. Treat this revised specification as the source of truth for the revised product direction.
2. Inspect the current repository, README, schema, and existing collector before making changes.
3. Preserve working code where suitable; do not rewrite the entire project without a clear reason.
4. Explain proposed changes that remove or replace existing components.
5. Prioritise food-catalogue correctness and historical-data feasibility.
6. Verify current data-source documentation rather than guessing endpoint fields or semantics.
7. Do not claim the website can forecast every food until coverage and evaluation support that claim.
8. Do not implement a forecasting model before the owner has discussed and approved the approach.
9. Use mock data only for clearly labelled UI development and testing.
10. Keep real observations, forecast outputs, and display-only chart anchors conceptually separate.
11. Do not call historical price statistics completed transactions unless the source explicitly supports that meaning.
12. Preserve local-first operation and avoid new paid dependencies without approval.
13. Update setup and project documentation when verified assumptions change.
14. Never claim forecasts are accurate or profitable without test results.

## 17. Current Decisions and Open Questions

### Decisions already made

- The project is named ArgentIQ.
- The initial game server is Asia.
- The initial item domain is food.
- The project is shifting from broad market analysis towards food market history and forecasting.
- The page will include a search bar and dropdowns for Food Type, optional Food, Enchantment, and Tier.
- The main chart will show history and prediction together.
- Historical prices will use a solid line.
- Predicted prices will use a dotted line.
- The dotted forecast line must connect to the final historical point.
- The prediction implementation is not yet chosen.
- The existing project is intended to remain local-first for now.

### Questions to resolve through investigation or discussion

- What historical food-price data is practically available for Asia?
- Which exact price statistic should be forecast?
- Should the first view focus on one food variant at a time or support multi-series comparison prominently?
- What historical ranges are supported by the data?
- What forecast horizons are appropriate for the available granularity?
- What minimum data coverage should be required before showing a forecast?
- How should freshness be defined and communicated?
- Which forecasting method best fits the available data and project constraints?
- How should the forecast be evaluated, and what performance would count as acceptable?
- Should uncertainty bands be shown, depending on the chosen method?
- Which parts of the original Java evidence/check component remain useful in the revised architecture?

These questions are intentionally open. Resolve them using the repository, verified data-source information, and a separate forecasting-method discussion rather than guessing in advance.

## 18. Guiding Principle

**ArgentIQ must make the distinction between what the market data shows and what the system predicts unmistakable.**

The solid historical line represents recorded observations from the selected source. The dotted line represents a forecast generated by a method that has yet to be selected and validated. Connecting the lines improves readability, but does not remove the distinction between evidence and prediction.

The immediate priority is to establish a reliable food catalogue and understand the available historical data. Only then should the project commit to a forecasting approach.
