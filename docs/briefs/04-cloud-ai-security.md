# Project 4 — Cloud, ERP & AI Vendor Intelligence

**Segment Revenue, Implied Market Share, and Security-Risk Exposure**

> A reproducible Python + DuckDB pipeline that fuses SEC segment financials, developer-adoption signals, and the
> NVD/CISA vulnerability record to quantify how enterprise-tech vendors' cloud growth trades off against their
> disclosed security risk.

**Difficulty:** Advanced · **Effort:** ~60–90h · **Data cleanliness:** ★★★☆☆ (CPE attribution is hard)

The **advanced capstone** — most differentiated (finance × cybersecurity), highest ceiling. This is your refinement
of the original "Agentic AI, ERP & Cloud market share, performance, security risk" idea into something *defensible*.

---

## Why it's compelling (the interview story)
"The enterprise-tech vendors compounding revenue fastest are also accumulating the most severe, most-exploited
vulnerabilities — here's that trade-off, measured, with every number traceable to a primary-source filing or a
government vulnerability record." It pairs financial-statement analysis with a real security dataset — a rare combo.

## Scope — refined to be defensible (the original idea was too broad)
- **~10 named vendors:** MSFT, AMZN, GOOGL, ORCL, CRM, SAP, NOW, SNOW (+ optional IBM, WDAY), **FY2016–present**.
- **Three tightly-linked pillars:**
  - **A — Financial performance:** reconstruct reportable-segment revenue, operating income, YoY growth from SEC EDGAR XBRL.
  - **B — Implied market position:** true market-share reports (Synergy/Canalys/Gartner/Statista) are **paywalled → do NOT claim precise share.** Instead compute a defensible *revenue-mix* view within the covered peer set, and corroborate momentum with **free developer-adoption signals** (Stack Overflow survey tool usage, optional GH Archive activity).
  - **C — Security exposure:** from NVD + CISA KEV, quantify per-vendor CVE counts, CVSS severity distribution, time-in-catalog, and share of vulnerabilities that became actively exploited.
- **Capstone:** join A and C into a vendor scorecard and test one crisp hypothesis — *is higher cloud-revenue growth associated with a heavier severe/exploited vulnerability load?*
- **Honesty constraint baked in:** AWS is a clean reportable segment, but **Azure and Google Cloud disclose growth % only** (MSFT reports blended "Intelligent Cloud"/"Microsoft Cloud"). Treat this asymmetry as a **first-class data-quality problem**, not something to paper over.

## Analytical questions
1. How has reportable cloud/ERP segment revenue & YoY growth evolved FY2016–present, and how does AWS's clean disclosure compare to MSFT's blended reporting and GCP's segment line?
2. Each vendor's implied revenue mix within the peer set — and where does the analysis hit the disclosure wall (cloud lines with no standalone dollar figure)?
3. Do free adoption signals (Stack Overflow tool-usage share, GH Archive activity) corroborate or contradict the revenue-based momentum ranking?
4. Which vendors/products carry the largest CVE burden in NVD, and how has their CVSS severity mix shifted YoY?
5. What fraction of each vendor's NVD CVEs appear in the **CISA KEV catalog** (actively exploited)? Highest "exploited rate"?
6. For KEV entries, distribution of time between CVE publication and KEV addition — does it differ by vendor?
7. Is faster cloud-revenue growth statistically associated (Spearman) with a heavier severe/exploited load?
8. (Exploratory, non-causal) Do spikes in a vendor's KEV additions coincide with observable equity moves?

## Verified datasets
| Source | What / how used | Access |
|--------|-----------------|--------|
| **NVD CVE API 2.0** (NIST) | **Primary security dataset:** CVEs per vendor via CPE/`virtualMatchString`; CVSS severity + dates → per-vendor burden & severity trends | **Free API key recommended** (5→50 req/30s; instant email signup). Paginate; sleep ~1s; cache. CPE attribution imperfect → validate |
| **CISA KEV catalog** | Flags actively-exploited CVEs; per-vendor "exploited rate," publication-to-KEV lag, ransomware-linked share | JSON/CSV, no key, no rate limit; GitHub mirror is CC0. Normalize `vendorProject`/`product` names |
| **SEC EDGAR XBRL** company facts / frames | **Primary financial dataset (Pillar A):** total & segment revenue/operating income per vendor; the revenue-mix view; demonstrates the AWS-vs-Azure/GCP disclosure asymmetry | No key; 10 req/s; **`User-Agent` header required.** us-gaap tags don't always expose the cloud sub-segment → may parse the 10-K segment note |
| **Stack Overflow Annual Developer Survey** | Pillar B corroboration: YoY share of respondents using each cloud/DB/AI tool vs revenue momentum | Free, no key. Columns change yearly → harmonize; self-selected sample → directional only (respect ODbL) |
| **GH Archive** (optional) | Pillar B enrichment: star/push activity for AI-framework & cloud repos as a mindshare proxy | Prefer **BigQuery within the free 1 TB/month tier** — never bulk-download the TB-scale history |
| **yfinance** (secondary) | Equity price panel for the exploratory KEV-vs-stock analysis + valuation sanity check | No key, fragile, cache. Non-causal — label as such |
| **MITRE cvelistV5** (fallback) | Offline bulk CVE validation / gap-fill | No key; large clone — shallow/sparse; keep secondary to avoid double-counting |

## Methodology
1. Config + **vendor crosswalk** (ticker ↔ CIK ↔ CPE vendor strings) — the hard entity-resolution artifact. 2. Ingest: NVD (rate-limited, cached), KEV (single file), EDGAR XBRL segment facts, Stack Overflow survey CSVs. 3. Land raw in DuckDB. 4. **Pillar A** — parse segment revenue/growth, build the panel + revenue-mix, flag `is_disclosed` for no-dollar cloud lines. 5. **Pillar C** — attribute CVEs to vendors via CPE, parse CVSS severity + dates, join KEV, compute exploited-rate + lag. 6. **Pillar B** — harmonize Stack Overflow tool usage YoY. 7. **Capstone** — vendor scorecard; Spearman correlation of growth vs severe/exploited load. 8. pandera gates, Streamlit scorecard, pytest, CI, README with per-source licensing & limitations.

## Visualizations
- Segment revenue & growth panel (with `is_disclosed` shading for Azure/GCP gaps).
- Revenue-mix within peer set (stacked/treemap).
- Adoption-vs-revenue momentum comparison (Stack Overflow share vs growth rank).
- Per-vendor CVE burden + CVSS severity mix over time (stacked area).
- **Exploited-rate ranked bar** (KEV / total NVD) + publication-to-KEV lag distributions.
- **Capstone scorecard scatter:** cloud-growth (x) vs severe/exploited load (y), bubble = revenue.

## Honest CV bullets
- Built an end-to-end **Python + DuckDB** pipeline integrating **4 primary-source datasets** (SEC EDGAR XBRL, NVD CVE API 2.0, CISA KEV, Stack Overflow Survey) to quantify the trade-off between enterprise-tech vendors' cloud-revenue growth and disclosed security-risk exposure across ~10 vendors over a 9-year window.
- Engineered **rate-limited, cached API ingestion** (NVD 50 req/30s with key, SEC 10 req/s with compliant User-Agent) and a layered raw→staging→marts DuckDB warehouse, reproducible with a single `make` command.
- Reconstructed reportable-segment revenue from XBRL and **surfaced a real disclosure asymmetry** (AWS clean segment vs Azure/GCP growth-% only), treating segment-tag coverage as a first-class data-quality problem.
- **Attributed 10k+ CVEs to vendors via CPE matching**, joined to CISA KEV to compute a per-vendor "actively-exploited rate" and publication-to-exploitation lag, and tested (Spearman) whether faster-growing cloud vendors carry heavier vulnerability loads.
- Corroborated paywalled market-share figures with free developer-adoption signals, explicitly labeling them directional rather than measured share.
- Shipped a **Streamlit vendor scorecard** plus pandera checks, pytest, GitHub Actions CI, and a documented licensing/limitations section per source.

## Risks / gotchas
- **Cloud segment asymmetry** — do NOT fabricate Azure/GCP dollar revenue; model the gap with an `is_disclosed` flag.
- **CPE-based attribution is imperfect** — per-vendor CVE counts are estimates; validate on a sample and report attribution error.
- **XBRL segment tags aren't standardized** — may need to parse the 10-K `Financial_Report.xlsx` segment note for some vendors.
- **Market share is paywalled** (Synergy/Canalys/Gartner/Statista) — use their public press-release headlines as *context only*, never as a dataset.
- **NVD rate limits / enrichment lag** — get the free key, cache aggressively; legacy yearly bulk feeds retired → use API 2.0 or MITRE cvelistV5.
- **Stack Overflow survey is self-selected** and columns change yearly — directional signal only.
- **yfinance unofficial** — keep equity analysis secondary and clearly non-causal.
- **Scope creep** — keep to ~10 vendors; expanding the CPE/CIK crosswalk balloons entity-resolution effort.

## Extensions
Event-study of KEV spikes vs short-window returns (caveated) · Hugging Face Hub + Papers-with-Code for agentic-AI framework momentum · NLP on 10-K "Risk Factors" cyber language vs actual KEV rate · incremental daily KEV/NVD refresh + scheduled dashboard · SSVC/EPSS exploit-prediction enrichment · package the crosswalk + CVE-attribution as a pip module.
