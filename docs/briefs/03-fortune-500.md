# Project 3 — Fortune 500 Financial Breakdowns

**A Multi-Year DuckDB Panel of Corporate America's Largest Firms**

> A reproducible Python + DuckDB data-engineering & analytics project that builds a multi-year Fortune 500 panel
> to quantify sector profitability, revenue-per-employee efficiency, geographic concentration, and year-over-year
> list churn — surfaced through a Streamlit dashboard.

**Difficulty:** Intermediate · **Effort:** ~40–70h · **Data cleanliness:** ★★★★☆ (community CSVs)

Recommended as the **quick win / first project** — most approachable data, best pure **data-engineering** showcase, and it builds the reusable toolkit (DuckDB warehouse, SEC client, yfinance caching) you reuse in the other three.

---

## Why it's compelling (the interview story)
"I engineered a reproducible DuckDB warehouse over ~10 years of Fortune 500 data, then showed that tech and pharma
dominate margins while retail dominates headcount, that revenue-per-employee varies ~20× across sectors, and that
~3–5% of the list turns over annually with churn concentrated in energy and retail." Recruiters care less about a
top-10 bar chart and more about turning a messy, multi-source, multi-year dataset into a clean analytical warehouse.

## Scope (a longitudinal panel, not "explore the data")
- Clean, tested, reproducible **multi-year panel of Fortune 500 (US)** companies (Global 500 optional stretch), canonical schema: `company, year, rank, revenue, profit, assets, employees, sector, industry, HQ city/state` + derived `net_margin, revenue_per_employee, rank_change`.
- **Core deliverable = the data engineering** (ingest heterogeneous CSVs/scrapes into DuckDB with cross-year entity resolution + unit normalization) plus ~7 fixed analytical questions answered with SQL + pandas and visualized.
- **Not** a full SEC reconciliation of every firm (stretch), not a stock-returns study, not a live pipeline. Everything runs from `make pipeline` on a fresh clone with only free data.

## Analytical questions
1. **Does size predict profitability?** Correlation between revenue/assets and net margin, overall and by sector — is "bigger = more profitable" true, or does margin decouple from scale?
2. Which sectors are most/least profitable (median net margin, ROA), and how have sector rankings shifted YoY?
3. How does **revenue-per-employee** vary across sectors, and which industries are the extreme outliers (energy/finance vs retail/hospitality)?
4. How concentrated is the list by industry & geography (top-10/25/50 revenue share, HHI over the decade)?
5. Where is corporate America headquartered (states/metros by count, revenue, employees; gainers vs losers)?
6. **How churny is the list?** Annual entry/exit rate, sector churn (disruption proxy), survival of former top-100 firms.
7. Biggest rank movers — do upward movers systematically differ (margin, growth, sector) from decliners?
8. Revenue & profit per employee leaderboards; total Fortune 500 headcount footprint by sector over time.

## Verified datasets
| Source | What / how used | Access |
|--------|-----------------|--------|
| **Fortune 500 multi-year CSV — `cmusam/fortune500`** (GitHub) | Longitudinal spine → DuckDB base fact table (company-year grain) | No key. ⚠️ **Combined-file URL 404s — data is per-year files `csv/fortune500-YYYY.csv` (2005–2019 verified).** Concatenate; pin a commit SHA; mirror into `data/raw/` |
| **Kaggle Fortune 500 / 1000 datasets** | Enrichment: sector, industry, HQ city/state, employees, market cap for recent year(s) | **Free Kaggle account + API token**; prefer CC0/CC BY datasets; pin slug+version |
| **Wikipedia — largest US companies by revenue** | Current-year refresh & cross-check (~top 100) | `pandas.read_html`, no key, set a User-Agent. Not the full 500 — use for recency/validation |
| **SEC EDGAR XBRL** company facts / frames | Validation/stretch: audited Revenues/NetIncome/Assets for public constituents | No key; 10 req/s; **`User-Agent` header required.** Covers only public filers (not Cargill, Koch, State Farm) |
| **yfinance** | Optional enrichment: sector/industry, employees, market cap for public firms | No key, fragile — cache to Parquet |
| **Damodaran NYU Stern** | Per-industry benchmark margins/ROC to contextualize Fortune sector aggregates | Direct `.xls`, no key; industry taxonomy differs → mapping table needed |

## Methodology
1. Typed config (URLs, pinned SHA, Kaggle slug+version, SEC User-Agent). 2. **Ingest** GitHub per-year CSVs, Kaggle enrichment, Wikipedia scrape, optional SEC/yfinance — cache all raw. 3. Land raw verbatim in DuckDB with source + `ingested_at` lineage. 4. **Clean/normalize** column names, types, **units to USD millions**, sector labels via mapping, HQ→city+state. 5. **Cross-year entity resolution** — resolve name variants (M&A, rebrands) to a stable `company_id` via normalized-name matching + alias/override table. 6. **Model marts** — `fact_company_year` (grain company×year) + `dim_company`; SQL **window functions** for `net_margin, roa, revenue_per_employee, rank_change`, entered/exited churn flags. 7. Data-quality gates (exactly 500 ranks/year, non-null keys, non-negative financials, valid sector enum). 8. Run the 8 analyses (correlation/regression, sector aggregates + Damodaran join, HHI/concentration, churn/survival). 9. Figures + Streamlit + pytest + CI + README with data dictionary.

## Visualizations
- Size-vs-margin scatter (log revenue vs net margin, colored by sector, trend line + outlier callouts).
- Sector profitability boxplot/violin with Damodaran benchmark markers.
- Revenue-per-employee ranked bars (log scale), extreme ends highlighted.
- Concentration trend lines (top-10/25/50 share + HHI).
- **US-state HQ choropleth** (Plotly) with revenue/employee toggles + top-metros bar.
- YoY churn stacked bars (entrants vs exits + churn-rate line), churn-by-sector small multiples.
- Rank-movement bump/slope chart, animated by year in the dashboard.

## Honest CV bullets
- Engineered a reproducible **Python + DuckDB** pipeline ingesting & reconciling **4+ heterogeneous free sources** (multi-year GitHub CSV, Kaggle, scraped Wikipedia, SEC EDGAR XBRL) into a layered warehouse (raw→staging→marts) covering **~10 years × 500 companies (~5,000 company-year records)**.
- Built **cross-year entity resolution** and unit-normalization logic to track firms through rebrands/M&A, enabling YoY rank-change, survival, and churn analysis with a documented alias table.
- Modeled a **fact/dimension schema** in DuckDB and used **SQL window functions** to derive net margin, ROA, revenue-per-employee, rank_change, and churn flags — quantifying that revenue-per-employee spans **~20×** across sectors and ~3–5% of the list turns over annually.
- Ran a size-vs-profitability analysis (Pearson/Spearman + per-sector regression) showing net margin largely decouples from scale, benchmarked against Damodaran NYU industry datasets.
- Shipped an interactive **Streamlit** dashboard (US-state HQ choropleth, concentration & churn views, animated rank movement) and enforced reliability with **pandera** gates, pytest, typed config with pinned source versions, and GitHub Actions CI.

## Risks / gotchas
- Fortune's rankings are **proprietary editorial data — no official free API**; the GitHub/Kaggle CSVs are *community reproductions* (cite them as such; accuracy varies).
- **Hardcoded URLs drift/404** — pin commit SHA / dataset version and mirror raw into the repo.
- Employees/sector/industry/HQ columns are **inconsistently present** across years — enrich the current year well, accept sparser history, document it.
- Fortune figures use **company-specific fiscal conventions** — won't tie exactly to SEC/yfinance; frame those as a validation layer.
- SEC/yfinance cover **only public filers** — private members have no data.
- Sector taxonomies differ across sources → a **crosswalk table is required** (also a skill to showcase).
- Nominal dollars aren't inflation-adjusted — deflate with a free CPI/GDP-deflator if making trend claims.

## Extensions
Add Global 500 (US vs rest-of-world) · full SEC XBRL reconciliation "data-quality chapter" · inflation-adjust with CPI · market-cap-to-revenue via yfinance · publish marts as Parquet + a small FastAPI/MotherDuck share · predict next-year list exit from margin/growth/rank · annual auto-refresh GitHub Action · M&A event annotations on the biggest rank jumps.
