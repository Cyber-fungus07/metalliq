"""Cached readers for the trade, price and country tables.

Prefers the processed parquet files and falls back to the raw CSVs,
so pages keep working before (or without) running the ETL script.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

try:
    import streamlit as st

    _cache = st.cache_data
except Exception:  # streamlit not available (plain python / tests)

    def _cache(func=None, **kwargs):
        def wrap(f):
            return f

        return wrap(func) if func else wrap


from src.constants import (
    COUNTRY_SUMMARY_FILE,
    PRICE_TRENDS_FILE,
    RAW_DIR,
    TRADE_FLOWS_FILE,
)


def _load_parquet_or_csv(path: str) -> pd.DataFrame | None:
    if os.path.exists(path):
        try:
            return pd.read_parquet(path)
        except Exception:
            pass
    fallback = Path(path).with_suffix(".csv")
    if fallback.exists():
        return pd.read_csv(fallback)
    return None


@_cache
def load_trade_flows() -> pd.DataFrame:
    """Merged trade flows, one row per reporter/partner/metal/year/flow."""
    merged = _load_parquet_or_csv(TRADE_FLOWS_FILE)
    if merged is not None and not merged.empty:
        return merged
    chunks = []
    raw = Path(RAW_DIR)
    if raw.exists():
        for csv_file in sorted(raw.glob("comtrade_*.csv")):
            try:
                chunks.append(pd.read_csv(csv_file))
            except Exception:
                continue
    if chunks:
        return pd.concat(chunks, ignore_index=True)
    return pd.DataFrame()


@_cache
def load_price_trends() -> pd.DataFrame:
    prices = _load_parquet_or_csv(PRICE_TRENDS_FILE)
    if prices is not None and not prices.empty:
        return prices
    raw_prices = Path(RAW_DIR) / "commodity_prices.csv"
    if raw_prices.exists():
        return pd.read_csv(raw_prices)
    return pd.DataFrame()


@_cache
def load_country_summary() -> pd.DataFrame:
    summary = _load_parquet_or_csv(COUNTRY_SUMMARY_FILE)
    if summary is not None and not summary.empty:
        return summary
    return pd.DataFrame()


def data_status() -> dict:
    """Which data files exist (shown on the home page)."""
    raw = Path(RAW_DIR)
    raw_files = sorted(
        p.name
        for p in raw.glob("*")
        if p.is_file() and p.suffix in (".csv", ".parquet") and not p.name.startswith("_")
    )
    return {
        "trade_flows": os.path.exists(TRADE_FLOWS_FILE),
        "price_trends": os.path.exists(PRICE_TRENDS_FILE),
        "country_summary": os.path.exists(COUNTRY_SUMMARY_FILE),
        "raw_files": raw_files,
    }
