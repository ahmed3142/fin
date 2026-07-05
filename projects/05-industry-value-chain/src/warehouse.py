"""Build the DuckDB star schema: conformed dim_industry + dim_vintage +
dim_region + map_industry_alias, one fact per Damodaran dataset, a firm-count
reconciliation fact, and the wide analytical mart. Runs the quality gates.
"""
from __future__ import annotations

import csv
import os

import duckdb
import pandas as pd

from . import config, parse, quality
from .crosswalk import Crosswalk, is_financial, normalize, sector_group_of

# fact table -> mart column prefix
PREFIX = {
    "fact_margins": "mgn", "fact_rnd": "rnd", "fact_financing_flows": "ff",
    "fact_multiples_ps": "ps", "fact_multiples_pe": "pe",
    "fact_dividends_fcfe": "div", "fact_growth_fundamental_eb": "gr",
}


def _reference_names() -> list[str]:
    for code in ("finflows_ts", "margins", "growth_eb", "finflows"):
        names = parse.industry_names(config.DATASETS_BY_CODE[code])
        if names:
            return names
    raise SystemExit("No raw files available to build the industry reference. Run `make ingest` first.")


def _parse_fact(ds: dict) -> pd.DataFrame | None:
    df = parse.parse_dataset(ds)
    if df is None and ds["code"] == "finflows":
        # fall back to the local tidy timeseries file, reusing finflows columns
        synth = dict(ds)
        synth["local"] = config.DATASETS_BY_CODE["finflows_ts"]["local"]
        synth["page"] = None
        df = parse.parse_dataset(synth)
    return df


def build() -> None:
    os.makedirs(config.RAW_DIR, exist_ok=True)
    xwalk = Crosswalk.build(_reference_names())

    # ---- parse every fact dataset, resolve industry_id, collect unresolved ----
    facts: dict[str, pd.DataFrame] = {}
    firmcounts = []
    for ds in config.DATASETS:
        if not ds.get("fact"):
            continue
        df = _parse_fact(ds)
        if df is None:
            print(f"  [skip ] {ds['fact']:28s} (no raw file for {ds['code']})")
            continue
        df = df.copy()
        df.insert(0, "industry_id", df["industry_name_raw"].map(xwalk.resolve))
        facts[ds["fact"]] = df
        if "num_firms" in df.columns:
            fc = df[["industry_id", "num_firms"]].copy()
            fc["dataset_code"] = ds["code"]
            firmcounts.append(fc)
        print(f"  [parse] {ds['fact']:28s} {len(df):>3d} rows from {ds['code']}")

    xwalk.assert_resolved()  # fail loud if any name across any file didn't resolve

    # ---- dimensions ----
    df_region = pd.DataFrame([{"region_id": 1, "region_code": "US", "region_name": "United States"}])
    df_vintage = pd.DataFrame([{
        "vintage_id": 1, "vintage_year": config.VINTAGE_YEAR, "data_asof_date": "2026-01-05",
        "ttm_through": "2025-Q3", "asc842_lease_break": True, "tcja174_rnd_break": True,
    }])
    df_industry = pd.DataFrame([
        {"industry_id": iid, "industry_name": name, "sector_group": sector_group_of(name),
         "is_financial": is_financial(name), "is_total_market_rollup": False, "region_id": 1}
        for iid, name in xwalk.industries
    ])
    # alias map rows (resolved to id)
    alias_rows = []
    with open(config.ALIASES_CSV, newline="") as fh:
        for row in csv.DictReader(fh):
            iid = xwalk.resolve(row["canonical_name"])
            alias_rows.append({
                "industry_name_raw": row["raw_name"], "canonical_name": row["canonical_name"],
                "industry_id": iid, "match_method": row.get("match_method", "manual"),
                "confidence": float(row.get("confidence", 1.0)),
            })
    df_alias = pd.DataFrame(alias_rows)
    df_firmcount = (pd.concat(firmcounts, ignore_index=True) if firmcounts
                    else pd.DataFrame(columns=["industry_id", "num_firms", "dataset_code"]))
    df_firmcount["vintage_id"] = 1
    df_firmcount["region_id"] = 1

    # ---- write DuckDB ----
    if os.path.exists(config.WAREHOUSE):
        os.remove(config.WAREHOUSE)
    con = duckdb.connect(config.WAREHOUSE)

    def load(name: str, df: pd.DataFrame):
        con.register("_df", df)
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM _df")
        con.unregister("_df")

    load("dim_region", df_region)
    load("dim_vintage", df_vintage)
    load("dim_industry", df_industry)
    load("map_industry_alias", df_alias)
    for fact_name, df in facts.items():
        cols = [c for c in df.columns if c != "industry_name_raw"]
        d = df[cols].copy()
        d["vintage_id"] = 1
        d["region_id"] = 1
        load(fact_name, d)
    load("fact_industry_firmcount", df_firmcount)

    _build_mart(con, list(facts.keys()))
    con.close()

    # ---- quality gates ----
    print("\nQuality gates:")
    quality.run_all(config.WAREHOUSE, expected_industries=94)
    print(f"\nWarehouse built: {config.WAREHOUSE}")
    print(f"  dims: dim_industry({len(df_industry)}), dim_vintage(1), dim_region(1), "
          f"map_industry_alias({len(df_alias)})")
    print(f"  facts: {', '.join(facts.keys())}")


def _build_mart(con: duckdb.DuckDBPyConnection, fact_names: list[str]) -> None:
    selects = ["i.industry_id", "i.industry_name", "i.sector_group", "i.is_financial"]
    joins = []
    for fact in fact_names:
        p = PREFIX.get(fact, fact)
        cols = [r[0] for r in con.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = '{fact}' "
            f"AND column_name NOT IN ('industry_id','vintage_id','region_id')").fetchall()]
        alias = f"f_{p}"
        for c in cols:
            selects.append(f"{alias}.{c} AS {p}_{c}")
        joins.append(f"LEFT JOIN {fact} {alias} ON {alias}.industry_id = i.industry_id")
    sql = ("CREATE VIEW mart_industry_wide AS\nSELECT\n  "
           + ",\n  ".join(selects) + "\nFROM dim_industry i\n" + "\n".join(joins))
    con.execute(sql)


if __name__ == "__main__":
    build()
