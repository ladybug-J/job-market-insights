import streamlit as st
from dbtools import queries

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

def ranking_table(conn, sts, days_old):
    df = queries.merge_sts(conn, sts, days_old)
    total = df.groupby(by=['city', 'country']).count()\
              .rename({'id': 'Total jobs'}, axis=1)\
              .drop(['date_posted', 'search_term'], axis=1)\
              .sort_values(by='Total jobs', ascending=False)

    total_country = total.groupby(by='country', axis=0).sum()

    """
    df = df.groupby(by=['city', 'search_term', 'country'], as_index=False)\
        .count()\
        .pivot(
            index=['city', 'country'],
            columns=['search_term'],
            values='id')\
        .fillna(0.0)

    merge_df = total.merge(df, on=['city', 'country']).sort_values('Total jobs', ascending=False)
    combined_cols = [col for col in merge_df.columns if "-" in col]
    merge_df['Mixed labels'] = merge_df[combined_cols].sum(axis=1)
    merge_df.drop(combined_cols, axis=1, inplace=True)

    for col in merge_df.columns:
        if col not in ['city', 'country', 'Total jobs']:
            merge_df[col] = (100*merge_df[col]/merge_df['Total jobs']).round(1).astype(float)
    
    st.table(merge_df.iloc[:10])
    """
    # Some cities are wrong:
    remove = ['Home Office', 'España', 'En remoto', 'DE']
    i = 0
    for index, row in total.iterrows():
        if (i < 10 and index[0] not in remove):
            total.loc[index, ('Percentage country')] = (100*row['Total jobs']/total_country.loc[index[1], 'Total jobs']).round(1)
            i+=1
    total.dropna(inplace=True)

    st.table(total)
    pass




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