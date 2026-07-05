const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, Header, Footer, PageBreak,
  ExternalHyperlink, TabStopType, TabStopPosition,
} = require("docx");

/* ---------- palette ---------- */
const NAVY = "16324F";
const STEEL = "2C6E9B";
const GOLD = "B4884D";
const BODY = "232A31";
const MUTE = "6B7680";
const ROW = "EEF3F7";
const CODEBG = "F4F6F8";
const RULE = "D8DEE5";
const WHITE = "FFFFFF";

const CONTENT_W = 9360; // US Letter, 1" margins

/* ---------- helpers ---------- */
const T = (text, o = {}) => new TextRun({ text, font: o.font || "Arial", size: o.size || 22, bold: o.bold, italics: o.italics, color: o.color || BODY, allCaps: o.allCaps });

function P(children, o = {}) {
  return new Paragraph({
    children: Array.isArray(children) ? children : [T(children, o)],
    spacing: { after: o.after != null ? o.after : 120, before: o.before || 0, line: o.line || 264 },
    alignment: o.align,
    tabStops: o.tabStops,
    keepNext: o.keepNext,
    border: o.border,
    indent: o.indent,
  });
}

const H1 = (text, o = {}) => new Paragraph({
  heading: HeadingLevel.HEADING_1, pageBreakBefore: o.pageBreak,
  children: [T(text, { font: "Arial", size: 30, bold: true, color: NAVY })],
  spacing: { before: o.pageBreak ? 0 : 300, after: 60, line: 264 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: GOLD, space: 6 } },
});
const H2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  children: [T(text, { font: "Arial", size: 25, bold: true, color: NAVY })],
  spacing: { before: 220, after: 40, line: 264 }, keepNext: true,
});
const H3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  children: [T(text, { font: "Arial", size: 21, bold: true, color: STEEL, allCaps: true })],
  spacing: { before: 160, after: 30, line: 264 }, keepNext: true,
});

const bullet = (children) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  children: Array.isArray(children) ? children : [T(children)],
  spacing: { after: 70, line: 258 },
});
const num = (ref, children) => new Paragraph({
  numbering: { reference: ref, level: 0 },
  children: Array.isArray(children) ? children : [T(children)],
  spacing: { after: 70, line: 258 },
});

/* callout: single-cell tinted box with a navy left border */
function callout(runs, fill = ROW, bar = NAVY) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    borders: {
      top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
      right: { style: BorderStyle.NONE }, insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
      left: { style: BorderStyle.SINGLE, size: 24, color: bar },
    },
    rows: [new TableRow({ children: [new TableCell({
      width: { size: CONTENT_W, type: WidthType.DXA },
      shading: { fill, type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 100, bottom: 100, left: 200, right: 160 },
      children: [new Paragraph({ children: Array.isArray(runs) ? runs : [T(runs)], spacing: { after: 0, line: 264 } })],
    })] })],
  });
}

/* clean table: navy header (white text, gold underline), alternating rows, horizontal rules only */
function table(headers, rows, widths) {
  const cellBorder = {
    top: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE },
  };
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: NAVY, type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      verticalAlign: VerticalAlign.CENTER,
      borders: { ...cellBorder, bottom: { style: BorderStyle.SINGLE, size: 12, color: GOLD } },
      children: [new Paragraph({ children: [T(h, { bold: true, color: WHITE, size: 19, allCaps: true })], spacing: { after: 0, line: 250 } })],
    })),
  });
  const bodyRows = rows.map((r, ri) => new TableRow({
    children: r.map((c, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: ri % 2 ? ROW : WHITE, type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 70, bottom: 70, left: 120, right: 120 },
      verticalAlign: VerticalAlign.CENTER,
      borders: cellBorder,
      children: (Array.isArray(c) ? c : [c]).map((line, li) =>
        new Paragraph({ children: Array.isArray(line) ? line : [T(line, { size: 19 })], spacing: { after: 0, line: 248 } })),
    })),
  }));
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    borders: {
      top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: RULE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [headerRow, ...bodyRows],
  });
}

const spacer = (h = 80) => new Paragraph({ children: [T("", {})], spacing: { after: h, line: 20 } });
const link = (text, url) => new ExternalHyperlink({ link: url, children: [new TextRun({ text, style: "Hyperlink", font: "Arial", size: 19 })] });

/* code block: monospace lines in a light-gray single cell */
function codeBlock(lines) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: RULE }, bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE },
      left: { style: BorderStyle.SINGLE, size: 4, color: RULE }, right: { style: BorderStyle.SINGLE, size: 4, color: RULE },
    },
    rows: [new TableRow({ children: [new TableCell({
      width: { size: CONTENT_W, type: WidthType.DXA },
      shading: { fill: CODEBG, type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 120, bottom: 120, left: 160, right: 160 },
      children: lines.map((l) => new Paragraph({ children: [new TextRun({ text: l || " ", font: "Consolas", size: 17, color: BODY })], spacing: { after: 0, line: 236 } })),
    })] })],
  });
}

/* ---------- content ---------- */
const b = (t) => T(t, { bold: true });
const i = (t) => T(t, { italics: true });
const children = [];

/* Cover */
children.push(new Paragraph({ spacing: { before: 900, after: 0 }, children: [T("FINANCE DATA-ANALYSIS", { size: 56, bold: true, color: NAVY })] }));
children.push(new Paragraph({ spacing: { before: 0, after: 120 }, children: [T("PORTFOLIO", { size: 56, bold: true, color: NAVY })] }));
children.push(new Paragraph({ spacing: { after: 160 }, border: { bottom: { style: BorderStyle.SINGLE, size: 18, color: GOLD, space: 10 } }, children: [T("", {})] }));
children.push(new Paragraph({ spacing: { after: 80 }, children: [T("Four production-grade projects in ", { size: 26, color: BODY }), T("Python · pandas · NumPy · DuckDB · matplotlib", { size: 26, bold: true, color: STEEL })] }));
children.push(new Paragraph({ spacing: { after: 60 }, children: [T("Deep-researched scopes, adversarially verified free datasets, and CV-ready framing.", { size: 22, color: MUTE, italics: true })] }));
children.push(new Paragraph({ spacing: { before: 500 }, children: [T("Prepared July 2026", { size: 20, color: MUTE }), T("      ·      ", { size: 20, color: GOLD }), T("Portfolio & Dataset Brief", { size: 20, color: MUTE })] }));

/* Executive summary */
children.push(H1("Executive Summary", { pageBreak: true }));
children.push(P([T("This brief specifies four finance-focused data-analysis projects designed for a professional portfolio. Each is scoped as a "), b("reproducible pipeline"), T(" — raw → staging → mart in a DuckDB warehouse, with data-quality validation, tests, CI, and a deployed dashboard — rather than a single notebook. Every dataset named here was "), b("adversarially verified as free and accessible"), T(" (43 independent checks); corrections from that verification are built into the briefs.")]));
children.push(P([T("The projects progress from an approachable data-engineering showcase to an advanced finance × cybersecurity capstone. Built in the recommended order, they share one reusable toolkit (a SEC EDGAR client, cached price/fundamentals fetchers, a DuckDB warehouse pattern, and a Streamlit template), so the marginal effort falls sharply after the first.")]));
children.push(callout([b("How to read this document.  "), T("Section 2 compares the four projects and gives a build order. Sections 3–6 are the individual project briefs. Section 7 is the master dataset reference. Section 8 is the production playbook and CV guidance that applies to all four.")], ROW, STEEL));

/* Portfolio at a glance */
children.push(H1("Portfolio at a Glance", { pageBreak: true }));
children.push(P([T("Four projects, ranked for CV impact and feasibility. "), i("Data cleanliness"), T(" reflects how automatable the sources are (★★★★★ = fully scripted, no manual extraction).")]));
children.push(table(
  ["#", "Project", "Core finance angle", "Difficulty", "Effort"],
  [
    [[[b("1")]], [[T("Post-COVID Sector Rotation", { size: 19, bold: true })], [T("★★★★★ data", { size: 16, color: MUTE })]], "Event study, drawdowns, macro linkage", "Int → Adv", "50–70h"],
    [[[b("2")]], [[T("Luxury Goods Market Share & Valuation", { size: 19, bold: true })], [T("★★★☆☆ data", { size: 16, color: MUTE })]], "Market share, segment mix, comps / multiples", "Int → Adv", "60–90h"],
    [[[b("3")]], [[T("Fortune 500 Financial Breakdowns", { size: 19, bold: true })], [T("★★★★☆ data", { size: 16, color: MUTE })]], "Sector profitability, concentration, churn", "Intermediate", "40–70h"],
    [[[b("4")]], [[T("Cloud / ERP / AI Vendor Intelligence", { size: 19, bold: true })], [T("★★★☆☆ data", { size: 16, color: MUTE })]], "Segment revenue × security-risk exposure", "Advanced", "60–90h"],
  ],
  [520, 2760, 3300, 1280, 1500],
));
children.push(spacer(120));
children.push(H3("Recommended build order"));
children.push(num("order", [b("Fortune 500 (quick win, first). "), T("Most approachable data; builds the reusable toolkit — DuckDB warehouse, SEC EDGAR client, yfinance caching, pandera validation, Streamlit template.")]));
children.push(num("order", [b("Post-COVID Sector Rotation (flagship). "), T("Cleanest free data and real quant methodology (market-model event study). Reuses the FRED + yfinance plumbing. Reads as “can do quantitative finance.”")]));
children.push(num("order", [b("Luxury Goods (finance-recruiter magnet). "), T("The most finance-brand project — comps, multiples, market share. The segment/geography mapping from filings is genuine analyst work.")]));
children.push(num("order", [b("Cloud / ERP / AI + Security (advanced capstone). "), T("Most differentiated; highest ceiling; hardest. Do it once the pipeline pattern is second nature.")]));
children.push(P([i("If you only build two: "), T("Fortune 500 (data-engineering showcase) + Post-COVID (quant / finance showcase) together tell the whole “analyst who can engineer” story.")], { before: 60 }));

/* ---- Project brief builder ---- */
function projectBrief(o) {
  children.push(H1(o.title, { pageBreak: true }));
  children.push(P([T(o.subtitle, { color: MUTE, italics: true, size: 21 })], { after: 60 }));
  children.push(callout([b(o.tagline)], ROW, GOLD));
  children.push(P([b("Difficulty  "), T(o.difficulty + "      "), b("Effort  "), T(o.effort + "      "), b("Data  "), T(o.data)], { before: 120, after: 60 }));

  children.push(H3("The interview story"));
  children.push(P([i("“" + o.story + "”")]));

  children.push(H3("Scope"));
  children.push(P(o.scope));

  children.push(H3("Analytical questions"));
  o.questions.forEach((q) => children.push(num(o.qref, q)));

  children.push(H3("Methodology (pipeline)"));
  o.methodology.forEach((m) => children.push(num(o.mref, [T(m, { size: 20 })])));

  children.push(H3("Key visualizations"));
  o.visuals.forEach((v) => children.push(bullet([T(v, { size: 20 })])));

  children.push(H3("Verified datasets"));
  children.push(table(["Source", "How it is used", "Access"], o.datasets, [2500, 4160, 2700]));

  children.push(H3("CV bullet points (honest, quantified)"));
  o.cv.forEach((c) => children.push(bullet(c)));

  children.push(H3("Skills demonstrated"));
  children.push(P([T(o.skills, { size: 20 })]));

  children.push(H3("Key risks & gotchas"));
  o.risks.forEach((r) => children.push(bullet([T(r, { size: 20 })])));

  children.push(H3("Extensions (stretch goals)"));
  o.extensions.forEach((e) => children.push(bullet([T(e, { size: 20 })])));
}

projectBrief({
  title: "Project 1 — Post-COVID Sector Rotation",
  subtitle: "An Event-Study and Macro-Linkage Analysis of U.S. Equity Sectors (2019–2025)",
  tagline: "Flagship — best effort-to-impressiveness ratio: cleanest free data plus real quant methodology.",
  difficulty: "Intermediate → Advanced", effort: "~50–70h", data: "★★★★★ (fully automatable)",
  qref: "qcovid", mref: "mcovid",
  methodology: [
    "Config & scaffold: tickers, SPY benchmark, window (2019 to present), event dates (peak 19-Feb, trough 23-Mar-2020, 250-day estimation window), and a sector-to-macro-series map in a typed config module.",
    "Ingest (idempotent, cached): ETF + SPY daily OHLCV via pandas-datareader Stooq (yfinance fallback), FRED macro + VIX via fredapi, OWID COVID CSV via requests; persist raw pulls to Parquet so the network is hit once.",
    "Clean & load to DuckDB: standardize dates, handle the frozen-OWID end date, resample monthly/quarterly macro to a common calendar, US-filter COVID, and write typed tables + a data dictionary.",
    "Feature layer (SQL views + pandas): daily & cumulative log returns, 21-day rolling annualized volatility, running max-drawdown, recovery-time, Sharpe/Sortino, and a wide returns matrix.",
    "Descriptive analysis: rank sectors by drawdown depth, volatility blow-up, and recovery time; compare 2019 vs 2023-2025 leadership to find structural re-rankings.",
    "Event study: estimate each sector's market model on the 250-day pre-peak window; compute abnormal returns and cumulative abnormal returns (CAR) across the crash window; t-test significance; repeat for the 2021-22 regime.",
    "Correlation-regime analysis: rolling pairwise correlations; quantify the March-2020 spike toward 1.0 and the subsequent dispersion.",
    "Macro linkage: align daily VIX and resampled macro to sector returns; regress recovery-time/drawdown on sector-specific macro damage and estimate per-sector VIX-beta.",
    "COVID-policy linkage: overlay US stringency index and case/death waves; test the stay-at-home vs physical-economy hypothesis.",
    "Validation & tests: pytest on return/drawdown/recovery math and event-window alignment; cross-check Stooq vs yfinance closes.",
    "Dashboard & docs: Streamlit app over DuckDB (sector/date/event-window controls) plus a README with methodology, data lineage, and a findings summary.",
  ],
  visuals: [
    "Small-multiples underwater drawdown curves for all 11 sectors + SPY, crash window shaded, each sector's recovery date annotated.",
    "Recovery-time ranking bar: trading days for each sector to reclaim its pre-COVID peak - the most quotable which-industries-bounced-back-fastest visual.",
    "Event-study CAR bar with error bars, colored by statistical significance (structural winners vs losers).",
    "Rolling-volatility ribbon (21-day annualized vol) showing the March-2020 spike and normalization time.",
    "Cross-sector correlation heatmaps at three snapshots: 2019 calm, March-2020 panic, 2023 post-COVID.",
    "Dual-axis macro overlay: market composite vs UNRATE and INDPRO, marking the market-leads-the-real-economy gap.",
    "COVID stringency overlay vs a stay-at-home-minus-physical-economy sector spread.",
    "Pre-vs-post leadership slope/bump chart connecting 2019 to 2023-2025 rankings.",
  ],
  skills: "Financial-markets literacy (drawdown, recovery, Sharpe/Sortino, sector rotation); event-study methodology & abnormal-return analysis; time-series and multi-frequency alignment; applied statistics (market-model OLS, hypothesis testing) with statsmodels/scipy; idempotent cached ETL into DuckDB; analytical SQL warehousing; pandas/numpy; macroeconomic reasoning (UNRATE, INDPRO, CPI, GDP, VIX); matplotlib/plotly storytelling; Streamlit deployment; software-engineering hygiene (tests, CI, config/secrets).",
  extensions: [
    "Add BEA GDP-by-industry value added for a markets-lead-the-real-economy chart (real-output recovery vs ETF recovery).",
    "Extend the event study to a second shock (2022 inflation/rate-hike regime) to test consistent resilience/fragility.",
    "Add a rules-based sector-rotation backtest vs SPY buy-and-hold, reported honestly with transaction-cost caveats.",
    "Incorporate BLS industry-level payrolls for a finer sector-to-industry employment map.",
    "Add a Fama-French factor lens to decompose COVID-era performance into market/size/value/momentum.",
    "Automate a weekly refresh via GitHub Actions that rebuilds the warehouse and redeploys the dashboard.",
  ],
  story: "I ran a formal market-model event study of the COVID crash across all 11 GICS sectors, measured cumulative abnormal returns vs. the S&P 500 over a 250-day estimation window to separate structural winners from losers, then linked recovery speed to sector-specific macro damage and the pandemic stringency timeline.",
  scope: [T("Universe: 11 SPDR sector ETFs (XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLU, XLB, XLRE, XLC) benchmarked against SPY, daily 2019-01-01 → present, plus 8 macro series and one COVID case/stringency series. Three layers: "), b("descriptive"), T(" (returns, rolling volatility, max drawdown, recovery time, Sharpe/Sortino, correlation regimes); "), b("event study"), T(" (cumulative abnormal returns vs. a market-model expectation around 19-Feb → 23-Mar-2020, 250-day estimation window); and "), b("macro linkage"), T(" (align monthly/quarterly macro + daily VIX + stringency to sector returns). Out of scope: single-stock alpha, options, intraday, international markets.")],
  questions: [
    [T("Which sector had the deepest COVID drawdown, and does that ranking match the ranking by recovery time (days to reclaim the pre-crash peak)?")],
    [T("In a formal event study, which sectors had statistically significant "), b("negative"), T(" cumulative abnormal returns vs. SPY versus significant "), b("positive"), T(" ones — and does the sign flip in the 2021–22 inflation regime?")],
    [T("Did cross-sector correlations spike toward 1.0 in the March-2020 panic (“diversification fails when you need it”) and then disperse?")],
    [T("Does sector-level macro damage (BLS/FRED industry payrolls, industrial production) explain recovery speed?")],
    [T("How did tighter lockdowns (stringency index / case waves) coincide with “physical-economy” vs. “stay-at-home” sector performance?")],
    [T("Comparing 2019 pre-COVID leadership to 2023–25, which sectors "), b("permanently re-ranked"), T(" versus mean-reverted?")],
  ],
  datasets: [
    [[[b("Sector ETFs + SPY OHLCV")], [T("via yfinance / pandas-datareader", { size: 16, color: MUTE })]], "Primary price panel: returns, volatility, drawdowns, recovery, correlations, abnormal returns", [[T("No key. ", { size: 19 }), T("Stooq CSV now bot-blocked", { size: 19, bold: true, color: GOLD }), T(" — use library fetchers + cache to Parquet", { size: 19 })]]],
    ["FRED (Federal Reserve)", "Macro-linkage + VIX beta: VIXCLS, UNRATE, INDPRO, CPIAUCSL, GDP, sector payrolls", "Free 32-char API key; use fredapi"],
    ["Our World in Data — COVID-19", "Stringency + case/death waves overlay", [[T("CSV, no key. ", { size: 19 }), T("frozen 19-Aug-2024", { size: 19, color: GOLD }), T(" → scope overlay to 2019–24", { size: 19 })]]],
    ["BLS API / BEA GDP-by-industry", "Optional: industry payroll & value-added recovery vs. ETF recovery", "Free key / UserID (many series also on FRED)"],
  ],
  cv: [
    [T("Built an end-to-end, reproducible "), b("Python + DuckDB"), T(" pipeline ingesting ~12 ETFs and 8 macro/COVID series (2019–2025) from 4 free APIs into a local SQL warehouse, with cached idempotent ingestion resilient to source-side rate-limiting and anti-bot blocks.")],
    [T("Engineered a formal "), b("market-model event study"), T(" of the Feb–Mar 2020 crash, estimating cumulative abnormal returns vs. SPY over a 250-day window for all 11 sectors and t-testing significance.")],
    [T("Quantified sector drawdowns (~30–50% peak-to-trough) and recovery times, ranking all 11 sectors by days-to-reclaim-peak.")],
    [T("Modeled the market-vs-fundamentals gap by aligning daily returns with monthly/quarterly macro and the daily VIX, estimating "), b("per-sector VIX-betas"), T(" and regressing recovery speed on macro damage.")],
    [T("Shipped an interactive "), b("Streamlit"), T(" dashboard (DuckDB-backed, deployed) and hardened it with a pytest suite over the financial math, ruff/pre-commit, and GitHub Actions CI.")],
  ],
  risks: [
    "Stooq's direct CSV endpoint is now behind a JavaScript anti-bot wall — use library fetchers + cache; never a naive requests.get.",
    "yfinance is fragile in 2025–26 (HTTP 429) — fetch once, cache to Parquet, add retry/back-off; never depend on it live.",
    "OWID's COVID CSV is frozen at 19-Aug-2024 — scope the COVID overlay accordingly.",
    "Frequency mismatch (GDP quarterly, macro monthly, prices daily) is the main trap — resampling must be explicit or correlations are spurious.",
    "The event-study estimation window (2019) must exclude other structural breaks; frame macro links as association, not causation.",
  ],
});

projectBrief({
  title: "Project 2 — Luxury Goods Market Share & Valuation",
  subtitle: "A Reproducible Python/DuckDB Pipeline Benchmarking 9 Global Luxury Houses",
  tagline: "The most finance-recruiter-appealing project — comps, multiples, market share, valuation-vs-fundamentals.",
  difficulty: "Intermediate → Advanced", effort: "~60–90h", data: "★★★☆☆ (PDF extraction is the slow part)",
  qref: "qlux", mref: "mlux",
  methodology: [
    "Universe & config: a YAML config of the 10 tickers, their CIKs (US filers), fiscal year-ends, reporting currency, and a documented segment/region mapping table reconciling each house's taxonomy to a common schema.",
    "Ingest raw: SEC company-facts JSON (EL/TPR/CPRI) with User-Agent + rate limiting; yfinance prices for all 10 tickers (cached to Parquet); Damodaran .xls; World Bank indicators; and segment & geographic revenue tables extracted from each URD via pdfplumber into a reviewed CSV.",
    "Stage & normalize: parse EDGAR XBRL into tidy statements, align March vs December fiscal year-ends, convert revenue/EBITDA to EUR and USD via documented annual-average FX, and unify segment/region labels via the mapping table.",
    "Load into DuckDB (raw to staging to marts): fct_financials, fct_segment_revenue, fct_geo_revenue, fct_valuation, dim_company.",
    "Market share & concentration: revenue share of each house within the peer set per year, sector HHI, and listed-peer aggregate vs the Bain total-market figure.",
    "Financial performance: 3/5/10-year revenue CAGR plus gross/operating/net margins and trends, ranked and currency-normalized.",
    "Valuation: enterprise value / sales and / EBITDA and trailing P/E per house; join Damodaran benchmarks to compute premium/discount vs sector.",
    "Reconcile & validate: diff yfinance fundamentals against EDGAR ground truth for the three US filers; run pandera checks (shares sum to 100%, no negative revenue, FX coverage complete) + pytest on the formulas.",
    "Analyze & narrate: a notebook answering each analytical question with a chart, culminating in a valuation-vs-fundamentals scatter that flags rich/cheap houses.",
    "Ship the dashboard: a multi-page Streamlit app reading from DuckDB, plus full docs (README, data dictionary, and the segment-mapping rationale) for one-command reproduction.",
  ],
  visuals: [
    "Stacked-area market share within the listed peer set (2015-2024), showing LVMH and Hermes gaining while others compress.",
    "Sector-concentration line chart (HHI over time) annotated with the 2024 downturn.",
    "Small-multiples of each house's segment mix (fashion & leather / watches & jewelry / wines & spirits / beauty / retail) as 100% stacked bars.",
    "Geographic revenue heatmap (houses x regions) highlighting China vs Japan vs Americas exposure.",
    "Slope/bump chart ranking houses by 5-year revenue CAGR, currency-normalized.",
    "Grouped margin bars per house with the Damodaran apparel-industry average as a reference line (Hermes premium pops out).",
    "Valuation-vs-fundamentals scatter: EV/EBITDA vs revenue CAGR or operating margin, bubble size = revenue, quadrant lines from the industry median.",
    "yfinance-vs-EDGAR reconciliation panel for EL/TPR/CPRI with percent variance per line item.",
  ],
  skills: "Comparable-company valuation (EV/Sales, EV/EBITDA, P/E, margin & growth benchmarking); financial-statement analysis across IFRS and US GAAP; layered warehouse/ETL design and reproducibility; DuckDB SQL; API integration (SEC EDGAR, World Bank) with proper headers/rate-limiting; PDF/table extraction and schema harmonization; currency normalization and CAGR/HHI computation; source reconciliation and data-quality engineering; Python software engineering (typed config, testing, CI); matplotlib/plotly/Streamlit; free-vs-paywalled sourcing due diligence.",
  extensions: [
    "Regress each house's regional revenue growth on World Bank consumption / GDP-per-capita trends for its exposure regions.",
    "Incorporate ESG/sustainability KPIs disclosed in the URDs for an ESG-vs-valuation angle.",
    "Add a reverse-DCF / implied-growth back-out to estimate the growth each house's multiple is pricing in.",
    "Build an earnings-date event study of share-price reaction (align yfinance prices with filing dates).",
    "Add quarterly granularity for the US filers using EDGAR 10-Qs.",
    "Add a peer-set share-of-total-market tracker that auto-updates with new Bain/Altagamma figures.",
    "Containerize with Docker and schedule a monthly price/valuation refresh.",
  ],
  story: "I built a comps model across the 9 listed global luxury houses — normalizing IFRS vs. US-GAAP filings and four currencies, hand-mapping each house's distinct segment and geographic taxonomy into a common schema, then benchmarking margins and EV/EBITDA, EV/Sales and P/E against Damodaran industry averages to flag who is expensive for their fundamentals.",
  scope: [T("Fixed universe of 9 listed houses (LVMH, Kering, Richemont, Hermès, Burberry, Prada, Brunello Cucinelli, Estée Lauder, Tapestry, Capri) over FY2015–FY2024. "), b("“Market share” is explicitly defined as revenue share within this listed peer set"), T(" (not the total Bain market, used only as context), keeping the metric reproducible from primary filings. Four pillars: market share & HHI concentration; revenue mix (segment + geography, mapped to a common schema); financial performance (CAGR, gross/operating/net margins, currency-normalized to EUR & USD); and valuation (EV/Sales, EV/EBITDA, P/E benchmarked vs. Damodaran). Out of scope: quarterly modeling, DCF, options, private brands.")],
  questions: [
    [T("Each house's revenue share within the peer set; how has sector "), b("HHI concentration"), T(" evolved 2015–2024; did the 2024 downturn consolidate or fragment share?")],
    [T("How does segment mix differ across houses, and which mix proved most resilient during the 2024 contraction?")],
    [T("How is each house's revenue split geographically, and how exposed is each to the China slowdown vs. Japan/US strength?")],
    [T("What are the 3/5/10-year revenue CAGRs per house once currency effects are normalized out?")],
    [T("Does Hermès's structural margin premium show cleanly vs. peers and vs. the Damodaran apparel-industry average?")],
    [T("Do current multiples (EV/Sales, EV/EBITDA, P/E) rank the houses the same way growth and margins do — who is “expensive for their fundamentals”?")],
  ],
  datasets: [
    ["SEC EDGAR XBRL", "Ground-truth financials for the US filers (EL, TPR, CPRI); reconciliation benchmark for yfinance", [[T("No key; ", { size: 19 }), T("User-Agent header required", { size: 19, bold: true }), T(". IFRS filers not here", { size: 19 })]]],
    [[[b("Registration Documents / Annual Reports (PDF)")]], "Primary source for segment & geographic revenue for all houses (esp. IFRS ones)", [[T("Direct PDF URLs. ", { size: 19 }), T("Taxonomies differ → documented mapping table", { size: 19, color: GOLD })]]],
    ["yfinance", "Share price, market cap, EV inputs for all houses; return series", [[T("No key, fragile. ", { size: 19 }), T("Non-US fundamentals often empty", { size: 19, color: GOLD }), T(" — prices only", { size: 19 })]]],
    ["Damodaran NYU Stern", "Industry-average margins & multiples benchmark", "Direct .xls; pin file + date (overwritten each Jan)"],
    ["Bain × Altagamma; World Bank", "Total-market context; regional consumption/GDP macro layer", "Free press releases / open API"],
  ],
  cv: [
    [T("Built an end-to-end "), b("Python/DuckDB"), T(" pipeline benchmarking 9 listed global luxury houses across 10 fiscal years, integrating 6 free sources into a layered analytical warehouse.")],
    [T("Normalized heterogeneous disclosures ("), b("IFRS vs. US GAAP; EUR/CHF/GBP/USD"), T(") and hand-mapped each house's distinct segment & geographic taxonomy into a common schema for apples-to-apples comparison.")],
    [T("Computed revenue-based market share, sector "), b("HHI"), T(", 3/5/10-year CAGRs, margins, and EV/Sales, EV/EBITDA and P/E multiples, benchmarking each house against Damodaran industry averages.")],
    [T("Implemented a data-integrity layer "), b("reconciling yfinance fundamentals against SEC EDGAR ground truth"), T(" for 3 US filers, quantifying line-item variance.")],
    [T("Delivered an interactive multi-page "), b("Streamlit"), T(" dashboard reading live from DuckDB, with pandera checks and a pytest suite covering every financial formula wired into CI.")],
  ],
  risks: [
    "Segment/geographic taxonomies differ materially by house — the common-schema crosswalk requires documented judgment; treat it as a transparent, first-class artifact.",
    "Fiscal year-ends are not aligned (Richemont & Burberry end in March) — state an explicit alignment convention.",
    "yfinance non-US fundamentals frequently return empty — use it for prices only; use filings for European income statements.",
    "Currency normalization introduces analyst choices (spot vs. average FX) — document the source and method.",
    "Do not scrape Statista / Macrotrends / stockanalysis.com (paywalled or ToS-forbidden) — use primary filings + free Bain/Altagamma headlines.",
  ],
});

projectBrief({
  title: "Project 3 — Fortune 500 Financial Breakdowns",
  subtitle: "A Multi-Year DuckDB Panel of Corporate America's Largest Firms",
  tagline: "Quick win / first project — the best pure data-engineering showcase, and it builds the toolkit you reuse everywhere.",
  difficulty: "Intermediate", effort: "~40–70h", data: "★★★★☆ (community CSVs)",
  qref: "qf500", mref: "mf500",
  methodology: [
    "Config & scaffolding: a typed config (dataset URLs, pinned GitHub commit SHA, Kaggle slug+version, SEC User-Agent) and a src/ sql/ data/ tests/ dashboard/ skeleton wired to a Makefile.",
    "Ingest: pull the GitHub per-year CSVs (spine), the Kaggle enrichment CSV via kagglehub, the current-year Wikipedia table via pandas.read_html, and optional SEC/yfinance fundamentals; cache every raw payload with retries.",
    "Land raw in DuckDB verbatim (raw_* schema) preserving source columns and adding source + ingested_at metadata for lineage.",
    "Clean & normalize (staging): standardize column names and types, normalize units to USD millions, standardize sector/industry labels via a mapping table, and split HQ into city + state.",
    "Entity resolution across years: resolve name variants (M&A, rebrands, punctuation) to a stable company_id via normalized-name matching plus a manual alias/override table.",
    "Model the warehouse (marts): fact_company_year (company x year) + dim_company, with SQL window functions deriving net_margin, ROA, revenue_per_employee, rank_change, and entered/exited churn flags.",
    "Data-quality gates: pandera checks (exactly 500 ranks per year, non-null keys, non-negative financials, valid sector enum, no duplicate company-year) that fail the pipeline loudly.",
    "Analyses: size-vs-profitability (Pearson/Spearman + regression), sector profitability & efficiency (+ Damodaran benchmarks), concentration & geography (HHI, HQ maps), and churn & rank dynamics.",
    "Visualize & ship: static figures for the report, then a Streamlit app (KPI cards + interactive views) reading from DuckDB; add pytest + a GitHub Actions smoke pipeline and a documented README.",
  ],
  visuals: [
    "Size-vs-margin scatter: revenue (log x) vs net margin, colored by sector, with a trend line and outlier callouts - the visual answer to is-bigger-more-profitable.",
    "Sector-profitability boxplot/violin of net margin (and ROA) by sector, with Damodaran industry-benchmark markers overlaid.",
    "Revenue-per-employee ranked bar by sector (log-scaled), highlighting the extreme high and low ends.",
    "Concentration trend lines: top-10/25/50 revenue share and an HHI series over the panel years.",
    "US-state HQ choropleth (Plotly) shaded by number of Fortune 500 HQs, with revenue/employee toggles and a top-metros bar.",
    "Year-over-year churn chart: stacked entrants vs exits with an overlaid churn-rate line, plus churn-by-sector small-multiples.",
    "Rank-movement bump/slope chart of top gainers and decliners, animated by year in the dashboard.",
  ],
  skills: "Data-engineering / ELT design (multi-source ingestion, raw to staging to marts); DuckDB and analytical SQL (window functions, HHI/correlation queries); dimensional data modeling (fact/dimension, grain); entity resolution and cross-time data cleaning; web scraping and REST API integration (Wikipedia, SEC EDGAR, yfinance, Kaggle); reproducible analytics engineering (Makefile, pinned sources); pandera + pytest data-quality testing; correlation/regression and concentration/churn analysis; matplotlib/Plotly/Streamlit; financial-statement literacy and benchmarking; software-engineering hygiene (typed config, CI/CD, linting, documentation).",
  extensions: [
    "Add the Global 500 as a parallel panel (US vs rest-of-world sector mix, margins, geographic concentration).",
    "Full SEC EDGAR reconciliation: pull audited figures via the XBRL frames API and quantify divergence from Fortune's numbers as a data-quality chapter.",
    "Inflation-adjust the panel with a free CPI or GDP-deflator series.",
    "Layer market data via yfinance for a market-cap-to-revenue and valuation-vs-fundamentals angle.",
    "Publish the marts as Parquet and expose a small read-only FastAPI or public DuckDB/MotherDuck share.",
    "Add a predictive model estimating the probability a firm exits the list next year, evaluated out-of-sample.",
    "Automate an annual refresh via a scheduled GitHub Action that re-scrapes and rebuilds the warehouse.",
  ],
  story: "I engineered a reproducible DuckDB warehouse over ~10 years of Fortune 500 data, then showed that tech and pharma dominate margins while retail dominates headcount, that revenue-per-employee varies ~20× across sectors, and that ~3–5% of the list turns over annually with churn concentrated in energy and retail.",
  scope: [T("A clean, tested, reproducible "), b("multi-year panel"), T(" of Fortune 500 (US) companies with a canonical schema (company, year, rank, revenue, profit, assets, employees, sector, industry, HQ) plus derived metrics (net margin, revenue-per-employee, rank_change). The core deliverable is the "), b("data engineering"), T(" — ingesting heterogeneous CSVs/scrapes into DuckDB with cross-year entity resolution and unit normalization — plus ~7 fixed analytical questions answered with SQL + pandas. Everything runs from a single make command on a fresh clone using only free data.")],
  questions: [
    [T("Does size predict profitability? Correlation between revenue/assets and net margin, overall and by sector — is “bigger = more profitable,” or does margin decouple from scale?")],
    [T("Which sectors are most and least profitable (median net margin, ROA), and how have rankings shifted year over year?")],
    [T("How does "), b("revenue-per-employee"), T(" vary across sectors, and which industries are the extreme outliers?")],
    [T("How concentrated is the list by industry and geography (top-10/25/50 revenue share, "), b("HHI"), T(" over the decade)?")],
    [T("How churny is the list — annual entry/exit rate, sector churn (a disruption proxy), and survival of former top-100 firms?")],
    [T("Who are the biggest rank movers, and do upward movers systematically differ (margin, growth, sector) from decliners?")],
  ],
  datasets: [
    [[[b("Fortune 500 multi-year CSV")], [T("cmusam/fortune500 (GitHub)", { size: 16, color: MUTE })]], "Longitudinal spine → DuckDB base fact table (company-year grain)", [[T("No key. ", { size: 19 }), T("Combined URL 404s — use per-year files", { size: 19, bold: true, color: GOLD }), T("; pin a commit SHA", { size: 19 })]]],
    ["Kaggle Fortune 500 / 1000", "Enrichment: sector, industry, HQ, employees, market cap", "Free account + API token; prefer CC0/CC BY"],
    ["Wikipedia (largest US cos.)", "Current-year refresh & cross-check (~top 100)", "pandas.read_html, no key"],
    ["SEC EDGAR XBRL", "Validation/stretch: audited revenue/net income/assets for public firms", "No key; User-Agent required; public filers only"],
    ["Damodaran NYU Stern", "Per-industry benchmark margins/ROC to contextualize sectors", "Direct .xls; mapping table for taxonomy"],
  ],
  cv: [
    [T("Engineered a reproducible "), b("Python + DuckDB"), T(" pipeline ingesting and reconciling 4+ heterogeneous free sources into a layered warehouse (raw → staging → marts) covering ~10 years × 500 companies (~5,000 company-year records).")],
    [T("Built "), b("cross-year entity resolution"), T(" and unit-normalization logic to track firms through rebrands and M&A, enabling year-over-year rank-change, survival, and churn analysis.")],
    [T("Modeled a "), b("fact/dimension schema"), T(" and used SQL window functions to derive net margin, ROA, revenue-per-employee, rank_change and churn flags — quantifying that revenue-per-employee spans ~20× across sectors.")],
    [T("Ran a size-vs-profitability analysis (Pearson/Spearman + per-sector regression) showing net margin largely decouples from scale, benchmarked against Damodaran datasets.")],
    [T("Shipped an interactive "), b("Streamlit"), T(" dashboard (US-state HQ choropleth, concentration & churn views) with pandera gates, pytest, typed config, and GitHub Actions CI.")],
  ],
  risks: [
    "Fortune's rankings are proprietary editorial data — the GitHub/Kaggle CSVs are community reproductions; cite them as such.",
    "Hardcoded source URLs drift and 404 — pin a commit SHA / dataset version and mirror raw data into the repo.",
    "Employees/sector/industry/HQ columns are inconsistently present across years — enrich the current year well; document sparser history.",
    "Fortune figures use company-specific fiscal conventions — they will not tie exactly to SEC/yfinance; frame those as a validation layer.",
    "Sector taxonomies differ across sources — a crosswalk table is required (and is itself a skill to showcase).",
  ],
});

projectBrief({
  title: "Project 4 — Cloud, ERP & AI Vendor Intelligence",
  subtitle: "Segment Revenue, Implied Market Share, and Security-Risk Exposure",
  tagline: "Advanced capstone — the original “Agentic AI, ERP & Cloud” idea refined into a defensible, differentiated scope.",
  difficulty: "Advanced", effort: "~60–90h", data: "★★★☆☆ (CPE attribution is hard)",
  qref: "qcloud", mref: "mcloud",
  methodology: [
    "Define config: covered vendors with their ticker, SEC CIK, and NVD CPE vendor string(s), plus the study window and severity buckets, in a versioned config.yaml.",
    "Ingest financials: map tickers to CIK via SEC company_tickers.json, then pull companyfacts for total and reportable-segment revenue & operating income; record where segment dollars are unavailable (Azure/GCP) as an is_disclosed flag.",
    "Ingest security data: page the NVD 2.0 API per vendor via CPE (API key, backoff, local cache); download the CISA KEV catalog; optionally clone a subset of MITRE cvelistV5 for cross-check.",
    "Ingest adoption signals: harmonize Stack Overflow survey CSVs across years; optionally aggregate GH Archive activity via BigQuery; pull a yfinance price panel.",
    "Build the DuckDB warehouse in layers: raw, staging (typed, vendor-name-normalized), and marts (segment_financials, cve_by_vendor_severity_year, kev_by_vendor, vendor_scorecard).",
    "Normalize vendor identity: reconcile ticker vs NVD CPE vendorProject vs KEV vendorProject via a curated crosswalk; validate on a sample and document attribution error.",
    "Pillar A metrics: YoY growth, multi-year CAGR, and revenue mix within the covered peer set; annotate disclosure gaps.",
    "Pillar C metrics: per-vendor CVE counts, CVSS severity distribution by year, KEV exploited rate, publication-to-KEV lag, and ransomware-linked share.",
    "Pillar B corroboration: survey tool-usage share trend (and optional GH Archive activity) per vendor vs the revenue-momentum ranking.",
    "Capstone join & hypothesis test: build the vendor scorecard joining growth to severe/exploited load; report Spearman correlation and a transparent ranked table (labeled associational, not causal).",
    "Data-quality gate + ship: pandera checks and pytest transforms before publishing marts; then a Streamlit dashboard, a written report with caveats, and a Makefile/README for one-command reproduction.",
  ],
  visuals: [
    "Small-multiple line charts of segment revenue and YoY growth per vendor, marking lines that are growth-only with no disclosed dollars (Azure/GCP).",
    "100-percent-stacked bar of implied revenue mix within the covered peer set over time (with a not-total-market-share disclaimer).",
    "Heatmap of CVE count by vendor x year, plus a companion CVSS-severity-share heatmap.",
    "Diverging bar ranking vendors by KEV exploited rate (share of their CVEs that became actively exploited).",
    "Histogram/box of publication-to-KEV lag (days), faceted by vendor.",
    "Capstone scatter: cloud-revenue CAGR vs severe-or-exploited vulnerability load, one point per vendor, with Spearman r annotated.",
    "Streamlit vendor scorecard: financial KPIs, security KPIs, severity mix, KEV timeline, and a composite risk-vs-growth badge.",
  ],
  skills: "Financial-statement literacy (10-K/10-Q reportable-segment disclosures and us-gaap XBRL tags); REST API engineering (pagination, rate-limit handling, API-key auth, retry/backoff, caching); DuckDB modeling and multi-source joins; entity resolution (ticker vs CPE vs KEV crosswalk); data-quality engineering in CI; analytical honesty (measured vs proxy, associational vs causal, disclosure gaps); cybersecurity data fluency (CVE/CVSS/CPE and the CISA KEV model); Streamlit dashboards + narrative reporting; reproducible research tooling; clear technical communication.",
  extensions: [
    "Add an event-study module correlating spikes in a vendor's KEV additions with short-window equity returns (caveated, non-causal).",
    "Extend the adoption signal with the Hugging Face Hub API and Papers-with-Code to trace agentic-AI framework momentum.",
    "Run NLP on 10-K Risk Factors cybersecurity language to build a disclosed-cyber-risk text score vs the actual KEV exploited rate.",
    "Build an incremental daily refresh (KEV + NVD modified deltas) and publish the dashboard via a scheduled GitHub Action.",
    "Add SSVC / EPSS exploit-prediction enrichment to prioritize vulnerabilities by likely exploitation.",
    "Package the vendor crosswalk and CVE-attribution logic as a reusable pip-installable module.",
  ],
  story: "The enterprise-tech vendors compounding revenue fastest are also accumulating the most severe, most-exploited vulnerabilities — here is that trade-off, measured, with every number traceable to a primary-source filing or a government vulnerability record.",
  scope: [T("~10 named vendors (MSFT, AMZN, GOOGL, ORCL, CRM, SAP, NOW, SNOW, + optional IBM, WDAY), FY2016–present, across three linked pillars. "), b("A — Financial performance: "), T("reportable-segment revenue & growth from SEC EDGAR XBRL. "), b("B — Implied market position: "), T("because true share reports are paywalled, compute a revenue-mix view within the peer set and corroborate with free developer-adoption signals. "), b("C — Security exposure: "), T("per-vendor CVE counts, CVSS severity, and actively-exploited rate from NVD + CISA KEV. The capstone tests one hypothesis — is faster cloud-revenue growth associated with a heavier severe/exploited vulnerability load? An honesty constraint is baked in: AWS is a clean segment but Azure & GCP disclose growth-% only, treated as a first-class data-quality problem.")],
  questions: [
    [T("How has reportable cloud/ERP segment revenue & growth evolved, and how does AWS's clean disclosure compare to Microsoft's blended reporting and Google Cloud's segment line?")],
    [T("Where does the analysis hit the "), b("disclosure wall"), T(" — which cloud lines have no standalone dollar figure, only growth percentages?")],
    [T("Do free adoption signals (Stack Overflow tool usage, GH Archive activity) corroborate or contradict the revenue-based momentum ranking?")],
    [T("Which vendors carry the largest CVE burden in NVD, and how has their CVSS severity mix shifted year over year?")],
    [T("What fraction of each vendor's CVEs appear in the "), b("CISA KEV catalog"), T(" (actively exploited), and who has the highest exploited rate?")],
    [T("Is faster cloud-revenue growth statistically associated (Spearman) with a heavier severe/exploited load across the covered vendors?")],
  ],
  datasets: [
    ["NVD CVE API 2.0 (NIST)", "Primary security dataset: CVEs per vendor via CPE; CVSS severity + dates", [[T("Free API key recommended", { size: 19, bold: true }), T(" (raises rate limit 5 → 50 / 30s)", { size: 19 })]]],
    ["CISA KEV catalog", "Flags actively-exploited CVEs; per-vendor exploited rate & lag", "JSON/CSV, no key, no rate limit; CC0 mirror"],
    ["SEC EDGAR XBRL", "Primary financials (Pillar A): total & segment revenue/operating income", [[T("No key; ", { size: 19 }), T("User-Agent required", { size: 19, bold: true }), T("; segment tags a known gap", { size: 19 })]]],
    ["Stack Overflow Developer Survey", "Pillar B corroboration: YoY tool-usage share vs. revenue momentum", "Free, no key; columns change yearly — harmonize"],
    ["GH Archive; yfinance; MITRE cvelistV5", "Optional: mindshare proxy; equity panel; CVE fallback", "BigQuery free tier / cached / shallow clone"],
  ],
  cv: [
    [T("Built an end-to-end "), b("Python + DuckDB"), T(" pipeline integrating 4 primary-source datasets (SEC EDGAR XBRL, NVD CVE API, CISA KEV, Stack Overflow Survey) to quantify the trade-off between cloud-revenue growth and disclosed security-risk exposure across ~10 vendors over a 9-year window.")],
    [T("Engineered "), b("rate-limited, cached API ingestion"), T(" (NVD 50 req/30s with key, SEC 10 req/s with compliant User-Agent) and a layered DuckDB warehouse reproducible with a single make command.")],
    [T("Reconstructed reportable-segment revenue from XBRL and surfaced a real "), b("disclosure asymmetry"), T(" (AWS clean segment vs. Azure/GCP growth-% only), treating segment-tag coverage as a first-class data-quality problem.")],
    [T("Attributed 10k+ CVEs to vendors via "), b("CPE matching"), T(", joined to CISA KEV to compute a per-vendor actively-exploited rate and publication-to-exploitation lag, and tested (Spearman) the growth-vs-risk hypothesis.")],
    [T("Shipped a "), b("Streamlit"), T(" vendor scorecard plus pandera checks, pytest, GitHub Actions CI, and a documented licensing/limitations section per source.")],
  ],
  risks: [
    "Cloud segment asymmetry — do NOT fabricate Azure/GCP dollar revenue; model the gap with an is_disclosed flag.",
    "CPE-based vendor attribution is imperfect — per-vendor CVE counts are estimates; validate on a sample and report attribution error.",
    "XBRL segment tags are not standardized — you may need to parse the 10-K segment note for some vendors.",
    "Market-share data is paywalled (Synergy/Canalys/Gartner/Statista) — use public press-release headlines as context only, never as a dataset.",
    "Keep scope to ~10 vendors — expanding the CPE/CIK crosswalk balloons the entity-resolution effort.",
  ],
});

/* Master dataset reference */
children.push(H1("Master Dataset Reference", { pageBreak: true }));
children.push(P([T("Every source was verified free and accessible. "), b("Open"), T(" = no account; "), b("free key"), T(" = free, instant registration.")]));
children.push(H3("Fully open (no account)"));
children.push(table(["Dataset", "Used by", "Notes"], [
  ["SEC EDGAR XBRL", "Luxury, F500, Cloud", "User-Agent: name email header required; 10 req/s; US filers only"],
  ["NVD CVE API 2.0", "Cloud", "Free key optional but recommended (5 → 50 req/30s)"],
  ["CISA KEV catalog", "Cloud", "No key, no rate limit; GitHub mirror CC0"],
  ["Our World in Data — COVID", "Post-COVID", "Direct CSV; frozen 19-Aug-2024"],
  ["Damodaran NYU Stern", "Luxury, F500", "Direct .xls; URLs overwritten each January — pin file + date"],
  ["Wikipedia (largest US cos.)", "Fortune 500", "pandas.read_html; ~top 100 only"],
  ["Stack Overflow Survey", "Cloud", "ODbL; columns change yearly"],
  ["World Bank Open Data API", "Luxury", "No key; paginated"],
  ["Bain × Altagamma", "Luxury", "Free press releases only (full decks gated)"],
  ["yfinance (Yahoo Finance)", "All four", "No key; fragile (HTTP 429) — fetch once, cache to Parquet"],
], [2800, 1900, 4660]));
children.push(spacer(120));
children.push(H3("Free but needs an instant free key"));
children.push(table(["Dataset", "Sign-up", "Limit"], [
  ["FRED (Federal Reserve)", "fredaccount.stlouisfed.org", "~120 req/min; use fredapi"],
  ["BEA GDP-by-Industry", "apps.bea.gov/api/signup", "DataSetName=GDPbyIndustry"],
  ["BLS Public Data API", "bls.gov/developers", "500 queries/day (many series also on FRED)"],
  ["Kaggle datasets", "kaggle.com + API token", "Prefer CC0/CC BY; pin slug + version"],
], [2800, 3200, 3360]));
children.push(spacer(120));
children.push(H3("Corrections found during verification"));
children.push(bullet([b("Stooq direct CSV"), T(" is now blocked by a JavaScript anti-bot wall → use yfinance / pandas-datareader and cache.")]));
children.push(bullet([b("Fortune 500 combined CSV"), T(" 404s → the cmusam/fortune500 repo stores per-year files; concatenate and pin a commit SHA.")]));
children.push(bullet([b("Financial Modeling Prep"), T(" free endpoints changed/limited → SEC EDGAR XBRL covers the same ground truth for free.")]));
children.push(H3("Paywalled — excluded (do not scrape)"));
children.push(P([T("Statista · Macrotrends (ToS forbids bots) · stockanalysis.com (no API) · full Gartner / Canalys / Synergy / IDC reports. Use SEC filings + free Bain/Altagamma headlines + revenue-mix / adoption proxies instead.")]));

/* Production playbook */
children.push(H1("Production Playbook & CV Guidance", { pageBreak: true }));
children.push(P([T("The four projects share one production skeleton, so the cost drops after the first. These are the signals that separate “engineer” from “notebook tinkerer.”")]));
children.push(H3("Repository structure"));
children.push(codeBlock([
  "project-name/",
  "  README.md                # pitch · problem · findings + screenshots · run steps",
  "  pyproject.toml  uv.lock  # deps + ruff/pytest config, pinned lockfile",
  "  Makefile                 # setup / data / build / test / lint / dashboard",
  "  .env.example             # documents env vars (NO secrets committed)",
  "  .github/workflows/ci.yml # ruff + pytest on push/PR  ->  green badge",
  "  config/config.yaml       # paths, date range, tickers, seed",
  "  data/  (git-ignored)     # raw/  staging/  mart/   (bronze / silver / gold)",
  "  sql/staging/  sql/mart/  # DuckDB SQL per layer",
  "  src/<pkg>/               # config ingest transform schemas warehouse viz pipeline",
  "  tests/test_transform.py  # pytest over pure transforms + a tiny fixture",
  "  dashboard/app.py         # Streamlit reading the mart layer",
]));
children.push(H3("Non-negotiables"));
[
  [b("Never commit data. "), T("Commit the download script + a tiny sample fixture so tests/CI run offline.")],
  [b("Layer explicitly: "), T("raw (immutable) → staging (cleaned/typed Parquet) → mart (analysis-ready). Name folders this way.")],
  [b("Use SQL and pandas: "), T("heavy joins/aggregations in DuckDB SQL; light reshaping in pandas.")],
  [b("Pure transform functions "), T("(DataFrame in → DataFrame out, no I/O) so they are unit-testable.")],
  [b("pandera validation between layers "), T("— bad data fails loudly, and “data quality is tested” becomes literally true.")],
  [b("README is the product: "), T("pitch → problem → data → approach → findings with 2–3 numbers → screenshots → reproduce. A recruiter must get it in 30 seconds.")],
  [b("Ship a live dashboard. "), T("A Streamlit Community Cloud link at the top of the README beats any amount of text.")],
].forEach((r) => children.push(bullet(r)));
children.push(H3("How to phrase these on a finance CV"));
[
  [b("Formula: "), T("[Action verb] + [what you built] + [tech] + [quantified result]. Title each project like a role: “Post-COVID Sector Rotation — Python, DuckDB, Streamlit (personal project).”")],
  [b("Quantify everything "), T("(rows, runtime, %, counts) — only ~30% of analyst resumes carry numbers; it is the biggest screen-out gap. Qualify estimates with “~”.")],
  [b("Spell out the stack for ATS: "), T("Python (pandas, NumPy, matplotlib), SQL (DuckDB), Parquet, pandera, pytest, GitHub Actions, Streamlit.")],
  [b("Honest finance keywords: "), T("financial modeling, time-series, ETL, data validation, backtesting, reconciliation, comps/valuation.")],
  [b("Link both "), T("the GitHub repo and the live dashboard directly on the CV.")],
].forEach((r) => children.push(bullet(r)));
children.push(spacer(80));
children.push(callout([b("Avoid: "), T("committing raw data · one giant messy notebook with hardcoded /Users/you/ paths · a README that never states the finding · toy datasets (Titanic/Iris) · no tests or CI · no quantified results · stopping at analysis with no deployed artifact · 15 shallow repos instead of 3–5 deep ones.")], "FBEEDD", GOLD));

/* ---------- assemble ---------- */
const doc = new Document({
  creator: "Finance Portfolio Brief",
  title: "Finance Data-Analysis Portfolio",
  styles: {
    default: { document: { run: { font: "Arial", size: 22, color: BODY } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, color: NAVY, font: "Arial" }, paragraph: { spacing: { before: 300, after: 60 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 25, bold: true, color: NAVY, font: "Arial" }, paragraph: { spacing: { before: 220, after: 40 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 21, bold: true, color: STEEL, font: "Arial" }, paragraph: { spacing: { before: 160, after: 30 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { run: { color: GOLD }, paragraph: { indent: { left: 460, hanging: 260 } } } }] },
      ...["order", "qcovid", "qlux", "qf500", "qcloud", "mcovid", "mlux", "mf500", "mcloud"].map((ref) => ({
        reference: ref,
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { run: { color: NAVY, bold: true }, paragraph: { indent: { left: 460, hanging: 300 } } } }],
      })),
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: {
      default: new Footer({ children: [new Paragraph({
        tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 6 } },
        children: [
          new TextRun({ text: "Finance Data-Analysis Portfolio", font: "Arial", size: 16, color: MUTE }),
          new TextRun({ text: "\t", font: "Arial", size: 16 }),
          new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: MUTE }),
        ],
      })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("/Users/ahmedrezatausif/varistyDump/asdf/finance-portfolio-projects/Finance-Portfolio-Brief.docx", buf);
  console.log("DOCX written:", buf.length, "bytes");
});
