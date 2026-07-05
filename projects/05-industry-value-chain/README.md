# Project 5 — Industry Value-Chain & the Margin-Distortion Anomaly

Conform ~8 of Aswath Damodaran's industry datasets onto **one `dim_industry` spine**
in DuckDB, test one honest cross-dataset thesis, and export a **Supabase-ready
Postgres database**. Part of the [finance data-analysis portfolio](../../README.md);
full write-up in [docs/briefs/05-…](../../docs/briefs/05-damodaran-industry-value-chain.md).

## The finding (headline)
> Across **84 non-financial U.S. industries** (Jan-2026 vintage, TTM ≈ Q3 2025),
> **EV/Sales tracks Damodaran's R&D/lease-adjusted operating margin better than the
> reported margin (R² 0.425 vs 0.406)** — modest evidence the market looks *through*
> R&D expensing. The adjustment itself reranks only **1 of 84** industries by ≥ 5
> positions (Spearman ρ = 0.998), so the distortion is **concentrated in the
> high-R&D tail, not broad**. `P/E` is noisier and slightly favours the reported margin.

**So what:** a naive cross-industry screen on *reported* margins misprices the
R&D-heavy tail (software, semis, pharma); use the adjusted figure there.

**What this is NOT:** these are value-weighted industry *aggregates* (n ≤ 94) — a
description, **not** firm-level behaviour and **not** causation (ecological fallacy,
single snapshot). The R&D-adjusted margin is Damodaran's own estimate, so we never
regress it *on* R&D intensity (that is his identity) — the empirical test points at a
market outcome instead. See the anti-circularity lint in `src/quality.py`.

## Run it
```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
make ingest     # download the 6 core Damodaran .xls (+ 2 local files) -> data/raw, hashed
make build      # parse + resolve industries + build warehouse.duckdb (+ quality gates)
make analysis   # rank-reversal + market-pricing -> analysis/headline.json
make export     # emit sql/postgres/*.sql (+ csv) for Supabase
make test       # 15 gates: parser, crosswalk anti-join, reconciliation, OLS math
```
(Or `make pipeline` for ingest→build→export→analysis. The repo ships the outputs
pre-built, so you can go straight to `sql/postgres/` or Supabase.)

## What's inside
| Layer | Files |
|-------|-------|
| **ingest** | `src/ingest.py` — canonical `/pc/datasets/<stem>.xls` URLs (the datafile HTML links are mislabeled), SHA-256 pinned into `data/raw/vintage=2026-01/` |
| **parse** | `src/parse.py` — dynamic header search (row-0 *and* row-7 layouts), `NA`/`#DIV/0!`→NULL, ratio→fraction, multiples left un-scaled, strips the two `Total Market` rows |
| **resolve** | `src/crosswalk.py` + `data/industry_aliases.csv` — surrogate `industry_id`, fixes Damodaran's real `Heathcare` typo, **fails loudly** on any unresolved name |
| **warehouse** | `src/warehouse.py` — conformed `dim_industry`/`dim_vintage`/`dim_region` + 8 facts + `mart_industry_wide` |
| **quality** | `src/quality.py` — 94-count, no-Total-rows, referential integrity, firm-count anchor (5,994), anti-circularity lint |
| **analysis** | `src/analysis.py` — rank-reversal + market-pricing OLS/HC3 (numpy) |
| **export** | `src/export_postgres.py` → `sql/postgres/{01_schema,02_seed,03_mart_view,04_rls}.sql` + `csv/` |
| **docs** | [SCHEMA.md](docs/SCHEMA.md) (ERD) · [data_dictionary.md](docs/data_dictionary.md) · [SUPABASE.md](docs/SUPABASE.md) |

## Load into Supabase
See [docs/SUPABASE.md](docs/SUPABASE.md) — paste `sql/postgres/01_schema.sql` →
`02_seed.sql` → `03_mart_view.sql` → `04_rls.sql` into the web SQL Editor, then browse
`industry.mart_industry_wide`. No connection string leaves your machine.

## Data & attribution
Industry data © Aswath Damodaran (NYU Stern), free for educational use; snapshots are
pinned + hashed under `data/raw/`, not rehosted as authoritative. See the repo `NOTICE`.
