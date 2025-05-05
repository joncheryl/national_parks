"""
Dash app for National Park units using dash-bootstrap-components.
"""

# %%
from dash import Dash, dcc, html, page_container
import dash_bootstrap_components as dbc

# import numpy as np
import pandas as pd

# import plotly.express as px

# %%

df = pd.read_csv("unit_visits.csv")
df["date"] = pd.to_datetime(df["date"])
df["month_num"] = df["date"].dt.month
df["month_name"] = df["date"].dt.month_name().str[:3]
df["year"] = df["date"].dt.year

df_wiki = pd.read_csv("wiki_data.csv")
df_wiki = df_wiki.dropna(subset=["area_acres", "lat", "lon"])
df_wiki["log_acres"] = df_wiki["area_acres"].clip(upper=3500000, lower=100000)

# %%

app = Dash(
    use_pages=True,
    title="NPS SCHTUFF",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
server = app.server

# Add this to customize the overall body style
# Could add in a seperate css/style.css file
app.index_string = app.index_string.replace(
    "</head>",
    """
<style>
  body {
    background-color: #d2e5cb;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    color: #333;
  }
</style>
</head>
""",
)

# the styles for the main content position it to the right of the sidebar and
# add some padding.
# CONTENT_STYLE = {
#     "margin-left": "18rem",
#     "margin-right": "2rem",
#     "padding": "2rem 1rem",
#     "background-color": "#f5f5f5",
# }

HR_STYLE = {
    "borderColor": "#888888",
    "opacity": "1",
}

sidebar = html.Div(
    [
        dbc.Row(html.Img(src="assets/images/nps_logo.svg")),
        html.Hr(style=HR_STYLE),
        dbc.Nav(
            [
                dbc.NavLink("NPS Database", href="/", active="exact"),
                dbc.NavLink("NPS Unit Info", href="/page-1", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
        html.Div(
            [
                html.Span("Made by "),
                html.Br(),
                html.A(
                    "John Sherrill",
                    href="https://joncheryl.github.io/",
                    target="_blank",
                ),
                html.Br(),
                html.Span("Built with "),
                html.Br(),
                html.A(
                    "Plotly Dash",
                    href="https://dash.plotly.com/",
                    target="_blank",
                ),
            ],
            className="subtitle-sidebar",
            style={"position": "absolute", "bottom": "10px", "width": "100%"},
        ),
    ],
    className="sidebar",
)

app.layout = html.Div(
    [
        dcc.Location(id="url"),
        sidebar,
        html.Div(page_container, className="page-content"),  # style=CONTENT_STYLE),
    ]
)


if __name__ == "__main__":
    app.run()
