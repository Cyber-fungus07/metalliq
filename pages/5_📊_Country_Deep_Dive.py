import streamlit as st
import plotly.express as px

from src.data_loader import load_trade_flows
from src.chart_builder import empty_figure
from src.data_processor import format_usd
from src.constants import METALS, YEARS, METAL_COLORS

st.set_page_config(page_title="Country Deep Dive", page_icon="📊", layout="wide")

st.title("📊 Country Deep Dive")

trades = load_trade_flows()
if trades.empty:
    st.warning("No trade data found. Please run the download script first.")
    st.stop()

countries = sorted(trades["reporter"].dropna().unique())

st.sidebar.header("Filters")
country = st.sidebar.selectbox("Select Country", options=countries, index=0 if countries else 0)
compare_with = st.sidebar.selectbox("Compare With (Optional)", options=["None"] + countries, index=0)
metal = st.sidebar.selectbox("Metal Filter", options=["All"] + list(METALS.keys()))
start_year, end_year = st.sidebar.slider(
    "Year Range", min_value=min(YEARS), max_value=max(YEARS), value=(min(YEARS), max(YEARS))
)

in_range = trades[(trades["year"] >= start_year) & (trades["year"] <= end_year)]


def show_country(name, data):
    st.subheader(f"Profile: {name}")
    if data.empty:
        st.info("No data available for this selection.")
        return

    exports = data[data["flow"] == "Export"]["trade_value_usd"].sum()
    imports = data[data["flow"] == "Import"]["trade_value_usd"].sum()

    exports_by_metal = (
        data[data["flow"] == "Export"].groupby("metal")["trade_value_usd"].sum().sort_values(ascending=False)
    )
    imports_by_metal = (
        data[data["flow"] == "Import"].groupby("metal")["trade_value_usd"].sum().sort_values(ascending=False)
    )
    top_export = exports_by_metal.index[0] if not exports_by_metal.empty else "N/A"
    top_import = imports_by_metal.index[0] if not imports_by_metal.empty else "N/A"

    cards = st.columns(5)
    cards[0].metric("Total Trade", format_usd(exports + imports))
    cards[1].metric("Trade Balance", format_usd(exports - imports))
    cards[2].metric("Top Export", top_export)
    cards[3].metric("Top Import", top_import)
    cards[4].metric("Trading Partners", data["partner"].nunique())

    left, right = st.columns(2)

    with left:
        mix = data.groupby(["flow", "metal"])["trade_value_usd"].sum().reset_index()
        if not mix.empty:
            fig = px.pie(
                mix,
                values="trade_value_usd",
                names="metal",
                facet_col="flow",
                hole=0.4,
                title="Trade Composition",
                color="metal",
                color_discrete_map=METAL_COLORS,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(empty_figure("Trade Composition"), use_container_width=True)

    with right:
        trend = data.groupby(["year", "flow"])["trade_value_usd"].sum().reset_index()
        if not trend.empty:
            fig = px.line(trend, x="year", y="trade_value_usd", color="flow", title="Trade Trend")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(empty_figure("Trade Trend"), use_container_width=True)

    st.markdown("##### Top Trading Partners")
    for_metal = data if metal == "All" else data[data["metal"] == metal]

    left, right = st.columns(2)
    with left:
        sold_to = (
            for_metal[for_metal["flow"] == "Export"]
            .groupby("partner")["trade_value_usd"]
            .sum()
            .nlargest(10)
            .reset_index()
        )
        if not sold_to.empty:
            fig = px.bar(
                sold_to,
                x="trade_value_usd",
                y="partner",
                orientation="h",
                title=f"Top Exports ({metal})",
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(empty_figure("Top Exports"), use_container_width=True)

    with right:
        bought_from = (
            for_metal[for_metal["flow"] == "Import"]
            .groupby("partner")["trade_value_usd"]
            .sum()
            .nlargest(10)
            .reset_index()
        )
        if not bought_from.empty:
            fig = px.bar(
                bought_from,
                x="trade_value_usd",
                y="partner",
                orientation="h",
                title=f"Top Imports ({metal})",
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(empty_figure("Top Imports"), use_container_width=True)


if compare_with != "None":
    left, right = st.columns(2)
    with left:
        show_country(country, in_range[in_range["reporter"] == country])
    with right:
        show_country(compare_with, in_range[in_range["reporter"] == compare_with])
else:
    show_country(country, in_range[in_range["reporter"] == country])
