import os
import json
import logging
import sqlite3

import pandas as pd

logging.basicConfig(
    format='%(asctime)s - %(levelname)s: %(message)s',
    level=logging.ERROR
)
logger = logging.getLogger(__name__)

def update_europe_table(db_path):
    """
    Add geojson to SQLite database, for being able to query coordinates of cities for plotting onto the map.

    If the city + country does not exist in the geojson file, it checks for alternative naming of the city.
    """
    conn = sqlite3.connect(db_path)
    filepath = os.path.dirname(__file__)

    with open(f"{filepath}/europe.geojson", 'rb') as f:
        geojson = json.load(f)

    # Extract coordinates
    coord_df = pd.DataFrame(
        [x['geometry']['coordinates'] for x in geojson['features']],
        columns=['lon', 'lat']
    )
    # Properties of the coordinates
    prop_df = pd.DataFrame(
        [x['properties'] for x in geojson['features']],
        columns=['name', 'ascii_name', 'cou_name_en', 'country_code', 'feature_code',
                 'alternate_names', 'timezone', 'population'
                 ]
    )
    # Merge
    geo_df = pd.concat(
        (prop_df, coord_df),
        axis=1
    )

    # Get city names in jobspy table and choose the ones that match
    distinct_cities = pd.read_sql("SELECT DISTINCT(city), country FROM jobspy;", conn)
    geo_df['alternate_names'] = geo_df["alternate_names"].combine_first(
        geo_df["name"].apply(lambda x: [x])
    )
    for idx, row in geo_df.iterrows():
        if row['name'] not in row['alternate_names']:
            print(f"Nope... {row['name']} not in alternates")

    # Check if the distinct cities and countries that are in jobspy, appear also in the geojson data.
    # If not, check if the alternative names for the cities do.
    for index, row in distinct_cities.iterrows():
        if geo_df.loc[
                    (geo_df['name'] == row['city'])
                    & (geo_df['cou_name_en'] == row['country'])
                    ].empty:
            loc_df = geo_df.loc[(geo_df['alternate_names'].apply(lambda x: row['city'] in x))
                                & (geo_df['cou_name_en'] == row['country'])
                                ]
            if (not loc_df.empty) & (len(loc_df.index)==1):
                print(f"Name in jobspy database {row['city']} \n")
                print(f"Name in geojson {loc_df['name']} \n")
                print("Changing geojson city name to jobspy name...")
                geo_df.loc[loc_df.index, "name"] = row['city']

    geo_df = geo_df[['name', 'ascii_name', 'cou_name_en', 'country_code', 'feature_code', 'timezone', 'lat', 'lon', 'population']]

    geo_df.to_sql(name='europe', con=conn, if_exists='replace')


if __name__ == '__main__':
    db_path = "../tests/test_jobs.db"
    update_europe_table(db_path)