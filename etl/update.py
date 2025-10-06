import sqlite3
import sys
import os

# Add project root to PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

import etl

def delete_last(conn, days=60):
    """
    Delete from database entries posted more than 'days' ago. Default 60 ~ 2 month.

    """
    # As there is a foreign key constrain, first the IDs should be saved and deleted from searchterms, and then
    # removed from jobspy
    query = f"""
        SELECT id 
        FROM jobspy
        WHERE date_posted <= date('now', '-{days} days')
    """

    ids = conn.cursor().execute(query).fetchall()
    flat_ids = [i[0] for i in ids]

    # Remove from both tables, first from the one with the foreign key constrain
    conn.cursor().execute(f"""
        DELETE FROM searchterms
        WHERE id in {tuple(flat_ids)}
    """)
    conn.cursor().execute(f"""
        DELETE FROM jobspy
        WHERE id in {tuple(flat_ids)}
    """)

    conn.commit()


if __name__ == '__main__':

    DB_PATH = "jobs.db"

    conn = sqlite3.connect(DB_PATH)
    delete_last(conn)
    conn.close()

    # Scrape default terms and countries:
    search_terms = ['Data Analyst', 'Data Scientist', 'Data Engineer']
    countries = ['Austria', 'France', 'Germany', 'Spain', 'Switzerland']
    HOURS_OLD = 168
    etl.pipeline.parallel_pipeline(
        countries,
        search_terms,
        HOURS_OLD,
        DB_PATH
    )
