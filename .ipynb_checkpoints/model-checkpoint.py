import psycopg2 as ps
import pandas as pd
import numpy as np
import minhash as mh
from tqdm import tqdm

# Establish connection
engine = ps.connect(host='examplecustomerdb.cvg88iwm6hkp.us-east-2.rds.amazonaws.com', 
                        database='examplecsvs', 
                        user='lnheinrich8', 
                        password='Skateboard4l!',
                        port='5432'
        )

# Query to get table names
query = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
"""

# Get table names
table_df = pd.read_sql(query, con=engine)
table_list = list(table_df['table_name'])

# Create dictionary of table columns
table_dict = {}
for table in table_list:
    q = 'select * from ' + table + ' limit 0'
    columnn_df = pd.read_sql(q, con=engine)
    column_list = list(columnn_df)
    table_dict[table] = column_list

# Create the minhashkey dataframe
findf = pd.DataFrame([])
for key in table_dict.keys():
    for i in table_dict[key]:
        minhashkey = key + '_' + i
        q = 'select ' + i + ' from ' + key
        df = pd.read_sql(q, con=engine)
        df.columns = ['match_string']
        df['minhashkey'] = minhashkey
        mydflength = np.arange(len(df))
        df['minhashkey'] = [i + '_' + str(j) for (i,j) in zip(df['minhashkey'], mydflength)]
        findf = pd.concat([findf, df], axis=0)

findf = findf[['minhashkey', 'match_string']]

# Ensure everything is a string
findf['match_string'] = findf['match_string'].astype('str')

# Clean the match_string column
tqdm.pandas()
findf['match_string'] = findf['match_string'].progress_apply(mh.clean, args=([], ))

# Converting minhash dataframe to shingles of 3 chars
match_shingles = findf.copy()
match_shingles = mh.chargrams(3, ['match_string'], match_shingles)

# Select only the required columns
match_shingles = match_shingles[['minhashkey', 'match_string_ngrams']]

# Replace nulls
match_shingles['match_string_ngrams'] = match_shingles['match_string_ngrams'].replace(np.nan, '')

# Create key set
match_shingles['key_set'] = list(zip(match_shingles['minhashkey'],match_shingles['match_string_ngrams']))

### for testing remove when done
match_shingles = match_shingles[:20]
match_shingles['minhash'] = match_shingles['key_set'].progress_apply(mh.prep_minhash)   

print(match_shingles.head(20))
