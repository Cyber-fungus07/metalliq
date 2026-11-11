"""Cleaning and enrichment for the trade tables.

Used by scripts/preprocess.py to turn the raw Comtrade-style CSVs into
the processed parquet files the dashboard reads.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def clean_trade_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df.columns = [name.strip().lower().replace(" ", "_") for name in df.columns]
    df = df.dropna(subset=["year", "reporter_iso3", "partner_iso3"])
    df["trade_value_usd"] = pd.to_numeric(df["trade_value_usd"], errors="coerce").fillna(0)
    if "net_weight_kg" in df.columns:
        df["net_weight_kg"] = pd.to_numeric(df["net_weight_kg"], errors="coerce").fillna(0)
    return df


def add_trade_balance(df: pd.DataFrame) -> pd.DataFrame:
    """Per reporter/metal/year net exports (exports minus imports)."""
    if df.empty:
        return df
    totals = (
        df.groupby(["reporter_iso3", "metal", "year", "flow"])["trade_value_usd"]
        .sum()
        .unstack(fill_value=0)
    )
    if "Export" not in totals.columns:
        totals["Export"] = 0
    if "Import" not in totals.columns:
        totals["Import"] = 0
    totals["trade_balance"] = totals["Export"] - totals["Import"]
    balances = totals.reset_index()[["reporter_iso3", "metal", "year", "trade_balance"]]
    return df.merge(balances, on=["reporter_iso3", "metal", "year"], how="left")


def add_yoy_growth(df: pd.DataFrame) -> pd.DataFrame:
    """Year-over-year growth (%) of each reporter/metal/flow series."""
    if df.empty:
        return df
    yearly = (
        df.groupby(["reporter_iso3", "metal", "flow", "year"])["trade_value_usd"]
        .sum()
        .reset_index()
        .sort_values(["reporter_iso3", "metal", "flow", "year"])
    )
    yearly["yoy_growth"] = (
        yearly.groupby(["reporter_iso3", "metal", "flow"])["trade_value_usd"].pct_change() * 100
    )
    growth = yearly[["reporter_iso3", "metal", "flow", "year", "yoy_growth"]]
    return df.merge(growth, on=["reporter_iso3", "metal", "flow", "year"], how="left")


def add_market_share(df: pd.DataFrame) -> pd.DataFrame:
    """Each row's share (%) of its metal/year/flow world total."""
    if df.empty:
        return df
    world_totals = df.groupby(["year", "metal", "flow"])["trade_value_usd"].transform("sum")
    df["market_share_pct"] = (df["trade_value_usd"] / world_totals.replace(0, np.nan)) * 100
    return df


def build_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    """One row per reporter: total trade, top metal, top partner."""
    if df.empty:
        return pd.DataFrame()
    totals = df.groupby("reporter_iso3")["trade_value_usd"].sum().reset_index()
    totals = totals.rename(columns={"trade_value_usd": "total_trade_usd"})

    by_metal = df.groupby(["reporter_iso3", "metal"])["trade_value_usd"].sum().reset_index()
    top_metal = by_metal.loc[by_metal.groupby("reporter_iso3")["trade_value_usd"].idxmax()]
    top_metal = top_metal[["reporter_iso3", "metal"]].rename(columns={"metal": "top_metal"})

    by_partner = (
        df.groupby(["reporter_iso3", "partner_iso3"])["trade_value_usd"].sum().reset_index()
    )
    top_partner = by_partner.loc[by_partner.groupby("reporter_iso3")["trade_value_usd"].idxmax()]
    top_partner = top_partner[["reporter_iso3", "partner_iso3"]].rename(
        columns={"partner_iso3": "top_partner"}
    )

    summary = totals.merge(top_metal, on="reporter_iso3", how="left")
    return summary.merge(top_partner, on="reporter_iso3", how="left")


def compute_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = add_trade_balance(df)
    df = add_yoy_growth(df)
    return add_market_share(df)


def format_usd(value) -> str:
    """Compact dollar label, e.g. 1_500_000 -> $1.5M (handles negatives)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "$0"
    amount = float(value)
    negative = amount < 0
    amount = abs(amount)
    if amount >= 1e12:
        text = f"${amount / 1e12:.2f}T"
    elif amount >= 1e9:
        text = f"${amount / 1e9:.1f}B"
    elif amount >= 1e6:
        text = f"${amount / 1e6:.1f}M"
    elif amount >= 1e3:
        text = f"${amount / 1e3:.1f}K"
    else:
        text = f"${amount:,.0f}"
    return f"-{text}" if negative else text
