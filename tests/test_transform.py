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