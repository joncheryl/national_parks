"""
Download weather data for National Park dashboard.
"""

# %%
import time
import calendar
import requests
import pandas as pd
import numpy as np

# %%

wiki_df = pd.read_csv("wiki_data.csv")
# wiki_df = wiki_df.dropna(subset=["lat", "lon"])

TOKEN = "owZwZlTmuUILneaHTSgryjMZepdPriRj"
MAX_STATIONS = 25

# %%


def euc_dist(x1, y1, x2, y2):
    """Euclidean distance helper function"""
    return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def get_nearest_station(lat, lon):
    """Find the closest weather station to NPS unit lat/lon"""

    # Skip units that have ill-defined lat/lon
    if pd.isna(lat) or pd.isna(lon):
        return None

    area_width = 0.5
    area_width_upper = area_width
    attempt = 0

    while attempt < 10:
        attempt += 1

        # Boundary boundaries.
        area_bounds = [
            lat - area_width,
            lon - area_width,
            lat + area_width,
            lon + area_width,
        ]
        area_string = ",".join(str(x) for x in area_bounds)

        endpoint = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
        headers = {"token": TOKEN}
        params = {
            "extent": area_string,
            "datacategoryid": "TEMP",
            "startdate": "2025-04-28",
        }
        print(f"area_width = {area_width}")

        try:

            response = requests.get(endpoint, headers=headers, params=params, timeout=5)

            # if response.status_code == 429:
            #     print("Rate limited. Sleeping and retrying...")
            #     time.sleep(2**attempt)  # Exponential backoff
            #     continue

            response.raise_for_status()
            data = response.json().get("results", [])

        except ValueError:
            print("ValueError")
            return (
                f"Error: Response was not valid JSON. Raw text: {response.text[:200]}"
            )
        except requests.exceptions.Timeout as e:
            print("Timeout")
            return f"Error: The request timed out. ({e})"

        print(f"len(data) = {len(data)}")

        # If 25 or more stations in area, decrease boundary size.
        if len(data) >= MAX_STATIONS:
            print("big")
            time.sleep(1)
            area_width_upper = area_width
            area_width /= 2
            continue

        # If closest 24 known, calculate nearest weather station.
        elif 0 < len(data) < MAX_STATIONS:

            print("med")
            data_df = pd.DataFrame(data)
            data_df["distance_to"] = euc_dist(
                data_df["latitude"], data_df["longitude"], lat, lon
            )
            return data_df.sort_values("distance_to")["id"].iloc[0]

        # If 0 stations in area, increase boundary size.
        else:
            print("small")
            time.sleep(1)
            area_width = max(area_width * 1.5, area_width_upper * 0.75)
            continue

    return "Error: No station found within bounds after 10 attempts."


# %%

wiki_df["nearest_station"] = wiki_df.apply(
    lambda row: get_nearest_station(row["lat"], row["lon"]), axis=1
)

# Repeat until not needed
wiki_df["nearest_station"] = wiki_df.apply(
    lambda row: (
        get_nearest_station(row["lat"], row["lon"])
        if isinstance(row["nearest_station"], str)
        and row["nearest_station"].startswith("Error")
        else row["nearest_station"]
    ),
    axis=1,
)

wiki_df.to_csv("weather_data.csv", index=False)
# %%
# Get monthly temperatures for each station.


def get_monthly_temps(station):
    """Function to obtain average monthly high and low at weather station."""

    # Skip units that have no chosen weather station
    if station == "none":
        return None

    # Get actual weather info
    data_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"

    print(station)
    headers = {"token": TOKEN}
    params = {
        "datasetid": "GSOM",
        "stationid": station,
        "startdate": "2024-03-01",
        "enddate": "2025-03-01",
        "datatypeid": ["TMAX", "TMIN"],
        "units": "standard",
        "limit": "100",
    }
    try:
        response = requests.get(data_url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json().get("results", [])

    except ValueError:
        print("ValueError")
        return f"Error: Response was not valid JSON. Raw text: {response.text[:200]}"
    except requests.exceptions.Timeout as e:
        print("Timeout")
        return f"Error: The request timed out. ({e})"

    if len(data) == 0:
        print("No temps found")
        return None

    weather_df = pd.DataFrame(data)
    weather_df["date"] = weather_df["date"].astype("datetime64[ns]")

    return (
        weather_df[["datatype", "value"]]
        .groupby([weather_df["date"].dt.month, "datatype"])
        .mean()
    )


# %%
########
# Actually get monthly average high and low
########
temp_dict = {
    station: get_monthly_temps(station) for station in wiki_df["nearest_station"]
}
# %%

# Repeat bad requests that timed out.
timedout_weather = [
    station for station in temp_dict.keys() if isinstance(temp_dict[station], str)
]
for station_bad in timedout_weather:
    temp_dict[station_bad] = get_monthly_temps(station_bad)

# %%
# Drop the stations that don't have temp data and NPS units that don't have stations.
temp_dict_findable = {
    station: temps
    for station, temps in temp_dict.items()
    if temp_dict[station] is not None
}

temp_df = pd.concat(temp_dict_findable).reset_index(0, names="station").reset_index()

# And add month name for displaying later:
temp_df["month_abbr"] = temp_df["date"].apply(lambda x: calendar.month_abbr[x])

# %%
temp_df.to_csv("temp_data.csv", index=False)
