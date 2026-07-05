# Project 2 — Luxury Goods Market Share & Equity Valuation Analytics

**A Reproducible Python/DuckDB Pipeline Benchmarking 9 Global Luxury Houses**

> Ingests segment/geographic revenue from company filings, US GAAP financials from SEC EDGAR, equity prices
> from yfinance, and industry benchmarks from Damodaran, then models market share, segment mix, margins,
> growth, and valuation multiples across the world's top luxury houses in an interactive Streamlit dashboard.

**Difficulty:** Intermediate→Advanced · **Effort:** ~60–90h · **Data cleanliness:** ★★★☆☆ (PDF extraction is the slow part)

The most **finance-recruiter-appealing** project — comps, multiples, market share, valuation-vs-fundamentals.

---

## Why it's compelling (the interview story)
"I built a comps model across the 9 listed global luxury houses — normalizing IFRS vs US-GAAP filings and four
currencies, hand-mapping each house's distinct segment and geographic taxonomy into a common schema, then
benchmarking margins and EV/EBITDA, EV/Sales and P/E against Damodaran industry averages to flag who's expensive
for their fundamentals. Hermès's structural margin premium shows up cleanly." That's real sell-side analyst work.

## Scope (fixed universe, FY2015–FY2024, annual)
- **Universe (9 listed houses):** LVMH (`MC.PA`), Kering (`KER.PA`), Richemont (`CFR.SW`), Hermès (`RMS.PA`), Burberry (`BRBY.L`), Prada (`1913.HK`), Brunello Cucinelli (`BC.MI`), Estée Lauder (`EL`), Tapestry (`TPR`), Capri (`CPRI`).
- **"Market share" is explicitly defined as revenue share *within this listed peer set*** (not total Bain market — that's context only), so the metric is reproducible from primary filings.
- **Four pillars:** (1) *Market share & concentration* — revenue share + HHI within the peer set. (2) *Revenue mix* — segment (fashion & leather, watches & jewelry, wines & spirits, beauty, retail) and geographic (Europe, Americas, Asia ex-Japan, Japan, other) decomposition, hand-mapped to a common schema. (3) *Financial performance* — revenue CAGR, gross/operating/net margins, currency-normalized to EUR & USD. (4) *Valuation* — EV/Sales, EV/EBITDA, trailing P/E benchmarked vs Damodaran, with valuation-vs-growth and valuation-vs-margin scatters.
- **Out of scope:** quarterly modeling, DCF, options, private (non-listed) brands.

## Analytical questions
1. Each house's revenue-based share within the peer set; how has sector HHI evolved 2015–2024; did the 2024 downturn consolidate or fragment share?
2. How does segment mix differ across houses, and which mix proved most resilient during the 2024 contraction?
3. Geographic revenue split per house, and exposure to the China slowdown vs Japan/US strength.
4. 3/5/10-year revenue CAGRs per house once currency effects are normalized out.
5. Gross/operating/net margins across houses/time — does Hermès's structural margin premium show cleanly vs Damodaran's apparel-industry average?
6. Do current multiples (EV/Sales, EV/EBITDA, P/E) rank houses the same way growth and margins do — who's "expensive for their fundamentals"?
7. Does the listed peer set's aggregate growth track the Bain/Altagamma total market — are listed houses gaining or losing share of the total?
8. Where do yfinance fundamentals diverge from SEC EDGAR ground truth for US filers (EL, TPR, CPRI)?

## Verified datasets
| Source | What / how used | Access |
|--------|-----------------|--------|
| **SEC EDGAR XBRL** company facts / frames | Ground-truth income statement & balance sheet for **EL, TPR, CPRI**; reconciliation benchmark for yfinance | No key; 10 req/s; **`User-Agent: name email` header required.** IFRS filers (European houses) are NOT here |
| **Company Universal Registration Documents / Annual Reports (PDF)** | **Primary source for segment & geographic revenue** for all houses (esp. the IFRS ones absent from EDGAR) | Direct PDF URLs (LVMH URD, Kering, Richemont, Hermès, Burberry, Prada IR pages). ⚠️ **taxonomies differ by house → documented manual mapping table** (itself a defensible artifact) |
| **yfinance** | Share price, market cap, EV inputs for EV/Sales, EV/EBITDA, P/E for **all** houses; return series | No key, fragile. ⚠️ **non-US fundamentals often empty** — use it for prices only, not European income statements |
| **Damodaran NYU Stern** datasets | Industry-average margins & multiples benchmark (margin.xls, vebitda.xls, pedata.xls, psdata.xls; +Europe/+Global variants) | Direct `.xls`, no key. ⚠️ URLs overwritten each January — pin the file + download date |
| **Bain × Altagamma Luxury Study** | Total-market denominator & segment/regional narrative context | Free press releases / Altagamma Monitor PDFs (full decks partly gated — headline figures are free) |
| **World Bank Open Data API** (optional) | Macro-context: correlate regional revenue exposure with consumption/GDP per capita | No key; paginated |
| **Financial Modeling Prep** (optional) | Convenience cross-check only | ⚠️ endpoints changed + free plan capped — **not core; EDGAR + URDs are ground truth** |

## Methodology
1. Config + skeleton. 2. Ingest: EDGAR XBRL (US filers), URD PDFs (segment/geo tables), yfinance prices (cache to Parquet), Damodaran `.xls`, World Bank API. 3. Land raw in DuckDB. 4. **The hard/valuable part — hand-map each house's segment & geographic taxonomy into a common schema** (documented crosswalk table). 5. **Currency-normalize** to EUR & USD (state FX source + spot-vs-average convention); align non-aligned fiscal year-ends (Richemont/Burberry end in March). 6. Marts: revenue share, HHI, CAGRs, margins, EV/Sales, EV/EBITDA, P/E. 7. Benchmark vs Damodaran; **reconcile yfinance vs EDGAR for US filers** and quantify variance. 8. pandera gates, figures, multi-page Streamlit, pytest over every formula, CI, README.

## Visualizations
- Market-share explorer (revenue share within peer set, HHI trend).
- Segment-mix stacked bars per house + resilience-during-2024 view.
- Geographic-exposure map/stacked bars (China vs Japan/US).
- Margin ladder (gross/op/net) with Damodaran benchmark markers — Hermès premium highlighted.
- **Valuation-vs-fundamentals scatter** (EV/EBITDA vs growth; multiple vs margin) with outlier callouts.
- yfinance-vs-EDGAR variance panel.

## Honest CV bullets
- Built an end-to-end **Python/DuckDB** pipeline benchmarking **9 listed global luxury houses across 10 fiscal years**, integrating **6 free sources** (SEC EDGAR XBRL, registration-document PDFs, yfinance, Damodaran, World Bank, Bain/Altagamma) into a layered warehouse.
- **Normalized heterogeneous disclosures (IFRS vs US GAAP; EUR/CHF/GBP/USD)** and hand-mapped each house's distinct segment & geographic taxonomy into a common schema, enabling apples-to-apples comparison.
- Computed revenue-based market share, sector **HHI**, 3/5/10-year CAGRs, margins, and **EV/Sales, EV/EBITDA, P/E** multiples, benchmarking each house vs Damodaran to flag valuation premia/discounts.
- Implemented a **data-integrity layer reconciling yfinance fundamentals against SEC EDGAR ground truth** for 3 US filers, quantifying line-item variance.
- Enforced quality with pandera + a pytest suite covering all financial formulas, wired into GitHub Actions CI; delivered an interactive multi-page Streamlit dashboard reading live from DuckDB.

## Risks / gotchas
- **Segment/geo taxonomies differ materially** (LVMH's 5 groups vs Kering's brand tiers vs Richemont's Jewellery Maisons/Watchmakers vs US beauty/accessories) — the crosswalk requires judgment; treat it as a transparent first-class artifact.
- **Fiscal year-ends not aligned** (Richemont/Burberry March) — state an alignment convention.
- **yfinance non-US fundamentals frequently empty** — prices only; cache aggressively.
- **EDGAR covers only US filers** — European/Asian financials come from PDFs (more manual).
- **Currency normalization introduces analyst choices** (spot vs average FX) — document them.
- **Don't scrape Statista/Macrotrends/stockanalysis.com** (paywalled / ToS forbids bots) — use primary filings + free Bain/Altagamma headlines.
- Corporate actions: Prada (owns Miu Miu; agreed to acquire Versace); Capri/Tapestry attempted-then-abandoned merger — note caveats so comps aren't distorted.

## Extensions
Regression of regional revenue growth on World Bank consumption/GDP · ESG KPIs from URDs vs valuation · reverse-DCF implied-growth back-out · earnings-date event study on share price · quarterly granularity for US filers via 10-Qs · auto-updating peer-set-share-of-total-market tracker · Docker + monthly refresh.
