import pandas as pd
import plotly.express as px
import streamlit as st

#def freq_keywords(conn, keywords):

def timeseries_from_db(conn, country, sts):
    if len(sts)==0:
        return
    elif len(sts)==1:
        filter_st = f"r.search_term IN '{sts[0]}'"
    else:
        filter_st = f"r.search_term IN {tuple(sts)}"

    query = f"""
        SELECT jobspy.id, jobspy.date_posted, GROUP_CONCAT(r.search_term, '-') as search_term
        FROM jobspy
        LEFT JOIN (
            SELECT DISTINCT id, search_term FROM searchterms
        ) r ON r.id = jobspy.id
        WHERE jobspy.country='{country}' AND {filter_st} AND jobspy.date_posted >= date('now', '-3 month')
        GROUP BY jobspy.id, jobspy.date_posted
        """
    df = pd.read_sql(query, conn)

    df_grouped = df.groupby(
        by=['date_posted', 'search_term'],
        as_index=False
    ).count()

    fig = px.area(
        df_grouped,
        x='date_posted',
        y='id',
        color='search_term'
    )
    fig.update_layout(
        xaxis_title="Date Posted",
        yaxis_title="Number of Jobs"
    )
    fig.update_traces(line=dict(width=1))
    st.plotly_chart(fig)