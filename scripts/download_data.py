"""Phase 2 — Data acquisition script.

Covers implementation.md Steps 2.2 – 2.5:
  2.2  UN Comtrade trade data by HS code (needs API key)
  2.3  World Bank Pink Sheet commodity prices
  2.4  world.geojson from Natural Earth / public mirrors
  2.5  Synthetic fallback generator (offline dev, no API key needed)

Usage:
    python scripts/download_data.py --all
    python scripts/download_data.py --comtrade --synthetic-fallback
    python scripts/download_data.py --prices
    python scripts/download_data.py --geo
    python scripts/download_data.py --synthetic   # generate realistic sample data only

UN Comtrade API key:
    Register at https://comtradeplus.un.org/ -> Profile -> API key,
    then either:
      export COMTRADE_API_KEY="your-key"
    or add to .streamlit/secrets.toml:
      COMTRADE_API_KEY = "your-key"

Without a key the script CANNOT hit the live API (it is rate-limited
and key-gated) — use --synthetic to unblock Phases 3-4.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

try:
    from src.constants import METALS, SAMPLE_COUNTRIES, YEARS
except ImportError:  # allow `python scripts/download_data.py` from repo root
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.constants import METALS, SAMPLE_COUNTRIES, YEARS

RAW_DIR = Path("data/raw")
GEO_DIR = Path("data/geo")

# ---------------------------------------------------------------------------
# 2.2 UN Comtrade
# ---------------------------------------------------------------------------

COMTRADE_BASE = "https://comtradeapi.un.org/data/v1/get/C/A/HS"


def _get_api_key() -> str | None:
    key = os.environ.get("COMTRADE_API_KEY")
    if key:
        return key
    secrets = Path(".streamlit/secrets.toml")
    if secrets.exists():
        for line in secrets.read_text().splitlines():
            line = line.strip()
            if line.startswith("COMTRADE_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def fetch_comtrade(
    hs_code: str,
    years: list[int] | None = None,
    reporter: str = "all",
    max_retries: int = 3,
    timeout: int = 60,
) -> pd.DataFrame:
    """Fetch one HS code from the UN Comtrade v1 API.

    Returns an empty DataFrame when the request fails (no key, rate
    limit, …) so callers can fall back to synthetic data.
    """
    api_key = _get_api_key()
    years = years or YEARS
    period = ",".join(str(y) for y in years)
    headers = {"Cache-Control": "no-cache"}
    if api_key:
        headers["Subscription-Key"] = api_key  # Comtrade Plus header name

    params = {
        "reporterCode": reporter,
        "period": period,
        "cmdCode": hs_code.replace(".", ""),
        "flowCode": "M,X",  # imports + exports
        "partnerCode": 0,  # world total (use bilateral via partnerCode=all, slower)
        "breakdownMode": "classic",
        "includeDesc": True,
    }
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(COMTRADE_BASE, params=params, headers=headers, timeout=timeout)
            if response.status_code in (401, 403):
                print(
                    "[comtrade] 401/403 — you need a (free) API key. "
                    "Register at https://comtradeplus.un.org/, then "
                    "export COMTRADE_API_KEY=... (see module docstring)."
                )
                return pd.DataFrame()
            if response.status_code == 429:
                wait = 10 * attempt
                print(f"[comtrade] rate-limited, sleeping {wait}s …")
                time.sleep(wait)
                continue
            response.raise_for_status()
            rows = response.json().get("data", [])
            if not rows:
                print(f"[comtrade] HS {hs_code}: no rows returned.")
                return pd.DataFrame()
            return pd.DataFrame(rows)
        except requests.RequestException as error:
            print(f"[comtrade] HS {hs_code} attempt {attempt}/{max_retries}: {error}")
            time.sleep(5 * attempt)
    return pd.DataFrame()


def download_all_comtrade(years: list[int] | None = None) -> None:
    """Loop over METALS, save data/raw/comtrade_<metal>.csv each."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    years = years or YEARS
    for metal, spec in METALS.items():
        slug = metal.lower().replace(" ", "_")
        out = RAW_DIR / f"comtrade_{slug}.csv"
        if out.exists():
            print(f"[comtrade] {metal}: {out} exists, skipping (delete to re-fetch).")
            continue
        hs_code = spec["hs_codes"][0]
        print(f"[comtrade] {metal} (HS {hs_code}) years {years[0]}–{years[-1]} …")
        df = fetch_comtrade(hs_code, years=years)
        if df.empty:
            print(f"[comtrade] {metal}: no live data — run with --synthetic-fallback.")
            continue
        df.to_csv(out, index=False)
        print(f"[comtrade] {metal}: wrote {out} ({len(df)} rows)")
        time.sleep(2)  # be nice to the API


# ---------------------------------------------------------------------------
# 2.3 World Bank Pink Sheet (commodity prices)
# ---------------------------------------------------------------------------

PINK_SHEET_CANDIDATES = [
    # These URLs change periodically; we try each in order.
    "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e87b70-0350012022/related/CMO-Pink-Sheet-History.xlsx",
    "https://www.worldbank.org/content/dam/Worldbank/documents/research/commodity-markets/CMO-Pink-Sheet-History.xlsx",
]


def download_pink_sheet(out: Path = RAW_DIR / "commodity_prices.csv") -> bool:
    """Try official Pink Sheet; return True on success."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for url in PINK_SHEET_CANDIDATES:
        try:
            print(f"[prices] trying {url} …")
            response = requests.get(url, timeout=120)
            if response.status_code != 200:
                print(f"[prices] HTTP {response.status_code}, trying next mirror.")
                continue
            tmp = RAW_DIR / "_pink_sheet.xlsx"
            tmp.write_bytes(response.content)
            # Pink Sheet layout: monthly prices below a few header rows.
            df = pd.read_excel(tmp, sheet_name=0, header=4)
            df.to_csv(out, index=False)
            print(f"[prices] wrote {out} from Pink Sheet.")
            tmp.unlink(missing_ok=True)
            return True
        except Exception as error:
            print(f"[prices] failed ({error}), trying next mirror.")
    print("[prices] official download failed — use --synthetic for price fallback.")
    return False


# ---------------------------------------------------------------------------
# 2.4 world.geojson
# ---------------------------------------------------------------------------

GEOJSON_CANDIDATES = [
    "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json",
    "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson",
]


def download_geojson(out: Path = GEO_DIR / "world.geojson") -> bool:
    GEO_DIR.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 10_000:
        print(f"[geo] {out} exists, skipping.")
        return True
    for url in GEOJSON_CANDIDATES:
        try:
            print(f"[geo] trying {url} …")
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            geo = response.json()  # validate JSON
            feature_count = len(geo.get("features", []))
            out.write_text(json.dumps(geo))
            print(f"[geo] wrote {out} ({feature_count} features, {out.stat().st_size/1e6:.1f} MB).")
            return True
        except Exception as error:
            print(f"[geo] failed ({error}), trying next mirror.")
    return False


# ---------------------------------------------------------------------------
# 2.5 Synthetic fallback (offline dev + CI)
# ---------------------------------------------------------------------------

# Baseline 2023 world trade value per metal, USD billions. Order-of-magnitude
# realistic: gold dwarfs everything, copper next, battery metals small but growing.
BASE_VALUE_BN = {
    "Gold": 480.0,
    "Silver": 38.0,
    "Platinum": 9.5,
    "Palladium": 18.0,
    "Copper": 210.0,
    "Lithium": 9.0,
    "Cobalt": 7.5,
    "Rare Earth Elements": 6.0,
}

# Yearly drift applied backwards from 2023 so trends look plausible.
YEARLY_GROWTH = {
    "Gold": 0.045,
    "Silver": 0.03,
    "Platinum": 0.01,
    "Palladium": 0.06,
    "Copper": 0.05,
    "Lithium": 0.22,
    "Cobalt": 0.12,
    "Rare Earth Elements": 0.10,
}

# Share of each metal's trade attributed to each reporter.
REPORTER_SHARES = {
    "CHE": 0.14, "CHN": 0.12, "USA": 0.08, "ARE": 0.07, "ZAF": 0.07,
    "AUS": 0.08, "CHL": 0.06, "PER": 0.05, "RUS": 0.06, "CAN": 0.05,
    "GBR": 0.04, "IND": 0.03, "JPN": 0.03, "DEU": 0.03, "HKG": 0.09,
}

PARTNER_POOL = ["CHE", "CHN", "USA", "IND", "ARE", "GBR", "HKG", "JPN", "DEU", "KOR"]


def generate_synthetic_comtrade(seed: int = 42, only_metals: list[str] | None = None) -> None:
    """Write data/raw/comtrade_<metal>.csv for all 8 metals (2010–2023).

    Schema matches the Phase 3 ETL contract:
      year, metal, hs_code, reporter_iso3, reporter, partner_iso3, partner,
      flow, trade_value_usd, net_weight_kg
    """
    rng = np.random.default_rng(seed)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    names_by_iso3 = dict(SAMPLE_COUNTRIES)
    metals = only_metals or list(METALS)
    for metal in metals:
        spec = METALS[metal]
        rows = []
        base = BASE_VALUE_BN[metal] * 1e9
        growth = YEARLY_GROWTH[metal]
        hs_code = spec["hs_codes"][0].replace(".", "")
        for year in YEARS:
            year_scale = (1 + growth) ** (year - 2023) * rng.uniform(0.92, 1.08)
            for code, weight in REPORTER_SHARES.items():
                for flow, flow_share in (("Export", 0.55), ("Import", 0.45)):
                    reporter_value = base * year_scale * weight * flow_share * rng.uniform(0.85, 1.15)
                    # Split each reporter total across 2 random partners to
                    # give Sankey/network pages something to chew on.
                    for partner in rng.choice(PARTNER_POOL, size=2, replace=False):
                        if partner == code:
                            continue
                        split = rng.uniform(0.3, 0.7)
                        rows.append({
                            "year": year,
                            "metal": metal,
                            "hs_code": hs_code,
                            "reporter_iso3": code,
                            "reporter": names_by_iso3.get(code, code),
                            "partner_iso3": partner,
                            "partner": names_by_iso3.get(partner, partner),
                            "flow": flow,
                            "trade_value_usd": round(reporter_value * split, 2),
                            "net_weight_kg": round(
                                reporter_value * split / price_per_kg(metal, year), 2
                            ),
                        })
        df = pd.DataFrame(rows)
        out = RAW_DIR / f"comtrade_{metal.lower().replace(' ', '_')}.csv"
        df.to_csv(out, index=False)
        print(f"[synthetic] wrote {out} ({len(df)} rows)")


def price_per_kg(metal: str, year: int) -> float:
    base = {
        "Gold": 55000, "Silver": 750, "Platinum": 32000, "Palladium": 55000,
        "Copper": 9, "Lithium": 18, "Cobalt": 35, "Rare Earth Elements": 25,
    }[metal]
    return base * (1 + YEARLY_GROWTH[metal]) ** (year - 2023)


def generate_synthetic_prices(seed: int = 7) -> None:
    """Write data/raw/commodity_prices.csv (annual avg USD per kg, 2010–2023)."""
    rng = np.random.default_rng(seed)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for metal in METALS:
        for year in YEARS:
            price = price_per_kg(metal, year) * rng.uniform(0.94, 1.06)
            rows.append({"year": year, "metal": metal, "price_usd_per_kg": round(price, 2)})
    out = RAW_DIR / "commodity_prices.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"[synthetic] wrote {out} ({len(rows)} rows)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2 data acquisition")
    parser.add_argument("--all", action="store_true", help="run comtrade + prices + geo")
    parser.add_argument("--comtrade", action="store_true", help="fetch UN Comtrade")
    parser.add_argument("--prices", action="store_true", help="fetch Pink Sheet prices")
    parser.add_argument("--geo", action="store_true", help="fetch world.geojson")
    parser.add_argument("--synthetic", action="store_true", help="generate synthetic raw CSVs only")
    parser.add_argument(
        "--synthetic-fallback",
        action="store_true",
        help="generate synthetic CSVs only for metals missing live data",
    )
    parser.add_argument("--years", default="2010-2023", help="e.g. 2010-2023 or 2020,2021,2022")
    args = parser.parse_args(argv)

    if args.years and "-" in args.years:
        start, end = args.years.split("-", 1)
        years = list(range(int(start), int(end) + 1))
    elif args.years:
        years = [int(y) for y in args.years.split(",")]
    else:
        years = YEARS

    if args.synthetic:
        generate_synthetic_comtrade()
        generate_synthetic_prices()
        return 0

    did_work = False
    if args.all or args.comtrade:
        download_all_comtrade(years=years)
        did_work = True
    if args.all or args.prices:
        if not download_pink_sheet():
            print("[prices] hint: re-run with --synthetic-fallback for offline prices.")
        did_work = True
    if args.all or args.geo:
        download_geojson()
        did_work = True
    if args.synthetic_fallback:
        missing = [
            metal for metal in METALS
            if not (RAW_DIR / f"comtrade_{metal.lower().replace(' ', '_')}.csv").exists()
        ]
        if missing:
            print(f"[fallback] synthesizing missing metals: {missing}")
            generate_synthetic_comtrade(only_metals=missing)
        else:
            print("[fallback] all metals already have live data.")
        if not (RAW_DIR / "commodity_prices.csv").exists():
            generate_synthetic_prices()
        did_work = True

    if not did_work:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
