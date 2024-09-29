import psycopg2 as ps
import pandas as pd
import numpy as np
import minhash as mh
from tqdm import tqdm
from datasketch import MinHash, MinHashLSH, LeanMinHash

# Establishes the connection to the specified database and returns the engine
def connect(host, database, user, password, port):
    # Establish connection
    engine = ps.connect(host=host, 
                        database=database, 
                        user=user, 
                        password=password,
                        port=port)
    return engine

# Initializes the minhash dataframe with specified shingle length and LSH threshold value (0 < threshold < 1)
def initialize_minhash_df(engine, shingle_length, threshold):

    mh.lsh = MinHashLSH(threshold=threshold, num_perm=128)

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
            reduced = i.replace('_', '')
            minhashkey = key + '_' + reduced
            q = 'select ' + i + ' from ' + key
            df = pd.read_sql(q, con=engine)
            df.columns = ['match_string']
            df['minhashkey'] = minhashkey
            mydflength = np.arange(len(df))
            df['minhashkey'] = [i + '_' + str(j) for (i,j) in zip(df['minhashkey'], mydflength)]
            findf = pd.concat([findf, df], axis=0)

    for table in table_list:
        q = 'select * from ' + table + ' limit 0'
        columnn_df = pd.read_sql(q, con=engine)
        column_list = list(columnn_df)
        column_list = [col.replace('_', '') for col in column_list]
        table_dict[table] = column_list

    findf = findf[['minhashkey', 'match_string']]

    # Ensure everything is a string
    findf['match_string'] = findf['match_string'].astype('str')

    # Clean the match_string column
    tqdm.pandas()
    findf['match_string'] = findf['match_string'].progress_apply(mh.clean, args=([], ))

    # Converting minhash dataframe to shingles of n chars
    full_df = findf.copy()
    full_df = mh.chargrams(shingle_length, ['match_string'], full_df)

    # Select only the required columns
    full_df = full_df[['minhashkey', 'match_string_ngrams']]

    return full_df, table_list, table_dict

# Returns the full dataframe with the added LSH index and matches columns
def find_matches(full_df):

    # Replace nulls
    full_df['match_string_ngrams'] = full_df['match_string_ngrams'].replace(np.nan, '')

    # Create key set
    full_df['key_set'] = list(zip(full_df['minhashkey'],full_df['match_string_ngrams']))

    # Create LSH index
    full_df['minhash'] = full_df['key_set'].progress_apply(mh.prep_minhash)   

    # Return list of approximate matches using minhash
    full_df['matches'] = full_df['minhash'].apply(mh.query_result)

    # Filter self matches
    full_df['matches'] = full_df.apply(mh.filter_self_matches, axis=1)

    return full_df

# Returns a dictionary of dictionaries for every table. These table dictionaries include a dictionary 
#   for every column where the keys are every other column of the other tables and the vbalues are the 
#   amount of matches from the current table column to the other table column.
#
#   example dictionary structure:
#
#                           table1
#                             |
# matchdict_dict:       {   dict1   ,    ...   }
#                            /\
#                           /  \
#                          /    \
# (cols of table1)  coldict11     coldict12
#                     |             |
#                  col21:20      col21:5
#                  col22:2       col22:0
#                  col31:96      col31:0
#                  col32:1       col32:438
#
def match_dictionaries(full_df, table_list, table_dict):

    # Create the dictionaries for each table
    matchdict_dict = {}
    for table in table_list:
        matchdict_dict[table] = {}

        # Create dictionaries for every column in the table
        for col in table_dict[table]:
            column_name = table + '_' + col
            matchdict_dict[table][column_name] = {}

            # Initialize with zeros
            for other_table in table_list:
                if other_table != table:
                    for other_col in table_dict[other_table]:
                        other_column_name = other_table + '_' + other_col
                        matchdict_dict[table][column_name][other_column_name] = 0

    # Look for matches in match list and increment in dictionary
    for i in range(len(full_df)):
        # Get the row with index
        df_row = full_df.iloc[i]
        mhkey = df_row['minhashkey']
        current_table = mh.get_table_name(mhkey)
        match_col = mh.get_table_name(mhkey) + '_' + mh.get_column_name(mhkey)

        # Update the dictionary with matches
        for match in df_row['matches']:
            other_col_name = mh.get_table_name(match) + '_' + mh.get_column_name(match)
            if other_col_name in matchdict_dict[current_table][match_col]:
                matchdict_dict[current_table][match_col][other_col_name] += 1

    return matchdict_dict