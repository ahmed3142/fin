# Project 5 — Industry Value-Chain & the Margin-Distortion Anomaly

**A Multi-Table Analysis of How U.S. Industries Invest, Profit, and Fund Themselves — Built on Damodaran's Industry Datasets**

> A reproducible Python + DuckDB pipeline that conforms ~30 of Aswath Damodaran's industry-level datasets onto one
> `dim_industry` spine, then tests a single, non-obvious thesis: **reported operating margins mis-rank U.S. industries
> versus R&D/lease-adjusted margins — and the equity market prices the adjusted number, so cross-industry screening on
> reported margins is wrong.** The engineering story is the *join* (entity resolution across a free-text industry key)
> and a *validation harness* that reproduces one of Damodaran's own published regressions from raw files.

**Difficulty:** Advanced · **Effort:** ~55–80h · **Data cleanliness:** ★★★★☆ (clean values, dirty join key + vintage traps)

Positioned as the **portfolio's "analytical thinking" capstone** — it reuses the Project 1–4 plumbing (DuckDB warehouse,
cached ingestion, pandera, Streamlit, CI) and spends the entire novelty budget on the *thesis* and the *data model*,
which is exactly where these three inputs — `margin.html`, `R&D.html`, `finflows.html` — are strongest.

---

## Why it's compelling (the interview story)
"Damodaran's industry tables are a commodity everyone re-skins. I did the opposite: I conformed thirty of them onto one
industry dimension, then used the *join* to surface a claim no single page states — that adjusting operating margins for
R&D and leases (Damodaran's own method) **reshuffles the industry margin ranking**, and that **EV/Sales tracks the
adjusted margin, not the reported one.** So a naive cross-industry margin or P/E screen systematically misprices
R&D-heavy sectors. Every number is validated by a pipeline that reproduces Damodaran's published capital-structure
regression from raw files, and I'm explicit that these are value-weighted industry aggregates — associations, not
firm-level causation." That is a variant perception with a decision attached, not a dashboard.

## The thesis (one claim, deliberately narrow)
- **Headline (descriptive, measured — not a regression):** Across ~94 U.S. industries, replacing reported operating
  margin with Damodaran's lease-&-R&D-adjusted operating margin **moves N industries by ≥K rank positions** (Spearman ρ
  between the two rankings = X); the reshuffle is concentrated in the **top R&D-intensity decile**, which gains ~Y pp of
  margin. This is an honest *restatement* of his adjustment, quantified — never presented as a discovery.
- **Payoff (empirical, non-tautological):** Regress market multiples — **EV/Sales (`psdata`) and P/E (`pedata`)** — on
  reported vs. adjusted margin across industries. **Which margin does the market track?** If EV/Sales follows the
  *adjusted* margin, screening on *reported* margins is provably misleading; if the market already prices the adjusted
  figure, that null is itself the finding. This points the empirical test at a **market outcome**, escaping the
  circularity that kills a naive "R&D → adjusted-margin" regression.
- **Strong alternative flagship (zero circularity, pure `finflows`):** **Leverage-funded capital return** — industries
  with net buybacks (negative Net Equity Change) that *co-occur* with net debt *raised* (positive Net Debt Change), and
  whose (dividends + buybacks) **exceed FCFE** (join `divfcfe`). Capital return funded by borrowing, not free cash flow.

## Scope (single vintage first; panel is the stretch)
- **Grain:** one row per **industry × vintage × region**. v1 = US, Jan-2026 vintage (TTM through ~Q3 2025 — *label it that
  way, it is not "2026 data"*).
- **Core inputs (the three given):** `margin.html` (gross/net/operating margins incl. R&D- & lease-adjusted, plus
  R&D/Sales, SBC/Sales), `R&D.html` (R&D intensity, capitalized-R&D estimate, 5y R&D), `finflows.html` (dividends,
  buybacks, equity issuance, debt raised/repaid, net-equity/net-debt change, lease-debt change).
- **Thesis-path additions:** `psdata` + `pedata` (the market-pricing payoff), `divfcfe` (payout vs FCFE).
- **Out of scope (v1):** the government cross-check layer (BEA/NSF/BLS/Census), a full SEC-EDGAR rebuild, and 20+ of the
  sibling facts — landed as raw/staging only, not modeled deeply. One thesis, executed, beats a taxonomy-bridging octopus.

## Analytical questions
1. How far does the R&D-&-lease adjustment move each industry's operating margin, and **how many rank reversals** does it
   cause between the reported and adjusted rankings? Where is the reshuffle concentrated?
2. Does the market (EV/Sales, P/E) track **reported or adjusted** margins across industries?
3. Which industries return capital **funded by debt** (net buybacks + net debt raised), and which return **more than their
   FCFE**? Is "shareholder yield" partly a leverage story?
4. In high-SBC industries, do **gross buybacks overstate cash returned** (buybacks large, but Net Equity Change ≈ 0)?
5. Do industries **cluster** into recognizable life-cycle / financing archetypes (growth reinvestors, mature cash-cows,
   leveraged capital-intensive, deleveraging mature) from the joined margin + R&D + financing features?
6. *(panel stretch)* Is the reported-vs-adjusted margin gap **widening** over the decade? Are buybacks rising as a share of
   book equity? (Requires stacked archive vintages — a real trend claim a single snapshot cannot make.)

## Verified datasets
| Source | What / how used | Access |
|--------|-----------------|--------|
| **Damodaran — `margin`, `R&D`, `finflows`** (the three given) | Core margin / intangible-investment / financing-flow facts, one row per industry | Free `.xls` at `pages.stern.nyu.edu/~adamodar/pc/datasets/<stem>.xls`. ⚠️ **overwritten every January** — hash + pin each vintage |
| **Damodaran — `psdata`, `pedata`** | Market multiples (EV/Sales, P/E) for the market-pricing payoff regression | Same host/convention; same 94-industry key |
| **Damodaran — `divfcfe`, `capex`, `EVA`/`roe`/`wacc`, `fundgr`/`histgr`, `betas`, `taxrate`, `MktCap`, `Employee`** | Sibling facts for clustering, life-cycle staging, value-creation (ROIC−WACC), sizing/weighting | Same host/convention. ⚠️ **filename traps** (US `betas.xls` but regional `betaEurope.xls`; `MktCap` case drift in old vintages) |
| **Damodaran archives** | Prior vintages → the multi-**year** panel | `.../pc/archives/<stem><YY>.xls` (verified 1/99→1/25). **Use this, not the Wayback Machine** for `.xls` binaries |
| **SEC EDGAR XBRL frames** (optional, Phase 2) | Rebuild **one** industry from company filings to **show within-industry dispersion** and defuse the ecological-fallacy critique | Free; `User-Agent: name email` header; ~10 req/s. **Not** a full validation rebuild (see risks) |
| **FRED** (optional, panel only) | Condition financing-flow behavior on the macro regime (rates, Baa/BBB credit spreads, GDP) | Free 32-char key; temporal join to each vintage year |
| **Fama-French 48/49 defs + Census NAICS↔SIC concordance** (optional, only if EDGAR) | Bridge Damodaran's custom industries ↔ SIC/NAICS for the EDGAR join | Free. GICS is **proprietary — no free crosswalk**; pivot on **SIC** (embedded in every EDGAR filer) |
| **BEA GDP-by-Industry · NSF BERD · BLS QCEW · Census SUSB** (context only) | Share-of-economy, government R&D cross-check, employment/coverage ratios | Free (some need instant keys). ⚠️ **basis mismatch** (value-added ≠ revenue; establishment ≠ firm) — context, not validation |

## Methodology
1. **Ingest & pin.** Download each `.xls` into `data/raw/vintage=YYYY-MM/` with retrieval timestamp + SHA-256; CI fails if a
   partition's hash changes (forces a *new* vintage, never a silent overwrite — the URLs rotate every January).
2. **Parse defensively.** Dynamic header search (each file has ~7 metadata rows before the `Industry Name` header, two
   sheets `Variables & FAQ` / `Industry Averages`); treat `NA`/blank/`#DIV/0!` as NULL; auto-detect percent scale
   (0–1 vs 0–100); assert post-parse row count.
3. **Entity resolution (the hard step).** Normalize the free-text key (trim, casefold, unify `&`/`and`, slashes,
   parentheticals) → resolve to a **surrogate `industry_id`** via `map_industry_alias`. **Never join on raw text** — a
   real Damodaran typo, `Heathcare Information and Technology` (missing the "l"), silently drops a row otherwise. Fuzzy
   matching only *proposes*; a human confirms; the load **fails loudly** on any unresolved name.
4. **Model — right-sized star schema.** Conformed `dim_industry` (+ `sector_group`, `is_financial`,
   `is_total_market_rollup`), `dim_vintage`, `dim_region`, and **~4–6 facts** (`fact_margins`, `fact_rnd`,
   `fact_financing_flows`, `fact_multiples_ps`/`_pe`, `fact_dividends_fcfe`) + a `fact_industry_firmcount` reconciliation.
   Strip the two `Total Market` rows before any cross-sectional stat. Bridge table + `dim_company` are a documented
   **Phase 2**, not v1 — proportionality is itself the senior signal.
5. **Wide mart.** `mart_industry_wide` = LEFT JOIN of all facts on `(industry_id, vintage_id, region_id)`, every measure
   **source-prefixed** (`mgn_net_margin` vs `ps_net_margin`) to defuse legitimate name collisions.
6. **Analysis.** (a) rank-reversal count reported vs adjusted; (b) market-pricing regression EV/Sales & P/E ~ reported vs
   adjusted margin, **HC3-robust + WLS weighted by # firms**, financials excluded, ≤5 regressors, bootstrap CIs; (c)
   life-cycle clustering (winsorize → z-score → PCA → k-means + Ward, k by silhouette/gap, **bootstrap Jaccard stability**);
   (d) the leverage-funded-buyback / SBC-offset exhibits.
7. **Validation harness (the credibility centerpiece).** Reproduce one of Damodaran's **own published regressions**
   (`dbtreg` or `divreg`) from raw files and assert coefficient signs/magnitudes + R² within tolerance as a **pytest CI
   gate** — proves the joins, parsing, and estimator are correct. pandera gates: no `Total` rows, ~94-industry count,
   crosswalk completeness (anti-join), denominator guards, percent-scale range, vintage-hash immutability, and an
   **R&D-adjusted-margin usage guard** that blocks pairing a capitalized-R&D column with an R&D-adjusted margin.

## Visualizations
- **Hero (README):** a sorted **reported-vs-adjusted margin dumbbell/slope chart**, one row per industry, sorted by gap.
- **Rank-reversal bump chart:** industries reshuffling between the reported and adjusted margin rankings.
- **Market-pricing scatter:** EV/Sales vs reported margin and vs adjusted margin, side by side with fitted lines + R².
- **Financing quadrant:** Net Equity Change (x) vs Net Debt Change (y), bubble = payout-over-FCFE, highlighting the
  leverage-funded-return quadrant.
- **Life-cycle cluster map:** industries on PC1 (profitability/maturity) × PC2 (reinvestment/growth), colored by cluster.
- **Streamlit:** argues *this* thesis (reported/adjusted toggle, outlier/residual table) — **no generic metric explorer.**

## Honest CV bullets
- Built a reproducible **Python + DuckDB** warehouse conforming **~30 industry-level financial datasets** onto a single
  `dim_industry` spine with **entity resolution over a free-text join key** (surrogate keys, an alias crosswalk, and a
  fail-loud anti-join gate that catches a real upstream misspelling and annual taxonomy drift).
- Surfaced a cross-dataset finding invisible in any single source: **R&D/lease margin adjustment reshuffles the
  industry margin ranking, and market multiples (EV/Sales, P/E) track the *adjusted* margin** — evidence that
  cross-industry screening on reported margins is misleading.
- Shipped a **validation harness that reproduces Damodaran's own published capital-structure regression from raw files**
  as a CI gate, proving every downstream number, plus pandera contracts (no-Total-rows, denominator guards,
  vintage-hash immutability, an anti-circularity lint).
- Modeled the annual refresh as a **vintage dimension** for a multi-year panel, flagging the **ASC 842 (2019) lease** and
  **TCJA §174 (2022) R&D-capitalization** methodology breaks so a definitional change is never read as a trend.
- Framed every result as **value-weighted, industry-aggregate association — not firm-level causation** — and demonstrated
  the caveat by rebuilding one industry from **SEC EDGAR** to show within-industry dispersion.

## Risks / gotchas
- **The naive flagship is circular.** Damodaran's adjusted margins are built *from* his capitalized-R&D estimate, so
  regressing one on the other re-derives an identity. **Firewall:** when R&D is a regressor use *only reported* margins;
  the empirical claim must point at a market outcome (multiples), not at his own adjusted number.
- **Value-weighted aggregates.** Each row is a dollar-weighted composite dominated by mega-caps — *not* the typical firm.
  Ecological fallacy / Simpson's paradox: industry-level relationships need not hold across firms. **Descriptive, n≈94.**
- **The join key is free text.** Silent inner-join drops (the `Heathcare` typo) and year-over-year renames — join on a
  surrogate id via the alias crosswalk, never on the string.
- **`Net Equity Change` = issuance − buybacks (dividends excluded)** — verified against the data, and it contradicts the
  file's own notes. Compute true net payout `(Dividends + Buybacks − Equity Issuance)` explicitly; don't reuse the column.
- **The panel is not free.** The local `finflows_timeseries.xlsx` holds only 2026 — a panel-*ready* schema, not a panel.
  Only claim "panel" after ≥3 real archive vintages, and gate cross-vintage comparisons of adjusted columns behind the
  **ASC 842 / §174 methodology-break flags** (SCD2 fixes renames, *not* definitional breaks).
- **URLs overwrite every January** — hash + pin, or history is unrecoverable.
- **EDGAR rebuild ≠ validation.** His universe (ADRs, modeled R&D/lease figures) won't reconcile to XBRL frames (US-only,
  ~2009+, inconsistent tags) — use EDGAR for **within-industry dispersion on one industry**, and validate the pipeline by
  replicating *his* regression instead.
- **Strip `Total Market` rows; segregate financials** (non-comparable margins); **correct for multiple testing** (FDR) and
  report cross-validated R², given ~94 points × dozens of ratios.

## Extensions
Stack 5–10 archive vintages into a true panel (widening-gap trend test) · cross-region replication on the identical schema
(is the pattern global or American?) · SEC-EDGAR within/between decomposition across 3–5 rebuilt industries · macro-regime
overlay of financing flows via FRED · a ~600-word writeup + hero visual for distribution · package the industry-name
crosswalk + parser as a small pip module.
