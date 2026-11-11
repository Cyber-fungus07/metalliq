"""ETL entry point: raw CSVs in data/raw -> parquet in data/processed.

Run:  python scripts/preprocess.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.constants import PROCESSED_DIR, RAW_DIR
from src.data_processor import (
    build_country_summary,
    clean_trade_frame,
    compute_derived_metrics,
)


def main() -> None:
    raw_dir = Path(RAW_DIR)
    out_dir = Path(PROCESSED_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    cleaned = []
    for csv_file in sorted(raw_dir.glob("comtrade_*.csv")):
        print(f"[preprocess] reading {csv_file}")
        try:
            cleaned.append(clean_trade_frame(pd.read_csv(csv_file)))
        except Exception as error:
            print(f"[preprocess] skip {csv_file}: {error}")
    if not cleaned:
        print("[preprocess] no raw comtrade_*.csv found. Run scripts/download_data.py first.")
        return

    trades = compute_derived_metrics(pd.concat(cleaned, ignore_index=True))
    trades.to_parquet(out_dir / "trade_flows.parquet", index=False)
    print(f"[preprocess] wrote {out_dir / 'trade_flows.parquet'} ({len(trades)} rows)")

    summary = build_country_summary(trades)
    summary.to_parquet(out_dir / "country_summary.parquet", index=False)
    print(f"[preprocess] wrote {out_dir / 'country_summary.parquet'} ({len(summary)} rows)")

    price_file = raw_dir / "commodity_prices.csv"
    if price_file.exists():
        pd.read_csv(price_file).to_parquet(out_dir / "price_trends.parquet", index=False)
        print(f"[preprocess] wrote {out_dir / 'price_trends.parquet'}")


if __name__ == "__main__":
    main()
