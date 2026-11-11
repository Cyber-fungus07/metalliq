import os
import tempfile

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from pyvis.network import Network

from src.data_loader import load_trade_flows
from src.constants import METALS, YEARS

st.set_page_config(page_title="Trade Networks", page_icon="🔗", layout="wide")

st.title("🔗 Trade Networks")
st.markdown("Explore bilateral trade flows and network structures.")

st.sidebar.header("Network Settings")
metal = st.sidebar.selectbox("Select Metal", list(METALS.keys()))
year = st.sidebar.selectbox("Select Year", sorted(YEARS, reverse=True))
top_n = st.sidebar.slider("Top N Routes", 5, 50, 15)
min_trade_value = st.sidebar.number_input("Min Trade Value (USD)", min_value=0, value=1000000, step=1000000)


@st.cache_data
def top_routes(metal_name, trade_year, limit, floor_value):
    trades = load_trade_flows()
    # Exports define each route's source -> target direction.
    exports = trades[
        (trades["metal"] == metal_name)
        & (trades["year"] == trade_year)
        & (trades["flow"] == "Export")
    ]
    exports = exports[exports["trade_value_usd"] >= floor_value]
    return exports.nlargest(limit, "trade_value_usd")


routes = top_routes(metal, year, top_n, min_trade_value)
if routes.empty:
    st.warning("No trade routes found for these settings. Try lowering the minimum value.")
    st.stop()

st.subheader(f"Top Trade Flows: {metal} ({year})")

sources = routes["reporter"].tolist()
targets = routes["partner"].tolist()
nodes = list(pd.unique(sources + targets))
node_ids = {name: i for i, name in enumerate(nodes)}

fig = go.Figure(
    data=[
        go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=nodes,
                color="blue",
            ),
            link=dict(
                source=[node_ids[name] for name in sources],
                target=[node_ids[name] for name in targets],
                value=routes["trade_value_usd"].tolist(),
            ),
        )
    ]
)
fig.update_layout(title_text="Sankey Diagram of Trade Flows", font_size=10, height=600)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Interactive Network Graph")

net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", directed=True)
net.barnes_hut()

totals = {}
for _, row in routes.iterrows():
    totals[row["reporter"]] = totals.get(row["reporter"], 0) + row["trade_value_usd"]
    totals[row["partner"]] = totals.get(row["partner"], 0) + row["trade_value_usd"]

for name, total in totals.items():
    net.add_node(name, label=name, title=f"{name}: ${total:,.0f}", size=max(10, total / 1e8))

for _, row in routes.iterrows():
    net.add_edge(
        row["reporter"],
        row["partner"],
        value=row["trade_value_usd"],
        title=f"${row['trade_value_usd']:,.0f}",
    )

tmp_path = None
try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        tmp_path = tmp.name
    net.save_graph(tmp_path)
    with open(tmp_path, encoding="utf-8") as handle:
        components.html(handle.read(), height=600)
except Exception as error:
    st.error(f"Could not render network graph: {error}")
finally:
    if tmp_path and os.path.exists(tmp_path):
        os.unlink(tmp_path)

st.subheader("Top Trade Routes Data")
columns = ["reporter", "partner", "trade_value_usd", "net_weight_kg"]
st.dataframe(
    routes[columns].sort_values("trade_value_usd", ascending=False),
    use_container_width=True,
    hide_index=True,
)
