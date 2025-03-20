import pandas as pd
import plotly.express as px
import streamlit as st


def jobs_in_db(conn, countries, sts, days_old):

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

    job_count = pd.read_sql(query, conn)
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