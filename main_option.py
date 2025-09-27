import streamlit as st

pages = {
    "Seleziona la versione":[
        st.Page("option_app.py", title="Versione 1", icon=":material/counter_1:"),
        st.Page("option_app_v2.py", title="Versione 2", icon=":material/counter_2:"),
        st.Page("option_app_v3.py", title="Versione 3", icon=":material/counter_3:"),
    ],
}

pg = st.navigation(pages)
pg.run()
