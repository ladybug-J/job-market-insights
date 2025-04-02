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

    df = queries.merge_sts(conn, sts, days_old, description=True)
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
    counts = pd.DataFrame(count_matrix.toarray(), columns=feature_names)

    nan_df = counts.replace(0, np.nan).dropna(axis=1, how='all')
    percent_df = nan_df.sum().sort_values(ascending=False)/nan_df.shape[0]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=percent_df.index,
        y=percent_df.values,
    ))

    st.plotly_chart(fig)

    return percent_df.iloc[:5]
