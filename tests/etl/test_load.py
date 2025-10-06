import pandas as pd

import etl

DB_PATH = "../jobs_test.db"

def test_connect():
    """ Check if connection responds something. """
    conn = etl.load.connect_db(DB_PATH)

    def connection_alive(conn):
        try:
            conn.execute("SELECT * FROM sqlite_master").fetchall()
            return True
        except:
            return False

    assert connection_alive(conn), f"Connection to {DB_PATH} fails!"


def test_create_tables():
    """ Check if tables 'jobspy' and 'searchterms' are created. """

    conn = etl.load.connect_db(DB_PATH)
    etl.load.create_tables(conn)
    assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobspy'").fetchall(),\
        f"jobspy table does not exist in {DB_PATH}"
    assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='searchterms'").fetchall(),\
        f"searchterms table does not exist in {DB_PATH}"


def test_write_sql():
    data = pd.DataFrame(
        {"id": ["123", "123", "124", "125"],
         "title": ["a", "a", "b", "c"],
         "company": 4*[" "],
         "date_posted": 4*[" "],
         "job_url": 4*[" "],
         "description": 4*[" "],
         "city": 4*[" "],
         "country": 4*[" "],
         "description_language": 4*[" "],
         "search_term": ["st1", "st2", "st1", "st1"]
         })
    conn = etl.load.connect_db(DB_PATH)
    etl.load.write_sql(conn, data)

    sts = conn.execute("SELECT search_term FROM searchterms WHERE id=123").fetchall()
    assert len(sts) == 2, "Search terms aren't properly saved"