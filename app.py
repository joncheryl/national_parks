"""
Dash app for National Park units using dash-bootstrap-components.
"""

from dash import Dash, dcc, html, page_container
import dash_bootstrap_components as dbc

app = Dash(
    use_pages=True,
    title="NPS SCHTUFF",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
server = app.server

sidebar = html.Div(
    [
        dbc.Row(html.Img(src="assets/images/nps_logo.svg")),
        html.Hr(className="custom-hr"),
        dbc.Nav(
            [
                dbc.NavLink("NPS Unit Info", href="/", active="exact"),
                dbc.NavLink("NPS Distance Calculator", href="/page-1", active="exact"),
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
        html.Div(page_container, className="page-content"),
    ]
)


if __name__ == "__main__":
    app.run()
