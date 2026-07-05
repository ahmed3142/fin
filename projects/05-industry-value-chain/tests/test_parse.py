"""Parser tests over the real local files (both header layouts)."""
import numpy as np
import pytest

from src import config, parse


def _have(code):
    return parse.find_raw_path(config.DATASETS_BY_CODE[code]) is not None


@pytest.mark.skipif(not _have("growth_eb"), reason="fundgrEB.xls missing")
def test_fundgreb_row7_header_and_na_to_null():
    ds = config.DATASETS_BY_CODE["growth_eb"]
    df = parse.parse_dataset(ds)
    assert list(df.columns)[:2] == ["industry_name_raw", "num_firms"]
    assert len(df) == 94  # Total Market rows stripped
    # financial industries carry 'NA' in ROC -> must be NULL, not text
    roc = df.set_index("industry_name_raw")["roc"]
    assert np.isnan(roc.get("Bank (Money Center)", np.nan))


@pytest.mark.skipif(not _have("finflows_ts"), reason="finflows_timeseries.xlsx missing")
def test_finflows_ts_row0_header():
    ds = dict(config.DATASETS_BY_CODE["finflows"])
    ds["local"] = "finflows_timeseries.xlsx"
    df = parse.parse_dataset(ds)
    assert len(df) == 94
    assert "net_equity_change_usd" in df.columns


@pytest.mark.skipif(not _have("margins"), reason="margin.xls not downloaded")
def test_margin_rnd_sales_not_confused_with_ebitdarnd():
    df = parse.parse_dataset(config.DATASETS_BY_CODE["margins"]).set_index("industry_name_raw")
    # R&D/Sales for a big-R&D sector should be a plausible fraction (~0.15-0.25),
    # not the EBITDAR&D/Sales value (which is much larger) -> matcher collision guard
    pharma = df.loc["Drugs (Pharmaceutical)", "rnd_sales"]
    assert 0.05 < float(pharma) < 0.45


@pytest.mark.skipif(not _have("multiples_ps"), reason="psdata.xls not downloaded")
def test_ev_sales_is_a_multiple_not_a_percent():
    df = parse.parse_dataset(config.DATASETS_BY_CODE["multiples_ps"]).set_index("industry_name_raw")
    # a 'multiple' type must NOT be divided by 100
    semi = float(df.loc["Semiconductor", "ev_sales"])
    assert semi > 2.0
