# dashboard/components/summary_stats.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc


# ── KPI Cards ────────────────────────────────────────────────────────────────

def build_kpi_cards(works_df: pd.DataFrame, country_edges_df: pd.DataFrame) -> list:
    """
    Returns a list of dbc.Col KPI cards summarising the filtered dataset.
    Intended to be placed inside a dbc.Row.
    """
    total = len(works_df)
    avg_citations = round(works_df["cited_by_count"].mean(), 1) if total > 0 else 0
    oa_pct = round(works_df["is_oa"].mean() * 100, 1) if total > 0 else 0

    # Unique collaborating countries — from the pre-built edges table, filtered
    # to only works present in the current filtered set
    collab_countries = country_edges_df[
        country_edges_df["work_id"].isin(works_df["id"])
    ]["country_code"].nunique()

    metrics = [
        ("Total Publications",       total,             "primary", "bi bi-journal-text"),
        ("Avg Citations / Work",      avg_citations,     "success",  "bi bi-graph-up"),
        ("Open Access %",             f"{oa_pct}%",      "info",     "bi bi-unlock"),
        ("Collaborating Countries",   collab_countries,  "warning",  "bi bi-globe"),
    ]

    cards = []
    for label, value, color, _ in metrics:
        cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H3(str(value), className=f"text-{color} fw-bold mb-1"),
                        html.P(label, className="text-muted small mb-0"),
                    ]),
                    className="shadow-sm border-0 h-100"
                ),
                xs=12, sm=6, md=3
            )
        )
    return cards


# ── Overview Charts ───────────────────────────────────────────────────────────

def build_annual_output_chart(works_df: pd.DataFrame) -> go.Figure:
    """
    Dual-axis bar + line: publication count (bars) and avg citations (line).
    """
    yearly = (
        works_df.groupby("year")
        .agg(count=("id", "count"), avg_citations=("cited_by_count", "mean"))
        .reset_index()
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=yearly["year"], y=yearly["count"],
        name="Publications",
        marker_color="#003E74",
        opacity=0.85,
        yaxis="y1"
    ))

    fig.add_trace(go.Scatter(
        x=yearly["year"], y=yearly["avg_citations"].round(1),
        name="Avg Citations",
        mode="lines+markers",
        marker=dict(size=6, color="#E8A020"),
        line=dict(width=2, color="#E8A020"),
        yaxis="y2"
    ))

    fig.update_layout(
        title="Annual Publication Output & Average Citations",
        xaxis=dict(title="Year", tickmode="linear", dtick=2),
        yaxis=dict(title="Number of Publications", showgrid=True),
        yaxis2=dict(title="Avg Citations", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template="plotly_white",
        margin=dict(t=60, b=40)
    )
    return fig


def build_discipline_breakdown_chart(works_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Horizontal bar chart of the top N disciplines by publication count.
    """
    counts = (
        works_df["top_concept"]
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    counts.columns = ["discipline", "count"]
    counts = counts.sort_values("count")  # ascending so largest is at top

    fig = px.bar(
        counts, x="count", y="discipline",
        orientation="h",
        title=f"Top {top_n} Disciplines by Publication Count",
        labels={"count": "Publications", "discipline": ""},
        color="count",
        color_continuous_scale="Blues",
        template="plotly_white"
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(margin=dict(t=60, b=40, l=180))
    return fig


def build_oa_trend_chart(works_df: pd.DataFrame) -> go.Figure:
    """
    Stacked area chart of OA status (gold / green / hybrid / bronze / closed) over time.
    """
    oa_yearly = (
        works_df.groupby(["year", "oa_status"])
        .size()
        .reset_index(name="count")
    )

    # Define a consistent color palette
    oa_colors = {
        "gold":   "#F5A623",
        "green":  "#4CAF50",
        "hybrid": "#2196F3",
        "bronze": "#CD7F32",
        "closed": "#9E9E9E",
    }

    fig = go.Figure()
    for status, color in oa_colors.items():
        subset = oa_yearly[oa_yearly["oa_status"] == status]
        if subset.empty:
            continue
        fig.add_trace(go.Scatter(
            x=subset["year"], y=subset["count"],
            name=status.capitalize(),
            stackgroup="one",
            fillcolor=color,
            line=dict(color=color),
            hovertemplate=f"{status.capitalize()}: %{{y}}<extra></extra>"
        ))

    fig.update_layout(
        title="Open Access Status Over Time",
        xaxis=dict(title="Year", tickmode="linear", dtick=2),
        yaxis=dict(title="Publications"),
        hovermode="x unified",
        template="plotly_white",
        
        # THE FIX: Move the legend to the bottom center
        legend=dict(
            orientation="h", 
            yanchor="top", 
            y=-0.2, 
            xanchor="center", 
            x=0.5
        ),
        
        # Increase the bottom margin (b=80) to make room for the legend
        margin=dict(t=50, b=80, l=20, r=20) 
    )
    return fig


def build_type_pie_chart(works_df: pd.DataFrame, top_n: int = 5) -> go.Figure:
    """
    Donut chart of publication types.
    Limits to the top N types and groups the rest into 'Other' 
    to prevent label overcrowding and chart shrinking.
    """
    counts = works_df["type"].value_counts().reset_index()
    counts.columns = ["type", "count"]

    # Group everything outside the top 5 into "Other"
    if len(counts) > top_n:
        top_types = counts.head(top_n).copy()
        other_count = counts.iloc[top_n:]["count"].sum()
        
        # Use pandas concat to append the Other row safely
        other_row = pd.DataFrame([{"type": "Other", "count": other_count}])
        counts = pd.concat([top_types, other_row], ignore_index=True)

    # Format strings for a cleaner display (e.g., 'book-chapter' -> 'Book Chapter')
    counts["type"] = counts["type"].str.replace("-", " ").str.title()

    fig = px.pie(
        counts, values="count", names="type",
        title=f"Publication Types (Top {top_n})",
        hole=0.45,
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    # Force labels inside the pie slices so the chart stays large
    fig.update_traces(
        textinfo="percent+label", 
        textposition="inside",
        insidetextorientation="radial"
    )
    
    fig.update_layout(
        showlegend=False, 
        margin=dict(t=60, b=20, l=20, r=20)
    )
    
    return fig


# ── Layout Assembly ──────────────────────────────────────────────────────────

def render_summary_tab(works_df: pd.DataFrame, country_edges_df: pd.DataFrame) -> html.Div:
    """
    Assembles the full Overview tab layout.
    Called from callbacks.py when the Overview tab is active.
    """
    if works_df.empty:
        return html.Div("No data matches the current filters.", className="text-muted p-4")

    return html.Div([
        # Row 1: annual output (full width)
        dbc.Row([
            dbc.Col(dcc.Graph(figure=build_annual_output_chart(works_df)), width=12)
        ], className="mb-4"),

        # Row 2: disciplines (left) + OA trend (right)
        dbc.Row([
            dbc.Col(dcc.Graph(figure=build_discipline_breakdown_chart(works_df)), md=7),
            dbc.Col(dcc.Graph(figure=build_oa_trend_chart(works_df)), md=5),
        ], className="mb-4"),

        # Row 3: publication type donut (left) + simple stats table (right)
        dbc.Row([
            dbc.Col(dcc.Graph(figure=build_type_pie_chart(works_df)), md=5),
            dbc.Col(_build_stats_table(works_df), md=7),
        ])
    ])


def _build_stats_table(works_df: pd.DataFrame) -> dbc.Card:
    """
    Generates a compact descriptive statistics table grouped by discipline.
    """
    if works_df["top_concept"].isna().all():
        return html.Div()

    stats = (
        works_df.groupby("top_concept")
        .agg(
            Works=("id", "count"),
            Avg_Citations=("cited_by_count", "mean"),
            Median_Citations=("cited_by_count", "median"),
            OA_Rate=("is_oa", "mean"),
            Avg_Authors=("author_count", "mean"),
        )
        .reset_index()
        .sort_values("Works", ascending=False)
        .head(12)
    )
    stats["Avg_Citations"]    = stats["Avg_Citations"].round(1)
    stats["Median_Citations"] = stats["Median_Citations"].round(1)
    stats["OA_Rate"]          = (stats["OA_Rate"] * 100).round(1).astype(str) + "%"
    stats["Avg_Authors"]      = stats["Avg_Authors"].round(1)
    stats.columns             = ["Discipline", "Works", "Avg Cit.", "Med. Cit.", "OA Rate", "Avg Authors"]

    from dash import dash_table
    return dbc.Card([
        dbc.CardHeader("Summary Statistics by Discipline"),
        dbc.CardBody(
            dash_table.DataTable(
                data=stats.to_dict("records"),
                columns=[{"name": c, "id": c} for c in stats.columns],
                sort_action="native",
                page_size=12,
                style_table={"overflowX": "auto"},
                style_cell={"fontSize": "12px", "padding": "6px"},
                style_header={"fontWeight": "bold", "backgroundColor": "#f8f9fa"},
                style_data_conditional=[{
                    "if": {"row_index": "odd"},
                    "backgroundColor": "#fafafa"
                }]
            )
        )
    ], className="shadow-sm border-0 h-100")