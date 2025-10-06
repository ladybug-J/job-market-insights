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
    #fig.for_each_trace(
    #    lambda trace: trace.update(visible='legendonly')
    #    if "-" in trace.name else None
    #)
    st.plotly_chart(fig, key=f"{country}_ts")


def description_language(conn, countries, search_term, days_old):
    lang_df = queries.count_languages(conn, countries, search_term, days_old)

    # Create a colormap using Matplotlib
    cmap = plt.get_cmap("inferno")

    diff_lang = pd.read_sql("SELECT DISTINCT description_language from jobspy;", conn) \
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


def bar_ranking(conn, sts, days_old, stack=False):
    df = queries.merge_sts(conn, sts, days_old)
    total = df.groupby(by=['city', 'country']).count() \
        .rename({'id': 'Total jobs'}, axis=1) \
        .drop(['date_posted', 'search_term'], axis=1) \
        .sort_values(by='Total jobs', ascending=False)

    total_country = total.groupby(by='country', axis=0).sum()
    # Some cities are wrong:
    remove = ['Home Office', 'España', 'En remoto', 'DE']
    i = 0
    for index, row in total.iterrows():
        if (i < 10 and index[0] not in remove):
            total.loc[index, ('Percentage country')] = (100 * row['Total jobs'] / total_country.loc[index[1], 'Total jobs']).round(1)
            i += 1

    total.dropna(inplace=True)
    total.reset_index(inplace=True)

    layout_dict = dict(
        yaxis=dict(autorange="reversed"),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    if not stack:
        fig = go.Figure()
        bar_dict = dict(
            y=total['city'],
            x=total['Total jobs'],
            orientation='h',
            marker=dict(
                color=total['Percentage country'],
                colorscale='blues',
                showscale=True,
                colorbar=dict(title="%")
            )
        )
        fig.add_trace(go.Bar(
            **bar_dict
        ))
        layout_dict.update(
            xaxis=dict(
                title='Number of job postings',
                showgrid=True,
                gridcolor="rgba(200,200,200,0.3)",
                dtick=20
            ),
        )

    else:
        fig = go.Figure()
        for i, city in enumerate(total["city"].unique()):
            df_city = total[total["city"] == city]
            fig.add_trace(go.Bar(
                y=df_city["country"],  # Countries as single bars
                x=df_city["Percentage country"],  # City jobs stacked within the country bar
                name=city,  # Legend for cities
                orientation='h',
                marker=dict(
                    color=i
                )
            ))
        layout_dict.update(
            barmode='stack',
            xaxis=dict(
                title='Percentage of jobs',
                showgrid=True,
                gridcolor="rgba(200,200,200,0.3)",
                dtick=10
            ),
        )


    fig.update_layout(
        **layout_dict
    )
    st.plotly_chart(fig)
