import streamlit as st

pages = {
    "Seleziona la versione":[
        st.Page("option_app.py", title="Versione 1", icon=":material/counter_1:"),
        st.Page("option_app_v2.py", title="Versione 2", icon=":material/counter_2:"),
        st.Page("option_app_v3.py", title="Versione 3", icon=":material/counter_3:"),
        st.Page("masaniello.py", title="Masaniello quota FISSA", icon=":material/counter_4:"),
        st.Page("masaniellov2.py", title="Masaniello Variabile", icon=":material/counter_5:"),
    ],
}

pg = st.navigation(pages)
pg.run()
