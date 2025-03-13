# Run ETL job
from .functions import extract, transform, load


def main(conn, search_term, country):
    print(f"Starting scraping jobs with search term '{search_term}' in {country}")
    jobs = extract(search_term=search_term, country=country)
    print(f"Jobspy scraping complete - {jobs.shape[0]} jobs queried")
    if not jobs.empty:
        jobs_transformed = transform(jobs=jobs, search_term=search_term, country=country)
        del jobs
        load(conn, jobs_transformed, search_term)
        print(f"ETL complete - {jobs_transformed.shape[0]} jobs saved into database")


if __name__ == "__main__":

    import argparse
    import sqlite3
    from .europe_table import update_europe_table

    argParser = argparse.ArgumentParser()
    argParser.add_argument("--conn", type=sqlite3.Connection, help="sqlite3.Connection object")
    argParser.add_argument("--search_term", type=str, help="Search term for scraper")
    argParser.add_argument("--country", type=str, help="Country of the search")
    args = argParser.parse_args()

    main(args.conn, args.search_term, args.country)