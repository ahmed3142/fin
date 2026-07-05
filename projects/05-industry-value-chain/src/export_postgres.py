"""Export the DuckDB warehouse to Supabase-ready Postgres artifacts:
  sql/postgres/01_schema.sql   CREATE TABLE dims/facts (types, PK/FK, comments)
  sql/postgres/02_seed.sql     INSERT ... the data
  sql/postgres/03_mart_view.sql  CREATE VIEW mart_industry_wide
  sql/postgres/04_rls.sql      enable RLS + public-read policy per table
  sql/postgres/csv/<table>.csv one CSV per table (Table-editor import path)
No database connection required — everything is emitted as text.
"""
from __future__ import annotations

import os

import duckdb

from . import config

DIM_ORDER = ["dim_region", "dim_vintage", "dim_industry", "map_industry_alias"]

PG_TYPE = {
    "BOOLEAN": "boolean", "TINYINT": "smallint", "SMALLINT": "smallint",
    "INTEGER": "integer", "BIGINT": "bigint", "HUGEINT": "numeric",
    "FLOAT": "double precision", "DOUBLE": "double precision", "REAL": "double precision",
    "DECIMAL": "numeric", "VARCHAR": "text", "DATE": "date", "TIMESTAMP": "timestamp",
}

PK = {
    "dim_region": ["region_id"], "dim_vintage": ["vintage_id"],
    "dim_industry": ["industry_id"], "map_industry_alias": ["industry_name_raw"],
    "fact_industry_firmcount": ["industry_id", "vintage_id", "region_id", "dataset_code"],
}
FACT_PK = ["industry_id", "vintage_id", "region_id"]

COMMENTS = {
    "dim_industry": "Conformed industry dimension (Damodaran ~94-industry US taxonomy). "
                    "is_financial flags banks/insurers whose margins are non-comparable.",
    "dim_vintage": "Annual Damodaran refresh. asc842_lease_break / tcja174_rnd_break flag "
                   "methodology breaks (2019 leases, 2022 R&D) that make adjusted columns "
                   "non-comparable across vintages.",
    "map_industry_alias": "Entity-resolution crosswalk for the dirty free-text join key "
                          "(e.g. the real 'Heathcare' misspelling).",
    "fact_financing_flows": "Financing flows by industry. NOTE net_equity_change_usd = "
                            "equity_issuance - buybacks (dividends NOT subtracted), verified "
                            "against the data despite the source file's own note.",
    "fact_margins": "Operating & net margins. pretax_lease_rnd_adj_operating_margin is "
                    "Damodaran's own adjusted figure (uses his capitalized-R&D estimate).",
    "fact_rnd": "R&D. rnd_capitalized_usd_m and cap_rnd_pct_invested_capital are Damodaran "
                "ESTIMATES (assumed amortizable life), not reported GAAP.",
}


def _tables(con) -> list[str]:
    dims = [t for t in DIM_ORDER if con.execute(
        f"SELECT count(*) FROM information_schema.tables WHERE table_name='{t}'").fetchone()[0]]
    facts = sorted(r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'fact_%'").fetchall())
    return dims + facts


def _columns(con, t: str) -> list[tuple[str, str]]:
    return [(r[0], r[1]) for r in con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        f"WHERE table_name='{t}' ORDER BY ordinal_position").fetchall()]


def _pg_type(duck_type: str) -> str:
    base = duck_type.split("(")[0].upper()
    return PG_TYPE.get(base, "numeric")


def _lit(v, pg_type: str) -> str:
    if v is None:
        return "NULL"
    if pg_type == "boolean":
        return "TRUE" if v else "FALSE"
    if pg_type in ("integer", "bigint", "smallint", "numeric", "double precision"):
        try:
            if v != v:  # NaN
                return "NULL"
        except TypeError:
            pass
        return str(v)
    s = str(v).replace("'", "''")
    return f"'{s}'"


def schema_sql(con, tables: list[str]) -> str:
    out = ["-- Project 5 — Industry Value-Chain :: Postgres schema (Supabase-ready)",
           "-- Generated from the DuckDB warehouse. Run this first.\n",
           "create schema if not exists industry;\nset search_path = industry, public;\n"]
    for t in tables:
        cols = _columns(con, t)
        defs = []
        for name, dt in cols:
            defs.append(f"  {name} {_pg_type(dt)}")
        pk = PK.get(t, FACT_PK)
        pk = [c for c in pk if c in {c0 for c0, _ in cols}]
        if pk:
            defs.append(f"  primary key ({', '.join(pk)})")
        out.append(f"create table if not exists industry.{t} (\n" + ",\n".join(defs) + "\n);")
        if t in COMMENTS:
            out.append(f"comment on table industry.{t} is '{COMMENTS[t].replace(chr(39), chr(39)*2)}';")
        out.append("")
    # foreign keys (added after all tables exist)
    out.append("-- foreign keys")
    for t in tables:
        colnames = {c for c, _ in _columns(con, t)}
        if t.startswith("fact_") or t == "map_industry_alias":
            if "industry_id" in colnames:
                out.append(f"alter table industry.{t} add constraint {t}_industry_fk "
                           f"foreign key (industry_id) references industry.dim_industry(industry_id);")
        if t.startswith("fact_"):
            if "vintage_id" in colnames:
                out.append(f"alter table industry.{t} add constraint {t}_vintage_fk "
                           f"foreign key (vintage_id) references industry.dim_vintage(vintage_id);")
            if "region_id" in colnames:
                out.append(f"alter table industry.{t} add constraint {t}_region_fk "
                           f"foreign key (region_id) references industry.dim_region(region_id);")
    return "\n".join(out) + "\n"


def seed_sql(con, tables: list[str]) -> str:
    out = ["-- Project 5 — seed data. Run after 01_schema.sql.",
           "set search_path = industry, public;\n"]
    for t in tables:
        cols = _columns(con, t)
        names = [c for c, _ in cols]
        types = {c: _pg_type(dt) for c, dt in cols}
        rows = con.execute(f"SELECT {', '.join(names)} FROM {t}").fetchall()
        if not rows:
            continue
        out.append(f"-- {t} ({len(rows)} rows)")
        vals = []
        for r in rows:
            vals.append("(" + ", ".join(_lit(v, types[c]) for v, c in zip(r, names)) + ")")
        out.append(f"insert into industry.{t} ({', '.join(names)}) values")
        out.append(",\n".join(vals) + ";\n")
    return "\n".join(out) + "\n"


def mart_view_sql(con) -> str:
    facts = sorted(r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'fact_%' "
        "AND table_name <> 'fact_industry_firmcount'").fetchall())
    from .warehouse import PREFIX
    selects = ["  i.industry_id", "  i.industry_name", "  i.sector_group", "  i.is_financial"]
    joins = []
    for f in facts:
        p = PREFIX.get(f, f)
        cols = [c for c, _ in _columns(con, f)
                if c not in ("industry_id", "vintage_id", "region_id")]
        a = f"f_{p}"
        for c in cols:
            selects.append(f"  {a}.{c} as {p}_{c}")
        joins.append(f"left join industry.{f} {a} on {a}.industry_id = i.industry_id")
    return ("-- Project 5 — wide analytical mart. Run after seed.\n"
            "set search_path = industry, public;\n\n"
            "create or replace view industry.mart_industry_wide as\nselect\n"
            + ",\n".join(selects) + "\nfrom industry.dim_industry i\n" + "\n".join(joins) + ";\n")


def rls_sql(con, tables: list[str]) -> str:
    out = ["-- Project 5 — Row Level Security: public read-only (Supabase web/REST needs this).",
           "set search_path = industry, public;\n"]
    for t in tables:
        out.append(f"alter table industry.{t} enable row level security;")
        out.append(f'create policy "public read {t}" on industry.{t} for select using (true);')
    out.append("\n-- expose the schema to the Supabase API (Dashboard > Settings > API > Exposed schemas)")
    out.append("grant usage on schema industry to anon, authenticated;")
    out.append("grant select on all tables in schema industry to anon, authenticated;")
    return "\n".join(out) + "\n"


def run() -> None:
    os.makedirs(config.SQL_OUT, exist_ok=True)
    csv_dir = os.path.join(config.SQL_OUT, "csv")
    os.makedirs(csv_dir, exist_ok=True)
    con = duckdb.connect(config.WAREHOUSE, read_only=True)
    tables = _tables(con)

    def write(name, text):
        with open(os.path.join(config.SQL_OUT, name), "w") as fh:
            fh.write(text)
        print(f"  wrote {name} ({len(text)} B)")

    write("01_schema.sql", schema_sql(con, tables))
    write("02_seed.sql", seed_sql(con, tables))
    write("03_mart_view.sql", mart_view_sql(con))
    write("04_rls.sql", rls_sql(con, tables))
    for t in tables:
        con.execute(f"COPY (SELECT * FROM {t}) TO '{os.path.join(csv_dir, t + '.csv')}' "
                    f"(HEADER, DELIMITER ',')")
    print(f"  wrote {len(tables)} CSVs to {csv_dir}")
    con.close()
    print(f"\nPostgres artifacts in {config.SQL_OUT}")


if __name__ == "__main__":
    run()
