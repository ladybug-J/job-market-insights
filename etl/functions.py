import jobspy
import sqlite3
import datetime
import streamlit as st
from langdetect import detect
from googletrans import Translator

#@st.cache_data(ttl=datetime.timedelta(hours=2))
def extract(search_term, country):
    """
    Get jobspy scropper DataFrame
    """

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

@st.cache_data(ttl=datetime.timedelta(days=1))
def transform(jobs, search_term, country):
    """
    Clean the data (analysed in Jupyter notebook analyse_jobspy.ipynb) by selecting wanted columns, removing duplicate
    entries from different sites (keeping indeed), separate city and country in two columns, convert markdown to plain
    text in description, detect language of the description and add it as a new feature, if the description is not in
    English, translate it.
    """
    # Select columns with non-null values and drop the ones not having full rows
    cols = ['id', 'site', 'title', 'company', 'location', 'date_posted', 'job_url', 'description']
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
            remove_index.extend(list(temp_dup.loc[temp_dup['site'] == 'glassdoor'].index))

    # Remove duplicates and drop site column
    jobs_red.drop(remove_index, axis=0, inplace=True)
    jobs_red.drop('site', axis=1, inplace=True)

    # Separate city and country
    jobs_red['city'] = jobs_red['location'].str.split(',').str[0]
    jobs_red['country'] = country
    jobs_red.drop('location', axis=1, inplace=True)

    # Remove markdown formatting
    markdown_removal_patterns = {
        r'(\*{1,2}|_{1,2})(.*?)\1': r'\2',  # Remove bold (**text**, __text__) and italics (*text*, _text_)
        r'\[([^\]]+)\]\([^)]+\)': r'\1',  # Remove links, keeping only the text
        r'https?://\S+': '',  # Remove standalone URLs
        r'\n': ' ',  # Remove newlines and replace with a space
        r'\\': '',
        r'#': '',
        r'\*': '',
        r'\--': ''
    }
    jobs_red['description'].replace(markdown_removal_patterns, regex=True, inplace=True)

    # Detect language
    jobs_red['description_language'] = jobs_red.description.apply(lambda x: detect(x)).values

    # Translate the ones that are not in English to English
    translator = Translator()
    index_nonen = jobs_red.loc[jobs_red['description_language'] != 'en'].index

    def translate_exception(text):
        try:
            return translator.translate(text, dest='en').text
        except:
            print("Translate exception entered!")
            return None

    jobs_red.loc[index_nonen, 'description'] = jobs_red.loc[index_nonen, 'description'].apply(
        lambda x: translate_exception(x)
    )

    # Drop NaNs that the exception might have generated
    jobs_red.dropna(subset='description', inplace=True)
    # Turn description to lower-case
    jobs_red['description'] = jobs_red['description'].str.lower()

    # Add search term column
    jobs_red['search_term'] = search_term

    return jobs_red

def load(jobs_df):
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    # Create jobspy table
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
            description_language TEXT,
            search_term TEXT
        )
    """)
    conn.commit()

    # Check already existing ids in database, and remove them from query if they exist
    ids = cursor.execute("SELECT id FROM jobspy").fetchall()
    already_db = [id_[0] for id_ in ids]
    remove_idx = jobs_df.loc[jobs_df['id'].isin(already_db)].index
    jobs_df.drop(remove_idx, axis=0, inplace=True)
    jobs_df.to_sql(
        "jobspy",
        conn,
        if_exists='append',
        index=False,
    )
    conn.commit()