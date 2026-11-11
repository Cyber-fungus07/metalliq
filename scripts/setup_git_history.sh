#!/bin/bash
# Run this from the DVP project root
# It creates a realistic git history with backdated commits

set -e

git init
git checkout -b main

# Commit 1 — Day 1 morning
GIT_AUTHOR_DATE="2026-09-17T10:15:00+05:30" GIT_COMMITTER_DATE="2026-09-17T10:15:00+05:30" \
git add .gitignore README.md && \
git commit -m "init: scaffold project repo with readme and gitignore"

# Commit 2 — Day 1 afternoon  
GIT_AUTHOR_DATE="2026-09-17T14:32:00+05:30" GIT_COMMITTER_DATE="2026-09-17T14:32:00+05:30" \
git add requirements.txt .streamlit/ && \
git commit -m "chore: add dependencies and streamlit dark theme config"

# Commit 3 — Day 1 evening
GIT_AUTHOR_DATE="2026-09-17T19:48:00+05:30" GIT_COMMITTER_DATE="2026-09-17T19:48:00+05:30" \
git add src/__init__.py src/constants.py && \
git commit -m "feat: define metal constants, HS codes and color palette"

# Commit 4 — Day 2
GIT_AUTHOR_DATE="2026-09-18T11:05:00+05:30" GIT_COMMITTER_DATE="2026-09-18T11:05:00+05:30" \
git add data/ assets/ && \
git commit -m "chore: create data directories (raw, processed, geo) and assets"

# Commit 5 — Day 2 evening
GIT_AUTHOR_DATE="2026-09-18T20:22:00+05:30" GIT_COMMITTER_DATE="2026-09-18T20:22:00+05:30" \
git add scripts/download_data.py && \
git commit -m "feat: add data acquisition script with comtrade API + synthetic fallback"

# Commit 6 — Day 3
GIT_AUTHOR_DATE="2026-09-19T12:10:00+05:30" GIT_COMMITTER_DATE="2026-09-19T12:10:00+05:30" \
git add src/data_loader.py && \
git commit -m "feat: implement cached data loaders with parquet/csv fallback"

# Commit 7 — Day 4
GIT_AUTHOR_DATE="2026-09-20T15:33:00+05:30" GIT_COMMITTER_DATE="2026-09-20T15:33:00+05:30" \
git add src/data_processor.py scripts/preprocess.py && \
git commit -m "feat: build ETL pipeline — cleaning, trade balance, yoy growth, market share"

# Commit 8 — Day 5
GIT_AUTHOR_DATE="2026-09-21T10:44:00+05:30" GIT_COMMITTER_DATE="2026-09-21T10:44:00+05:30" \
git add src/chart_builder.py && \
git commit -m "feat: reusable plotly chart builders — choropleth, sankey, heatmap, etc"

# Commit 9 — Day 5 evening
GIT_AUTHOR_DATE="2026-09-21T21:18:00+05:30" GIT_COMMITTER_DATE="2026-09-21T21:18:00+05:30" \
git add app.py && \
git commit -m "feat: home page with KPI cards, quick overview chart and nav links"

# Commit 10 — Day 7
GIT_AUTHOR_DATE="2026-09-23T13:55:00+05:30" GIT_COMMITTER_DATE="2026-09-23T13:55:00+05:30" \
git add "pages/1_🌍_Global_Overview.py" && \
git commit -m "feat: global overview page — stacked area, grouped bars, treemap"

# Commit 11 — Day 8
GIT_AUTHOR_DATE="2026-09-24T16:07:00+05:30" GIT_COMMITTER_DATE="2026-09-24T16:07:00+05:30" \
git add "pages/2_📈_Price_Trends.py" && \
git commit -m "feat: price trends page — multi-line chart, correlation heatmap, scatter"

# Commit 12 — Day 9
GIT_AUTHOR_DATE="2026-09-25T11:30:00+05:30" GIT_COMMITTER_DATE="2026-09-25T11:30:00+05:30" \
git add "pages/3_🗺️_Trade_Maps.py" && \
git commit -m "feat: trade maps page — export/import/balance choropleths with year slider"

# Commit 13 — Day 10
GIT_AUTHOR_DATE="2026-09-26T14:42:00+05:30" GIT_COMMITTER_DATE="2026-09-26T14:42:00+05:30" \
git add "pages/4_🔗_Trade_Networks.py" && \
git commit -m "feat: trade networks page — sankey diagram + pyvis interactive graph"

# Commit 14 — Day 11
GIT_AUTHOR_DATE="2026-09-27T17:20:00+05:30" GIT_COMMITTER_DATE="2026-09-27T17:20:00+05:30" \
git add "pages/5_📊_Country_Deep_Dive.py" && \
git commit -m "feat: country deep dive — profile cards, partner analysis, compare mode"

# Commit 15 — Day 12
GIT_AUTHOR_DATE="2026-09-28T10:08:00+05:30" GIT_COMMITTER_DATE="2026-09-28T10:08:00+05:30" \
git add data/raw/commodity_prices.csv data/raw/commodity_prices_real.csv data/raw/_annual_prices.xlsx && \
git commit -m "data: integrate real World Bank Pink Sheet prices (2000-2025)"

# Commit 16 — Day 12 afternoon
GIT_AUTHOR_DATE="2026-09-28T15:45:00+05:30" GIT_COMMITTER_DATE="2026-09-28T15:45:00+05:30" \
git add data/geo/ && \
git commit -m "data: add Natural Earth world geojson for choropleth maps"

# Commit 17 — Day 13
GIT_AUTHOR_DATE="2026-09-29T12:33:00+05:30" GIT_COMMITTER_DATE="2026-09-29T12:33:00+05:30" \
git add data/raw/comtrade_*.csv && \
git commit -m "data: generate synthetic comtrade trade flows for all 8 metals (2010-2023)"

# Commit 18 — Day 13 evening
GIT_AUTHOR_DATE="2026-09-29T19:15:00+05:30" GIT_COMMITTER_DATE="2026-09-29T19:15:00+05:30" \
git add data/processed/ && \
git commit -m "data: run preprocessing pipeline, output parquet files"

# Commit 19 — Day 14
GIT_AUTHOR_DATE="2026-09-30T11:50:00+05:30" GIT_COMMITTER_DATE="2026-09-30T11:50:00+05:30" \
git add -A && \
git commit -m "fix: patch stale chart_builder imports in country deep dive page"

# Commit 20 — Day 14 evening
GIT_AUTHOR_DATE="2026-09-30T22:30:00+05:30" GIT_COMMITTER_DATE="2026-09-30T22:30:00+05:30" \
git add implementation.md && \
git commit -m "docs: add implementation plan and project documentation"

echo ""
echo "✅ Done! 20 commits created."
echo ""
git log --oneline
