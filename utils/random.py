import streamlit as st


def generate_diff_metrics(cursor, countries, sts):
    if countries:
        cols = st.columns(len(countries))
        for i, col in enumerate(cols):
            st_placeholders = ','.join('?' * len(sts))

            count_1day = cursor.execute(f"""SELECT count(*) FROM jobspy WHERE country='{countries[i]}'
                AND date_posted > date('now', '-1 days')
                AND id IN (
                    SELECT id 
                    FROM searchterms
                    WHERE search_term in ({st_placeholders})
                    );
                """, sts).fetchall()[0][0]

            count_2day = cursor.execute(f"""SELECT count(*) FROM jobspy WHERE country='{countries[i]}' 
                AND date_posted > date('now', '-2 days')
                AND date_posted <= date('now', '-1 days')
                AND id IN (
                    SELECT id 
                    FROM searchterms
                    WHERE search_term in ({st_placeholders})
                    );
                """, sts).fetchall()[0][0]

            col.metric(f"{countries[i]}", count_1day, count_1day-count_2day, border=True)


def url_ad(cursor, country, search_term):

    query = f"""
        SELECT job_url
        FROM jobspy
        WHERE country='{country}'
        AND id IN (
            SELECT id
            FROM searchterms
            WHERE search_term='{search_term}'
        ) 
        ORDER BY RANDOM() LIMIT 1
    """
    return cursor.execute(query).fetchall()[0][0]