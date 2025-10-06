import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
import numpy as np

from dbtools import queries


def jobs_in_db(conn, countries, sts, days_old):
    job_count = queries.count_total_map(conn, countries, sts, days_old)
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
    job_count = queries.count_total_map(conn, countries, sts, days_old)
    # Create Hover Text
    job_count["hover_text"] = \
        job_count["city"] + \
        "<br>Number of jobs: " + job_count["nr_jobs"].astype(str)

    fig = go.Figure(go.Scattermap(
        lat=job_count['lat'],
        lon=job_count['lon'],
        mode="markers",
        marker=dict(
            size=8.0 * np.log(job_count['nr_jobs']+1),
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
        margin=dict(l=0, r=0, t=0, b=0),
        height=600
    )

    st.plotly_chart(fig)