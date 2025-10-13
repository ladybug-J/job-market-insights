import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed

import etl

def transform_load(data, country, searchterm, dbpath):
    print(f"Entered transform_load for: ({country}, {searchterm})...")
    data = etl.transform.run(data, country, searchterm)
    etl.load.run(data, dbpath)
    print(f"Exited transform_load for: ({country}, {searchterm})...")


def parallel_pipeline(countries, search_terms, hours_old, dbpath):
    """
    Parallelize in threads the ETL pipeline for a search term and country. The extract
    """
    with ThreadPoolExecutor(max_workers=len(search_terms)*len(countries)) as extract_executor,\
            ThreadPoolExecutor(max_workers=5) as transform_executor:
        # Map extract to all the combis
        combis = list(itertools.product(countries, search_terms))
        combis_with_hours = [(country, term, hours_old) for country, term in combis]
        extracted_futures = {
            extract_executor.submit(etl.extract.run, *tup): tup
            for tup in combis_with_hours
        }

        futures = list()
        for ext_df in as_completed(extracted_futures.keys()):
            print("New extracted dataset..")
            tup = extracted_futures[ext_df]
            ft = transform_executor.submit(transform_load, *(ext_df.result(), tup[0], tup[1], dbpath))
            futures.append(ft)
        for f in futures:
            f.result()

    return True


if __name__ == '__main__':

    countries = ["Spain", "Germany", "France"]
    search_terms = ["Data Scientist", "Data Analyst"]
    hours_old = 72
    db_path = "../tests/test_jobs.db"

    parallel_pipeline(countries, search_terms, hours_old, db_path)