import time

import streamlit as st
import pandas as pd
import plotly.express as px

from src.data_loader import load_trade_flows
from src.constants import METALS, YEARS

st.set_page_config(page_title="Trade Maps", page_icon="🗺️", layout="wide")

st.title("🗺️ Global Trade Maps")
st.markdown("Visualize the geospatial distribution of metal trade across the globe.")

st.sidebar.header("Map Settings")
metal = st.sidebar.selectbox("Select Metal", list(METALS.keys()))
flow = st.sidebar.radio("Trade Flow", ["Export", "Import", "Balance"])
animated = st.sidebar.checkbox("Animate across years")

trades = load_trade_flows()
if trades.empty:
    st.warning("No trade data found. Run the download script first.")
    st.stop()


def map_data_for(metal_name, year, flow_name):
    subset = trades[(trades["metal"] == metal_name) & (trades["year"] == year)]
    if flow_name in ("Export", "Import"):
        matched = subset[subset["flow"] == flow_name]
        return matched.groupby(["reporter_iso3", "reporter"])["trade_value_usd"].sum().reset_index()
    exports = (
        subset[subset["flow"] == "Export"]
        .groupby(["reporter_iso3", "reporter"])["trade_value_usd"]
        .sum()
        .reset_index()
        .rename(columns={"trade_value_usd": "exports"})
    )
    imports = (
        subset[subset["flow"] == "Import"]
        .groupby(["reporter_iso3", "reporter"])["trade_value_usd"]
        .sum()
        .reset_index()
        .rename(columns={"trade_value_usd": "imports"})
    )
    merged = pd.merge(exports, imports, on=["reporter_iso3", "reporter"], how="outer").fillna(0)
    merged["trade_value_usd"] = merged["exports"] - merged["imports"]
    return merged


map_slot = st.empty()
table_slot = st.sidebar.empty()
year_slot = st.sidebar.empty()


def render(year):
    data = map_data_for(metal, year, flow)
    if flow == "Balance":
        colors, midpoint = px.colors.diverging.RdYlGn, 0
        title = f"Trade Balance for {metal} in {year}"
    elif flow == "Export":
        colors, midpoint = px.colors.sequential.Plasma, None
        title = f"Exports of {metal} in {year}"
    else:
        colors, midpoint = px.colors.sequential.Viridis, None
        title = f"Imports of {metal} in {year}"

    fig = px.choropleth(
        data,
        locations="reporter_iso3",
        color="trade_value_usd",
        hover_name="reporter",
        color_continuous_scale=colors,
        color_continuous_midpoint=midpoint,
        title=title,
    )
    fig.update_geos(
        showcoastlines=True,
        coastlinecolor="Black",
        showland=True,
        landcolor="lightgrey",
        projection_type="natural earth",
    )
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    map_slot.plotly_chart(fig, use_container_width=True)

    top_10 = data.sort_values("trade_value_usd", ascending=False).head(10)
    table = top_10[["reporter", "trade_value_usd"]].rename(
        columns={"reporter": "Country", "trade_value_usd": "USD"}
    )
    with table_slot.container():
        st.markdown(f"**Top 10 {flow}s**")
        st.dataframe(table, hide_index=True)


if animated:
    for year in sorted(YEARS):
        year_slot.markdown(f"**Year: {year}**")
        render(year)
        time.sleep(1)
else:
    year = year_slot.slider("Year", min_value=min(YEARS), max_value=max(YEARS), value=max(YEARS))
    render(year)
