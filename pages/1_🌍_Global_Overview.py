import streamlit as st
import plotly.express as px

from src.data_loader import load_trade_flows
from src.data_processor import format_usd
from src.constants import METALS, METAL_COLORS, YEARS

st.set_page_config(page_title="Global Overview", page_icon="🌍", layout="wide")

st.title("🌍 Global Trade Overview")

trades = load_trade_flows()
if trades.empty:
    st.warning("No trade data found. Make sure the data is loaded correctly.")
    st.stop()

st.sidebar.header("Filters")

oldest, newest = int(min(YEARS)), int(max(YEARS))
start_year, end_year = st.sidebar.slider("Select Year Range", oldest, newest, (oldest, newest))

metal_names = list(METALS.keys())
chosen_metals = st.sidebar.multiselect("Select Metals", metal_names, default=metal_names)
focus_year = st.sidebar.selectbox("Focus Year (for detailed charts)", list(reversed(YEARS)))

filtered = trades[
    (trades["year"] >= start_year)
    & (trades["year"] <= end_year)
    & (trades["metal"].isin(chosen_metals))
]
if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

st.subheader("At a Glance")

latest = filtered[filtered["year"] == end_year]
total_value = latest["trade_value_usd"].sum()

reporters = set(latest["reporter"].dropna().unique())
partners = set(latest["partner"].dropna().unique())
country_count = len(reporters | partners)

metal_totals = latest.groupby("metal")["trade_value_usd"].sum()
most_traded = metal_totals.idxmax() if not metal_totals.empty else "N/A"

previous = filtered[filtered["year"] == end_year - 1]
fastest_growing = "N/A"
growth_label = None
if not previous.empty and not latest.empty:
    previous_totals = previous.groupby("metal")["trade_value_usd"].sum()
    growth = ((metal_totals - previous_totals) / previous_totals).dropna()
    if not growth.empty:
        fastest_growing = growth.idxmax()
        growth_label = f"{growth[fastest_growing] * 100:.1f}% YoY"

cards = st.columns(4)
cards[0].metric(f"Total Trade ({end_year})", format_usd(total_value))
cards[1].metric("Trading Countries", country_count)
cards[2].metric("Most Traded", most_traded)
cards[3].metric("Fastest Growing", fastest_growing, delta=growth_label)

st.divider()

st.subheader("Trade Value Over Time")

trend = filtered.groupby(["year", "metal"])["trade_value_usd"].sum().reset_index()
fig = px.area(
    trend,
    x="year",
    y="trade_value_usd",
    color="metal",
    color_discrete_map=METAL_COLORS,
    labels={"trade_value_usd": "Trade Value (USD)", "year": "Year"},
)
fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), xaxis_title="")
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader(f"Deep Dive: {focus_year}")

focus = trades[(trades["year"] == focus_year) & (trades["metal"].isin(chosen_metals))]
if focus.empty:
    st.info(f"Not enough data to display detailed charts for {focus_year}.")
    st.stop()

left, right = st.columns(2)

with left:
    st.markdown("**Export vs Import by Metal**")
    flows = focus.groupby(["metal", "flow"])["trade_value_usd"].sum().reset_index()
    fig = px.bar(
        flows,
        x="metal",
        y="trade_value_usd",
        color="flow",
        barmode="group",
        color_discrete_sequence=["#4C72B0", "#55A868"],
        labels={"trade_value_usd": "Value (USD)", "metal": "Metal"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("**Global Distribution (Metal → Country)**")
    # Exports only, so mirrored import legs don't double-count the total.
    exports_only = focus[focus["flow"].str.lower() == "export"]
    treemap_data = (
        exports_only.groupby(["metal", "reporter"])["trade_value_usd"].sum().reset_index()
    )
    treemap_data = treemap_data[treemap_data["trade_value_usd"] > 0]
    fig = px.treemap(
        treemap_data,
        path=["metal", "reporter"],
        values="trade_value_usd",
        color="metal",
        color_discrete_map=METAL_COLORS,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
