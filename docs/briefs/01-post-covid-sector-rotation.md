# Project 1 — Post-COVID Sector Rotation

**An Event-Study and Macro-Linkage Analysis of U.S. Equity Sectors (2019–2025)**

> A reproducible Python + DuckDB pipeline that quantifies how the 11 U.S. equity sectors crashed,
> recovered, and structurally re-ranked through and after COVID-19 — linking sector returns, drawdowns,
> and volatility to macro indicators and the pandemic stringency timeline via a formal Feb–Mar 2020 event study.

**Difficulty:** Intermediate→Advanced · **Effort:** ~50–70h · **Data cleanliness:** ★★★★★ (fully automatable)

Recommended as the **flagship / best effort-to-impressiveness ratio**: cleanest free data, real quant methodology.

---

## Why it's compelling (the interview story)
"I ran a formal market-model event study of the COVID crash across all 11 GICS sectors, measured cumulative
abnormal returns vs. the S&P 500 over a 250-day estimation window, and showed which sectors were *structural*
losers vs. winners — then linked recovery speed to sector-specific macro damage (payrolls, industrial production)
and the pandemic stringency timeline." That's a defensible, quantitative, finance-literate narrative.

## Scope (tight & defensible)
- **Universe:** 11 SPDR sector ETFs — XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLU, XLB, XLRE, XLC — vs. **SPY** benchmark.
- **Window:** daily, 2019-01-01 → present. + 8 macro series + one COVID case/stringency series.
- **Three layers:** (1) *Descriptive* — returns, rolling vol, max drawdown, recovery time, Sharpe/Sortino, correlation regimes. (2) *Event study* — cumulative abnormal returns (CAR) vs. a market-model expectation around 19-Feb→23-Mar-2020, 250-day pre-event estimation window. (3) *Macro linkage* — align monthly/quarterly macro + daily VIX + stringency to sector returns; regress recovery speed on sector macro damage.
- **Out of scope:** single-stock alpha, options, intraday, international markets.

## Analytical questions
1. Which sector had the deepest COVID drawdown, and does that ranking match the ranking by *recovery time* (days to reclaim pre-crash peak)? Did the hardest-hit also recover slowest, or did Tech do both?
2. In a formal market-model event study, which sectors had statistically significant **negative** CARs (Energy, Financials?) vs. **positive** CARs (Tech, Staples, Health Care?) — and does the sign flip in the 2021–22 inflation regime?
3. Did cross-sector correlations spike toward 1.0 in the March-2020 panic ("diversification fails when you need it") and then disperse?
4. How did rolling 21-day annualized volatility evolve — which sectors blew up most, and how long to normalize to 2019 baseline?
5. Does sector-level macro damage explain recovery speed (BLS/FRED industry payrolls, industrial production)?
6. Relationship between the COVID stringency index / case waves and short-horizon sector returns — did lockdowns hit "physical-economy" vs "stay-at-home" sectors?
7. Which sectors had the highest **VIX beta** during the shock?
8. Comparing 2019 pre-COVID leadership to 2023–25 post-COVID leadership: which sectors *permanently* re-ranked vs. mean-reverted?

## Verified datasets
| Source | What / how used | Access |
|--------|-----------------|--------|
| **Sector ETFs + SPY daily OHLCV** — via **yfinance** (`yf.download([...])`) **or** `pandas-datareader` `StooqDailyReader` | Primary price panel: returns, vol, drawdowns, recovery, correlations, abnormal returns | No key. ⚠️ **Stooq's direct CSV endpoint is now behind a JS anti-bot wall** — use the library fetchers and **cache to Parquet** (hit network once) |
| **FRED** (Federal Reserve Economic Data) | Macro-linkage + VIX beta: `VIXCLS` (daily), `UNRATE`, `INDPRO`, `CPIAUCSL`, `GDP`, sector payrolls `MANEMP`/`USCONS`/`USTRADE` | **Free 32-char API key** (fredaccount.stlouisfed.org). Use `fredapi` or `pandas_datareader.DataReader(name,'fred')` |
| **Our World in Data — COVID-19** | Stringency + case/death waves overlay | Direct CSV, no key. ⚠️ **frozen 19-Aug-2024** → scope COVID overlay to 2019–2024 |
| **Oxford OxCGRT** (optional) | Decompose stringency into containment vs. economic-support sub-indices | `OxCGRT_compact_national_v1.csv`, no key |
| **BLS Public Data API** (optional) | Industry-specific payroll collapse/recovery | Free v2 key → 500 queries/day (many series also on FRED) |
| **BEA GDP-by-Industry** (optional) | "Markets lead the real economy": value-added recovery vs. ETF recovery | Free 36-char UserID (apps.bea.gov/api/signup) |

## Methodology (pipeline)
1. Config (tickers, date range, series IDs, seed) → skeleton (`src/`, `sql/`, `data/raw|staging|mart`, `tests/`, `dashboard/`).
2. **Ingest once, cache to Parquet:** prices via yfinance/pandas-datareader; macro via FRED; COVID via OWID CSV. Retry/back-off.
3. Land raw in DuckDB (`raw_*`), then staging: adjust, compute daily/cumulative returns, align calendars.
4. **Descriptive marts:** rolling 21-day annualized vol, max drawdown, recovery-time-to-peak, Sharpe/Sortino, rolling correlation matrices.
5. **Event study:** estimate each sector's market model (α, β vs SPY) over the 250-day pre-peak window; compute abnormal returns and CARs across the crash window; t-test significance.
6. **Macro linkage:** resample monthly/quarterly macro to align with daily returns (document the resampling!); estimate per-sector VIX beta; regress recovery speed on macro damage.
7. Data-quality gates (pandera), figures, Streamlit dashboard, pytest + CI, README with findings.

## Visualizations
- Drawdown & recovery ranking (bar) — depth vs. days-to-recover, side by side.
- Event-study CAR chart — CAR paths per sector around the crash window, significance-flagged.
- Correlation-regime heatmaps — pre-shock vs. March-2020 panic vs. post.
- Rolling-volatility small multiples with a 2019-baseline line.
- Stringency/case overlay on sector returns.
- VIX-beta ranked bar. 2019-vs-2025 leadership slope/bump chart.
- Streamlit: sector/date/event-window controls over the DuckDB mart.

## Honest CV bullets
- Built an end-to-end reproducible **Python + DuckDB** pipeline ingesting ~12 ETFs and 8 macro/COVID series (2019–2025) from 4 free APIs (yfinance/Stooq, FRED, OWID, BEA/BLS) into a local SQL warehouse, with **cached idempotent ingestion resilient to source rate-limiting and anti-bot blocks**.
- Engineered a formal **market-model event study** of the Feb–Mar 2020 crash, estimating cumulative abnormal returns vs. SPY over a 250-day window for all 11 sectors and **t-testing significance** to separate structural winners from losers.
- Quantified sector drawdowns (~30–50% peak-to-trough) and recovery times, ranking all 11 sectors by days-to-reclaim-peak.
- Modeled the market-vs-fundamentals gap by aligning daily returns with monthly/quarterly macro and the daily VIX, estimating **per-sector VIX-betas** and regressing recovery speed on macro damage.
- Shipped an interactive **Streamlit** dashboard (DuckDB-backed, deployed publicly) and hardened it with pytest over financial-math + data-quality checks, ruff/pre-commit, and **GitHub Actions CI**.

## Risks / gotchas
- **Stooq CSV is behind a JS anti-bot wall** (verified) — use library fetchers + cache; don't do naive `requests.get`.
- **yfinance is fragile in 2025–26** (HTTP 429) — fetch once, cache, retry/back-off; never depend on it live.
- **OWID COVID CSV frozen 19-Aug-2024** — scope the overlay accordingly.
- Price series are split-adjusted but **exclude dividends** — for total-return claims use adjusted close and state the method.
- **Frequency mismatch** (GDP quarterly, macro monthly, prices daily) is the main analytical trap — resampling must be explicit or correlations are spurious.
- Event-study validity needs a **clean estimation window** (2019 must exclude other structural breaks).
- Correlation ≠ causation — frame macro findings as associations/regimes.

## Extensions
BEA "markets lead the economy" chart · second-shock event study (2022 rate-hike regime) · rules-based sector-rotation backtest vs SPY (with cost caveats) · Fama-French factor decomposition · international sector comparison · weekly auto-refresh via GitHub Actions.
