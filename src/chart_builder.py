"""Small plot helpers shared by the dashboard pages."""

import plotly.graph_objects as go


def _dark_layout(fig, title):
    fig.update_layout(
        template="plotly_dark",
        title=title,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def empty_figure(message="Waiting for data..."):
    """Placeholder shown when a filter combination returns no rows."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=20),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _dark_layout(fig, "")
