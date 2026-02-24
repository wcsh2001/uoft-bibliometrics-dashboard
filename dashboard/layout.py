# dashboard/layout.py
import dash_bootstrap_components as dbc
from dash import dcc, html
from etl.load import load_all

# Load data using your existing ETL function
works, _, _ = load_all()

# Extract unique years and force them to be standard Python ints
years = sorted([int(y) for y in works["year"].dropna().unique()])

# Extract unique concepts from the nested list of dictionaries
unique_concepts = set()
# Drop NAs to prevent errors on rows with no concept data
for concept_list in works["all_top_concepts"].dropna():
    for concept in concept_list:
        unique_concepts.add(concept["name"])

concepts = sorted(list(unique_concepts))

sidebar = dbc.Card([
    html.H5("Filters", className="card-title"),
    html.Label("Publication Year Range"),
    dcc.RangeSlider(
        id="year-slider",
        min=min(years), max=max(years),
        value=[2020, 2024],
        marks={y: str(y) for y in years if y % 5 == 0},
        tooltip={"placement": "bottom"}
    ),
    html.Br(),
    html.Label("Discipline / Topic"),
    dcc.Dropdown(
        id="concept-filter",
        options=[{"label": c, "value": c} for c in concepts],
        multi=True,
        placeholder="Search all disciplines & sub-topics..."
    ),
    html.Br(),
    html.Label("Publication Type"),
    dcc.Dropdown(
        id="type-filter",
        options=[
            {"label": "Journal Article", "value": "article"},
            {"label": "Book Chapter", "value": "book-chapter"},
            {"label": "Preprint", "value": "preprint"},
        ],
        multi=True,
        placeholder="All types"
    ),
    html.Br(),
    html.Label("Open Access Status"),
    dcc.Checklist(
        id="oa-filter",
        options=[{"label": "Open Access only", "value": "oa"}],
        value=[]
    ),
], body=True)

tabs = dbc.Tabs([
    dbc.Tab(label="Overview & Trends", tab_id="overview"),
    dbc.Tab(label="Collaboration Map", tab_id="map"),
    dbc.Tab(label="Network Graph", tab_id="network"),
    dbc.Tab(label="Data Table", tab_id="table"),
], id="main-tabs", active_tab="overview")

layout = dbc.Container([
    dbc.Row([
        html.H2("University of Toronto Research Dashboard"),
        html.P("Explore UofT's research output, trends, and collaborations using OpenAlex data.")
    ]),
    html.Hr(),
    dbc.Row([
        dbc.Col(sidebar, width=3),
        dbc.Col([
            dbc.Row(id="kpi-cards"),
            html.Br(),
            tabs,
            html.Div(id="tab-content")
        ], width=9)
    ])
], fluid=True)