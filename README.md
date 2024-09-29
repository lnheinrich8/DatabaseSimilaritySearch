# Project Overview

This project creates a web application using Streamlit to find similarities in non-relational postgreSQL database. The similarities are determined using MinHash and LSH (Locality-Sensitive Hashing) techniques. This app allows users to connect to a database, adjust shingle length and matching thresholds, and compute similarities between tables shown on a heat map.

# How It Works
1. Connect to a PostgreSQL database:
    - Users provide connection details (host, database, port, username, and password) and establish a connection to the PostgreSQL database.
3. MinHash dataframe initialization:
    - A dataframe is created by querying the database to retrieve all table names and column names.
    - Each column's data is cleaned and converted into character-level n-grams (shingles) based on the user-specified shingle length.
4. LSH index creation and querying:
    - A MinHash signature is generated for each column, and the signatures are inserted into an LSH index.
    - The index is used to find approximate matches between columns across different tables.
5. Resulting matches:
    - The similarity matches are computed for each column based on the LSH index.
    - A heatmap visualization shows the amount of similarity between columns, allowing users to easily identify where similar data exists.

# How to Run
1. Install Required Libraries:
    > pip install psycopg2 pandas numpy tqdm datasketch Levenshtein streamlit
2. Run the Application:
    > streamlit run app.py
3. Input Database Credentials:
    - Enter the host, database, port, username, and password to connect to your PostgreSQL database.
4. Adjust Parameters:
    - Input the desired shingle length and matching threshold to fine-tune the similarity analysis.
5. View Results:
    - Once connected and parameters are set, a heatmap will be generated to visualize the similarities between different columns in the tables.







