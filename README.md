Project Overview

This project creates a web application using Streamlit to find similarities between different columns in tables from a PostgreSQL database. 
The similarities are determined using MinHash and LSH (Locality-Sensitive Hashing) techniques. This app allows users to input database credentials, 
connect to a database, and then adjust shingle length and matching thresholds to compute similarities between tables.

Features
Connect to a PostgreSQL Database:

Users can enter their database credentials and connect to a database using the app interface.
PostgreSQL connection is established using psycopg2.
Data Similarity Analysis:

The application uses MinHash to compute approximate Jaccard similarities between the columns of different tables in the database.
Users can adjust the shingle length and matching threshold to customize the similarity analysis.
LSH (Locality-Sensitive Hashing):

The app employs LSH to index and query for approximate similarities between columns. This allows for efficient similarity search even with large datasets.
