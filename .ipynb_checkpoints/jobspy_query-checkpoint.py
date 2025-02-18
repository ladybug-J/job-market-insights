from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=[
        "indeed",
        "glassdoor"
    ],
    search_term="data science",
    location="Spain",
    results_wanted=200,
    hours_old=72,
    country_indeed='Spain'
)
pass