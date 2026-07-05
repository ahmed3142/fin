"""Parse: turn a raw Damodaran .xls/.xlsx into a tidy DataFrame keyed on the
raw industry name, with canonical columns resolved via config matchers.

Handles the two header layouts we verified:
  * finflows_timeseries.xlsx  -> header on row 0, data on sheet 'Data'
  * fundgrEB.xls              -> 7 metadata rows, header on row 7, sheet 'Industry Averages'
by dynamically searching for the 'Industry Name' header row on whichever sheet
carries it. Text sentinels ('NA', '#DIV/0!', 'NM', ...) become NULL; ratio
columns are normalized to fractions; 'Total Market' aggregate rows are dropped.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from . import config

NULL_TOKENS = {"", "na", "n/a", "nm", "#div/0!", "#n/a", "#value!", "#ref!", "nan", "none"}


def find_raw_path(ds: dict) -> str | None:
    if ds.get("local"):
        p = os.path.join(config.RAW_DIR, ds["local"])
        return p if os.path.exists(p) else None
    # match "<code>__*.xls*" in the raw folder
    prefix = f"{ds['code']}__"
    cands = [f for f in os.listdir(config.RAW_DIR) if f.startswith(prefix)]
    if not cands:
        return None
    return os.path.join(config.RAW_DIR, sorted(cands)[0])


def _clean_cell(v):
    if isinstance(v, str):
        s = v.strip()
        if s.lower() in NULL_TOKENS:
            return np.nan
        return s
    return v


def _load_headered(path: str) -> pd.DataFrame:
    """Read every sheet header-less, pick the one with an 'Industry Name'
    header row, and return a DataFrame with that row promoted to columns."""
    sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=object)
    for _, raw in sheets.items():
        if raw.empty:
            continue
        hdr_idx = None
        for i in range(min(15, len(raw))):
            row = [str(x).strip().lower() for x in raw.iloc[i].tolist()]
            if "industry name" in row:
                hdr_idx = i
                break
        if hdr_idx is None:
            continue
        cols = [str(x).strip() if x is not None else "" for x in raw.iloc[hdr_idx].tolist()]
        # canonicalize the join-key column name (handles casing/spacing drift)
        cols = ["Industry Name" if str(c).strip().lower() == "industry name" else c for c in cols]
        body = raw.iloc[hdr_idx + 1:].copy()
        body.columns = cols
        body = body.map(_clean_cell)  # DataFrame.map (pandas >=2.1; applymap removed in 3.0)
        # drop fully-empty columns and any column with a blank header
        body = body.loc[:, [c for c in body.columns if str(c) and str(c).lower() != "nan"]]
        if "Industry Name" not in body.columns:
            continue  # not the data sheet; keep searching
        # de-duplicate any repeated headers, keep first
        body = body.loc[:, ~pd.Index(body.columns).duplicated()]
        # keep only rows that actually have an industry name
        body = body[body["Industry Name"].notna()]
        return body.reset_index(drop=True)
    raise ValueError(f"No 'Industry Name' header row found in {os.path.basename(path)}")


def _strip_total_rows(df: pd.DataFrame) -> pd.DataFrame:
    name = df["Industry Name"].astype(str).str.strip().str.lower()
    mask = np.zeros(len(df), dtype=bool)
    for marker in config.TOTAL_ROW_MARKERS:
        mask |= name.str.startswith(marker)
    return df[~mask].reset_index(drop=True)


def _match_column(headers: list[str], m: dict) -> str | None:
    low = {h: h.lower() for h in headers}
    for h in headers:
        s = low[h]
        if all(tok in s for tok in m.get("all", [])) \
           and (not m.get("any") or any(tok in s for tok in m["any"])) \
           and not any(tok in s for tok in m.get("none", [])):
            return h
    return None


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _normalize_ratio(series: pd.Series) -> tuple[pd.Series, str]:
    """Store ratios as fractions. If the column looks like 0-100 (median |x|>1.5)
    divide by 100. Returns (series, scale_applied)."""
    s = _to_numeric(series)
    nonnull = s.dropna().abs()
    if len(nonnull) and float(nonnull.median()) > 1.5:
        return s / 100.0, "div100"
    return s, "asis"


def parse_dataset(ds: dict) -> pd.DataFrame | None:
    """Return a tidy frame: industry_name_raw + resolved canonical columns."""
    path = find_raw_path(ds)
    if path is None:
        return None
    df = _strip_total_rows(_load_headered(path))
    headers = list(df.columns)
    out = pd.DataFrame({"industry_name_raw": df["Industry Name"].astype(str).str.strip()})
    for m in ds.get("columns", []):
        src = _match_column(headers, m)
        canon = m["canonical"]
        if src is None:
            out[canon] = np.nan
            continue
        col = df[src]
        if m["type"] == "count":
            out[canon] = _to_numeric(col).round().astype("Int64")
        elif m["type"] in ("money", "multiple"):
            # multiples (EV/Sales, P/E, PEG) are ratios but NOT percentages -> no scaling
            out[canon] = _to_numeric(col)
        elif m["type"] == "ratio":
            out[canon], _ = _normalize_ratio(col)
        else:
            out[canon] = col
    return out


def industry_names(ds: dict) -> list[str] | None:
    """Just the cleaned industry-name list (Total rows stripped)."""
    path = find_raw_path(ds)
    if path is None:
        return None
    df = _strip_total_rows(_load_headered(path))
    return df["Industry Name"].astype(str).str.strip().tolist()
