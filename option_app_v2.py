import pandas as pd
import numpy as np
import streamlit as st


# --- FUNZIONI HELPER ---
# Le funzioni per la logica dei colori sono perfette così come sono.
# Le teniamo qui per chiarezza.

def get_risk_indicator(risk_point):
    """Restituisce un colore e un'etichetta di rischio in base al punteggio."""
    if risk_point > 270:
        return "#F90000", "Molto Alto" # Rosso
    elif risk_point >= 170:
        return "#F99300", "Alto" # Arancione
    elif risk_point >= 70:
        return "#00f900", "Medio" # Verde Chiaro
    else:
        return "#008000", "Basso" # Verde Scuro

def get_distance_color(diff_percent):
    """Restituisce il codice colore per la distanza percentuale dallo strike."""
    if diff_percent < 4.50:
        return "🔴"  # Red
    elif diff_percent <= 10.0:
        return "🟢"  # Green
    else:
        return "🌟"  # Gold (Star emoji)

# --- IMPOSTAZIONI DELLA PAGINA ---
#st.set_page_config(layout="wide") # Usiamo un layout più ampio per dare più spazio

# --- SIDEBAR PER GLI INPUT ---
with st.sidebar:
    st.header("📊 Impostazioni di Calcolo")

    # Sezione 1: Calcolo dello Strike
    st.subheader("Analisi dello Strike")
    asset_price = st.number_input("Prezzo Sottostante", min_value=0.0, value=6000.0, step=1.0, key="price")
    target_price = st.number_input("Strike Price", min_value=0.0, value=6000.0, step=1.0, key="strike")

    # Sezione 2: Analisi di Mercato
    st.subheader("Analisi Ingresso a Mercato")
    capitale = st.number_input("Capitale Iniziale (€)", min_value=100, value=1000, step=100)
    valore_selezionato = st.slider(
        "Rendimento Atteso (%)",
        min_value=1.0,
        max_value=100.0,
        value=10.0,
        step=0.1,
        format="%.2f%%"
    )
    sicure_price = st.number_input("Prezzo di Sicurezza", min_value=0.0, value=220.0, step=0.05)
    risk_point = st.slider("Punteggio di Rischio", min_value=1, max_value=400, value=60, step=1)

# --- AREA PRINCIPALE PER I RISULTATI ---

# Calcoli della prima sezione
diff_value = asset_price - target_price
try:
    diff_percent = (diff_value / asset_price) * 100
except ZeroDivisionError:
    diff_percent = 0.0

# Calcoli della seconda sezione
progress_value = valore_selezionato / 100.0
premio = progress_value * capitale
prezzo_indicativo = (sicure_price * progress_value * 50 / risk_point) if risk_point > 0 else 0
number_contract = (premio / prezzo_indicativo) if prezzo_indicativo > 0 else 0


st.header("📊 Trading in Opzioni")
#st.header("Risultati dell'Analisi")
st.divider()

# --- Visualizzazione con st.metric ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distanza dallo Strike")
    # Usiamo st.metric per un look più pulito
    emoji_distanza = get_distance_color(diff_percent)
    st.metric(
        label=f"Variazione Percentuale {emoji_distanza}",
        value=f"{diff_percent:.2f} %",
        help="Indica quanto lo strike price è lontano dal prezzo attuale del sottostante."
    )

with col2:
    st.subheader("⠀") # Spazio vuoto per allineare i titoli
    st.metric(
        label="Distanza Assoluta",
        value=f"{diff_value:.2f}",
        help="La differenza numerica tra il prezzo del sottostante e lo strike price."
    )


st.divider()

st.subheader("Simulazione di Ingresso")
col1, col2, col3 = st.columns(3)

with col1:
    # Mostriamo il premio potenziale con st.metric
    st.metric(
        label="Premio Potenziale",
        value=f"€ {premio:.2f}",
        help="Il guadagno massimo ottenibile in base al capitale e al rendimento atteso."
    )

with col2:
    st.metric(
        label="Prezzo Indicativo per Contratto",
        value=f"€ {prezzo_indicativo:.2f}",
        help="Il prezzo stimato a cui aprire la posizione per raggiungere il rendimento atteso."
    )

with col3:
    st.metric(
        label="Numero Massimo Contratti",
        value=f"{number_contract:.2f}",
        help="Quanti contratti puoi aprire con il premio calcolato."
    )

st.divider()

# --- Indicatore di Rischio ---
st.subheader("Indicatore di Rischio")
color_risk, label_risk = get_risk_indicator(risk_point)

# Creiamo un indicatore visivo per il rischio usando HTML e CSS,
# perché è un buon modo per mostrare un badge colorato.
st.markdown(
    f"""
    <div style="
        background-color: {color_risk};
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-weight: bold;
    ">
        Rischio: {label_risk} (Punteggio: {risk_point})
    </div>
    """,
    unsafe_allow_html=True
)
st.caption("Il livello di rischio è calcolato in base al punteggio inserito. Un punteggio più basso indica un rischio minore.")