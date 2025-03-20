import os
import json
import sqlite3
import pandas as pd

def update_europe_table(conn):
    filepath = os.path.dirname(__file__)
    geojson = json.load(open(f"{filepath}/europe.geojson", 'rb'))

    lon = [x['geometry']['coordinates'][0] for x in geojson['features']]
    lat = [x['geometry']['coordinates'][1] for x in geojson['features']]

    geometry = pd.DataFrame({'lat': lat, 'lon': lon})
    geo_df = pd.concat((pd.DataFrame([x['properties'] for x in geojson['features']]), geometry), axis=1)

    # Alternate names can be useful later, but for now remove:
    #geo_df.drop('alternate_names', axis=1, inplace=True)

    # Get city names in jobspy table and choose the ones that match
    distinct_cities = pd.read_sql("SELECT DISTINCT(city), country FROM jobspy;", conn)
    geo_df['alternate_names'] = geo_df['alternate_names'].fillna(geo_df['name'])

    for index, row in distinct_cities.iterrows():
        if geo_df.loc[(geo_df['name'] == row['city']) & (geo_df['cou_name_en'] == row['country'])].empty:
            loc_df = geo_df.loc[(geo_df['alternate_names'].apply(lambda x: row['city'] in x)) & (geo_df['cou_name_en']==row['country'])]
            if (not loc_df.empty) & (len(loc_df.index)==1):
                print(f"Name in jobspy database {row['city']} \n")
                print(f"Name in geojson {loc_df['name']} \n")
                print("Changing geojson city name to jobspy name...")
                geo_df.loc[loc_df.index, "name"] = row['city']

    # Now, delete alternate names:
    #geo_df.drop('alternate_names', axis=1, inplace=True)
    geo_df = geo_df[['name', 'ascii_name', 'cou_name_en', 'country_code', 'feature_code', 'timezone', 'lat', 'lon', 'population']]

    geo_df.to_sql(name='europe', con=conn, if_exists='replace')