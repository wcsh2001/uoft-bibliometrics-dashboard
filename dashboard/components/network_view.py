# dashboard/components/network_view.py
import pandas as pd
import dash_cytoscape as cyto
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

# Register Cytoscape layout algorithms
cyto.load_extra_layouts()

UOFT_NODE_ID = "University of Toronto"


def _build_cytoscape_elements(
    institution_edges_df: pd.DataFrame,
    works_df: pd.DataFrame,
    top_n: int = 20  # <-- Changed default to 20
) -> list:
    """
    Builds the list of Cytoscape node and edge elements.
    Nodes are institutions; dynamically scaled by relative co-authorship volume.
    """
    filtered = institution_edges_df[
        institution_edges_df["work_id"].isin(works_df["id"])
    ]

    if filtered.empty:
        return []

    edge_agg = (
        filtered.groupby(["source", "target", "target_country"])
        .size()
        .reset_index(name="weight")
        .sort_values("weight", ascending=False)
    )

    top_targets = edge_agg.head(top_n)["target"].unique()
    edge_agg = edge_agg[edge_agg["target"].isin(top_targets)]

    # --- THE DYNAMIC SIZING FIX ---
    # Find the bounds of our current data slice
    max_weight = edge_agg["weight"].max()
    min_weight = edge_agg["weight"].min()
    
    # Define our visual pixel bounds (smallest node vs largest node)
    MIN_PX = 15
    MAX_PX = 65

    def calculate_node_size(w):
        if max_weight == min_weight: # Fallback if all institutions have the exact same count
            return (MIN_PX + MAX_PX) / 2
        # Min-Max Normalization formula
        return MIN_PX + ((w - min_weight) / (max_weight - min_weight)) * (MAX_PX - MIN_PX)
    # ------------------------------

    elements = []
    seen_nodes = set()

    elements.append({
        "data": {"id": UOFT_NODE_ID, "label": "U of T", "size": 75, "type": "hub"},
        "classes": "hub"
    })
    seen_nodes.add(UOFT_NODE_ID)

    for _, row in edge_agg.iterrows():
        if row["target"] not in seen_nodes:
            elements.append({
                "data": {
                    "id": row["target"],
                    "label": row["target"],
                    "country": row.get("target_country", ""),
                    
                    # Apply the dynamic scaling function
                    "size": calculate_node_size(row["weight"]),
                    
                    "works_count": int(row["weight"]),
                    "type": "institution"
                },
                "classes": "institution"
            })
            seen_nodes.add(row["target"])

        elements.append({
            "data": {
                "source": UOFT_NODE_ID,
                "target": row["target"],
                "weight": int(row["weight"]),
                "label": str(int(row["weight"]))
            }
        })

    return elements


def _cytoscape_stylesheet() -> list:
    return [
        # Hub node
        {
            "selector": ".hub",
            "style": {
                "background-color": "#003E74",
                "width": "60px", "height": "60px",
                "label": "data(label)",
                "color": "#fff",
                "font-size": "11px",
                "text-valign": "center",
                "text-halign": "center",
                "font-weight": "bold",
                "border-width": 2,
                "border-color": "#fff"
            }
        },
        # Institution nodes
        {
            "selector": ".institution",
            "style": {
                "background-color": "#E8A020",
                "width": "data(size)", "height": "data(size)",
                "label": "data(label)",
                "font-size": "9px",
                "text-valign": "bottom",
                "text-halign": "center",
                "color": "#333",
                "text-wrap": "wrap",
                "text-max-width": "80px"
            }
        },
        # Edges
        {
            "selector": "edge",
            "style": {
                "width": "mapData(weight, 1, 50, 1, 8)",
                "line-color": "#ccc",
                "opacity": 0.7,
                "curve-style": "bezier"
            }
        },
        # Hover highlight
        {
            "selector": "node:selected",
            "style": {
                "border-width": 3,
                "border-color": "#E53935",
                "background-color": "#FFCDD2"
            }
        },
        {
            "selector": "edge:selected",
            "style": {"line-color": "#E53935", "opacity": 1}
        }
    ]


def build_network_graph(
    institution_edges_df: pd.DataFrame,
    works_df: pd.DataFrame,
    top_n: int = 40,
    layout: str = "cose"
) -> cyto.Cytoscape:

    """
    Returns a Dash Cytoscape component (the network graph).
    layout options: 'cose' (force-directed), 'circle', 'concentric', 'breadthfirst'
    """
    elements = _build_cytoscape_elements(institution_edges_df, works_df, top_n)

    
    return cyto.Cytoscape(
        id="institution-network",
        elements=elements,
        layout={
            "name": layout,
            "animate": False,          # <-- TURN THIS OFF
            "animationDuration": 0,    # <-- SET TO ZERO
            "nodeRepulsion": 8000,
            "idealEdgeLength": 100,
            "gravity": 0.25
        },
        stylesheet=_cytoscape_stylesheet(),
        style={"width": "100%", "height": "580px", "background": "#FAFAFA"},
        minZoom=0.3,
        maxZoom=3.0,
        responsive=True
    )


def build_top_institutions_bar(
    institution_edges_df: pd.DataFrame,
    works_df: pd.DataFrame,
    top_n: int = 20
) -> go.Figure:
    """
    Horizontal bar chart: top N partner institutions by number of co-authored works.
    Complements the network graph with precise counts.
    """
    filtered = institution_edges_df[
        institution_edges_df["work_id"].isin(works_df["id"])
    ]
    if filtered.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data.", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

    counts = (
        filtered.groupby(["target", "target_country"])
        .size()
        .reset_index(name="works")
        .sort_values("works", ascending=True)
        .tail(top_n)
    )

    fig = px.bar(
        counts, x="works", y="target",
        orientation="h",
        color="target_country",
        title=f"Top {top_n} Partner Institutions by Co-authored Works",
        labels={"works": "Co-authored Works", "target": "", "target_country": "Country"},
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
        margin=dict(t=60, b=40, l=220)
    )
    return fig


# ── Node click info panel ────────────────────────────────────────────────────

def build_node_info_panel(tap_node_data: dict | None) -> html.Div:
    """
    Displayed beside the network graph. Shows details for whichever
    node the user clicks.
    """
    if not tap_node_data or tap_node_data.get("type") == "hub":
        return html.Div(
            "Click on an institution node to see details.",
            className="text-muted small p-3"
        )
    return dbc.Card([
        dbc.CardHeader(tap_node_data.get("label", "Institution")),
        dbc.CardBody([
            html.P(f"Country: {tap_node_data.get('country', 'N/A')}"),
            
            # THE FIX: Use works_count instead of size
            html.P(f"Co-authored Works: {tap_node_data.get('works_count', 'N/A')}")
        ])
    ], className="shadow-sm border-0")


# ── Layout Assembly ──────────────────────────────────────────────────────────

def render_network_tab(
    institution_edges_df: pd.DataFrame,
    works_df: pd.DataFrame
) -> html.Div:
    """
    Full layout for the Network Graph tab.
    Left: Cytoscape graph. Right: node info panel + controls.
    Bottom: top institutions bar chart.
    """
    if works_df.empty:
        return html.Div("No data matches the current filters.", className="text-muted p-4")

    layout_options = [
        {"label": "Force-directed (CoSE)",  "value": "cose"},
        {"label": "Circle",                  "value": "circle"},
        {"label": "Concentric",              "value": "concentric"},
        {"label": "Breadth-first",           "value": "breadthfirst"},
    ]

    return html.Div([
        dbc.Row([
            dbc.Col(html.P(
                "Nodes represent research institutions. Edge thickness reflects the number of "
                "co-authored works. Click a node for details. Use the layout selector to rearrange.",
                className="text-muted small"
            ))
        ]),

        # Controls
        dbc.Row([
            dbc.Col([
                html.Label("Graph Layout", className="small fw-bold"),
                dcc.Dropdown(
                    id="network-layout-selector",
                    options=layout_options,
                    value="cose",
                    clearable=False,
                    style={"width": "240px"}
                )
            ], width="auto"),
            dbc.Col([
                html.Label("Max Institutions Shown", className="small fw-bold"),
                dcc.Slider(
                    id="network-topn-slider",
                    min=10, max=40, step=10, value=40,
                    marks={v: str(v) for v in [10, 20, 30, 40]},
                    tooltip={"placement": "bottom"}
                )
            ], md=4)
        ], className="mb-3 align-items-end"),

        # Graph + info panel
        dbc.Row([
            dbc.Col(
                build_network_graph(institution_edges_df, works_df),
                md=9
            ),
            dbc.Col(
                html.Div(id="node-info-panel", children=build_node_info_panel(None)),
                md=3
            )
        ], className="mb-4"),

        # Bar chart below
        dbc.Row([
            dbc.Col(
                dcc.Graph(figure=build_top_institutions_bar(institution_edges_df, works_df)),
                width=12
            )
        ])
    ])