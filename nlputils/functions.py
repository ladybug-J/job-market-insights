import os
import json
import spacy
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sklearn.feature_extraction.text import CountVectorizer

from dbtools import queries


def lemmatize_description(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    words = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]  # Lemmatization & stopword removal
    return words

def count_tools(conn, countries, sts, days_old):

    df = queries.merge_sts(conn, sts, days_old, description=True, group_concat=False)
    # Read vocabulary from Json
    filepath = os.path.dirname(__file__)
    json_tools = json.load(open(f"{filepath}/data_tools.json", "rb"))

    json_vocab = set([tool for domain in json_tools.values() for alternatives in domain for tool in alternatives])

    # Initialize Count Vectorizer
    vectorizer = CountVectorizer(vocabulary=json_vocab)

    # Fit and transform the texts
    count_matrix = vectorizer.fit_transform(df['description'].values)

    # Convert the matrix into a DataFrame
    feature_names = vectorizer.get_feature_names_out()
    index = pd.MultiIndex.from_tuples(
        list(zip(df['id'].values, df['search_term'])),
        names=['id', 'search_term']
    )
    counts = pd.DataFrame(
        count_matrix.toarray(),
        index=index,
        columns=feature_names
    )

    nan_df = counts.replace(0, np.nan).dropna(axis=1, how='all')

    if st.session_state.sort_st:
        word_freq = nan_df.xs(st.session_state.sort_st, level='search_term').count() \
                    / nan_df.xs(st.session_state.sort_st, level='search_term').shape[0]
    else:
        word_freq = nan_df.count() / nan_df.shape[0]

    # Sort words by their overall frequency (highest first)
    sorted_words = word_freq.sort_values(ascending=False).index

    # Reorder columns in nan_df based on sorted word order
    nan_df = nan_df[sorted_words]

    fig = go.Figure()
    for search_term in df['search_term'].unique():
        freq_df = (nan_df.xs(search_term, level='search_term').count()/nan_df.xs(search_term, level='search_term').shape[0])

        fig.add_trace(go.Bar(
            x=freq_df.iloc[:int(freq_df.shape[0]/2)].index,
            y=freq_df.iloc[:int(freq_df.shape[0]/2)].values,
            name=search_term
        ))

    fig.update_layout(
        barmode="group",
        #title=dict(
        #    text="Top mentioned tools",
        #    font=dict(
        #        size=24
        #    )
        #),
        yaxis=dict(
            title='Normalized word frequency'
        )
    )
    st.plotly_chart(
        fig
    )

    return freq_df.iloc[:5]
