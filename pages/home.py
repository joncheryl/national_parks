"""
Dashboard for looking at the 'visit-ability' of different national parks.
"""

# %%%
from urllib.parse import parse_qs
from dash import dcc, html, Input, Output, callback, register_page
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# %%

df = pd.read_csv("unit_visits.csv")
df["date"] = pd.to_datetime(df["date"])
df["month_num"] = df["date"].dt.month
df["month_name"] = df["date"].dt.month_name().str[:3]
df["year"] = df["date"].dt.year

df_wiki = pd.read_csv("wiki_data.csv")
df_wiki["log_acres"] = (
    df_wiki["area_acres"].fillna(10).clip(upper=3500000, lower=100000)
)

weather_df = pd.read_csv("weather_data.csv")
temp_df = pd.read_csv("temp_data.csv")


def adapt_round(number):
    """Helper function to adaptively round numbers"""
    if number >= 100:
        return f"{round(number):,}"
    elif number >= 10:
        return f"{number:,.1f}"
    else:
        return f"{number:,.2f}"


# %%

register_page(__name__, path="/")

#######################################################################################
######################################## LAYOUT #######################################
#######################################################################################
layout = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),
        html.H4("National Park Dashboard"),
        html.P("Select NPS Unit:"),
        dcc.Dropdown(
            id="dropdown",
            options=[
                {"label": name, "value": code}
                for code, name in df[["park_code", "park_name"]]
                .drop_duplicates()
                .values
            ],
            value="ZION",
            clearable=False,
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("NPS Unit Size", className="text-center"),
                            dbc.CardBody(
                                [
                                    html.H6(
                                        "-",
                                        id="area_id",
                                        className="card-text",
                                    )
                                ]
                            ),
                        ],
                        className="shadow-style",
                    ),
                    width=2,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Visitors (2024)", className="text-center"),
                            dbc.CardBody(
                                [
                                    html.H6(
                                        "-",
                                        id="visits_id",
                                        className="card-text",
                                    )
                                ]
                            ),
                        ],
                        className="shadow-style",
                    ),
                    width=2,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                "Visitor Density (2024)", className="text-center"
                            ),
                            dbc.CardBody(
                                [
                                    html.H6(
                                        "-",
                                        id="density_id",
                                        className="card-text",
                                    )
                                ]
                            ),
                        ],
                        className="shadow-style",
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Links", className="text-center"),
                            dbc.CardBody(
                                [
                                    html.A(
                                        "Official NPS page",
                                        href="http://www.google.com/",
                                        target="_blank",
                                        id="nps_url_id",
                                    ),
                                    html.Br(),
                                    html.A(
                                        "Wikipedia page",
                                        href="http://www.google.com/",
                                        target="_blank",
                                        id="wiki_id",
                                    ),
                                ],
                                className="text-center",
                            ),
                        ],
                        className="shadow-style",
                    ),
                    width=3,
                ),
            ],
            justify="center",
            align="center",
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        id="monthly_visits_graph_id",
                        figure={},
                        className="chart-style",
                    ),
                ),
                dbc.Col(
                    dcc.Graph(
                        id="graph_years",
                        figure={},
                        className="chart-style",
                    ),
                    width=4,
                ),
                dbc.Col(
                    dcc.Graph(
                        id="weather_id",
                        figure={},
                        className="chart-style",
                    ),
                    width=4,
                ),
            ],
            className="mb-4",
        ),
    ],
    fluid=True,
)


####################################
# Callback to sync dropdown and url search terms.
####################################
@callback(
    Output("dropdown", "value"),
    Input("url", "search"),
)
def sync_dropdown_with_url(search):
    """Make dropdown menu same as search term in url."""
    if not search:
        return "ZION"  # default

    query_params = parse_qs(search.lstrip("?"))
    return query_params.get("park", ["ZION"])[0]


####################################
# Callback to change text displays
####################################
@callback(
    Output(component_id="area_id", component_property="children"),
    Output(component_id="visits_id", component_property="children"),
    Output(component_id="density_id", component_property="children"),
    Output(component_id="wiki_id", component_property="href"),
    Output(component_id="nps_url_id", component_property="href"),
    Input(component_id="dropdown", component_property="value"),
)
def display_text(selected_park_code):
    """Lookup data of NPS unit for card component texts"""

    park_data = df_wiki.loc[df_wiki["park_code"] == selected_park_code,]

    # NPS Unit area
    acres = park_data["area_acres"].iloc[0]
    if pd.isna(acres):
        area_text = "-"
    else:
        area_text = adapt_round(park_data["area_acres"].iloc[0]) + " acres"

    # NPS Unit visits (2024)
    visitors_2024 = df.loc[
        (df["park_code"] == selected_park_code) & (df["year"] == 2024), "visits"
    ].sum()
    if pd.isna(visitors_2024):
        visits_text = "-"
    else:
        visits_text = f"{round(visitors_2024):,} visits"

    # NPS Unit visits per acre (2024)
    visits_per_acre = visitors_2024 / park_data["area_acres"].iloc[0]
    if pd.isna(visits_per_acre):
        visits_per_acre_text = "-"
    else:
        visits_per_acre_text = adapt_round(visits_per_acre) + " visitors per acres"

    # Wikipedia link
    wiki_text = park_data["wiki_url"].iloc[0]

    # Official NPS link
    nps_link_text = park_data["nps_url"].iloc[0]

    return (
        area_text,
        visits_text,
        visits_per_acre_text,
        wiki_text,
        nps_link_text,
    )


####################
# Generate bar graph of average visits per month
####################
@callback(
    Output(component_id="monthly_visits_graph_id", component_property="figure"),
    Input(component_id="dropdown", component_property="value"),
)
def display_bar(selected_park_code):
    """Update graph."""
    local_df = df.loc[
        df["park_code"] == selected_park_code,
        ["date", "month_num", "month_name", "visits", "park_name"],
    ]

    monthly = (
        local_df.groupby(["month_num", "month_name"])["visits"].mean().reset_index()
    )
    monthly = monthly.sort_values("month_num")
    monthly["visits_rounded"] = monthly["visits"].astype(int).map(lambda x: f"{x:,}")

    fig = (
        px.bar(
            monthly,
            x="month_name",
            y="visits",
            title="Average Monthly Visits",
            range_y=[0, 1.1 * max(monthly["visits"])],
            text="visits_rounded",
            color_discrete_sequence=["#4e7a3e"],
            hover_name="month_name",
            hover_data={"visits": ":.0f", "month_name": False, "visits_rounded": False},
        )
        # .update_traces(hovertemplate=None)
        .update_layout(
            template="plotly_white",
            xaxis_title="month",
            yaxis_title="average visits",
            xaxis={"tickangle": 45},
            margin=dict(l=40, r=30),
        )
    )

    return fig


####################
# Callback for graph of annual visitations.
####################
@callback(
    Output(component_id="graph_years", component_property="figure"),
    Input(component_id="dropdown", component_property="value"),
)
def display_graph_years(selected_park_code):
    """Update graph."""
    local_df = df.loc[
        df["park_code"] == selected_park_code,
        ["year", "visits", "park_name"],
    ]

    yearly = local_df.groupby(["year"])["visits"].sum().reset_index()

    fig = px.line(
        yearly,
        x="year",
        y="visits",
        title="Annual Visits",
        range_y=[0, 1.1 * max(yearly["visits"])],
        color_discrete_sequence=["#4e7a3e"],
    ).update_layout(
        template="plotly_white",
        xaxis={"tickangle": 45},
        margin=dict(l=40, r=30),
    )

    return fig


####################
# Generate graph of average monthly temps.
####################
@callback(
    Output(component_id="weather_id", component_property="figure"),
    Input(component_id="dropdown", component_property="value"),
)
def display_weather(selected_park_code):
    """Generate line graph of average monthly temps."""

    station = weather_df.loc[
        weather_df["park_code"] == selected_park_code, "nearest_station"
    ].iloc[0]

    local_temps = temp_df.loc[
        temp_df["station"] == station, ["date", "datatype", "value", "month_abbr"]
    ]

    fig = px.line(
        local_temps,
        x="month_abbr",
        y="value",
        title="Average Monthly Temps",
        subtitle="at lat/lon found on Wikipedia page",
        color="datatype",
        color_discrete_sequence=["#EF553B", "#636EFA"],
        labels={
            "datatype": "",
        },
        hover_data={"month_abbr": False},
    ).update_layout(
        template="plotly_white",
        xaxis_title="month",
        yaxis_title="temp (\u00b0F)",
        xaxis={"tickangle": 45},
        hovermode="x unified",
        margin=dict(l=40),
    )

    return fig
