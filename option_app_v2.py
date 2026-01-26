import streamlit as st
import numpy as np
import pandas as pd

# --- FUNZIONI DI UTILITÀ ---

def inizializza_stato():
    if 'rendimento_atteso' not in st.session_state:
        st.session_state['rendimento_atteso'] = 10.0

def update_from_slider():
    st.session_state['rendimento_atteso'] = st.session_state.rendimento_slider
    if st.session_state['rendimento_atteso'] > 100.0:
        st.session_state['rendimento_atteso'] = 100.0

def update_from_number_input():
    st.session_state['rendimento_atteso'] = st.session_state.rendimento_input
    if st.session_state['rendimento_atteso'] < 1.0:
        st.session_state['rendimento_atteso'] = 1.0
    elif st.session_state['rendimento_atteso'] > 100.0:
        st.session_state['rendimento_atteso'] = 100.0

def get_risk_indicator(risk_point):
    if risk_point > 270:
        return "#F90000", "Molto Alto"
    elif risk_point >= 170:
        return "#F99300", "Alto"
    elif risk_point >= 70:
        return "#00f900", "Medio"
    else:
        return "#008000", "Basso"

def get_distance_color(diff_percent):
    if diff_percent < 4.50:
        return "🔴"
    elif diff_percent <= 10.0:
        return "🟢"
    else:
        return "🌟"

# --- NUOVA FUNZIONE CALCOLATORE SPREAD (Senza Grafici) ---
def calcolatore_bull_put_avanzato():
    with st.container(border=True):
        st.subheader("🤖 Assistente Strategia Bull Put")
        
        # --- INPUT INIZIALI ---
        col_inp1, col_inp2, col_inp3 = st.columns(3)
        with col_inp1:
            prezzo_sottostante = st.number_input("Prezzo Attuale US500", value=6950.0, step=1.0)
            cambio_eurusd = st.number_input("Cambio EUR/USD", value=1.08, step=0.01, help="Necessario per convertire i $ di US500 in € del tuo conto")
        with col_inp2:
            capitale_totale = st.number_input("Tuo Capitale Totale (€)", value=1000.0, step=100.0)
        with col_inp3:
            distanza_safety = st.slider("Distanza Strike (%)", 1.0, 10.0, 5.0) / 100

        # --- LOGICA DI CONSIGLIO AUTOMATICO ---
        # 1. Calcolo Strike Venduto (consigliato al -5%)
        strike_venduto_sugg = prezzo_sottostante * (1 - distanza_safety)
        # Arrotondiamo a 5 o 10 punti (tipico degli strike US500)
        strike_venduto_sugg = round(strike_venduto_sugg / 5) * 5
        
        # 2. Impostiamo uno spread standard (es. 100 punti di larghezza per efficienza)
        strike_protezione_sugg = strike_venduto_sugg - 100

        st.info(f"💡 **Consiglio Strategia:** Strike Venduto: **{strike_venduto_sugg}** | Strike Protezione: **{strike_protezione_sugg}**")

        # --- DETTAGLI PREZZI (Inseriti manualmente dopo aver visto AvaOptions) ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            prezzo_put_venduta = st.number_input("Premio Put Venduta ($)", value=25.0)
        with c2:
            prezzo_put_prot = st.number_input("Costo Put Protezione ($)", value=5.0)

        # --- CALCOLO LOTTI BASATO SUL RISCHIO (50% CAPITALE) ---
        # Rischio massimo tollerato in €
        rischio_max_eur = capitale_totale * 0.50
        rischio_max_usd = rischio_max_eur * cambio_eurusd
        
        # Rischio per singolo lotto in $ (Larghezza spread - credito netto)
        credito_netto_unit_usd = prezzo_put_venduta - prezzo_put_prot
        larghezza_spread = strike_venduto_sugg - strike_protezione_sugg
        rischio_unit_usd = larghezza_spread - credito_netto_unit_usd
        
        # Numero lotti suggeriti
        if rischio_unit_usd > 0:
            lotti_suggeriti = int(rischio_max_usd / rischio_unit_usd)
        else:
            lotti_suggeriti = 0

        # --- RISULTATI FINALI ---
        st.divider()
        res1, res2, res3 = st.columns(3)
        
        res1.metric("Lotti Suggeriti", f"{lotti_suggeriti}")
        
        # Calcolo guadagno/perdita finale in €
        guadagno_max_eur = (credito_netto_unit_usd * lotti_suggeriti) / cambio_eurusd
        perdita_max_eur = (rischio_unit_usd * lotti_suggeriti) / cambio_eurusd
        
        res2.metric("Vincita Massima stimata (€)", f"€ {guadagno_max_eur:.2f}")
        res3.metric("Rischio Reale (€)", f"€ {perdita_max_eur:.2f}")

        if perdita_max_eur > rischio_max_eur:
            st.warning("Attenzione: Il rischio calcolato supera leggermente il budget a causa dell'arrotondamento lotti.")
# --- CONFIGURAZIONE PAGINA E MAIN LOOP ---
st.set_page_config(page_title="Trading Opzioni", layout="wide", page_icon="📈")
st.title(":chart_with_upwards_trend: Trading in opzioni")

# Inizializza session state
inizializza_stato()

# --- 1. SEZIONE CALCOLO SPREAD (NUOVA) ---
# La inseriamo per prima o dopo l'analisi base, a tua scelta. Qui la metto in evidenza.
calcolatore_bull_put_avanzato()

# --- 2. SEZIONE CALCOLO CLASSICO (TUO CODICE PRECEDENTE) ---
with st.container(border=True):	
	st.subheader("🎯 Calcolo dello Strike Price (Analisi Semplice)")
		
	sott, strike, var = st.columns([0.35, 0.35, 0.30])
	asset_price = sott.number_input("Prezzo Sottostante Attuale", min_value=0.0, value=6000.0, step=1.0, key="price")
	target_price = strike.number_input("Strike Price Obiettivo", min_value=0.0, value=6000.0, step=1.0, key="strike")

	diff_value = asset_price - target_price
	try:
	    diff_percent = (diff_value / asset_price) * 100
	except ZeroDivisionError:
	    diff_percent = 0.0

	emoji_distanza = get_distance_color(diff_percent)
	var.metric(
	    label=f"Variazione dallo Strike {emoji_distanza}",
	    value=f"{diff_percent:.2f} %",
	    delta=f"Distanza Assoluta: {diff_value:.2f}"
	)

with st.container(border=True):
	st.subheader("💹 Money Management")

	col3, col4, col5, col6 = st.columns([0.20, 0.35, 0.15, 0.30])
	
	with col3:
		capitale = st.number_input("Capitale Iniziale (€)", min_value=100, value=1000, step=100)
		
	with col4:
	    st.slider(
	        "Rendimento Atteso (%)",
	        min_value=1.0,
	        max_value=100.0,
	        value=st.session_state.rendimento_atteso, 
	        step=0.1,
	        format="%.2f%%",
	        key="rendimento_slider",
	        on_change=update_from_slider
	    )

	with col5:
	    st.number_input(
	        "(%)",
	        min_value=1.0,
	        max_value=100.0,
	        value=st.session_state.rendimento_atteso,
	        step=0.1,
	        key="rendimento_input",
	        on_change=update_from_number_input,
	        format="%.2f",
	        label_visibility="hidden"
	    )

	progress_value = st.session_state.rendimento_atteso / 100.0
	premio = progress_value * capitale

	col6.metric(
	    label="Premio Potenziale",
	    value=f"€ {premio:.2f}"
	)
	
	risk, sic, color = st.columns([0.35, 0.35, 0.30])
	sicure_price = sic.number_input("Prezzo Opzione Stimato", min_value=0.0, value=220.0, step=0.05, help="Inserisci il prezzo medio dell'opzione che intendi vendere")
	risk_point = risk.number_input("Punteggio di Rischio (Custom)", min_value=1, max_value=400, value=60, step=1)
	
    # Calcolo indicativo basato sulla tua logica
	prezzo_indicativo = (sicure_price * progress_value * 50 / risk_point) if risk_point != 0 else 0
	number_contract = (premio / sicure_price) if sicure_price != 0 else 0	

	color_risk, label_risk = get_risk_indicator(risk_point)				
	color.markdown(
        f"""
        <div style="background-color:{color_risk}; padding:10px; border-radius:10px; text-align:center; color:white; font-weight:bold;">
	        Rischio: {label_risk} (Punteggio: {risk_point})
        </div>
        """,
        unsafe_allow_html=True
	)

with st.container(border=True):
    st.subheader("📉 Risultati Operativi")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="Prezzo Indicativo Calcolato",
            value=f"€ {prezzo_indicativo:.2f}",
            help="Prezzo derivato dalla formula del rischio."
        )
    with col2:
        st.metric(
            label="Contratti necessari per Target",
            value=f"{number_contract:.2f}",
            help="N. contratti = Premio Potenziale / Prezzo Opzione"
        )


