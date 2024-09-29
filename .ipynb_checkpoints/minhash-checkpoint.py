import string
import pandas as pd
import re
import Levenshtein
from datasketch import MinHash, MinHashLSH, LeanMinHash

global lsh
lsh = MinHashLSH(threshold=0.40, num_perm=128)

def clean(my_str, stop_words):
    # Remove punctuation
    my_str = my_str.translate(str.maketrans('', '', string.punctuation))
    # lower case
    my_str=my_str.lower()
    # remove stop words
    for i in stop_words:
        my_str = re.sub("\\b"+i+"\\b", '', my_str)
    # remove whitespace
    my_str=my_str.strip()
    return my_str

# Function to create character n-grams
def chargrams(n, collist, df):
    for col in collist:
        df[col + '_ngrams'] = [
            j if pd.isnull(j) else [j[i:i+n] for i in range(len(j)-n+1)] if len(j) > n else [j]
            for j in df[col]
        ]
    return df

# Function that minhashes and returns tuple with keyid
def prep_minhash(keyset):
    keyid = keyset[0]
    setlist = keyset[1]
    m = MinHash(num_perm=128) #This parameter should be adjusted for speed & memory with accuracy trade-off
    for d in setlist:
        m.update(d.encode('utf8'))
    lean_m=LeanMinHash(m)
    lsh.insert(keyid, lean_m)
    return (keyid, lean_m)

### test function
# Prepare MinHashes and insert into LSH
def prep_minhash2(row):
    minhash = MinHash(num_perm=128)
    for shingle in row['match_string_ngrams']:
        minhash.update(shingle.encode('utf8'))
    lean_minhash = LeanMinHash(minhash)
    lsh.insert(row['minhashkey'], lean_minhash)
    return lean_minhash

# Function to approximate jaccard similarity using LSH index created
# Returns list of keyids matching that minhashed set
def query_result(hashset):
    result = lsh.query(hashset[1])
    return result

# Function returns the Levenshtein distance. Input is a tuple of names
def calc_lev(names):
    result = Levenshtein.ratio(names[0], names[1])
    return result

# Function to get table name from minhashkey
def get_table_name(minhashkey):
    return minhashkey.split('_')[0]

# Filtering out self-matches
def filter_self_matches(row):
    table_name = get_table_name(row['minhashkey'])
    filtered_matches = [match for match in row['matches'] if get_table_name(match) != table_name]
    return filtered_matches