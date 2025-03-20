import sqlite3
import subprocess
import requests
import urllib
import streamlit as st
import etl
from visualization import map_plots, var_plots
import streamlit.components.v1 as components

st.set_page_config(
        page_title="Job market insights",
        page_icon="🧊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

EU_countries = ["Austria", "Belgium", "Czech Republic", "Denmark", "Finland", "France", "Germany", "Greece",
                "Hungary", "Ireland", "Italy", "Luxembourg", "Netherlands", "Norway", "Poland", "Portugal",
                "Romania", "Spain", "Sweeden", "Switzerland", "Turkey", "Ukraine"
                ]

def run_etl(conn, search_term, countries, hours_old):
    # Sequential:
    #for country in countries:
        #subprocess.run(["python3", "./etl/main.py", "--search_term", search_term, "--country", country])
        #etl.main(conn, search_term, country, hours_old)
        #etl.update_europe_table(conn)
    # Parallel:
    etl.run_parallel_etl([search_term], countries, hours_old)
    etl.update_europe_table(conn)

@st.cache_resource
def connect2db(db_name):
    return sqlite3.connect(db_name, check_same_thread=False)


def generate_diff_metrics(cursor, countries, sts):
    if countries:
        cols = st.columns(len(countries))
        for i, col in enumerate(cols):
            st_placeholders = ','.join('?' * len(sts))

            count_1day = cursor.execute(f"""SELECT count(*) FROM jobspy WHERE country='{countries[i]}'
                AND date_posted > date('now', '-1 days')
                AND id IN (
                    SELECT id 
                    FROM searchterms
                    WHERE search_term in ({st_placeholders})
                    );
                """, sts).fetchall()[0][0]

            count_2day = cursor.execute(f"""SELECT count(*) FROM jobspy WHERE country='{countries[i]}' 
                AND date_posted > date('now', '-2 days')
                AND date_posted <= date('now', '-1 days')
                AND id IN (
                    SELECT id 
                    FROM searchterms
                    WHERE search_term in ({st_placeholders})
                    );
                """, sts).fetchall()[0][0]

            col.metric(f"{countries[i]}", count_1day, count_1day-count_2day, border=True)


def url_ad(cursor, country, search_term):

    query = f"""
        SELECT job_url
        FROM jobspy
        WHERE country='{country}'
        AND id IN (
            SELECT id
            FROM searchterms
            WHERE search_term='{search_term}'
        ) 
        ORDER BY RANDOM() LIMIT 1
    """
    return cursor.execute(query).fetchall()[0][0]


if __name__ == "__main__":

    import pandas as pd

    DEBUG = True
    db_name = "jobs.db"
    conn = connect2db(db_name)
    cursor = conn.cursor()

    st.title(" Job market insights")
    st.markdown("<div style='text-align: justify;'>"
                "The goal of this dashboard is to get better insights of the job market trends in Europe. Given the "
                "search terms and countries you are interested in, you can update the database, and after selecting "
                "them in the metrics sidebar, generate automated visualizations and insights. The data is scraped from "
                "Indeed and Glassdoor job portals using an open-source Python library: JobSpy."
                "</div>",
                unsafe_allow_html=True
                )
    st.write("")
    st.markdown("<div style='text-align: justify;'>"
                "One of the most important data of the job posts is contained in the job descriptions. To be able to "
                "extract key information from them (as the specific field for general jobs as 'data scientist', or tools "
                "and experience the companies require), the current open-source Large Language Models (LLMs) will be "
                "leveraged."
                "</div>",
                unsafe_allow_html=True
                )
    st.write("")
    st.markdown("⚠️ App still under construction!")

    with st.sidebar:

        st.header("Query data", divider="green", help="The selected search term will be used to scrape indeed and "
                                                      "glassdoor for a maximum of 400 job postings each. Duplicates "
                                                      "between job boards will be removed, and the descriptions will "
                                                      "be translated to English.")
        with st.expander("Options"):
            search_term = st.text_input(
                "Search job term",
                value="data scientist"
            )
            countries = st.multiselect(
                "Select countries for looking for the search term",
                options=EU_countries,
                default=["Austria", "France", "Germany", "Spain", "Switzerland"]
            )

            #with st.expander(f"Last data in DB from..."):
            query = f"""
                SELECT country AS Country, MAX(date_posted) AS 'Last date' FROM jobspy WHERE id IN (
                    SELECT id FROM searchterms WHERE search_term='{search_term}'
                    ) GROUP BY country
            """
            st.table(pd.read_sql(query, conn).set_index('Country'))

            hours_old = st.number_input(
                label="How many hours old should the job postings be when querying and saving?",
                placeholder="Insert integer",
                value=None,
                step=24,
                min_value=0,
                help="If no value is inserted, the entire data available will be queried (with a maximum of 400 posts per "
                     "job board)"
            )

            update_database = st.button(
                "Update database",
                key="run_etl",
                on_click=run_etl,
                args=(conn, search_term, countries, hours_old),
                disabled=len(countries)==0

            )

        st.header("Metrics", divider="green")

        try:
            unique_countries = [x[0] for x in cursor.execute("SELECT DISTINCT(country) FROM jobspy").fetchall()]
            unique_st = [x[0] for x in cursor.execute("SELECT DISTINCT(search_term) FROM searchterms").fetchall()]
        except: #sqlite3.OperationalError:
            unique_countries = []
            unique_st = []

        select_countries = st.multiselect(
            "Select countries to show in metrics",
            options=unique_countries,
            default=unique_countries,
            help="This select box shows the countries that are already in the database. If you are looking for another "
                 "country's data, please update database."
        )

        select_sts = st.multiselect(
            "Select search terms",
            options=unique_st,
            default=unique_st,
            help="This select box shows the search terms that are already in the database. If you are looking for another "
                 "search term's data, please update database."
        )

    with st.container():
        st.subheader("Job postings today")
        st.write("This metrics correspond to the sum of ")
        if select_countries or select_sts:
            generate_diff_metrics(cursor, select_countries, select_sts)

    #timeseries, somethingelse = st.columns([0.6, 0.4])

    with st.container():
        st.subheader("Time-series from DB")
        st.write("Just the last 3 months will be visualized, as probably postings before are not open positions anymore. "
                 "The combined labels (e.g. data scientis-AI engineer) correspond to jobs that are queried with both "
                 "search terms. ")
        tabs = st.tabs(select_countries)
        for i, tab in enumerate(tabs):
            with tab:
                var_plots.timeseries_from_db(conn, select_countries[i], select_sts)

    st.subheader("Original language of the description text")
    sts = st.multiselect(
        "Select search terms",
        options=unique_st,
        default=select_sts
    )
    st_cols = st.columns(len(sts))
    for i, search_term in enumerate(sts):
        with st_cols[i]:
            var_plots.description_language(conn, select_countries, search_term)





    # Show plot with ads per city for each country
    with st.container():
        st.subheader("Job locations around Europe")
        st.write("Beware the cluster numbers refer to the number of locations in the area, not the number of job postings.")
        map_plots.jobs_in_db(conn, select_countries, select_sts)
