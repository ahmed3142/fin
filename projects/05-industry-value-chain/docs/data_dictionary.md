# Data dictionary

Source = the Damodaran file each fact is parsed from. **Units:** `USD mm` = US-dollar
millions; `fraction` = a ratio stored as a decimal (0.23 = 23%); `multiple` = a valuation
ratio kept as published (e.g. EV/Sales 6.2×); `count` = integer.

> All values are **value-weighted industry aggregates** (Σ numerators / Σ denominators
> across the firms Damodaran tracks) — the "industry portfolio", not a typical firm.

## dim_industry
| column | type | meaning |
|--------|------|---------|
| `industry_id` | int PK | surrogate key (stable across reloads) |
| `industry_name` | text | canonical Damodaran industry name |
| `sector_group` | text | coarse ~11-bucket rollup (heuristic) |
| `is_financial` | bool | banks/insurers/REITs — margins & leverage non-comparable |
| `is_total_market_rollup` | bool | always false here (Total Market rows are stripped) |
| `region_id` | int FK | → dim_region |

## dim_vintage
| column | type | meaning |
|--------|------|---------|
| `vintage_id` | int PK | 1 = the Jan-2026 pull |
| `vintage_year` | int | 2026 |
| `data_asof_date` | text | file "Date updated" (2026-01-05) |
| `ttm_through` | text | trailing-12-months cutoff (2025-Q3) — **not** full-year 2026 |
| `asc842_lease_break` | bool | lease-capitalization methodology break (~2019) |
| `tcja174_rnd_break` | bool | R&D-capitalization tax break (2022) — gate cross-vintage trends |

## fact_margins  (source: `margin.xls`)
| column | units | meaning |
|--------|-------|---------|
| `num_firms` | count | firms in the margin aggregate (Σ = 5,994) |
| `gross_margin` | fraction | gross profit / revenue |
| `net_margin` | fraction | net income / revenue |
| `pretax_operating_margin` | fraction | **reported** pre-tax operating margin (expenses R&D) |
| `pretax_lease_rnd_adj_operating_margin` | fraction | **adjusted** — Damodaran adds back R&D & capitalizes leases |
| `ebitda_sales`, `ebitdarnd_sales` | fraction | EBITDA/Sales and EBITDA-with-R&D-added-back/Sales |
| `rnd_sales`, `sga_sales`, `sbc_sales` | fraction | R&D, SG&A, stock-based-comp as % of sales |

## fact_rnd  (source: `R&D.xls`)
| column | units | meaning |
|--------|-------|---------|
| `rnd_capitalized_usd_m` | USD mm | **Damodaran ESTIMATE** of capitalized R&D (assumed amortizable life) |
| `cap_rnd_pct_invested_capital` | fraction | capitalized R&D / invested capital |
| `rnd_ltm_usd_m` | USD mm | last-twelve-months R&D |
| `current_rnd_pct_revenue` | fraction | R&D intensity |
| `rnd_cagr_5y` | fraction | 5-yr R&D growth (survivorship-biased to current constituents) |

## fact_financing_flows  (source: `finflows.xls`)
| column | units | meaning |
|--------|-------|---------|
| `dividends`, `buybacks`, `equity_issuance` | USD mm | cash out/in to equity |
| `net_equity_change_usd` | USD mm | **= equity_issuance − buybacks** (dividends NOT subtracted — verified against data; the source file's own note is wrong) |
| `net_equity_change_pct_book_equity` | fraction | scaled by book equity (can blow up when book equity ≈ 0) |
| `debt_repaid`, `debt_raised`, `net_debt_change_usd` | USD mm | debt flows |
| `net_debt_change_pct_total_debt` | fraction | scaled by total debt |
| `change_in_lease_debt` | USD mm | Δ capitalized-lease debt |

## fact_multiples_ps / fact_multiples_pe  (source: `psdata.xls`, `pedata.xls`)
| column | units | meaning |
|--------|-------|---------|
| `price_sales`, `ev_sales` | multiple | Price/Sales, EV/Sales |
| `current_pe`, `trailing_pe`, `forward_pe`, `peg` | multiple | PE variants + PEG |
| `expected_growth` | fraction | Value-Line expected growth, next 5y |
| `net_margin`, `pretax_operating_margin` | fraction | margins carried on the psdata sheet |

## fact_dividends_fcfe  (source: `divfcfe.xls`)
| column | units | meaning |
|--------|-------|---------|
| `dividends`, `dividends_plus_buybacks`, `fcfe` | USD mm | payout vs free-cash-flow-to-equity |
| `payout` | fraction | dividend payout ratio |
| `cash_return_pct_net_income` | fraction | (div+buyback) / net income |
| `net_cash_returned_pct_fcfe` | fraction | net cash returned / FCFE (>1 ⇒ returning more than FCFE) |

## fact_growth_fundamental_eb  (source: `fundgrEB.xls`, local)
| column | units | meaning |
|--------|-------|---------|
| `roc` | fraction | return on capital |
| `reinvestment_rate` | fraction | reinvestment / EBIT(1−t) |
| `expected_growth_ebit` | fraction | ROC × reinvestment (financials carry NULL) |

## fact_industry_firmcount
Long-format `num_firms` per `dataset_code` — the reconciliation fact. All seven files
report the same 5,994-firm universe this vintage (Damodaran computes them from one run),
so it's a coverage/QA check, not a source of divergence.

## mart_industry_wide (view)
One row per industry with every measure above, **source-prefixed** so identically-named
columns coexist: `mgn_` margins · `rnd_` R&D · `ff_` financing · `ps_` P/S+EV/S ·
`pe_` P/E · `div_` dividends/FCFE · `gr_` growth. This is the single table the analysis,
dashboards, and Supabase REST API read.
