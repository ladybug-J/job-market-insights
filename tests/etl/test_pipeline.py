import os
import etl

def test_parallel_pipeline():
    COUNTRIES = ["Spain", "Germany"]
    SEARCH_TERMS = ["Data Scientist", "Data Analyst"]
    HOURS_OLD = 72
    DB_PATH = "tests/test_jobs.db"

    assert etl.pipeline.parallel_pipeline(COUNTRIES, SEARCH_TERMS, HOURS_OLD, DB_PATH), "Pipeline failed"

    os.remove(DB_PATH)