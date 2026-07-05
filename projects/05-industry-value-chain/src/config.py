"""Central configuration: paths, the Damodaran dataset registry, and the
curated source-column -> canonical-column matchers that keep the warehouse
schema stable even if Damodaran's headers drift slightly.

A matcher resolves ONE source column by lowercase-substring rules:
  all  : every token must appear in the header
  any  : at least one token must appear (optional)
  none : no token may appear (optional)
type: money (USD millions) | ratio (stored as a fraction) | count | text
"""
from __future__ import annotations

import os

# ---- paths -----------------------------------------------------------------
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(PROJECT_DIR))
VINTAGE = "2026-01"
VINTAGE_YEAR = 2026
RAW_DIR = os.path.join(REPO_ROOT, "data", "raw", f"vintage={VINTAGE}")
WAREHOUSE = os.path.join(PROJECT_DIR, "warehouse.duckdb")
ALIASES_CSV = os.path.join(PROJECT_DIR, "data", "industry_aliases.csv")
SQL_OUT = os.path.join(PROJECT_DIR, "sql", "postgres")
ANALYSIS_OUT = os.path.join(PROJECT_DIR, "analysis")

DATAFILE_BASE = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/"
# Canonical dataset host. The datafile/*.html "download" links are unreliable
# (R&D.html points to roe.xls, finflows.html to fundgrEB.xls), so we hit the
# stable /pc/datasets/<stem>.xls URLs directly and fall back to page-scrape.
DATASETS_BASE = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/"
USER_AGENT = "industry-value-chain/0.1 (portfolio project; contact ahmedrezatausif@gmail.com)"

# Aggregate rows to strip before any cross-sectional statistic.
TOTAL_ROW_MARKERS = ("total market",)

# Damodaran financial-sector industries (non-comparable margins/leverage).
FINANCIAL_INDUSTRIES = {
    "Bank (Money Center)", "Banks (Regional)", "Brokerage & Investment Banking",
    "Financial Svcs. (Non-bank & Insurance)", "Insurance (General)",
    "Insurance (Life)", "Insurance (Prop/Cas.)", "Investments & Asset Management",
    "R.E.I.T.", "Reinsurance",
}

# ---- dataset registry ------------------------------------------------------
# Each entry: code, human name, the datafile HTML page (to resolve the .xls
# link), an optional local file (used as-is, no download), the destination fact
# table, and the curated column map.
DATASETS = [
    {
        "code": "margins", "name": "Operating & Net Margins", "page": "margin.html", "xls": "margin.xls",
        "local": None, "fact": "fact_margins",
        "columns": [
            {"canonical": "num_firms", "all": ["number", "firm"], "type": "count"},
            {"canonical": "gross_margin", "all": ["gross", "margin"], "type": "ratio"},
            {"canonical": "net_margin", "all": ["net", "margin"], "none": ["pre", "after"], "type": "ratio"},
            {"canonical": "pretax_operating_margin", "all": ["pre-tax", "unadjusted", "operating", "margin"], "type": "ratio"},
            {"canonical": "pretax_lease_rnd_adj_operating_margin", "all": ["pre-tax", "lease", "r&d", "margin"], "type": "ratio"},
            {"canonical": "ebitda_sales", "all": ["ebitda/sales"], "none": ["r&d", "sg&a"], "type": "ratio"},
            {"canonical": "ebitdarnd_sales", "all": ["ebitdar&d/sales"], "type": "ratio"},
            {"canonical": "rnd_sales", "all": ["r&d/sales"], "none": ["ebitda"], "type": "ratio"},
            {"canonical": "sga_sales", "all": ["sg&a", "sales"], "none": ["ebitda"], "type": "ratio"},
            {"canonical": "sbc_sales", "all": ["stock-based", "compensation"], "type": "ratio"},
        ],
    },
    {
        "code": "rnd", "name": "R&D Expenditures", "page": "R&D.html", "xls": "R&D.xls",
        "local": None, "fact": "fact_rnd",
        "columns": [
            {"canonical": "num_firms", "all": ["number", "firm"], "type": "count"},
            {"canonical": "rnd_capitalized_usd_m", "all": ["r&d capitalized"], "type": "money"},
            {"canonical": "cap_rnd_pct_invested_capital", "all": ["capitalized r&d as % of invested"], "type": "ratio"},
            {"canonical": "rnd_ltm_usd_m", "all": ["r&d", "ltm"], "type": "money"},
            {"canonical": "current_rnd_pct_revenue", "all": ["current r&d as % of revenue"], "type": "ratio"},
            {"canonical": "rnd_cagr_5y", "all": ["cagr", "r&d"], "type": "ratio"},
        ],
    },
    {
        "code": "finflows", "name": "Financing Flows by Sector", "page": "finflows.html", "xls": "finflows.xls",
        "local": None, "fact": "fact_financing_flows",
        "columns": [
            {"canonical": "num_firms", "all": ["number", "firm"], "type": "count"},
            {"canonical": "dividends", "all": ["dividend"], "none": ["yield", "payout", "%"], "type": "money"},
            {"canonical": "buybacks", "all": ["buyback"], "type": "money"},
            {"canonical": "equity_issuance", "all": ["equity issuance"], "type": "money"},
            {"canonical": "net_equity_change_usd", "all": ["net equity change"], "none": ["%"], "type": "money"},
            {"canonical": "net_equity_change_pct_book_equity", "all": ["net equity change", "%"], "type": "ratio"},
            {"canonical": "debt_repaid", "all": ["debt repaid"], "type": "money"},
            {"canonical": "debt_raised", "all": ["debt raised"], "type": "money"},
            {"canonical": "net_debt_change_usd", "all": ["net debt change"], "none": ["%"], "type": "money"},
            {"canonical": "net_debt_change_pct_total_debt", "all": ["debt", "%", "total debt"], "type": "ratio"},
            {"canonical": "change_in_lease_debt", "all": ["change in lease debt"], "type": "money"},
        ],
    },
    {
        "code": "multiples_ps", "name": "Price & EV to Sales", "page": "psdata.html", "xls": "psdata.xls",
        "local": None, "fact": "fact_multiples_ps",
        "columns": [
            {"canonical": "num_firms", "all": ["number", "firm"], "type": "count"},
            {"canonical": "price_sales", "all": ["price/sales"], "type": "multiple"},
            {"canonical": "ev_sales", "all": ["ev/sales"], "type": "multiple"},
            {"canonical": "net_margin", "all": ["net margin"], "type": "ratio"},
            {"canonical": "pretax_operating_margin", "all": ["pre-tax operating margin"], "type": "ratio"},
        ],
    },
    {
        "code": "multiples_pe", "name": "PE Ratios & Expected Growth", "page": "pedata.html", "xls": "pedata.xls",
        "local": None, "fact": "fact_multiples_pe",
        "columns": [
            {"canonical": "num_firms", "all": ["number", "firm"], "type": "count"},
            {"canonical": "current_pe", "all": ["current pe"], "type": "multiple"},
            {"canonical": "trailing_pe", "all": ["trailing pe"], "type": "multiple"},
            {"canonical": "forward_pe", "all": ["forward pe"], "type": "multiple"},
            {"canonical": "expected_growth", "all": ["expected growth"], "type": "ratio"},
            {"canonical": "peg", "all": ["peg"], "type": "multiple"},
        ],
    },
    {
        "code": "dividends_fcfe", "name": "Dividends vs FCFE", "page": "divfcfe.html", "xls": "divfcfe.xls",
        "local": None, "fact": "fact_dividends_fcfe",
        "columns": [
            {"canonical": "num_firms", "all": ["number", "firm"], "type": "count"},
            {"canonical": "dividends", "all": ["dividends"], "none": ["+", "/", "payout"], "type": "money"},
            {"canonical": "payout", "all": ["payout"], "type": "ratio"},
            {"canonical": "dividends_plus_buybacks", "all": ["dividends + buybacks"], "none": ["-", "/"], "type": "money"},
            {"canonical": "cash_return_pct_net_income", "all": ["cash return as % of net income"], "type": "ratio"},
            {"canonical": "fcfe", "all": ["fcfe"], "none": ["/", "returned"], "type": "money"},
            {"canonical": "net_cash_returned_pct_fcfe", "all": ["net cash returned/fcfe"], "type": "ratio"},
        ],
    },
    # ---- local files (no download; demonstrate the two header layouts) ----
    {
        "code": "finflows_ts", "name": "Financing Flows (tidy timeseries file)",
        "page": None, "local": "finflows_timeseries.xlsx", "fact": None,  # QA cross-check only
        "columns": [],
    },
    {
        "code": "growth_eb", "name": "Fundamental Growth in EBIT", "page": None,
        "local": "fundgrEB.xls", "fact": "fact_growth_fundamental_eb",
        "columns": [
            {"canonical": "num_firms", "all": ["number", "firm"], "type": "count"},
            {"canonical": "roc", "all": ["roc"], "type": "ratio"},
            {"canonical": "reinvestment_rate", "all": ["reinvestment"], "type": "ratio"},
            {"canonical": "expected_growth_ebit", "all": ["expected growth"], "type": "ratio"},
        ],
    },
]

DATASETS_BY_CODE = {d["code"]: d for d in DATASETS}
