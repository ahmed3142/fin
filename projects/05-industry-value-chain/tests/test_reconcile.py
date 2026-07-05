"""Warehouse quality-gate + anti-circularity tests (require a built warehouse)."""
import os

import duckdb
import pytest

from src import config, quality

pytestmark = pytest.mark.skipif(
    not os.path.exists(config.WAREHOUSE), reason="run `make build` first")


def test_hard_gates_pass():
    quality.run_all(config.WAREHOUSE, expected_industries=94)  # raises on failure


def test_firmcount_anchor_is_5994():
    con = duckdb.connect(config.WAREHOUSE, read_only=True)
    anchor = con.execute("SELECT sum(num_firms) FROM fact_industry_firmcount "
                         "WHERE dataset_code='margins'").fetchone()[0]
    con.close()
    assert abs(int(anchor) - 5994) <= 500


def test_referential_integrity_and_no_totals():
    con = duckdb.connect(config.WAREHOUSE, read_only=True)
    try:
        quality.gate_no_total_rows(con)
        quality.gate_referential_integrity(con)
    finally:
        con.close()


def test_anti_circularity_lint_blocks_the_identity():
    # pairing capitalized R&D with an R&D-adjusted margin re-derives Damodaran's identity
    with pytest.raises(ValueError, match="Anti-circularity"):
        quality.anti_circularity_lint("cap_rnd_pct_invested_capital",
                                      "pretax_lease_rnd_adj_operating_margin")
    # reported margin vs a market outcome is allowed
    quality.anti_circularity_lint("mgn_pretax_operating_margin", "ps_ev_sales")
