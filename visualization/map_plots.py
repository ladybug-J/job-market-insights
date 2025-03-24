import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
import numpy as np


def query_map(conn, countries, sts, days_old):
    if len(countries)==0:
        return
    elif len(countries)==1:
        country_filter = f"WHERE country='{countries[0]}'"
    else:
        country_filter = f"WHERE country IN {tuple(countries)}"

    if len(sts)==0:
        return
    elif len(sts)==1:
        subquery = f"""SELECT id
                    FROM searchterms
                    WHERE search_term='{sts[0]}'
                    """
    else:
        subquery = f"""SELECT id
                        FROM searchterms
                        WHERE search_term IN {tuple(sts)}
                        """

    query = f"""
        SELECT subquery.city, lat, lon, subquery.nr_jobs
        FROM europe
        JOIN 
            (
            SELECT id, city, country, count(*) as nr_jobs
            FROM jobspy
            WHERE id IN (
                {subquery}
                )
            AND jobspy.date_posted >= date('now', '-{days_old} days')
            GROUP BY city 
            ) AS subquery
        ON europe.name=subquery.city AND europe.cou_name_en=subquery.country
        {country_filter}
        """

    return pd.read_sql(query, conn)


def jobs_in_db(conn, countries, sts, days_old):

    job_count = query_map(conn, countries, sts, days_old)

    job_count['size'] = 200

    fig = px.scatter_map(
        job_count,
        lat="lat",
        lon="lon",
        size="size",
        hover_name='city',
        hover_data=['nr_jobs', 'lat', 'lon'],
        zoom=3,
        center={'lat': 46.0, 'lon': 9.0},
        text='city'
    )
    fig.update_traces(
        cluster=dict(
            enabled=True
        )
    )

    st.plotly_chart(fig)


def color_size_plot(conn, countries, sts, days_old):

    job_count = query_map(conn, countries, sts, days_old)
    # Create Hover Text
    job_count["hover_text"] = job_count["city"] + "<br>Number of jobs: " + job_count["nr_jobs"].astype(str)

    fig = go.Figure(go.Scattermap(
        lat=job_count['lat'],
        lon=job_count['lon'],
        mode="markers",
        marker=dict(
            size=8.0 * np.log(job_count['nr_jobs']),
            color=job_count['nr_jobs'],
            colorscale="viridis",  # Color scale applied
            colorbar=dict(title="Number of Jobs")

        ),
        hovertext=job_count['hover_text'],
        hoverinfo="text"
    ))

    # Update Layout (Mapbox settings)
    fig.update_layout(
        map=dict(
            center=dict(
                lat=47.0,
                lon=9.0
            ),
            zoom=3.0
        ),
        coloraxis=dict(colorscale='viridis'),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig)