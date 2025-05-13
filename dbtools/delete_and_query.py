import sqlite3
import sys
import os

# Add project root to PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from etl.parallel_ETL import run_parallel_etl
from queries import delete_last_30

# Delete last 30 days:
conn = sqlite3.connect("jobs.db")
delete_last_30(conn)
conn.commit()

# Scrape default terms and countries:
search_terms = ['Data Analyst', 'Data Scientist', 'Data Engineer']
countries = ['Austria', 'France', 'Germany', 'Spain', 'Switzerland']
HOURS_OLD = 168

for search_term in search_terms:
    run_parallel_etl([search_term], countries, HOURS_OLD)

