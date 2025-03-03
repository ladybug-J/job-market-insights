import sqlite3
import subprocess
import requests
import urllib
import streamlit as st
import etl
from visualization import map_plots
import streamlit.components.v1 as components

st.set_page_config(
        page_title="Job market insights",
        page_icon="🧊",
        #layout="centered",
        initial_sidebar_state="expanded"
    )

EU_countries = ["Austria", "Belgium", "Czech Republic", "Denmark", "Finland", "France", "Germany", "Greece",
                "Hungary", "Ireland", "Italy", "Luxembourg", "Netherlands", "Norway", "Poland", "Portugal",
                "Romania", "Spain", "Sweeden", "Switzerland", "Turkey", "Ukraine"
                ]

def run_etl(search_term, countries):
    for country in countries:
        #subprocess.run(["python3", "./etl/main.py", "--search_term", search_term, "--country", country])
        etl.main(search_term, country)

@st.cache_resource
def connect2db(db_name):
    return sqlite3.connect(db_name, check_same_thread=False)

def generate_card(col):
    wch_colour_box = (0, 204, 102)
    wch_colour_font = (0, 0, 0)
    fontsize = 18
    valign = "left"
    iconname = "fas fa-asterisk"
    sline = "Observations"
    lnk = '<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.12.1/css/all.css" crossorigin="anonymous">'
    i = 123

    htmlstr = f"""<p style='background-color: rgb({wch_colour_box[0]}, 
                                                  {wch_colour_box[1]}, 
                                                  {wch_colour_box[2]}, 0.75); 
                            color: rgb({wch_colour_font[0]}, 
                                       {wch_colour_font[1]}, 
                                       {wch_colour_font[2]}, 0.75); 
                            font-size: {fontsize}px; 
                            border-radius: 7px; 
                            padding-left: 12px; 
                            padding-top: 18px; 
                            padding-bottom: 18px; 
                            line-height:25px;'>
                            <i class='{iconname} fa-xs'></i> {i}
                            </style><BR><span style='font-size: 14px; 
                            margin-top: 0;'>{sline}</style></span></p>"""

    st.markdown(lnk + htmlstr, unsafe_allow_html=True)

def generate_diff_metrics(cursor, countries, sts):
    if countries:
        cols = st.columns(len(countries))
        for i, col in enumerate(cols):
            st_placeholders = ','.join('?' * len(sts))

            count_1day = cursor.execute(f"""SELECT count(*) FROM jobspy WHERE country='{countries[i]}'
                AND date_posted >= date('now', '-1 days')
                AND search_term IN ({st_placeholders});
                """, sts).fetchall()[0][0]

            count_2day = cursor.execute(f"""SELECT count(*) FROM jobspy WHERE country='{countries[i]}' 
                AND date_posted >= date('now', '-2 days')
                AND date_posted < date('now', '-1 days')
                AND search_term IN ({st_placeholders});
                """, sts).fetchall()[0][0]

            col.metric(f"{countries[i]}", count_1day, count_1day-count_2day, border=True)

#def barplot_cities():

def url_ad(cursor, country):
    query = f"""
        SELECT job_url
        FROM jobspy
        WHERE country='{country}'
        ORDER BY RANDOM() LIMIT 1
    """
    return cursor.execute(query).fetchall()[0][0]

if __name__ == "__main__":

    db_name = "jobs.db"
    conn = connect2db(db_name)
    cursor = conn.cursor()

    st.title(" Job market insights")
    st.markdown(" The goal of this dashboard is to get better insights of the job market trends in Europe. \
                "
                )
    with st.sidebar:

        st.title("Options")

        st.header("Query data", divider="green")
        search_term = st.text_input(
            "Search job term",
            value="data scientist"
        )
        countries = st.multiselect(
            "Select countries for looking for the search term",
            options=EU_countries,
            default=["Austria", "France", "Germany", "Spain", "Switzerland"]
        )

        st.button(
            "Update database",
            key="run_etl",
            on_click=run_etl,
            args=(search_term, countries),
            disabled=len(countries)==0

        )

        st.header("Metrics", divider="green")

        try:
            unique_countries = [x[0] for x in cursor.execute("SELECT DISTINCT(country) FROM jobspy").fetchall()]
            unique_st = [x[0] for x in cursor.execute("SELECT DISTINCT(search_term) FROM jobspy").fetchall()]
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

    st.header("Number of jobs posted the last 24h - difference with previous day")

    if select_countries or select_sts:
        generate_diff_metrics(cursor, select_countries, select_sts)

    # Show plot with ads per city for each country
    with st.container():
        map_plots.jobs_today(conn)

    st.markdown("""
        * Map should adapt to the screen size
        * Plotly does not allow clustering and showing the aggregated value of a variable (e.g. number of jobs in the 
        cluster), it just shows the number of locations within the cluster...
        """)
    # Choose random ad and show link view
    tabs = st.tabs(select_countries)
    for i, tab in enumerate(tabs):
        with tab:
            country = select_countries[i]
            st.header(f"Random ad for {country}")
            st.write(url_ad(cursor, country))
            placeholder = st.empty()

            components.iframe(
                url_ad(cursor, country),
                scrolling=True
            )


    #st.page_link("pages/page_1.py", label="Page 1", icon="1️⃣")