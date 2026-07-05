# Master Dataset Reference — all free & verified

Every source below was **adversarially verified** (43 checks). Verdicts:
`verified_free` = open, no account · `free_with_account` = free but needs a (free, instant) key/token.

## ✅ Fully open (no account)
| Dataset | URL | Used by | Notes |
|---------|-----|---------|-------|
| **SEC EDGAR XBRL** company facts / frames | `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` | Luxury, Fortune 500, Cloud/AI | **`User-Agent: name email` header required**; 10 req/s; US filers only |
| **NVD CVE API 2.0** | `https://services.nvd.nist.gov/rest/json/cves/2.0` | Cloud/AI | Free key optional but recommended (5→50 req/30s) |
| **CISA KEV catalog** | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` (+ `.csv`) | Cloud/AI | No key, no rate limit; GitHub mirror CC0 |
| **MITRE cvelistV5** | `https://github.com/CVEProject/cvelistV5` | Cloud/AI (fallback) | Large git repo — shallow/sparse clone |
| **Our World in Data — COVID-19** | `https://covid.ourworldindata.org/data/owid-covid-data.csv` | Post-COVID | ⚠️ frozen 19-Aug-2024 |
| **Oxford OxCGRT** | `https://github.com/OxCGRT/covid-policy-dataset` (`OxCGRT_compact_national_v1.csv`) | Post-COVID | Stringency sub-indices |
| **Damodaran NYU Stern** | `https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html` (margin.xls, vebitda.xls, pedata.xls, psdata.xls; +Europe/+Global) | Luxury, Fortune 500 | ⚠️ URLs overwritten each January — pin file + date |
| **Wikipedia — largest US companies by revenue** | `https://en.wikipedia.org/wiki/List_of_largest_companies_in_the_United_States_by_revenue` | Fortune 500 | `pandas.read_html`; ~top 100 only |
| **Stack Overflow Developer Survey** | `https://survey.stackoverflow.co/` | Cloud/AI | ODbL; columns change yearly |
| **World Bank Open Data API** | `https://api.worldbank.org/v2/country/.../indicator/NE.CON.PRVT.PC.KD?format=json` | Luxury | Paginated |
| **Bain × Altagamma Luxury Study** | `https://altagamma.it/en/studi-e-ricerche/` · `https://www.bain.com/insights/` | Luxury | Free press releases only (full decks gated) |
| **Company URDs / Annual Reports (PDF)** | LVMH `https://urd.lvmh.com/en/2024` · Kering / Richemont / Hermès / Burberry / Prada IR pages | Luxury | Segment & geo revenue; taxonomies differ → mapping table |
| **yfinance** (Yahoo Finance) | `https://github.com/ranaroussi/yfinance` | All | No key, **fragile (HTTP 429)** — fetch once, cache to Parquet, retry/back-off |
| **GH Archive** | `https://www.gharchive.org/` | Cloud/AI (optional) | Use BigQuery ≤1 TB/mo free tier — don't bulk-download |

## 🔑 Free but needs an instant free account/key
| Dataset | Sign-up | Used by | Limit |
|---------|---------|---------|-------|
| **FRED** (Federal Reserve) | `fredaccount.stlouisfed.org` (32-char key) | Post-COVID | ~120 req/min; use `fredapi` |
| **BEA GDP-by-Industry** | `apps.bea.gov/api/signup` (36-char UserID) | Post-COVID (optional) | `DataSetName=GDPbyIndustry` |
| **BLS Public Data API** | `bls.gov/developers` (v2 key) | Post-COVID (optional) | 500 queries/day (many series also on FRED) |
| **Kaggle** (Fortune 500/1000 datasets) | `kaggle.com` + API token | Fortune 500 | Prefer CC0/CC BY; pin slug+version |

## ⚠️ Corrections found during verification
- **Stooq direct CSV** (`stooq.com/q/d/l/?s=xlk.us&i=d`) → **PAYWALLED/blocked** by a JS anti-bot wall. **Replacement:** `yfinance` `yf.download([...])` or `pandas-datareader` `StooqDailyReader`, cached.
- **Fortune 500 combined CSV** (`.../fortune500-2005-2021.csv`) → **DEAD (404).** Real path: per-year `csv/fortune500-YYYY.csv` in `cmusam/fortune500` (2005–2019 verified). Concatenate + pin SHA.
- **Financial Modeling Prep** free endpoint → changed/limited. **Replacement:** SEC EDGAR XBRL (already core, free). FMP is optional only.

## 🚫 Paywalled — excluded (do NOT scrape)
Statista · Macrotrends (ToS forbids bots) · stockanalysis.com (no API) · full Gartner / Canalys / Synergy / IDC market-share reports.
Use SEC filings + free Bain/Altagamma headlines + revenue-mix/adoption proxies instead.

## The reusable data toolkit (shared across projects)
- **SEC EDGAR XBRL client** (3 of 4 projects) — CIK map at `https://www.sec.gov/files/company_tickers.json`.
- **yfinance price/fundamentals fetcher** with Parquet caching + retry (all four).
- **Damodaran `.xls` benchmark loader** (Luxury + Fortune 500).
- **Generic cached HTTP client** (retry/back-off, on-disk cache) reused for every REST/CSV source.
