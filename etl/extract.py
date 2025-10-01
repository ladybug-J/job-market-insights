import logging

import pandas as pd

import jobspy

logging.basicConfig(
    format='%(asctime)s - %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

COLUMNS = ['id', 'title', 'company', 'location', 'date_posted', 'job_url', 'description', 'site']
MAX_RESULTS = 400
SITES = ["indeed", "glassdoor"]

def call_jobspy(search_term, country, hours_old, max_results=MAX_RESULTS, sites=SITES):
    """
    Scrape data using JobSpy - expected pandas DataFrame with at least the columns ['id', 'company', 'title']
    """
    jobs_df = pd.DataFrame(jobspy.scrape_jobs(
        site_name=sites,
        search_term=search_term,
        location=country,
        results_wanted=max_results,
        hours_old=hours_old,
        country_indeed=country
    ))
    if jobs_df.empty:
        logger.info(f"No jobs found for '{search_term}' in {country}.")

    logger.debug(f"Dataframe head: {jobs_df.head(20)}")

    return jobs_df


def drop_duplicates(jobs_df):
    """
    Removes duplicates between different job boards and cities
    """
    duplicates = jobs_df.duplicated(subset=['company', 'title'], keep=False)
    duplicate_rows = jobs_df[duplicates]

    remove_idx = []
    for _, row in duplicate_rows.iterrows():
        temp_dup = jobs_df[(jobs_df['company'] == row['company']) & (jobs_df['title'] == row['title'])]
        if {'indeed', 'glassdoor'}.issubset(temp_dup['site'].unique()):
            remove_idx.extend(temp_dup[temp_dup['site'] == 'glassdoor'].index)

    return jobs_df.drop(remove_idx).drop(columns=['site'])


def run(country, search_term, hours_old):
    """
    Scrapes job postings with Jobspy library, removes duplicates between different job boards, and returns a
    pandas DataFrame
    """
    logger.info(f"Extracting jobs for '{search_term}' in {country}...")
    # Scrape with Jobspy:
    jobs_df = call_jobspy(
        search_term,
        country,
        hours_old
    )
    # Select necessary columns:
    jobs_df = jobs_df[COLUMNS]
    # Drop duplicates:
    jobs_df = drop_duplicates(jobs_df)

    logger.info(f"Extracted {jobs_df.shape[0]} unique jobs for '{search_term}' in {country}.")

    return jobs_df