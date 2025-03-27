import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from dbtools import queries


def timeseries_from_db(conn, country, sts, days_old):

    df = queries.merge_sts(conn, sts, days_old)
    df = df.loc[df['country'] == country].drop(['country', 'city'], axis=1)

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
    st.plotly_chart(fig, key=f"{country}_ts")


def description_language(conn, countries, search_term, days_old):
    lang_df = queries.count_languages(conn, countries, search_term, days_old)

    # Create a colormap using Matplotlib
    cmap = plt.get_cmap("inferno")

    diff_lang = pd.read_sql("SELECT DISTINCT description_language from jobspy;", conn)\
                    .sort_values(by='description_language')

    # Normalize indices to map them to colors
    norm = plt.Normalize(0, diff_lang.shape[0] - 1)
    colors = [cmap(norm(i))[:3] for i in range(diff_lang.shape[0])]
    # Convert to Plotly-compatible RGB strings
    rgb_colors = [f"rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})" for r, g, b in colors]
    color_map = dict(zip(list(diff_lang['description_language'].values), rgb_colors))

    lang_df = lang_df.pivot(
        index='country',
        columns=['description_language'],
        values='Number of Jobs') \
        .fillna(0.0)

    fig = go.Figure()
    for lang in lang_df.columns[::-1]:
        fig.add_trace(go.Bar(
            y=lang_df.index,  # Categories on the Y-axis
            x=lang_df[lang],  # Values for the first category
            name=lang,  # Name of the first group
            orientation='h',  # Horizontal orientation
            marker=dict(color=color_map[lang])
        ))

    fig.update_layout(
        barmode='stack',
        title=f'{search_term.upper()}',
        xaxis_title='Number of Jobs',
        yaxis_title='Country',
    )
    st.plotly_chart(fig, key=f"{search_term}_lang")
