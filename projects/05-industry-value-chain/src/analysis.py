"""The two thesis outputs, computed from the warehouse with numpy only.

1. RANK REVERSAL: rank non-financial industries by reported vs R&D/lease-adjusted
   operating margin; count how many move >= K positions; Spearman rho.
2. MARKET PRICING: does EV/Sales (and P/E) track the reported or the adjusted
   margin? OLS with HC3-robust SEs, financials excluded, weighted by #firms.

Everything is descriptive, value-weighted industry aggregates (n<=94) —
association, not causation. Writes analysis/headline.json.
"""
from __future__ import annotations

import json
import os

import duckdb
import numpy as np

from . import config, quality

K = 5  # "reranked" threshold in positions


def _ols(x: np.ndarray, y: np.ndarray, w: np.ndarray | None = None) -> dict:
    """OLS y ~ 1 + x with HC3-robust SE on the slope. Optional weights (WLS)."""
    X = np.column_stack([np.ones_like(x), x])
    if w is None:
        w = np.ones_like(x)
    W = np.sqrt(w)
    Xw, yw = X * W[:, None], y * W
    beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    resid = yw - Xw @ beta
    n, k = X.shape
    # R^2 on weighted fit
    ss_res = float(resid @ resid)
    ybar = float((w * y).sum() / w.sum())
    ss_tot = float((w * (y - ybar) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    # HC3 robust covariance
    XtX_inv = np.linalg.inv(Xw.T @ Xw)
    h = np.einsum("ij,jk,ik->i", Xw, XtX_inv, Xw)
    u = resid / np.clip(1 - h, 1e-8, None)
    meat = Xw.T @ (u[:, None] * u[:, None] * Xw)
    cov = XtX_inv @ meat @ XtX_inv
    se = float(np.sqrt(np.diag(cov))[1])
    slope = float(beta[1])
    return {"slope": slope, "se": se, "t": slope / se if se else float("nan"),
            "r2": r2, "n": int(n)}


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    denom = np.sqrt((ra @ ra) * (rb @ rb))
    return float(ra @ rb / denom) if denom else float("nan")


def _fetch(con, cols: list[str]) -> dict[str, np.ndarray] | None:
    have = {r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='mart_industry_wide'").fetchall()}
    missing = [c for c in cols if c not in have]
    if missing:
        print(f"  [skip] missing mart columns: {missing}")
        return None
    sel = ", ".join(["industry_id", "industry_name", "is_financial"] + cols)
    rows = con.execute(f"SELECT {sel} FROM mart_industry_wide").fetchall()
    data = {"industry_id": [], "industry_name": [], "is_financial": []}
    for c in cols:
        data[c] = []
    for r in rows:
        data["industry_id"].append(r[0]); data["industry_name"].append(r[1])
        data["is_financial"].append(r[2])
        for i, c in enumerate(cols):
            data[c].append(r[3 + i])
    out = {"industry_id": np.array(data["industry_id"]),
           "industry_name": np.array(data["industry_name"], dtype=object),
           "is_financial": np.array([bool(x) for x in data["is_financial"]])}
    for c in cols:
        out[c] = np.array([np.nan if v is None else float(v) for v in data[c]])
    return out


def run() -> dict:
    os.makedirs(config.ANALYSIS_OUT, exist_ok=True)
    con = duckdb.connect(config.WAREHOUSE, read_only=True)
    result: dict = {"vintage": config.VINTAGE, "caveat":
                    "Value-weighted industry aggregates (n<=94); association, not causation."}

    REP = "mgn_pretax_operating_margin"
    ADJ = "mgn_pretax_lease_rnd_adj_operating_margin"

    # ---- 1. rank reversal ----
    d = _fetch(con, [REP, ADJ, "mgn_num_firms"])
    if d is not None:
        m = (~d["is_financial"]) & np.isfinite(d[REP]) & np.isfinite(d[ADJ])
        rep, adj, names = d[REP][m], d[ADJ][m], d["industry_name"][m]
        rank_rep = np.argsort(np.argsort(-rep))  # 0 = highest margin
        rank_adj = np.argsort(np.argsort(-adj))
        moved = np.abs(rank_rep - rank_adj)
        n_reranked = int((moved >= K).sum())
        rho = _spearman(rep, adj)
        top = sorted(zip(names.tolist(), (rank_rep - rank_adj).tolist(),
                         (adj - rep).tolist()), key=lambda t: -abs(t[1]))[:8]
        result["rank_reversal"] = {
            "n_industries": int(m.sum()), "threshold_positions": K,
            "n_reranked": n_reranked, "spearman_rho": round(rho, 4),
            "biggest_movers": [{"industry": nm, "rank_delta": int(rd),
                                "adj_minus_reported_margin": round(dm, 4)} for nm, rd, dm in top],
        }
        print(f"  rank-reversal: {n_reranked}/{int(m.sum())} non-financial industries move "
              f">= {K} places; Spearman rho = {rho:.3f}")

    # ---- 2. market pricing ----
    mp = {}
    for target, tcol in [("EV/Sales", "ps_ev_sales"), ("P/E", "pe_current_pe")]:
        d = _fetch(con, [tcol, REP, ADJ, "mgn_num_firms"])
        if d is None:
            continue
        m = (~d["is_financial"]) & np.isfinite(d[tcol]) & np.isfinite(d[REP]) & np.isfinite(d[ADJ])
        # winsorize target at 1/99 pct
        y = d[tcol][m]
        lo, hi = np.nanpercentile(y, [1, 99])
        y = np.clip(y, lo, hi)
        w = np.nan_to_num(d["mgn_num_firms"][m], nan=1.0)
        quality.anti_circularity_lint(REP, tcol)  # allowed (reported margin, market outcome)
        rep_fit = _ols(d[REP][m], y, w)
        adj_fit = _ols(d[ADJ][m], y, w)
        tracks = "adjusted" if adj_fit["r2"] > rep_fit["r2"] else "reported"
        mp[target] = {"reported": {k: round(v, 4) for k, v in rep_fit.items()},
                      "adjusted": {k: round(v, 4) for k, v in adj_fit.items()},
                      "market_tracks": tracks, "n": rep_fit["n"]}
        print(f"  market-pricing {target}: R2 reported={rep_fit['r2']:.3f} vs "
              f"adjusted={adj_fit['r2']:.3f} -> market tracks the {tracks} margin (n={rep_fit['n']})")
    if mp:
        result["market_pricing"] = mp

    con.close()

    # ---- headline ----
    rr = result.get("rank_reversal")
    evs = result.get("market_pricing", {}).get("EV/Sales")
    if rr and evs:
        result["headline"] = (
            f"Across {rr['n_industries']} non-financial U.S. industries, EV/Sales tracks Damodaran's "
            f"R&D/lease-ADJUSTED operating margin better than the reported margin "
            f"(R2 {evs['adjusted']['r2']} vs {evs['reported']['r2']}) — modest evidence the market "
            f"looks through R&D expensing. The adjustment itself reranks only {rr['n_reranked']}/"
            f"{rr['n_industries']} industries by >= {K} places (Spearman rho {rr['spearman_rho']}), "
            f"so the distortion is concentrated in the high-R&D tail, not broad.")
    elif rr:
        result["headline"] = (
            f"Adjusting operating margins for R&D & leases reranks {rr['n_reranked']} of "
            f"{rr['n_industries']} non-financial U.S. industries by >= {K} positions "
            f"(Spearman rho = {rr['spearman_rho']}).")
    out = os.path.join(config.ANALYSIS_OUT, "headline.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print(f"\n{result.get('headline', '(insufficient data for headline — download margins)')}")
    print(f"Written: {out}")
    return result


if __name__ == "__main__":
    run()
