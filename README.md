# Finance Data-Analysis Portfolio — 5 Production-Grade Projects

Five CV-ready, finance-focused data analysis & visualization projects in Python
(**numpy · pandas · DuckDB · matplotlib** + Streamlit / plotly). Every dataset below was
**adversarially verified as free and accessible** (43 checks). Corrections from that
verification are baked into each brief. **Project 5 ships as a runnable pipeline** with a
Supabase-ready Postgres database — see [`projects/05-industry-value-chain/`](projects/05-industry-value-chain/).

> Built for a finance-major portfolio: each project is scoped as a *reproducible pipeline*
> (raw → staging → mart in DuckDB) with tests, CI, and a deployed dashboard — not a notebook dump.

---

## The five projects

| # | Project | Core finance angle | Difficulty | Effort | Data cleanliness |
|---|---------|--------------------|------------|--------|------------------|
| 1 | [Post-COVID Sector Rotation](docs/briefs/01-post-covid-sector-rotation.md) | Event study, drawdowns, macro linkage | Int→Adv | 50–70h | ★★★★★ (cleanest, fully automatable) |
| 2 | [Luxury Goods Market Share & Valuation](docs/briefs/02-luxury-goods.md) | Market share, segment mix, comps/multiples | Int→Adv | 60–90h | ★★★☆☆ (PDF extraction is manual) |
| 3 | [Fortune 500 Financial Breakdowns](docs/briefs/03-fortune-500.md) | Sector profitability, concentration, churn | Int | 40–70h | ★★★★☆ (community CSVs) |
| 4 | [Cloud / ERP / AI Vendor Intelligence](docs/briefs/04-cloud-ai-security.md) | Segment revenue × security-risk trade-off | Adv | 60–90h | ★★★☆☆ (CPE attribution hard) |
| 5 | [Industry Value-Chain & Margin-Distortion](docs/briefs/05-damodaran-industry-value-chain.md) ⟶ [code](projects/05-industry-value-chain/) | Cross-dataset entity resolution, margins vs valuation | Adv | 55–80h | ★★★★☆ (clean values, dirty join key) |

See [DATASETS.md](docs/DATASETS.md) for the master verified-source table.

---

## Recommended sequence (do them in this order)

1. **Fortune 500 (quick win, first).** Most approachable data; builds the reusable toolkit
   you'll reuse everywhere: DuckDB warehouse pattern, SEC EDGAR client, yfinance caching,
   pandera validation, the Streamlit template. Ship this first to have *one* polished repo fast.
2. **Post-COVID Sector Rotation (flagship — best effort-to-impressiveness ratio).** Cleanest
   free data, real quant methodology (market-model event study, CARs), reuses the FRED + yfinance
   plumbing. This is the one that reads as "this person can actually do quantitative finance."
3. **Luxury Goods (finance-recruiter magnet).** The most *finance-brand* project — comps,
   multiples, market share. The segment/geography mapping from filings is real analyst work.
4. **Cloud/ERP/AI + Security (advanced capstone).** Most differentiated (finance × cybersecurity),
   highest ceiling, hardest. Do it last, when the pipeline pattern is second nature.
5. **Industry Value-Chain & Margin-Distortion (Damodaran capstone — built).** Conforms ~8 of Damodaran's
   industry datasets onto one `dim_industry` spine and ships a **Supabase-ready Postgres DB**. The value is
   the *join* + one honest, non-circular thesis (the market prices R&D-adjusted margins) — not the plumbing.

**If you only build two:** #1 (Fortune 500) as the data-engineering showcase + #2 (Post-COVID)
as the quant/finance showcase. Together they cover the whole "analyst who can engineer" story.

---

## Shared toolkit (build once, reuse across all four)

All four projects share the same production skeleton, so the marginal cost drops after the first:

- **Ingestion clients** with retry/back-off + local Parquet caching (`requests`, `yfinance`, `fredapi`).
- **SEC EDGAR XBRL client** (`data.sec.gov`, requires a `User-Agent: name email` header) — used by 3 of 4 projects.
- **DuckDB warehouse** with a `raw → staging → mart` (bronze/silver/gold) medallion layering.
- **pandera** schema validation as quality gates between layers.
- **pytest** over pure transform functions + a tiny sample fixture.
- **Streamlit** dashboard reading the mart layer, deployed free on Streamlit Community Cloud.
- **uv** for env/lockfile, **ruff** for lint/format, **GitHub Actions** CI, **Makefile** one-command runs.

---

## Production-grade playbook (applies to every project)

### Repo structure
```
project-name/
  README.md                # pitch · problem · findings + screenshots · run steps
  pyproject.toml           # deps + ruff/pytest config
  uv.lock                  # pinned reproducible lockfile
  Makefile                 # setup / data / build / test / lint / dashboard
  .gitignore               # ignores data/, .venv/, *.duckdb, .env
  .env.example             # documents env vars (NO secrets committed)
  .pre-commit-config.yaml  # ruff on commit
  .github/workflows/ci.yml # ruff + pytest on push/PR  → green badge in README
  config/config.yaml       # paths, date range, tickers, seed
  data/                    # ALL git-ignored (.gitkeep only)
    raw/  staging/  mart/   # bronze / silver / gold
  sql/staging/  sql/mart/  # DuckDB SQL per layer
  src/<pkg>/
    config.py ingest.py transform.py schemas.py warehouse.py viz.py pipeline.py
  scripts/download_data.py # standalone fetch entrypoint
  notebooks/               # clean narrative that IMPORTS from src/ (not logic dumps)
  reports/figures/         # exported charts referenced by README
  tests/test_transform.py  # pytest over pure transforms
  dashboard/app.py         # Streamlit reading the mart layer
```

### Non-negotiables (these separate "engineer" from "notebook tinkerer")
- **Never commit data.** Commit the *download script* + a tiny sample fixture so tests/CI run offline.
- **Layer explicitly:** raw (immutable) → staging (cleaned/typed Parquet) → mart (analysis-ready). Name folders this way.
- **Use SQL *and* pandas:** heavy joins/aggregations in DuckDB SQL; light reshaping in pandas.
- **Pure transform functions** (DataFrame in → DataFrame out, no I/O) so they're unit-testable.
- **pandera validation between layers** — bad data fails loudly, and you can say "data quality is tested" truthfully.
- **README is the product:** one-line pitch → problem → data → approach → *key findings with 2–3 numbers* → screenshots → how to reproduce. A recruiter must get it in 30 seconds.
- **Style matplotlib deliberately:** kill chart junk (top/right spines), label axes with units, write takeaway titles ("Momentum decays after 6 months") not mechanic titles ("Line chart of returns").
- **Ship a live dashboard.** A Streamlit Community Cloud link at the top of the README beats any amount of text.

### How to phrase these on a finance CV
Formula: **[Action verb] + [what you built] + [tech] + [quantified result]**.
- Title each like a role: *"Post-COVID Sector Rotation — Python, DuckDB, Streamlit (personal project)"*.
- **Quantify everything** (rows, runtime, %, counts) — only ~30% of analyst resumes have numbers; it's the biggest screen-out gap. Qualify estimates with `~`.
- Spell out the stack for ATS: *"Python (pandas, NumPy, matplotlib), SQL (DuckDB), Parquet, pandera, pytest, GitHub Actions, Streamlit"*.
- Honest finance keywords: financial modeling, time-series, ETL, data validation, backtesting, reconciliation, comps/valuation.
- Link the GitHub repo **and** the live dashboard on the CV.

### Common mistakes to avoid
Committing raw data · one giant messy notebook with hardcoded `/Users/you/` paths · README that never states the *finding* · toy datasets (Titanic/Iris) · no tests/CI · no quantified results · stopping at analysis with no deployed artifact · 15 shallow repos instead of 3–5 deep ones (pin the best, archive the rest).

---

## Key dataset corrections from verification (read before you start)

- **Post-COVID prices:** Stooq's direct CSV endpoint is now behind a JS anti-bot wall — **use `yfinance` (`yf.download([...])`) or `pandas-datareader`'s `StooqDailyReader`, and cache to Parquet.** Don't write a naive `requests.get(csv_url)`.
- **Fortune 500 spine:** the combined multi-year CSV path 404s — the `cmusam/fortune500` repo stores **per-year files** at `csv/fortune500-YYYY.csv`. Concatenate them; pin a commit SHA and mirror into `data/raw/`.
- **Financial Modeling Prep:** endpoints changed and it's paywall-limited — it's optional; **SEC EDGAR XBRL covers ground truth for free.**
- **Free API keys needed (all instant, free):** FRED, BEA, BLS, Kaggle, and an NVD key (raises rate limit). Store in `.env`, never commit.
- **Paywalled — do NOT scrape:** Statista, Macrotrends (ToS forbids bots), stockanalysis.com, full Gartner/Canalys/Synergy reports. Use primary filings + Bain/Altagamma free press releases for context only.
