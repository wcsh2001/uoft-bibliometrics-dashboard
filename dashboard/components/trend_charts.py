# dashboard/components/trend_charts.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc
import numpy as np


def build_citation_distribution_chart(works_df: pd.DataFrame) -> go.Figure:
    """
    Box plots of citation counts grouped by discipline.
    Outliers are shown as individual points.
    Capped at 99th percentile to prevent extreme outliers from crushing the chart.
    """
    cap = works_df["cited_by_count"].quantile(0.99)
    plot_df = works_df[works_df["top_concept"].notna()].copy()
    plot_df["cited_by_count_capped"] = plot_df["cited_by_count"].clip(upper=cap)

    # Order by median for readability
    order = (
        plot_df.groupby("top_concept")["cited_by_count_capped"]
        .median()
        .sort_values(ascending=False)
        .head(15)
        .index.tolist()
    )
    plot_df = plot_df[plot_df["top_concept"].isin(order)]

    fig = px.box(
        plot_df,
        x="top_concept", y="cited_by_count_capped",
        category_orders={"top_concept": order},
        title="Citation Distribution by Discipline (capped at 99th pct.)",
        labels={"top_concept": "", "cited_by_count_capped": "Citations"},
        template="plotly_white",
        color="top_concept",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(showlegend=False)
    fig.update_xaxes(tickangle=-35)
    fig.update_layout(margin=dict(t=60, b=120))
    return fig


def build_growth_rate_chart(works_df: pd.DataFrame) -> go.Figure:
    """
    Year-over-year publication growth rate (%) as a line chart.
    Useful for spotting research momentum or contraction.
    """
    yearly = works_df.groupby("year").size().reset_index(name="count")
    yearly = yearly.sort_values("year")
    yearly["yoy_growth"] = yearly["count"].pct_change() * 100

    fig = go.Figure()
    colors = ["#4CAF50" if v >= 0 else "#F44336" for v in yearly["yoy_growth"].fillna(0)]

    fig.add_trace(go.Bar(
        x=yearly["year"],
        y=yearly["yoy_growth"].round(1),
        marker_color=colors,
        name="YoY Growth %",
        hovertemplate="Year: %{x}<br>Growth: %{y:.1f}%<extra></extra>"
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="grey")

    fig.update_layout(
        title="Year-over-Year Publication Growth Rate",
        xaxis=dict(title="Year", tickmode="linear", dtick=2),
        yaxis=dict(title="Growth Rate (%)"),
        template="plotly_white",
        margin=dict(t=60, b=40)
    )
    return fig


def build_field_share_over_time(works_df: pd.DataFrame, top_n: int = 8) -> go.Figure:
    """
    Normalised stacked area chart showing each discipline's share of
    total annual output. Reveals if UofT is shifting its research focus.
    """
    top_concepts = (
        works_df["top_concept"]
        .value_counts()
        .head(top_n)
        .index.tolist()
    )
    plot_df = works_df[works_df["top_concept"].isin(top_concepts)].copy()
    plot_df["top_concept"] = plot_df["top_concept"].where(
        plot_df["top_concept"].isin(top_concepts), other="Other"
    )

    share = (
        plot_df.groupby(["year", "top_concept"])
        .size()
        .reset_index(name="count")
    )
    total_per_year = share.groupby("year")["count"].transform("sum")
    share["share_pct"] = share["count"] / total_per_year * 100

    fig = px.area(
        share,
        x="year", y="share_pct",
        color="top_concept",
        title=f"Discipline Share of Annual Output (Top {top_n} Fields)",
        labels={"share_pct": "Share (%)", "year": "Year", "top_concept": "Discipline"},
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_layout(
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40)
    )
    return fig


def build_citation_trend_by_field(works_df: pd.DataFrame, top_n: int = 6) -> go.Figure:
    """
    Line chart: average citations per work over time, one line per discipline.
    Shows which fields are producing increasingly high-impact research.
    """
    top_concepts = (
        works_df["top_concept"]
        .value_counts()
        .head(top_n)
        .index.tolist()
    )
    plot_df = works_df[works_df["top_concept"].isin(top_concepts)]

    trend = (
        plot_df.groupby(["year", "top_concept"])["cited_by_count"]
        .mean()
        .reset_index()
    )

    fig = px.line(
        trend,
        x="year", y="cited_by_count",
        color="top_concept",
        markers=True,
        title=f"Average Citations per Work Over Time (Top {top_n} Disciplines)",
        labels={"cited_by_count": "Avg Citations", "year": "Year", "top_concept": "Discipline"},
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(t=60, b=40)
    )
    return fig


def build_rolling_avg_chart(works_df: pd.DataFrame, window: int = 3) -> go.Figure:
    """
    Publication count per year with a rolling average overlay.
    Smooths out year-to-year noise to show the underlying trend.
    """
    yearly = works_df.groupby("year").size().reset_index(name="count").sort_values("year")
    yearly[f"rolling_{window}yr"] = yearly["count"].rolling(window, center=True).mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=yearly["year"], y=yearly["count"],
        name="Annual Count",
        marker_color="#BBDEFB",
        hovertemplate="Year: %{x}<br>Count: %{y}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=yearly["year"], y=yearly[f"rolling_{window}yr"].round(1),
        name=f"{window}-Year Rolling Avg",
        mode="lines",
        line=dict(color="#1565C0", width=2.5),
        hovertemplate=f"{window}yr avg: %{{y:.1f}}<extra></extra>"
    ))
    fig.update_layout(
        title=f"Publication Output with {window}-Year Rolling Average",
        xaxis=dict(title="Year", tickmode="linear", dtick=2),
        yaxis=dict(title="Publications"),
        template="plotly_white",
        hovermode="x unified",
        margin=dict(t=60, b=40)
    )
    return fig


# ── Layout Assembly ──────────────────────────────────────────────────────────

def render_trends_tab(works_df: pd.DataFrame) -> html.Div:
    """
    Full layout for the Trends deep-dive tab (if you add one).
    Can also be called from the Overview tab for secondary charts.
    """
    if works_df.empty:
        return html.Div("No data matches the current filters.", className="text-muted p-4")

    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=build_rolling_avg_chart(works_df)), md=6),
            dbc.Col(dcc.Graph(figure=build_growth_rate_chart(works_df)), md=6),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=build_field_share_over_time(works_df)), md=7),
            dbc.Col(dcc.Graph(figure=build_citation_trend_by_field(works_df)), md=5),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=build_citation_distribution_chart(works_df)), md=12),
        ])
    ])