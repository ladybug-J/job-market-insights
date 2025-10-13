import logging
import pandas as pd

from langdetect import detect
from googletrans import Translator


logging.basicConfig(
    format='%(asctime)s - %(levelname)s: %(message)s',
    level=logging.ERROR
)
logger = logging.getLogger(__name__)

def city_country(jobs_df, country):
    """
    Extract city from full location, add country and city columns
    """
    # Drop rows with NaNs and reset index:
    jobs_df = jobs_df.dropna().reset_index(drop=True)
    # Location is separated by commas, being the first element the city:
    jobs_df['city'] = jobs_df['location'].str.split(',').str[0]
    jobs_df['country'] = country
    jobs_df.drop(columns=['location'], inplace=True)

    return jobs_df

def remove_formatting(jobs_df):
    """
    Remove markdown formatting from description
    """
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
    jobs_df['description'].replace(markdown_patterns, regex=True, inplace=True)

    return jobs_df

def detect_language(jobs_df):
    """
    Detect language & add column 'description_language'
    """
    jobs_df['description_language'] = jobs_df['description'].apply(lambda x: detect(x))
    return jobs_df

def translate2en_description(jobs_df):
    """
    Translate description (if it is not in English) and remove job offer if translation fails.
    """
    translator = Translator()

    def translate_safe(text):
        try:
            return translator.translate(text, dest='en').text
        except:
            logger.info(f"Translation failed - for text: {text[:100]}")
            return None

    non_en_idx = jobs_df[jobs_df['description_language'] != 'en'].index
    jobs_df.loc[non_en_idx, 'description'] = jobs_df.loc[non_en_idx, 'description'].apply(translate_safe)
    jobs_df.dropna(subset=['description'], inplace=True)

    return jobs_df

def add_lower_columns(jobs_df, search_term):
    """
    Add search term in lowercase as column and convert to description to lowercase
    """
    jobs_df['description'] = jobs_df['description'].str.lower()
    jobs_df['search_term'] = search_term.lower()
    return jobs_df

def run(jobs_df, country, search_term):
    """
    Run sequence of transformations
    """
    return (
        jobs_df
        .pipe(lambda df: city_country(df, country))
        .pipe(remove_formatting)
        .pipe(detect_language)
        .pipe(translate2en_description)
        .pipe(lambda df: add_lower_columns(df, search_term))
    )