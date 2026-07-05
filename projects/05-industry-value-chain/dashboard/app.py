"""Minimal Streamlit view of the thesis — argues ONE claim, not a metric browser.
Run: streamlit run dashboard/app.py   (needs `pip install streamlit`, reads warehouse.duckdb)
"""
import os
import sys

import duckdb
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config  # noqa: E402

st.set_page_config(page_title="Industry Margin-Distortion", layout="wide")
st.title("Reported margins mislead cross-industry screening")
st.caption("Damodaran industry aggregates, Jan-2026 (TTM ~Q3 2025). Value-weighted, "
           "n≤94 — association, not causation.")

con = duckdb.connect(config.WAREHOUSE, read_only=True)
df = con.execute("""
    select industry_name, sector_group,
           mgn_pretax_operating_margin              as reported,
           mgn_pretax_lease_rnd_adj_operating_margin as adjusted,
           mgn_rnd_sales as rnd_sales, ps_ev_sales as ev_sales
    from mart_industry_wide where not is_financial
""").df()
df["gap"] = df["adjusted"] - df["reported"]

st.subheader("Where the R&D/lease adjustment moves margins most")
st.dataframe(df.reindex(df["gap"].abs().sort_values(ascending=False).index)
             [["industry_name", "reported", "adjusted", "gap", "rnd_sales"]].head(15),
             use_container_width=True)

st.subheader("EV/Sales vs reported and adjusted margin")
c1, c2 = st.columns(2)
c1.scatter_chart(df.dropna(subset=["ev_sales"]), x="reported", y="ev_sales")
c2.scatter_chart(df.dropna(subset=["ev_sales"]), x="adjusted", y="ev_sales")
st.info("EV/Sales tracks the adjusted margin slightly better (R² 0.425 vs 0.406) — "
        "the market looks partly through R&D expensing.")
