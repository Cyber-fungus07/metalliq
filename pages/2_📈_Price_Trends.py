import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import load_trade_flows, load_price_trends
from src.constants import METALS, METAL_COLORS

st.set_page_config(page_title="Price Trends", page_icon="📈", layout="wide")

st.title("📈 Global Metal Price Trends")

prices = load_price_trends()
trades = load_trade_flows()

if prices.empty:
    st.warning("Price data is currently unavailable.")
    st.stop()

st.sidebar.header("Filters")
metal_names = list(METALS.keys())

fallbacks = ["Gold", "Silver", "Platinum"]
defaults = [metal for metal in fallbacks if metal in metal_names] or metal_names[:3]
chosen_metals = st.sidebar.multiselect("Select Metals", options=metal_names, default=defaults)
if not chosen_metals:
    st.warning("Pick at least one metal from the sidebar to continue.")
    st.stop()

first_year, last_year = int(prices["year"].min()), int(prices["year"].max())
start_year, end_year = st.sidebar.slider("Year Range", first_year, last_year, (first_year, last_year))
normalize = st.sidebar.checkbox("Normalize Prices (Base 100)", value=False)

filtered = prices[
    (prices["year"] >= start_year)
    & (prices["year"] <= end_year)
    & (prices["metal"].isin(chosen_metals))
].copy()
if filtered.empty:
    st.warning("No price data found for these filters.")
    st.stop()

st.subheader("Price History")

if normalize:
    # Rebase every series to 100 at the start year so cheap
    # industrial metals can be compared against gold visually.
    filtered["norm_price"] = filtered.groupby("metal")["price_usd_per_kg"].transform(
        lambda series: (series / series.iloc[0]) * 100 if len(series) else np.nan
    )
    value_col, y_label = "norm_price", "Normalized Price (Index = 100)"
else:
    value_col, y_label = "price_usd_per_kg", "Price (USD / kg)"

fig = px.line(filtered, x="year", y=value_col, color="metal", color_discrete_map=METAL_COLORS, markers=True)
fig.update_layout(yaxis_title=y_label, xaxis_title="Year", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Price Correlation")
    pivoted = filtered.pivot(index="year", columns="metal", values="price_usd_per_kg")
    if len(chosen_metals) > 1 and not pivoted.empty:
        fig = px.imshow(
            pivoted.corr().round(2),
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
        )
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pick at least 2 metals to see correlation.")

with right:
    st.subheader("Year-over-Year Change (%)")
    current = filtered[filtered["year"] == end_year].set_index("metal")["price_usd_per_kg"]
    previous = filtered[filtered["year"] == end_year - 1].set_index("metal")["price_usd_per_kg"]
    if current.empty or previous.empty:
        st.info(f"Not enough sequential data to calculate YoY change for {end_year}.")
    else:
        changes = ((current - previous) / previous * 100).dropna().reset_index()
        changes.columns = ["metal", "pct_change"]
        changes["bar_color"] = np.where(changes["pct_change"] >= 0, "#2ecc71", "#e74c3c")
        fig = go.Figure(
            go.Bar(
                x=changes["pct_change"],
                y=changes["metal"],
                orientation="h",
                marker_color=changes["bar_color"],
                text=changes["pct_change"].round(1).astype(str) + "%",
                textposition="auto",
            )
        )
        fig.update_layout(
            xaxis_title=f"% Change ({end_year - 1} to {end_year})",
            yaxis_title="",
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Price vs. Trade Volume")

scatter_year = st.selectbox(
    "Select Year for Scatter Plot",
    options=range(start_year, end_year + 1),
    index=end_year - start_year,
)

if trades.empty:
    st.info("Trade flow data is missing entirely.")
    st.stop()

year_trades = trades[(trades["year"] == scatter_year) & (trades["metal"].isin(chosen_metals))]
if year_trades.empty:
    st.info("No trade data available for this year/metal combo.")
    st.stop()

volumes = year_trades.groupby("metal")["net_weight_kg"].sum().reset_index()
year_prices = filtered[filtered["year"] == scatter_year]
merged = pd.merge(volumes, year_prices, on="metal", how="inner")

if merged.empty:
    st.info("Missing overlap between trade and price data for this year.")
    st.stop()

# Log scales: gold volumes vs base-metal volumes are worlds apart.
fig = px.scatter(
    merged,
    x="net_weight_kg",
    y="price_usd_per_kg",
    color="metal",
    hover_name="metal",
    color_discrete_map=METAL_COLORS,
    log_x=True,
    log_y=True,
    size_max=15,
)
fig.update_traces(marker=dict(size=12, line=dict(width=1, color="white")))
fig.update_layout(
    xaxis_title="Total Trade Volume (kg, log scale)",
    yaxis_title="Price (USD/kg, log scale)",
    margin=dict(l=0, r=0, t=10, b=0),
)
st.plotly_chart(fig, use_container_width=True)
