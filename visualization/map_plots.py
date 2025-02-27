import pandas as pd
import plotly.express as px
import streamlit as st


def jobs_today(conn):
    query = """
        SELECT subquery.city, lat, lon, subquery.nr_jobs
        FROM europe
        JOIN 
            (
            SELECT city, count(*) as nr_jobs
            FROM jobspy
            GROUP BY city
            ) AS subquery
        ON europe.name=subquery.city
        """
    job_count = pd.read_sql(query, conn)
    job_count['size'] = 200

    fig = px.scatter_map(
        job_count,
        lat="lat",
        lon="lon",
        size='size',
        hover_name='city',
        hover_data=['nr_jobs', 'lat', 'lon'],
        zoom=3,
        center={'lat': 53.0, 'lon': 9.0},
        text='city'
    )
    fig.update_traces(cluster=dict(enabled=True))

    st.plotly_chart(fig)