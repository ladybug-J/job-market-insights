import jobspy
import sqlite3
import pandas as pd

def connect_db(db_path):
    """ Return SQL connection with a timeout """
    return sqlite3.connect(db_path, timeout=10)

def create_tables(conn):
    """
    Create 'jobspy' and 'searchterms tables, if they do not exist already.

    ## This and the following functions could be refactored further into a general class for tables ##
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobspy (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            date_posted TEXT,
            job_url TEXT,
            description TEXT,
            city TEXT,
            country TEXT,
            description_language TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS searchterms (
            id TEXT,
            search_term TEXT,
            country TEXT,
            FOREIGN KEY (id) REFERENCES jobspy(id),
            PRIMARY KEY (id, search_term, country)
        )
    """)
    conn.commit()

def write_sql(conn, table_df):
    """
    Write scraped jobs into two normalized tables: `jobspy` and `searchterms`.

    - `jobspy`: stores unique job postings (primary key = id).
    - `searchterms`: links job IDs to the search term(s) they were found with.
      A job can appear under multiple search terms, enabling queries like
      "find jobs that match more than one search term".

    Uses INSERT OR IGNORE to avoid duplicate rows (based on primary keys),
    so we don't need to pre-filter with Pandas.
    """
    # Fill jobspy table:
    data = table_df[[
        "id", "title", "company", "date_posted", "job_url", "description", "city", "country", "description_language"
    ]].values.tolist()

    # Ignore if primary key (id) already exists --> Saves checking indexes with Pandas
    query = f"""
    INSERT OR IGNORE INTO 'jobspy'
    (id, title, company, date_posted, job_url, description, city, country, description_language)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.executemany(query, data)
    conn.commit()

    # Fill searchterms table:
    data = table_df[[
        "id", "search_term", "country"
    ]].values.tolist()

    query = f"""
    INSERT OR IGNORE INTO 'searchterms'
    (id, search_term, country)
    VALUES (?, ?, ?)
    """
    conn.executemany(query, data)
    conn.commit()


def run(data, db_path):
    conn = connect_db(db_path)
    create_tables(conn)
    write_sql(conn, data)
    conn.close()