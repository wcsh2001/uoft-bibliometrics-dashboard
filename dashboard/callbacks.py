# dashboard/callbacks.py

from dash import Input, Output, callback, html, dcc, dash_table
import dash_bootstrap_components as dbc

from dashboard.components.summary_stats import render_summary_tab, build_kpi_cards
from dashboard.components.trend_charts import render_trends_tab
from dashboard.components.map_view import render_map_tab
from dashboard.components.network_view import render_network_tab, build_node_info_panel
from dashboard.components.network_view import render_network_tab, build_node_info_panel, _build_cytoscape_elements
from etl.load import load_all


# ── Load data once at module import time ─────────────────────────────────────
# All three tables are loaded here and shared across every callback.
# Because Dash runs callbacks in the same process, this is safe and efficient —
# no repeated disk reads per request.
works, country_edges, institution_edges = load_all()


# ── Shared filter helper ──────────────────────────────────────────────────────

# Inside dashboard/callbacks.py

def apply_filters(year_range, selected_concepts, types, oa):
    """
    Returns a filtered slice of the works DataFrame based on sidebar inputs.
    All callback functions call this before doing anything else.
    """
    # 1. Filter by Year
    filtered = works[
        (works["year"] >= year_range[0]) & (works["year"] <= year_range[1])
    ].copy()

    # 2. Filter by Concepts (Checking inside the nested dictionaries)
    if selected_concepts:
        # Create a boolean mask: True if any selected concept matches a concept name in the row's list
        mask = filtered["all_top_concepts"].apply(
            lambda concept_list: any(
                c["name"] in selected_concepts for c in concept_list
            ) if isinstance(concept_list, list) else False
        )
        filtered = filtered[mask]

    # 3. Filter by Publication Type
    if types:
        filtered = filtered[filtered["type"].isin(types)]
        
    # 4. Filter by Open Access Status
    if "oa" in (oa or []):
        filtered = filtered[filtered["is_oa"] == True]

    return filtered


# ── KPI Cards ─────────────────────────────────────────────────────────────────

@callback(
    Output("kpi-cards", "children"),
    [
        Input("year-slider", "value"),
        Input("concept-filter", "value"),
        Input("type-filter", "value"),
        Input("oa-filter", "value"),
    ]
)
def update_kpis(year_range, concepts, types, oa):
    filtered = apply_filters(year_range, concepts, types, oa)
    # Delegates to summary_stats.py which owns the card rendering logic
    return build_kpi_cards(filtered, country_edges)


# ── Tab Content ───────────────────────────────────────────────────────────────

@callback(
    Output("tab-content", "children"),
    [
        Input("main-tabs", "active_tab"),
        Input("year-slider", "value"),
        Input("concept-filter", "value"),
        Input("type-filter", "value"),
        Input("oa-filter", "value"),
    ]
)
def render_tab(active_tab, year_range, concepts, types, oa):
    filtered = apply_filters(year_range, concepts, types, oa)

    if active_tab == "overview":
        return render_summary_tab(filtered, country_edges)
    elif active_tab == "trends":
        return render_trends_tab(filtered)
    elif active_tab == "map":
        return render_map_tab(filtered, country_edges)
    elif active_tab == "network":
        return render_network_tab(institution_edges, filtered)
    elif active_tab == "table":
        return render_data_table(filtered)

    return html.Div("Select a tab above.", className="text-muted p-4")


# ── Data Table Tab ────────────────────────────────────────────────────────────
# Defined here rather than in a component file because it's simple enough
# to not warrant its own module — it's just a styled DataTable.

def render_data_table(filtered):
    if filtered.empty:
        return html.Div("No data matches the current filters.", className="text-muted p-4")

    display_cols = ["title", "year", "type", "top_concept",
                    "cited_by_count", "is_oa", "oa_status",
                    "author_count", "source_name"]
    
    # Only show columns that actually exist (guards against schema changes)
    available = [c for c in display_cols if c in filtered.columns]
    table_df = filtered[available].copy()

    # Human-readable column labels
    col_labels = {
        "title": "Title", "year": "Year", "type": "Type",
        "top_concept": "Discipline", "cited_by_count": "Citations",
        "is_oa": "Open Access", "oa_status": "OA Status",
        "author_count": "Authors", "source_name": "Journal/Source"
    }

    return html.Div([
        html.P(
            f"Showing {len(table_df):,} works. Click column headers to sort.",
            className="text-muted small mb-2"
        ),
        dash_table.DataTable(
            data=table_df.to_dict("records"),
            columns=[
                {"name": col_labels.get(c, c), "id": c}
                for c in available
            ],
            sort_action="native",
            filter_action="native",       # adds per-column search boxes
            page_size=20,
            page_action="native",
            style_table={"overflowX": "auto"},
            style_cell={
                "fontSize": "12px",
                "padding": "8px",
                "textAlign": "left",
                "maxWidth": "300px",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
            },
            style_header={
                "fontWeight": "bold",
                "backgroundColor": "#003E74",
                "color": "white",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
                {"if": {"filter_query": "{is_oa} = True"},
                 "backgroundColor": "#E8F5E9", "color": "#2E7D32"},
            ],
            tooltip_data=[
                {
                    "title": {"value": str(row.get("title", "")), "type": "markdown"}
                }
                for row in table_df.to_dict("records")
            ],
            tooltip_duration=None,
        )
    ])


# ── Network Graph Interactivity ───────────────────────────────────────────────

@callback(
    Output("node-info-panel", "children"),
    Input("institution-network", "tapNodeData")
)
def update_node_info(tap_data):
    return build_node_info_panel(tap_data)


@callback(
    Output("institution-network", "layout"),
    Input("network-layout-selector", "value")
)
def update_network_layout(layout_name):
    return {"name": layout_name, "animate": True, "animationDuration": 600}

@callback(
    Output("institution-network", "elements"),
    [
        Input("network-topn-slider", "value"),
        # We also pass the sidebar filters so the graph respects the current data slice
        Input("year-slider", "value"),
        Input("concept-filter", "value"),
        Input("type-filter", "value"),
        Input("oa-filter", "value"),
    ],
    prevent_initial_call=True
)
def update_network_elements(top_n, year_range, concepts, types, oa):
    """Listens to the slider and updates the nodes/edges dynamically."""
    filtered = apply_filters(year_range, concepts, types, oa)
    return _build_cytoscape_elements(institution_edges, filtered, top_n)