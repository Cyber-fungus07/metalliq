import streamlit as st
import plotly.express as px

from src.data_loader import load_trade_flows
from src.data_processor import format_usd

st.set_page_config(page_title="Global Metals Trade", page_icon="🌍", layout="wide")

st.title("🌍 Global Trade of Valuable Metals")
st.markdown("### Discover the flow of critical and precious metals across the globe.")
st.markdown("Explore imports, exports, and market trends of materials driving the modern economy — from gold and silver to rare earths and battery metals.")
st.divider()

trades = load_trade_flows()

if trades.empty:
    st.error("⚠️ No data available! Please run the data download scripts first.")
    st.stop()

# Halve the total so mirrored import/export legs aren't counted twice.
total_trade = trades["trade_value_usd"].sum() / 2
year_span = f"{trades['year'].min()} - {trades['year'].max()}"

cards = st.columns(4)
cards[0].metric("Total Global Trade", format_usd(total_trade))
cards[1].metric("Countries Tracked", trades["reporter"].nunique())
cards[2].metric("Metals Covered", trades["metal"].nunique())
cards[3].metric("Years of Data", year_span)

st.divider()

st.subheader("Top Metals by Total Trade Value")

by_metal = trades.groupby("metal")["trade_value_usd"].sum().reset_index()
by_metal["trade_value_usd"] = by_metal["trade_value_usd"] / 2
by_metal = by_metal.sort_values("trade_value_usd", ascending=True)

fig = px.bar(by_metal, x="trade_value_usd", y="metal", orientation="h", template="plotly_dark")
fig.update_layout(
    xaxis_title="Total Trade Value (USD)",
    yaxis_title="",
    height=400,
    margin=dict(l=0, r=0, t=30, b=0),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.markdown("### 🧭 Explore the Dashboard")
left, middle, right = st.columns(3)

with left:
    st.markdown("#### 🗺️ Global Trade Map\nVisualize trade flows across the world on an interactive choropleth map.")
    st.markdown("#### 📈 Price & Volume Trends\nSee how metal prices correlate with global trading volumes over time.")

with middle:
    st.markdown("#### 🔗 Trade Network\nExplore the complex web of trading partners using network graphs.")
    st.markdown("#### 📊 Country Deep Dive\nGet a detailed breakdown of a specific country's imports and exports.")

with right:
    st.markdown("#### 🧮 Data Explorer\nDive into the raw data, filter, sort, and export to CSV for your own analysis.")

st.divider()

st.markdown("""
**Data Sources:**
- UN Comtrade (Trade Flows)
- World Bank / IMF (Pricing Data)

*Built with ❤️ using Streamlit & Plotly*
""")
