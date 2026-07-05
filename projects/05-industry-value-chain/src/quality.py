"""Quality gates over the built warehouse. Hard gates raise; soft gates report.

Hard   : industry count == 94, no 'Total Market' rows survived, referential
         integrity (every fact.industry_id resolves to dim_industry).
Soft    : firm-count reconciliation across files (+ the margins ~5,994 anchor),
         denominator sanity on ratio columns.
Static : anti-circularity lint — refuse to pair a capitalized-R&D column with an
         R&D-adjusted margin column (that relationship is a Damodaran identity).
"""
from __future__ import annotations

import duckdb

CAP_RND_COLS = {"rnd_cap_rnd_pct_invested_capital", "cap_rnd_pct_invested_capital",
                "rnd_capitalized_usd_m", "rnd_rnd_capitalized_usd_m"}
RND_ADJ_MARGIN_COLS = {"mgn_pretax_lease_rnd_adj_operating_margin",
                       "pretax_lease_rnd_adj_operating_margin", "mgn_ebitdarnd_sales",
                       "ebitdarnd_sales"}


def _facts(con) -> list[str]:
    return [r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name LIKE 'fact_%'").fetchall()]


def gate_industry_count(con, expected: int = 94) -> None:
    n = con.execute("SELECT count(*) FROM dim_industry").fetchone()[0]
    assert n == expected, f"industry count {n} != expected {expected}"
    print(f"  [PASS] industry count == {expected}")


def gate_no_total_rows(con) -> None:
    n = con.execute("SELECT count(*) FROM dim_industry "
                    "WHERE lower(industry_name) LIKE '%total market%'").fetchone()[0]
    assert n == 0, f"{n} 'Total Market' rows leaked into dim_industry"
    print("  [PASS] no 'Total Market' rows in dim_industry")


def gate_referential_integrity(con) -> None:
    bad = []
    for f in _facts(con):
        n = con.execute(
            f"SELECT count(*) FROM {f} x LEFT JOIN dim_industry i USING (industry_id) "
            f"WHERE i.industry_id IS NULL").fetchone()[0]
        if n:
            bad.append(f"{f}:{n}")
    assert not bad, f"referential-integrity violations: {bad}"
    print(f"  [PASS] referential integrity across {len(_facts(con))} facts")


def gate_firmcount_reconcile(con) -> None:
    rows = con.execute(
        "SELECT dataset_code, sum(num_firms) FROM fact_industry_firmcount "
        "GROUP BY dataset_code ORDER BY dataset_code").fetchall()
    parts = ", ".join(f"{c}={int(s) if s is not None else 'NA'}" for c, s in rows)
    print(f"  [info] firm totals by file: {parts}")
    anchor = con.execute(
        "SELECT sum(num_firms) FROM fact_industry_firmcount WHERE dataset_code='margins'"
    ).fetchone()[0]
    if anchor:
        flag = "~5,994 expected" if abs(int(anchor) - 5994) <= 500 else "OUTSIDE expected band!"
        print(f"  [info] margins firm-count anchor = {int(anchor)} ({flag})")


def gate_denominator_sanity(con) -> None:
    # ratio columns should mostly sit within [-5, 5] as fractions; report outliers
    cols = con.execute(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_name LIKE 'fact_%' AND (column_name LIKE '%pct%' OR column_name LIKE '%margin%' "
        "OR column_name LIKE '%_sales' OR column_name LIKE '%rate%')").fetchall()
    flagged = 0
    for t, c in cols:
        n = con.execute(f"SELECT count(*) FROM {t} WHERE abs({c}) > 5").fetchone()[0]
        if n:
            flagged += 1
    print(f"  [info] denominator sanity: {flagged} ratio column(s) have |value|>5 outliers (winsorize in analysis)")


def anti_circularity_lint(x_col: str, y_col: str) -> None:
    """Refuse capitalized-R&D vs R&D-adjusted-margin pairings (Damodaran identity)."""
    if x_col in CAP_RND_COLS and y_col in RND_ADJ_MARGIN_COLS or \
       y_col in CAP_RND_COLS and x_col in RND_ADJ_MARGIN_COLS:
        raise ValueError(
            f"Anti-circularity lint: pairing {x_col!r} with {y_col!r} re-derives a Damodaran "
            f"accounting identity (capitalized R&D feeds the R&D-adjusted margin). Use a REPORTED "
            f"margin as the input, or a market outcome (multiples) as the target.")


def run_all(warehouse_path: str, expected_industries: int = 94) -> None:
    con = duckdb.connect(warehouse_path, read_only=True)
    try:
        gate_industry_count(con, expected_industries)
        gate_no_total_rows(con)
        gate_referential_integrity(con)
        gate_firmcount_reconcile(con)
        gate_denominator_sanity(con)
    finally:
        con.close()
