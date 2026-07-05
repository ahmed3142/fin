"""Entity-resolution tests: the Heathcare typo resolves, and an unknown name
fails loudly (the anti-join gate)."""
import pytest

from src.crosswalk import Crosswalk, normalize, sector_group_of, is_financial

REF = ["Advertising", "Aerospace/Defense", "Healthcare Information and Technology",
       "Software (System & Application)", "Bank (Money Center)", "Utility (Water)"]


def _xwalk():
    return Crosswalk.build(REF)


def test_normalize_unifies_ampersand_and_space():
    assert normalize("  Brokerage  &  Investment Banking ") == "brokerage and investment banking"


def test_healthcare_typo_resolves_to_canonical():
    x = _xwalk()
    # the real Damodaran misspelling (missing the 'l') must map via the alias csv
    iid_typo = x.resolve("Heathcare Information and Technology")
    iid_ok = x.resolve("Healthcare Information and Technology")
    assert iid_typo is not None and iid_typo == iid_ok
    x.assert_resolved()  # no unresolved names -> gate passes


def test_unknown_industry_fails_loudly():
    x = _xwalk()
    assert x.resolve("Totally Made Up Industry") is None
    with pytest.raises(ValueError, match="Anti-join gate FAILED"):
        x.assert_resolved()


def test_sector_and_financial_flags():
    assert is_financial("Bank (Money Center)") is True
    assert is_financial("Software (System & Application)") is False
    assert sector_group_of("Utility (Water)") == "Utilities"
    assert sector_group_of("Bank (Money Center)") == "Financials"
