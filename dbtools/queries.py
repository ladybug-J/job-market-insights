import pandas as pd

def count_total_map(conn, countries, sts, days_old):
    if len(countries)==0:
        return
    elif len(countries)==1:
        country_filter = f"WHERE country='{countries[0]}'"
    else:
        country_filter = f"WHERE country IN {tuple(countries)}"

    if len(sts)==0:
        return
    elif len(sts)==1:
        subquery = f"""SELECT id
                    FROM searchterms
                    WHERE search_term='{sts[0]}'
                    """
    else:
        subquery = f"""SELECT id
                        FROM searchterms
                        WHERE search_term IN {tuple(sts)}
                        """

    query = f"""
        SELECT subquery.city, lat, lon, subquery.nr_jobs
        FROM europe
        JOIN 
            (
            SELECT id, city, country, count(*) as nr_jobs
            FROM jobspy
            WHERE id IN (
                {subquery}
                )
            AND jobspy.date_posted >= date('now', '-{days_old} days')
            GROUP BY city 
            ) AS subquery
        ON europe.name=subquery.city AND europe.cou_name_en=subquery.country
        {country_filter}
        """

    return pd.read_sql(query, conn)



def merge_sts(conn, sts, days_old, description=False, group_concat=True):
    if len(sts)==0:
        return
    elif len(sts)==1:
        filter_st = f"r.search_term = '{sts[0]}'"
    else:
        filter_st = f"r.search_term IN {tuple(sts)}"

    select_add = ""
    if description:
        select_add = ", jobspy.description, jobspy.job_url"

    if group_concat:
        search_terms = "GROUP_CONCAT(r.search_term, '-') as search_term"
    else:
        search_terms = "r.search_term"

    query = f"""
        SELECT jobspy.id, jobspy.date_posted, {search_terms},
                jobspy.country, jobspy.city{select_add}
        FROM jobspy
        LEFT JOIN (
            SELECT DISTINCT id, search_term FROM searchterms
        ) r ON r.id = jobspy.id
        WHERE {filter_st} 
        AND jobspy.date_posted >= date('now', '-{days_old} days')
        AND jobspy.date_posted < date('now', '+1 days')
        GROUP BY jobspy.id, jobspy.date_posted
        """

    return pd.read_sql(query, conn)


def count_languages(conn, countries, search_term, days_old):
    desc_lang = pd.read_sql(
        "SELECT DISTINCT description_language FROM jobspy ORDER BY description_language DESC;",
        conn
    )
    query = f"""
        SELECT country, COUNT(description_language) AS 'Number of Jobs', description_language
        FROM jobspy
        WHERE country IN {tuple(countries)} AND id IN (
            SELECT id FROM searchterms WHERE search_term='{search_term}'
        ) AND date_posted >= date('now', '-{days_old} days')
        GROUP BY description_language, country
    """

    return pd.read_sql(query, conn)