import streamlit as st

lab1_page = st.Page("Lab1.py", title="Lab 1")
lab2_page = st.Page("Lab2.py", title="Lab 2")
lab3_page = st.Page("Lab3.py", title="Lab 3")
lab4_page = st.Page("Lab4.py", title="Lab 4", default=True)

pg = st.navigation([lab1_page, lab2_page, lab3_page, lab4_page])
pg.run()
