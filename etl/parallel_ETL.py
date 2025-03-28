import jobspy
import sqlite3
import datetime
import pandas as pd
import streamlit as st
from langdetect import detect
from googletrans import Translator
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = "jobs.db"

#@st.cache_data(ttl=datetime.timedelta(days=14))
def extract(search_term, country, hours_old):
    """
    Scrapes job postings and removes duplicates in this step.
    """
    print(f"Extracting jobs for '{search_term}' in {country}...")
    jobs_df = pd.DataFrame(jobspy.scrape_jobs(
        site_name=["indeed", "glassdoor"],
        search_term=search_term,
        location=country,
        results_wanted=400,
        hours_old=hours_old,
        country_indeed=country
    ))

    if jobs_df.empty:
        print(f"No jobs found for '{search_term}' in {country}.")
        return jobs_df

    # Remove duplicate job ads (keep Indeed over Glassdoor)
    duplicates = jobs_df.duplicated(subset=['company', 'title'], keep=False)
    duplicate_rows = jobs_df[duplicates]

    remove_idx = []
    for _, row in duplicate_rows.iterrows():
        temp_dup = jobs_df[(jobs_df['company'] == row['company']) & (jobs_df['title'] == row['title'])]
        if {'indeed', 'glassdoor'}.issubset(temp_dup['site'].unique()):
            remove_idx.extend(temp_dup[temp_dup['site'] == 'glassdoor'].index)

    jobs_df.drop(remove_idx, inplace=True)
    jobs_df.drop(columns=['site'], inplace=True)

    print(f"Extracted {jobs_df.shape[0]} unique jobs for '{search_term}' in {country}.")
    return jobs_df


#@st.cache_data(ttl=datetime.timedelta(days=1))
def transform(jobs_chunk, search_term, country):
    """
    Transforms a chunk of job data: cleans, detects language, and translates descriptions.
    """
    print(f"Transforming chunk of {jobs_chunk.shape[0]} jobs for '{search_term}' in {country}...")

    if jobs_chunk.empty:
        return jobs_chunk

    cols = ['id', 'title', 'company', 'location', 'date_posted', 'job_url', 'description']
    jobs_chunk = jobs_chunk[cols].dropna().reset_index(drop=True)

    # Extract city from location
    jobs_chunk['city'] = jobs_chunk['location'].str.split(',').str[0]
    jobs_chunk['country'] = country
    jobs_chunk.drop(columns=['location'], inplace=True)

    # Clean markdown and formatting
    markdown_patterns = {
        r'(\*{1,2}|_{1,2})(.*?)\1': r'\2',
        r'\[([^\]]+)\]\([^)]+\)': r'\1',
        r'https?://\S+': '',
        r'\n': ' ',
        r'\\': '',
        r'#': '',
        r'\*': '',
        r'\--': ''
    }
    jobs_chunk['description'].replace(markdown_patterns, regex=True, inplace=True)

    # Detect language & translate if not English
    translator = Translator()
    jobs_chunk['description_language'] = jobs_chunk['description'].apply(lambda x: detect(x))

    non_en_idx = jobs_chunk[jobs_chunk['description_language'] != 'en'].index

    def translate_safe(text):
        try:
            return translator.translate(text, dest='en').text
        except:
            return None

    jobs_chunk.loc[non_en_idx, 'description'] = jobs_chunk.loc[non_en_idx, 'description'].apply(translate_safe)
    jobs_chunk.dropna(subset=['description'], inplace=True)

    # Convert descriptions to lowercase
    jobs_chunk['description'] = jobs_chunk['description'].str.lower()
    jobs_chunk['search_term'] = search_term

    print(f"Transformation complete for {jobs_chunk.shape[0]} jobs in chunk for '{search_term}' in {country}.")
    return jobs_chunk


def load(jobs_chunk, search_term):
    """
    Loads a chunk of transformed jobs into SQLite database.
    First removes existing IDs from 'searchterms', then from 'jobspy'.
    """
    if jobs_chunk.empty:
        print("No jobs to load.")
        return

    conn = sqlite3.connect(DB_PATH)
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

    print(f"Checking for existing jobs in the database for search term '{search_term}'...")

    # Remove existing IDs from searchterms table
    existing_search_ids = set(id_[0] for id_ in cursor.execute(
        "SELECT id FROM searchterms WHERE search_term=?", (search_term,)
    ).fetchall())

    jobs_chunk = jobs_chunk[~jobs_chunk['id'].isin(existing_search_ids)]

    if not jobs_chunk.empty:
        search_df = jobs_chunk[['id']].copy()
        search_df['search_term'] = search_term
        search_df['country'] = jobs_chunk['country']
        search_df.to_sql("searchterms", conn, if_exists='append', index=False)

    conn.commit()

    # Remove existing IDs from jobspy table
    existing_jobspy_ids = set(id_[0] for id_ in cursor.execute("SELECT id FROM jobspy").fetchall())
    jobs_chunk = jobs_chunk[~jobs_chunk['id'].isin(existing_jobspy_ids)]

    if not jobs_chunk.empty:
        jobs_chunk.drop(columns=['search_term']).to_sql("jobspy", conn, if_exists='append', index=False)

    conn.commit()
    conn.close()

    print(f"Loaded {jobs_chunk.shape[0]} jobs into the database for '{search_term}'.")


def process_chunk(jobs_chunk, search_term, country):
    """
    Process a single chunk: transform and load.
    """
    transformed_jobs = transform(jobs_chunk, search_term, country)
    load(transformed_jobs, search_term)


def etl(search_term, country, hours_old):
    """
    Runs ETL pipeline for a single search term and country.
    Extracts jobs, splits them into chunks, and processes each chunk in parallel.
    """
    jobs_df = extract(search_term, country, hours_old)
    if jobs_df.empty:
        return

    chunk_size = 10  # Number of rows per chunk
    chunks = [jobs_df.iloc[i:i + chunk_size] for i in range(0, len(jobs_df), chunk_size)]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_chunk, chunk, search_term, country) for chunk in chunks]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing chunk: {e}")


def run_parallel_etl(search_terms, countries, hours_old):
    """
    Runs the ETL pipeline in parallel for multiple search terms & countries.
    """
    print(f"Starting parallel ETL for {search_terms} in {countries}")

    with ThreadPoolExecutor(max_workers=len(search_terms) * len(countries)) as executor:
        futures = {executor.submit(etl, search_term, country, hours_old): (search_term, country)
                   for search_term in search_terms for country in countries}

        for future in as_completed(futures):
            search_term, country = futures[future]
            try:
                future.result()
                print(f"ETL completed for '{search_term}' in {country}.")
            except Exception as e:
                print(f"Error processing '{search_term}' in {country}: {e}")

    print("Parallel ETL completed successfully.")


# Example usage
if __name__ == "__main__":
    search_terms = ["Data Scientist", "Data Analyst", "AI Engineer"]
    countries = ["Spain", "Germany", "Austria", "France", "Switzerland"]
    run_parallel_etl(search_terms, countries, None)
