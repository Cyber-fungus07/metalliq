"""Shared constants: metals, years, colors and data paths."""

METALS = {
    "Gold": {"hs_codes": ["7108"], "color": "#D4AF37", "unit": "kg"},
    "Silver": {"hs_codes": ["7106"], "color": "#C0C0C0", "unit": "kg"},
    "Platinum": {"hs_codes": ["711011", "7110.11"], "color": "#8E8E93", "unit": "kg"},
    "Palladium": {"hs_codes": ["711021", "7110.21"], "color": "#B08D57", "unit": "kg"},
    "Copper": {"hs_codes": ["7403"], "color": "#B87333", "unit": "kg"},
    "Lithium": {"hs_codes": ["282520", "2825.20"], "color": "#A871E8", "unit": "kg"},
    "Cobalt": {"hs_codes": ["8105"], "color": "#3B82C4", "unit": "kg"},
    "Rare Earth Elements": {"hs_codes": ["2846"], "color": "#34C77B", "unit": "kg"},
}

YEARS = list(range(2010, 2024))

METAL_COLORS = {metal: spec["color"] for metal, spec in METALS.items()}

# Reporter countries used by the synthetic fallback data in
# scripts/download_data.py (real data keeps whatever Comtrade returns).
SAMPLE_COUNTRIES = [
    ("CHE", "Switzerland"),
    ("CHN", "China"),
    ("USA", "United States"),
    ("ARE", "United Arab Emirates"),
    ("ZAF", "South Africa"),
    ("AUS", "Australia"),
    ("CHL", "Chile"),
    ("PER", "Peru"),
    ("RUS", "Russia"),
    ("CAN", "Canada"),
    ("GBR", "United Kingdom"),
    ("IND", "India"),
    ("JPN", "Japan"),
    ("DEU", "Germany"),
    ("HKG", "Hong Kong"),
]

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
GEO_DIR = "data/geo"

TRADE_FLOWS_FILE = "data/processed/trade_flows.parquet"
PRICE_TRENDS_FILE = "data/processed/price_trends.parquet"
COUNTRY_SUMMARY_FILE = "data/processed/country_summary.parquet"
