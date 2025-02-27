import json
import sqlite3
import pandas as pd

geojson = json.load(open("./europe.geojson", 'rb'))

lon = [x['geometry']['coordinates'][0] for x in geojson['features']]
lat = [x['geometry']['coordinates'][1] for x in geojson['features']]

geometry = pd.DataFrame({'lat': lat, 'lon': lon})
geo_df = pd.concat((pd.DataFrame([x['properties'] for x in geojson['features']]), geometry), axis=1)

# Alternate names can be useful later, but for now remove:
geo_df.drop('alternate_names', axis=1, inplace=True)

conn = sqlite3.connect("../jobs.db")
geo_df.to_sql(name='europe', con=conn)