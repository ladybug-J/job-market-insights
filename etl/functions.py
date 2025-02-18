import jobspy
import sqlite3


def extract(search_term, country):
    return jobspy.scrape_jobs(
        site_name=[
            "indeed",
            "glassdoor"
        ],
        search_term=search_term,
        location=country,
        results_wanted=200,
        hours_old=72,
        country_indeed=country
    )


def transform(jobs, country):
    """
    Remove
    """
    # Select columns with non-null values and drop the ones not having full rows
    cols = ['site', 'title', 'company', 'location', 'date_posted', 'job_url', 'description']
    jobs_red = jobs[cols].dropna().reset_index(drop=True)

    # Find duplicate ads (given title and company, they can exist in different locations)
    duplicates = jobs_red[['company', 'title']].duplicated()
    dup_df = jobs_red.loc[duplicates]

    # Find duplicates and remove the glassdoor one, as it usually has less data than the indeed output
    remove_index = []
    for index, row in dup_df.iterrows():
        temp_dup = jobs_red.loc[(jobs_red.company == row['company']) & (jobs_red.title == row['title'])]
        # If there are duplicates between sites, remove glassdoor:
        if (('indeed' in temp_dup['site'].unique()) & ('glassdoor' in temp_dup['site'].unique())):
            remove_index.append(temp_dup.loc[temp_dup['site'] == 'glassdoor'].index.item())
    jobs_red.drop(remove_index, axis=0, inplace=True)

    # Separate city and country
    jobs_red['city'] = jobs_red['location'].str.split(',').str[0]
    jobs_red['country'] = country
    jobs_red.drop('location', axis=1, inplace=True)

    return jobs_red

def load():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    # Create jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT
        )
    """)
    conn.commit()
