import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="UofT Research Dashboard",
    suppress_callback_exceptions=True
)
server = app.server  # For deployment

from dashboard.layout import layout
from dashboard import callbacks  # noqa: registers callbacks

app.layout = layout

if __name__ == "__main__":
    app.run(debug=True)