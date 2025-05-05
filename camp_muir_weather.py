"""

Weather data on MT Rainier from
https://waterdata.morageology.com/station.php?g=OSOMUR

"""

# %%
import re
from io import StringIO
import requests
import pandas as pd
import plotly.express as px

# %%


def month_weather(location, year):
    """function for monthly weather download"""
    url = (
        "https://waterdata.morageology.com/csv.php?g="
        + location
        + "&s="
        + str(year)
        + "-05-24&e="
        + str(year)
        + "-06-07"
    )

    response = requests.get(url, timeout=100)
    html = response.text

    # Extract the CSV block between the comment tags
    match = re.search(
        r"<!-- START RAW DATA -->(.*?)<!-- END RAW DATA -->", html, re.DOTALL
    )
    if not match:
        raise ValueError("CSV block not found")

    csv_block = match.group(1)

    # Replace <br> with newlines to format it like a normal CSV
    csv_text = csv_block.replace("<br>", "\n").strip()

    return pd.read_csv(StringIO(csv_text))


# %%
# Weather data for Camp Muir
muir_dict = {year: month_weather("OSOMUR", year) for year in range(2015, 2025)}
muir = pd.concat(muir_dict)
muir['Local Datetime'] = pd.to_datetime(muir['Local Datetime'])

muir["temp_f"] = muir["Air Temperature"] * 9 / 5 + 32
muir["wind_speed_mph"] = muir["Wind Speed"] * 2.23694

daily_mins = (
    muir
    .assign(date=muir['Local Datetime'].dt.date)
    .groupby('date')
    .min()
)

# Plot histogram
px.histogram(
    daily_mins,
    "temp_f",
    nbins=100,
    title="Daily Min Air Temp (F) from May 24 to June 7 at Camp Muir (10100') "
    + "from 2015 through 2024",
    subtitle="from https://waterdata.morageology.com/",
).show()

# Show basic weather data.
daily_mins.describe()

# %%

# Obtain data for Camp Schurman.
schurman_dict = {year: month_weather("MORAWXCS", year) for year in range(2000, 2024)}
schurman = pd.concat(schurman_dict)

# Convert C to F.
schurman["temp_f"] = schurman["Air Temperature"] * 9 / 5 + 32

# Identify missing wind speed data.
schurman.loc[schurman["Wind Speed"] == -999, 'Wind Speed'] = pd.NA
schurman["wind_speed_mph"] = schurman["Wind Speed"] * 2.23694

# Plot histogram.
px.histogram(
    schurman,
    "temp_f",
    nbins=100,
    title="Hourly Air Temps (F) from May 24 to June 7 at Camp Schurman (9500') "
    + "from 2000 through 2023",
    subtitle="from https://waterdata.morageology.com/",
).show()

# Show basic weather data.
schurman.describe()


# %%
