import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


def timeseries_from_db(conn, country, sts, days_old):
    if len(sts)==0:
        return
    elif len(sts)==1:
        filter_st = f"r.search_term = '{sts[0]}'"
    else:
        filter_st = f"r.search_term IN {tuple(sts)}"

    query = f"""
        SELECT jobspy.id, jobspy.date_posted, GROUP_CONCAT(r.search_term, '-') as search_term
        FROM jobspy
        LEFT JOIN (
            SELECT DISTINCT id, search_term FROM searchterms
        ) r ON r.id = jobspy.id
        WHERE jobspy.country='{country}' AND {filter_st} AND jobspy.date_posted >= date('now', '-{days_old} days')
        GROUP BY jobspy.id, jobspy.date_posted
        """
    df = pd.read_sql(query, conn)
    #query = f"""
    #        SELECT id, count(search_term) as countst
    #        FROM searchterms
    #        WHERE search_term IN {tuple(sts)}
    #        GROUP BY id
    #        HAVING countst > 1
    #        """
    #st.table(pd.read_sql(query, conn))

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
    fig.for_each_trace(
        lambda trace: trace.update(visible='legendonly')
        if "-" in trace.name else None
    )
    st.plotly_chart(fig)

def description_language(conn, countries, search_term, days_old):

    query = f"""
        SELECT country, COUNT(description_language) AS 'Number of Jobs', description_language
        FROM jobspy
        WHERE country IN {tuple(countries)} AND id IN (
            SELECT id FROM searchterms WHERE search_term='{search_term}'
        ) AND date_posted >= date('now', '-{days_old} days')
        GROUP BY description_language, country
    """
    lang_df = pd.read_sql(query, conn).pivot(index='country',
                                             columns=['description_language'],
                                             values='Number of Jobs')\
                                      .fillna(0.0)


    fig = go.Figure()
    for lang in lang_df.columns:
        fig.add_trace(go.Bar(
            y=lang_df.index,  # Categories on the Y-axis
            x=lang_df[lang],  # Values for the first category
            name=lang,  # Name of the first group
            orientation='h'  # Horizontal orientation
        ))

    fig.update_layout(
        barmode='stack',
        title=f'{search_term.upper()}',
        xaxis_title='Number of Jobs',
        yaxis_title='Country',
    )
    st.plotly_chart(fig)