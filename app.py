import sqlite3
import subprocess
import requests
import urllib
#import torch
import streamlit as st
import streamlit.components.v1 as components

import etl
from visualization import map_plots, var_plots
from utils.random import generate_diff_metrics, ranking_table
from dbtools import queries
import nlputils

#torch.classes.__path__ = []

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
    #etl.update_europe_table(conn)

@st.cache_resource
def connect2db(db_name):
    return sqlite3.connect(db_name, check_same_thread=False)


if __name__ == "__main__":

    import pandas as pd

    DEBUG = True
    db_name = "jobs.db"
    conn = connect2db(db_name)
    cursor = conn.cursor()

    st.title(" Job market insights")
    st.write("")
    st.write("This dashboard provides insights into job market trends across selected European countries. It aims to " 
             "answer key questions for job seekers and professionals looking to understand industry demands."
             )

    with st.expander("Key-questions"):
        st.markdown("""
                    * **Which data-related positions are most in demand?**
                        * Job seekers can get a grasp on the most demanded positions in order to direct their learning toward 
                        one or other field. The data-related jobs are the ones selected by default.
                    * **What proportion of job descriptions are in English versus the local language?**
                        * Even if a search is conducted in English, many job postings may still require fluency in the local 
                        language. This insight helps non-native speakers assess job accessibility in different countries. 
                        However, it does not remove the fact that the position might require fluency in the local language.
                    * **How are jobs geographically distributed?**
                        * Job clusters can indicate economic hubs, higher living standards, and potentially higher living 
                        costs (e.g., rent)
                    * **Which tools and technologies are most mentioned in job descriptions?**
                        * Understanding trending tools helps job seekers focus on the most relevant skills to improve their 
                        employability. 
                     
                    """
                    )
    with st.expander("Basic usage and defaults"):
        st.markdown("Use the sidebar to scrape data from Indeed and Glassdoor, given a search term and the countries for the "
             "search. The database is already pre-filled with data positions (Data Analyst/Scientist/Engineer) for "
             "five european countries (Germany, Spain, Switzerland, Austria, and France). The selection of the terms and "
             "countries to build the visualizations can be done using the sidebar's metrics settings.")
    #with st.expander("Summary Analysis"):
    #    st.markdown("""
    #
    #    """)

    st.write("")

    st.markdown("⚠️ App still under construction!")

    with st.sidebar:

        st.header("Scrape data", divider="green", help="The selected search term will be used to scrape indeed and "
                                                      "glassdoor for a maximum of 400 job postings each.")
        with st.expander("Options"):
            search_term = st.text_input(
                "Search job term",
                value="Data Scientist"
            )
            countries = st.multiselect(
                "Select countries for looking for the search term",
                options=EU_countries,
                default=["Austria", "France", "Germany", "Spain", "Switzerland"]
            )

            #with st.expander(f"Last data in DB from..."):
            try:
                query = f"""
                    SELECT country AS Country, MAX(date_posted) AS 'Last date' FROM jobspy WHERE id IN (
                        SELECT id FROM searchterms WHERE search_term='{search_term}'
                        ) GROUP BY country
                """
                st.table(pd.read_sql(query, conn).set_index('Country'))
                DB_ON = True
            except:
                st.write("No data into the database")
                DB_ON = False

            hours_old = st.number_input(
                label="How many hours old should the job postings be when querying and saving?",
                placeholder="Insert integer",
                value=None,
                step=24,
                min_value=None,
                help="If no value is inserted, the entire data available will be queried (with a maximum of 400 posts per "
                     "job board)"
            )

            update_database = st.button(
                "Update database",
                key="run_etl",
                on_click=run_etl,
                args=(conn, search_term, countries, hours_old),
                disabled=len(countries) == 0

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
                 "country's data, please update database.",
            key="select_countries"
        )

        select_sts = st.multiselect(
            "Select search terms",
            options=unique_st,
            default=["Data Scientist", "Data Analyst", "Data Engineer"],
            help="This select box shows the search terms that are already in the database. If you are looking for another "
                 "search term's data, please update database.",
            key="select_sts"
        )

    if DB_ON:
        with st.container():
            st.subheader("Number of job postings the last 7 days versus previous")
            st.write("This metrics correspond to the sum of all job postings from the selected search terms per country the"
                     "last 7 days.")
            if select_countries or select_sts:
                generate_diff_metrics(cursor, select_countries, select_sts)


        st.write("")
        st.write("")
        st.write("")

        days_old = st.slider(
            "Input the number of days from job posting",
            min_value=1,
            max_value=60,
            value=20
        )
        st.markdown(f"## Trends the last {days_old} days")

        with st.container():
            st.subheader("Search term popularity - time series from DB")
            st.write("The following time series show the amount of jobs in the database for the selected time-period and "
                     "search term. The combined labels (e.g. data scientis-AI engineer) correspond to jobs that are "
                     "found with both search terms. The colored areas give a better visualization of the dominant search "
                     "term.")


            tabs = st.tabs(select_countries[::-1])

            for i, tab in enumerate(tabs):
                with tab:
                    country = select_countries[::-1][i]
                    var_plots.timeseries_from_db(conn, country, select_sts, days_old)

        st.subheader("Original language of the description text")
        st.write("Even if the search term is written in English, the job descriptions can still be in a different language. "
                 "The following bar plots show the number of job offers for each term and the languages of their descriptions "
                 "per country.")
        st_cols = st.columns(len(select_sts))
        for i, search_term in enumerate(select_sts):
            with st_cols[i]:
                var_plots.description_language(conn, select_countries, search_term, days_old)


        with st.container():
            col1, col2 = st.columns([0.6, 0.4])
            with col1:
                st.subheader("Job locations around Europe")
                st.write(
                    "The following map plot gives an insight of the job offer distribution around Europe, where the "
                    "size and color of the points represents the number of jobs in each of the locations.")
                map_plots.color_size_plot(conn, select_countries, select_sts, days_old)
            with col2:
                st.subheader("Top 10 cities")
                #tc_tabs = st.tabs(["Top 10 cities", "Distribution"])
                #with tc_tabs[0]:
                stack = st.checkbox(
                    "Stack per country",
                    value=False,
                    help="Stack the cities grouped by country and representing the percentage they correspond to "
                         "the total jobs in the country."
                )
                if not stack:
                    st.write(f"The top ten cities with the most jobs the last {days_old} days. The color of the bars "
                             "represent the percentage of the jobs the city has with respect to the entire country.")
                var_plots.bar_ranking(conn, select_sts, days_old, stack=stack)

        with st.container():
            st.subheader("Top mentioned tools")
            st.write("ChatGPT has been used to extract the main technologies mentioned in the job descriptions and saved "
                     "into a JSON file. This file is then used as vocabulary for the CountVectorizer from scikit-learn. "
                     "The barplots show the frequency with which different technologies are mentioned in job posts, "
                     "normalized by the amount of job posts per searh term. The plot can be sorted for identifying the "
                     "trending tools for each search term. Grouped bars are possible to visualize clickling on the plotly "
                     "chart legend traces.")
            st.radio(
                "Select search term to sort by",
                select_sts,
                horizontal=True,
                key="sort_st"
            )

            top_5 = nlputils.count_tools(conn, select_countries, select_sts, days_old)