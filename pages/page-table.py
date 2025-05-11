"""
Page for showing table of all National Parks.

Should get park name to be link.

Park Name | average visits since 2021 | visitors per acre | distance from (x, y)

"""

# %%
from dash import (
    register_page,
    html,
    dash_table,
    dcc,
    Input,
    Output,
    State,
    callback,
)
from dash.dash_table import Format
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable


def format_fixed(precision):
    """Helper function to format columns in table"""
    return Format.Format(
        group=Format.Group.yes, precision=precision, scheme=Format.Scheme.fixed
    )


# %%

df = pd.read_csv("unit_visits.csv")
df["date"] = pd.to_datetime(df["date"])

df_wiki = pd.read_csv("wiki_data.csv")
df_wiki = df_wiki.dropna(subset=["area_acres", "lat", "lon"])

# Create dataframe with data averaged by year.
display_df = (
    df.query("2021 <= date.dt.year < 2025")
    .assign(year=lambda d: d["date"].dt.year)
    .groupby(["park_code", "year"])["visits"]
    .sum()
    .groupby("park_code")
    .mean()
    .reset_index()
    .merge(df_wiki, on="park_code")
)

# Calculate average visits per acre (since 2021)
display_df["visits_per_acre"] = display_df["visits"] / display_df["area_acres"]

# Round appropriately for display.
display_df["visits"] = display_df["visits"].round(1)
display_df["visits_per_acre"] = display_df["visits_per_acre"].round(2)

# Make park_name into appropriate wiki links.
display_df["park_name"] = display_df.apply(
    lambda row: f"[{row['park_name']}]({row['wiki_url']} \"_blank\")", axis=1
)

# %%
register_page(__name__, path="/page-table")

#######################################################################################
######################################## LAYOUT #######################################
#######################################################################################

layout = html.Div(
    [
        html.H4("National Park Unit Visitation Data and Distance from Address"),
        html.Div(style={"height": "20px"}),
        dcc.Input(
            id="address-input",
            type="text",
            placeholder="Enter address here",
            debounce=True,
            style={"width": "400px"},
        ),
        html.Button("Calculate Distance", id="calculate-button", className="button"),
        html.Div(style={"height": "20px"}),
        dash_table.DataTable(
            id="parks-table",
            columns=[
                {"name": "Park Name", "id": "park_name", "presentation": "markdown"},
                {
                    "name": "Average Annual Visits*",
                    "id": "visits",
                    "type": "numeric",
                    "format": format_fixed(1),
                },
                {"name": "Area (Acres)", "id": "area_acres"},
                {
                    "name": "Average Annual Visits per Acre*",
                    "id": "visits_per_acre",
                    "type": "numeric",
                    "format": format_fixed(2),
                },
                {
                    "name": "Distance from Address (mi)",
                    "id": "distance",
                    "type": "numeric",
                    "format": format_fixed(1),
                },
            ],
            data=[],
            sort_action="native",
            page_size=10,
            style_cell={"textAlign": "left", "whiteSpace": "normal"},
            style_table={"maxWidth": "1100px", "margin": "auto"},
            style_cell_conditional=[
                {
                    "if": {"column_id": "park_name"},
                    "width": "35%",
                },
                {
                    "if": {"column_id": "visits"},
                    "width": "20`%",
                },
                {
                    "if": {"column_id": "area_acres"},
                    "width": "10%",
                },
                {
                    "if": {"column_id": "visits_per_acre"},
                    "width": "20%",
                },
                {
                    "if": {"column_id": "distance"},
                    "width": "15%",
                },
            ],
        ),
        html.Div(
            html.Small("* Averages calculated since 2021."),
            style={
                "textAlign": "right",
                "marginTop": "10px",
                "maxWidth": "1100px",
                "margin": "10px auto",
            },
        ),
    ]
)


@callback(
    Output("parks-table", "data"),
    [
        Input("address-input", "n_submit"),  # hit Return
        Input("calculate-button", "n_clicks"),  # click Button
    ],
    State("address-input", "value"),
)
def update_distances(_n_submit, _n_clicks, address):
    """Calculate distances from address to NPS units"""

    if not address:
        return display_df.assign(distance=None).to_dict("records")

    geolocator = Nominatim(user_agent="my-dash-app", timeout=5)

    try:
        location = geolocator.geocode(address)
    except (GeocoderTimedOut, GeocoderUnavailable):
        # If the server is down or slow, handle gracefully
        return display_df.assign(distance=None).to_dict("records")

    if location is None:
        # Address not found
        return display_df.assign(distance=None).to_dict("records")

    user_location = (location.latitude, location.longitude)

    def compute_distance(row):
        park_location = (row["lat"], row["lon"])
        return geodesic(user_location, park_location).miles

    display_df_with_dist = display_df.copy()
    display_df_with_dist["distance"] = display_df_with_dist.apply(
        compute_distance, axis=1
    )
    display_df_with_dist["distance"] = display_df_with_dist["distance"].round(1)

    return display_df_with_dist.to_dict("records")
