"""
Downloading data from wikipedia per park unit

NAVA and NAVC are deprecated park units.

Still some weirdness with getting wiki page for WHHO. Works when %27 is substituted
for apostrophe.
"""

# %%
from io import StringIO
import unicodedata
import pandas as pd
import requests

# %%

# Import directory of parks. Drop parks that had no NPS webpage (NAVA and NAVC are
# deprecated NPS units).
directory = (
    pd.read_csv("unit_visits.csv", usecols=["park_code", "park_name"])
    .drop_duplicates()
    .loc[lambda df: ~df["park_name"].str.startswith("Error")]
    .reset_index(drop=True)
)

# Format park names.
park_names = (
    directory["park_name"]
    .str.replace(" ", "_")
    .str.replace("&", "and")
    .apply(
        lambda name: unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode("utf-8")
    )
)

# Make wikipedia urls.
directory["wiki_url"] = "https://en.wikipedia.org/wiki/" + park_names
# Make official NPS urls.
directory["nps_url"] = "https://www.nps.gov/" + directory["park_code"] + "/index.htm"

#######################################################################################
#################################### MANUAL EDITS #####################################
#######################################################################################
# WWI Memorial
directory.loc[directory["park_code"] == "WWIM", "wiki_url"] = (
    "https://en.wikipedia.org/wiki/National_World_War_I_Memorial_(Washington,_D.C.)"
)
# Glacier National Park
directory.loc[directory["park_code"] == "GLAC", "wiki_url"] = (
    "https://en.wikipedia.org/wiki/Glacier_National_Park_(U.S.)"
)

# %%
# Download wikipedia page tables.
wiki_data = {}
unfound_parks = {}
for row in directory.itertuples(index=False):
    try:
        response = requests.get(row.wiki_url, timeout=20)
        response.raise_for_status()  # Raises HTTPError for bad status codes like 404
        tables = pd.read_html(StringIO(response.text))
        wiki_data[row.park_code] = tables
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error for {row.park_name}: {e}")
        unfound_parks[row.park_code] = row.park_name
    except ValueError as e:
        print(f"Failed to fetch {row.park_name}: {e}")
        unfound_parks[row.park_code] = row.park_name

# %%
# Extract the correct dataframe from each list of dataframes.

for unit, tables in wiki_data.items():
    for table in tables:
        if not isinstance(table, pd.DataFrame):
            continue
        if table.iloc[:, 0].isin(["Coordinates", "Length"]).any():
            # Remove duplicated fields and transpose table to have columns.
            wiki_data[unit] = table.loc[~table.iloc[:, 0].duplicated()].transpose()
            # First row of df has columns names.
            wiki_data[unit].columns = wiki_data[unit].iloc[0]
            # Drop first row now that it is column names.
            wiki_data[unit] = wiki_data[unit].iloc[1:, :]
            break

# %%
# Build dataframe to save to file.
wiki_df = pd.concat(wiki_data).reset_index(level=1, drop=True)
wiki_df = wiki_df[["Coordinates", "Area"]]
wiki_df = wiki_df.reset_index(names="park_code").merge(directory, on="park_code")

# Clean up area column.
wiki_df["area_acres"] = wiki_df["Area"].str.extract(r"([\d,.]+)")
wiki_df["area_acres"] = wiki_df["area_acres"].str.replace(",", "").astype(float)
wiki_df = wiki_df.drop(columns=["Area"])

# Clean up the coordinates column.
wiki_df[["lat", "lon"]] = wiki_df["Coordinates"].str.extract(
    r"([+-]?\d+\.\d+)°[NS].*?([+-]?\d+\.\d+)°[EW]"
)
wiki_df["lat"] = wiki_df["lat"].astype(float)
wiki_df["lon"] = wiki_df["lon"].astype(float)
# Fix signs: make West/South negative
wiki_df["lon"] = (
    wiki_df["Coordinates"]
    .str.contains("W")
    .where(wiki_df["lon"].notna(), False)
    .map({True: -1, False: 1})
    * wiki_df["lon"]
)
wiki_df["lat"] = (
    wiki_df["Coordinates"]
    .str.contains("S")
    .where(wiki_df["lat"].notna(), False)
    .map({True: -1, False: 1})
    * wiki_df["lat"]
)
wiki_df = wiki_df.drop(columns=["Coordinates"])

#######################################################################################
#################################### MANUAL EDITS #####################################
#######################################################################################
# Washington Monument
wiki_df.loc[wiki_df["park_code"] == "WAMO", "area_acres"] = 106.01
# Valles Caldera National Preserve
wiki_df.loc[wiki_df["park_code"] == "VALL", "area_acres"] = 89766
# Devils Tower National Monument
wiki_df.loc[wiki_df["park_code"] == "DETO", "area_acres"] = 1346.91
# Florissant Fossil Beds National Monument
wiki_df.loc[wiki_df["park_code"] == "FLFO", "area_acres"] = 5998.09
# Florissant Fossil Beds National Monument
wiki_df.loc[wiki_df["park_code"] == "FLFO", "area_acres"] = 57.92

# %%
# Write to file.
wiki_df.to_csv("wiki_data.csv", index=False)
