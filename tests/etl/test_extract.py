import pandas as pd

import etl

# INTEGRATION TEST
def test_jobspy_df():
    """ Expected pandas DataFrame with at least the columns ['id', 'company', 'title'] """
    COLUMNS = ['id', 'title', 'company', 'location', 'date_posted', 'job_url', 'description', 'site']
    jobs = etl.extract.call_jobspy(
        search_term="Data Scientist",
        country="Spain",
        hours_old=72,
        max_results=100
    )
    #breakpoint()
    assert set(COLUMNS).issubset(jobs.columns), f"Missing columns in jobs: {[col for col in COLUMNS if col not in jobs.columns]}"

# UNIT
def test_remove_duplicates():
    df = pd.DataFrame({
        'id': ["001", "002", "003"],
        'title': ["DS_1", "DS_2", "DS_1"],
        'company': ["C_1", "C_2", "C_1"],
        'location': ["loc_1", "loc_2", "loc_2"],
        'date_posted': ["D_1", "D_2", "D_3"],
        'job_url': [" ", " ", " "],
        'description': ["bla", "bla", "bla"],
        'site': ['indeed', 'indeed', 'glassdoor']
        })
    df = etl.extract.drop_duplicates(df)

    assert df.shape[0] == 2, "More than 2 rows!"


