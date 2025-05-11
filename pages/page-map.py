"""
Dashboard for looking at the 'visibility' of different national parks.
"""

# %%%
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


def adapt_round(number):
    """Helper function to adaptively round numbers"""
    if number >= 100:
        return f"{round(number):,}"
    elif number >= 10:
        return f"{number:,.1f}"
    else:
        return f"{number:,.2f}"


# %%

register_page(__name__, path="/page-map")

#######################################################################################
######################################## LAYOUT #######################################
#######################################################################################
layout = dbc.Container(
    [
        html.H4("Map of All National Park Service Units"),
        html.P("Select NPS Unit:"),
        dcc.Dropdown(
            id="dropdown",
            options=[
                {"label": name, "value": code}
                for code, name in df[["park_code", "park_name"]]
                .drop_duplicates()
                .values
            ],
            value="GLAC",
            clearable=False,
        ),
        html.Br(),
        dcc.Graph(
            id="map_id",
            figure={},
            className="chart-style",
        ),
    ]
)


####################
# Callback for map that's centered at NPS unit.
####################
@callback(
    Output(component_id="map_id", component_property="figure"),
    Input(component_id="dropdown", component_property="value"),
)
def display_map(selected_park_code):
    """Update graph."""

    center_of_map = (
        df_wiki.loc[df_wiki["park_code"] == selected_park_code, ["lat", "lon"]]
        .iloc[0]
        .to_dict()
    )

    if pd.isna(center_of_map["lat"]):
        center_of_map["lat"] = 39
        center_of_map["lon"] = -77

    # Make column of dataframe for labeling of color legend.
    df_wiki["acres"] = df_wiki["area_acres"].where(
        df_wiki["park_code"] != selected_park_code, 10000000
    )
    # Make column of dataframe for labeling of sizes.
    df_wiki["size"] = df_wiki["log_acres"].where(
        df_wiki["park_code"] != selected_park_code, 10000000
    )

    fig_map = px.scatter_map(
        df_wiki,
        lat="lat",
        lon="lon",
        size="size",
        color="acres",
        hover_name="park_name",
        hover_data={col: False for col in df_wiki.columns},
        color_continuous_scale=px.colors.cyclical.IceFire,
        zoom=1.7,
        map_style="basic",
        center=center_of_map,
    )

    fig_map.update_layout(map_style="open-street-map")
    fig_map.update_layout(margin={"r": 13, "t": 13, "l": 13, "b": 13})

    return fig_map
