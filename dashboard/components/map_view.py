# dashboard/components/map_view.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc
import pycountry

def _iso2_to_iso3(code: str) -> str | None:
    try:
        country = pycountry.countries.get(alpha_2=code.upper())
        return country.alpha_3 if country else None
    except Exception:
        return None

def _prepare_map_data(works_df: pd.DataFrame, country_edges_df: pd.DataFrame, agg_metric: str = "works"):
    filtered_edges = country_edges_df[
        country_edges_df["work_id"].isin(works_df["id"])
    ].copy()

    if filtered_edges.empty:
        return pd.DataFrame(), ""

    # Aggregating by country only, removing year for speed and stability
    if agg_metric == "works":
        agg = filtered_edges.groupby(["country_code"]).size().reset_index(name="value")
        agg.rename(columns={"value": "Co-authored Works"}, inplace=True)
        value_col = "Co-authored Works"
    else:
        agg = filtered_edges.groupby(["country_code"])["work_id"].nunique().reset_index(name="Unique Works")
        value_col = "Unique Works"

    agg["iso3"] = agg["country_code"].apply(_iso2_to_iso3)
    agg = agg.dropna(subset=["iso3"])

    # Map country names efficiently
    agg["country_name"] = agg["iso3"].apply(
        lambda c: pycountry.countries.get(alpha_3=c).name if pycountry.countries.get(alpha_3=c) else c
    )

    return agg, value_col

def build_choropleth(works_df: pd.DataFrame, country_edges_df: pd.DataFrame) -> go.Figure:
    """Static choropleth map optimized for performance."""
    agg, value_col = _prepare_map_data(works_df, country_edges_df, agg_metric="works")
    
    if agg.empty:
        return _empty_figure("No collaboration data available for this filter selection.")

    fig = px.choropleth(
        agg,
        locations="iso3",
        color=value_col,
        hover_name="country_name",
        color_continuous_scale="YlOrRd",
        projection="natural earth",
        title="International Research Collaborations (Selected Period)",
        template="plotly_white"
    )
    
    fig.update_geos(
        showcoastlines=True, coastlinecolor="lightgrey",
        showland=True, landcolor="#F5F5F5",
        showocean=True, oceancolor="#EBF5FB",
        showframe=False
    )
    
    fig.update_layout(
        height=550, 
        margin=dict(t=60, b=20, l=0, r=0),
        coloraxis_colorbar=dict(title="Works", thickness=12)
    )
    
    return fig

def build_top_countries_bar(works_df: pd.DataFrame, country_edges_df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    """Static horizontal bar chart of the top N collaborating countries."""
    filtered_edges = country_edges_df[country_edges_df["work_id"].isin(works_df["id"])]
    
    if filtered_edges.empty:
        return _empty_figure("No collaboration data.")

    counts = (
        filtered_edges.groupby("country_code")
        .size()
        .reset_index(name="works")
        .sort_values("works", ascending=True)
        .tail(top_n)
    )

    counts["country_name"] = counts["country_code"].apply(
        lambda c: pycountry.countries.get(alpha_2=c).name
        if pycountry.countries.get(alpha_2=c) else c
    )

    fig = px.bar(
        counts, x="works", y="country_name",
        orientation="h",
        title=f"Top {top_n} Collaborating Countries",
        labels={"works": "Co-authored Works", "country_name": ""},
        color="works",
        color_continuous_scale="Blues",
        template="plotly_white"
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(margin=dict(t=60, b=40, l=140))
    
    return fig

def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color="grey")
    )
    fig.update_layout(template="plotly_white", height=400)
    return fig

def render_map_tab(works_df: pd.DataFrame, country_edges_df: pd.DataFrame) -> html.Div:
    """Full layout for the Collaboration Map tab."""
    if works_df.empty:
        return html.Div("No data matches the current filters.", className="text-muted p-4")

    return html.Div([
        dbc.Row([
            dbc.Col(html.P(
                "The map shows countries with which UofT researchers have published co-authored works "
                "during the selected time period.",
                className="text-muted small"
            ))
        ]),
        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    figure=build_choropleth(works_df, country_edges_df),
                    config={"displayModeBar": True, "scrollZoom": True}
                ),
                width=12
            )
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(
                dcc.Graph(figure=build_top_countries_bar(works_df, country_edges_df)),
                width=12
            )
        ])
    ])