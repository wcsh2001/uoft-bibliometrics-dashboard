# University of Toronto Bibliometric Dashboard (to-be-updated)

An interactive web dashboard built with Python and Plotly Dash to explore the research output, open-access trends, and global collaboration networks of University of Toronto authors. 

The data is sourced directly from the [OpenAlex API](https://openalex.org/), processed through a custom ETL pipeline, and visualized using dynamic charts, maps, and network graphs.

## Features
* **Automated ETL Pipeline:** Extracts deeply nested JSON data from OpenAlex, transforms it into relational tables, and saves it locally as highly compressed Parquet files.
* **Global Collaboration Map:** A Plotly choropleth map highlighting international co-authorship volume.
* **Institutional Network Graph:** An interactive, dynamically scaled network graph of UofT's top partner institutions built with Dash Cytoscape.
* **Trend Analysis:** Breakdown of open access status, publication types, and year-over-year citation impact.
* **Granular Filtering:** Allows users to slice the data by publication year range, specific sub-disciplines, and publication types.

## Tech Stack
* **Data Extraction:** `pyalex`, `python-dotenv`
* **Data Processing:** `pandas`, `pyarrow` (Parquet)
* **Web Framework:** `dash`, `dash-bootstrap-components`
* **Visualizations:** `plotly`, `dash-cytoscape`

## Project Structure
```text
uoft-bibliometrics-dashboard/
├── data/
│   ├── processed/          # Cleaned .parquet files for the dashboard
│   └── raw/                # Raw API data backups
├── dashboard/
│   ├── components/         # Modular visualization scripts (map, network, etc.)
│   ├── callbacks.py        # Dash interactivity logic
│   └── layout.py           # Dash UI layout
├── etl/
│   ├── extract.py          # API connection and pagination
│   ├── transform.py        # Data flattening and edge list generation
│   ├── load.py             # Parquet read/write helpers
│   └── refresh.py          # Main execution script for the pipeline
├── .env                    # Local environment variables (NOT tracked in git)
├── .gitignore              # Git ignore rules
├── app.py                  # Main dashboard entry point
├── recover.py              # Fallback script to bypass API extraction
└── requirements.txt        # Python dependencies
