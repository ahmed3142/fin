"""Entity resolution for the free-text 'Industry Name' join key.

The key is dirty across files (Damodaran's real 'Heathcare' typo, '&' vs 'and',
stray whitespace) so we NEVER inner-join on the raw string. Every raw name is
resolved to a surrogate industry_id through a normalized lookup plus a
hand-maintained alias crosswalk. Unresolved names FAIL LOUDLY (anti-join gate);
fuzzy matches only *propose* a fix for a human to add to the crosswalk.
"""
from __future__ import annotations

import csv
import difflib
import re

from . import config

# ---- sector attributes -----------------------------------------------------
SECTOR_KEYWORDS = [
    ("Financials", ["bank", "insurance", "brokerage", "reinsurance", "financial svcs",
                     "investments & asset", "r.e.i.t"]),
    ("Real Estate", ["real estate"]),
    ("Technology", ["software", "semiconductor", "computer", "information services",
                    "electronics", "internet"]),
    ("Communication Services", ["telecom", "entertainment", "publishing", "advertising",
                                "broadcasting", "cable"]),
    ("Healthcare", ["healthcare", "hospital", "drug", "biotech", "pharma"]),
    ("Energy", ["oil", "gas", "coal", "energy", "power"]),
    ("Utilities", ["utility"]),
    ("Materials", ["chemical", "metals", "mining", "paper", "steel", "building materials"]),
    ("Consumer Staples", ["food", "beverage", "tobacco", "household", "farming", "retail (grocery"]),
    ("Consumer Discretionary", ["apparel", "auto", "retail", "restaurant", "hotel", "recreation",
                                "furn", "shoe", "homebuilding"]),
    ("Industrials", ["aerospace", "defense", "machinery", "transportation", "air transport",
                     "engineering", "construction", "business & consumer svcs", "environmental",
                     "shipbuilding", "trucking", "railroad"]),
]


def normalize(name: str) -> str:
    s = (name or "").strip().lower()
    s = s.replace("&", " and ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def is_financial(canonical_name: str) -> bool:
    return canonical_name in config.FINANCIAL_INDUSTRIES


def sector_group_of(canonical_name: str) -> str:
    low = canonical_name.lower()
    for group, kws in SECTOR_KEYWORDS:
        if any(k in low for k in kws):
            return group
    return "Other"


class Crosswalk:
    """Builds the canonical industry registry and resolves raw names to ids."""

    def __init__(self, alias_map: dict[str, str], canonical: dict[str, tuple[int, str]]):
        self.alias_map = alias_map              # normalized raw -> canonical display name
        self.by_norm = canonical                # normalized canonical -> (id, display)
        self.unresolved: list[tuple[str, str]] = []

    @classmethod
    def build(cls, reference_names: list[str]) -> "Crosswalk":
        alias_map: dict[str, str] = {}
        with open(config.ALIASES_CSV, newline="") as fh:
            for row in csv.DictReader(fh):
                alias_map[normalize(row["raw_name"])] = row["canonical_name"].strip()
        # canonical set = reference names after alias substitution, deduped
        canon_names = set()
        for nm in reference_names:
            canon_names.add(alias_map.get(normalize(nm), nm.strip()))
        ordered = sorted(canon_names, key=str.lower)
        by_norm = {normalize(nm): (i + 1, nm) for i, nm in enumerate(ordered)}
        return cls(alias_map, by_norm)

    def resolve(self, raw_name: str) -> int | None:
        canonical = self.alias_map.get(normalize(raw_name), raw_name.strip())
        hit = self.by_norm.get(normalize(canonical))
        if hit:
            return hit[0]
        # propose a fuzzy fix but do NOT auto-apply
        cands = difflib.get_close_matches(
            normalize(raw_name), list(self.by_norm.keys()), n=1, cutoff=0.85)
        suggestion = self.by_norm[cands[0]][1] if cands else "(no close match)"
        self.unresolved.append((raw_name, suggestion))
        return None

    def assert_resolved(self) -> None:
        if self.unresolved:
            lines = "\n".join(f"    - {raw!r}  -> did you mean {sug!r}? "
                              f"(add to industry_aliases.csv)"
                              for raw, sug in self.unresolved)
            raise ValueError(
                f"Anti-join gate FAILED: {len(self.unresolved)} industry name(s) did "
                f"not resolve to a canonical industry_id:\n{lines}")

    @property
    def industries(self) -> list[tuple[int, str]]:
        return sorted(self.by_norm.values())
