import pandas as pd

import etl

def test_city_country():
    locations = ["Paris, A8, FR", "Lyon, ARA, FR"]
    pass


def test_remove_formatting():
    df = pd.DataFrame({
        'description': ['** About us: **', '### Offer \n\n']
    })
    etl.transform.remove_formatting(df)

    assert df['description'].iloc[0] == " About us: ", "Asterisks are not removed"
    assert df['description'].iloc[1] == " Offer   ", "Headers and newlines not properly removed"

def test_detect_language():
    df = pd.DataFrame({
        'description': ["Hola! Me llamo Judit.", "Hallo! Ich heiße Judit."]
    })
    etl.transform.detect_language(df)

    assert df['description_language'].iloc[0] == "es", "Spanish not detected"
    assert df['description_language'].iloc[1] == "de", "German not detected"

def test_run():
    df = pd.DataFrame({
        'title': ['Data Analyst QDD - H/F', 'Data Analyst internship'],
        'location': ['Paris 9e, A8, FR', 'Paris, A8, FR'],
        'description': [
            '**Présentation de la direction générale et du service**\nLa Banque de France recrute un "Data analyst" en charge de la Qualité des Données (QDD) pour renforcer ses équipes.\n\n\n',
            'Do you have a passion for diving into data sets and uncovering insights that drive data\\-based decision\\-making? Join us in transforming P\\&G’s brand\\-building efforts through '
        ]
    })
    SEARCH_TERM = "Data Analyst"
    COUNTRY = "France"

    df = etl.transform.run(df, COUNTRY, SEARCH_TERM)

    assert set(['city', 'country', 'description_language', 'search_term']).issubset(df.columns), \
        "All the expected columns have not been generated"
    assert df['search_term'].iloc[0] == SEARCH_TERM.lower()
