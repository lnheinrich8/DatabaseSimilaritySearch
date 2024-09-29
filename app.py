import streamlit as st
import model as md
import pandas as pd
import matplotlib.pyplot as plt 
import matplotlib.colors as colors 

# Helper function to hide inputs after successful connection
def hide_inputs():
    host_container.empty()
    database_container.empty()
    port_container.empty()
    user_container.empty()
    pass_container.empty()
    connect_bcontainer.empty()

st.title('Data Simularity Heat Map')

# Setting up text inputs and buttons
host_container = st.empty()
database_container = st.empty()
port_container = st.empty()
user_container = st.empty()
pass_container = st.empty()
connect_bcontainer = st.empty()

# Initialize session state variables if not already done
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'calculation_done' not in st.session_state:
    st.session_state.calculation_done = False

if not st.session_state.connected:
    host = host_container.text_input('PostgreSQL database host:', key='host')
    databasename = database_container.text_input('Database name:', key='database')
    port = port_container.text_input('Port:', key='port')
    username = user_container.text_input('Master username:', key='username')
    password = pass_container.text_input('Password:', key='password', type='password')

    connect_clicked = connect_bcontainer.button('Connect')

    if connect_clicked:
        try:
            st.session_state.con = md.connect(
                host=st.session_state.host, 
                database=st.session_state.database, 
                user=st.session_state.username, 
                password=st.session_state.password,
                port=st.session_state.port
            )
            hide_inputs()
            st.session_state.connected = True
            st.success('Connected successfully!')
        except Exception as e:
            st.warning('Please check that all of your information is correct and try again')
            print(f"Connection failed: {e}")

if st.session_state.connected:
    st.write("  In a non-relational database, the user may want to find where the same data exists in different tables.")

    st.write("  When searching for similarites in data, words should not have to be identical to count as a match. The"
             " substring length determines how text is split, and the matching threshold sets the percentage of matching parts required.") 
    
    st.write("Higher values for both result in more accurate matches but fewer results, while lower values make it easier"
             " to find matches but increase noise. Finding the right combination is key. The substring length should be a positive"
             " integer, and the matching threshold should be a decimal between 0 and 1 (non inclusive).")

    shingle_length_container = st.empty()
    shingle_length = shingle_length_container.text_input('Characters per substring:', help="Short shingles capture more fine-grained similarities but can lead to a higher chance of noise (i.e., unrelated shingles appearing similar)." 
                                                         " They might also increase the computational load since there are more shingles to compare. Longer shingles reduce the number of shingles created, potentially decreasing noise and improving efficiency."
                                                         " However, they may miss some local similarities, especially in cases where relevant patterns span shorter lengths.", key='shingle_length')
    threshold_container = st.empty()
    threshold = threshold_container.text_input('Matching Threshold:', help="This value represents the percent of shingles that must be identical for the strings to be considered a match." 
                                               " A higher threshold (e.g., 0.7 or 0.8) indicates that the sets must have a high degree of overlap to be considered similar. This is useful when false positives are a concern."
                                               " A lower threshold (e.g., 0.3 or 0.4) allows for more sets to be classified as similar, which might be appropriate in contexts where a broader similarity is acceptable.", key='threshold')
    calc_bcontainer = st.empty()
    calc_button = calc_bcontainer.button('Calculate')

    if calc_button:
        try:
            shingle_length = int(shingle_length)
            threshold = float(threshold)
            if shingle_length <= 0 or not (0 < threshold < 1):
                st.warning('The shingle length must be greater than zero and the threshold should be between 0 and 1.')
            else:
                calc_bcontainer.empty()

                with st.spinner('Creating LSH indices...'):
                    full_df, table_list, table_dict = md.initialize_minhash_df(st.session_state.con, shingle_length, threshold)
                    st.session_state.table_dict = table_dict
                    full_df = md.find_matches(full_df)
                    st.session_state.matchdict_dict = md.match_dictionaries(full_df, table_list, table_dict)
                shingle_length_container.empty()
                threshold_container.empty()
                st.success('Data frame initialized and matches found successfully!')
                st.session_state.calculation_done = True

        except ValueError:
            st.warning('Please ensure the shingle length is an integer greater than 0 and the threshold is a decimal value between 0 and 1')
        
    # code block that creates a heatmap of all matches
    if st.session_state.calculation_done:

        column_list = []
        for table in st.session_state.table_dict.keys():
            for column in st.session_state.table_dict[table]:
                column_list.append(table + '_' + column)

        # Initialize the 2D matrix with zeros
        matrix = pd.DataFrame(0, index=column_list, columns=column_list)

        for base_dict in st.session_state.matchdict_dict.keys():
            current_base = st.session_state.matchdict_dict[base_dict]
            for matrixrow in current_base.keys():
                current_row = current_base[matrixrow]
                for matrixcol in current_row.keys():
                    matrix.loc[matrixrow, matrixcol] = current_row[matrixcol]

        st.dataframe(matrix.style.background_gradient(cmap='YlOrRd'))
