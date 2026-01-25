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
def calcolatore_bull_put_numerico():
    with st.container(border=True):
        st.subheader("🛡️ Calcolatore Bull Put Spread (Dati Numerici)")
        st.markdown("Inserisci i dati delle due gambe per calcolare il rischio e il rendimento.")

        # --- INPUT DATI ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### 🔴 Gamba Venduta (Short)")
            strike_short = st.number_input("Strike Venduto", value=6350.0, step=10.0, format="%.2f")
            price_short = st.number_input("Premio Incassato", value=25.42, step=0.1, format="%.2f")
        
        with col2:
            st.markdown("##### 🟢 Gamba Acquistata (Long)")
            strike_long = st.number_input("Strike Protezione", value=6250.0, step=10.0, format="%.2f")
            price_long = st.number_input("Costo Protezione", value=5.00, step=0.1, format="%.2f")

        with col3:
            st.markdown("##### ⚙️ Dettagli Ordine")
            n_lotti = st.number_input("Numero Lotti", value=12, step=1)
            moltiplicatore = st.number_input("Moltiplicatore", value=1, help="1 per AvaOptions")

        # --- CALCOLI MATEMATICI ---
        # 1. Credito Netto (Guadagno Massimo) per unità
        net_credit_unit = price_short - price_long
        total_max_profit = net_credit_unit * n_lotti * moltiplicatore

        # 2. Rischio Massimo (Larghezza spread - Credito netto)
        spread_width = strike_short - strike_long
        max_risk_unit = spread_width - net_credit_unit
        total_max_loss = max_risk_unit * n_lotti * moltiplicatore

        # 3. Break-Even
        breakeven = strike_short - net_credit_unit
        
        # 4. ROI (Rendimento su Capitale a Rischio)
        roi = (total_max_profit / total_max_loss * 100) if total_max_loss != 0 else 0

        st.divider()

        # --- VISUALIZZAZIONE KPI ---
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Guadagno Massimo (Incasso)", f"€ {total_max_profit:,.2f}", delta="Scenario Migliore")
        k2.metric("Perdita Massima (Rischio)", f"€ -{total_max_loss:,.2f}", delta="Scenario Peggiore", delta_color="inverse")
        k3.metric("Break-Even Point", f"{breakeven:,.2f}", help="Sopra questo prezzo non perdi nulla")
        k4.metric("ROI Potenziale", f"{roi:.2f}%", help="Rendimento sul capitale bloccato a margine")

        st.divider()

        # --- SIMULATORE PREZZO E TABELLA SCENARI ---
        st.subheader("🔍 Verifica Puntuale")
        
        sim_col1, sim_col2 = st.columns([1, 2])
        
        with sim_col1:
            st.markdown("**Simula un prezzo a scadenza:**")
            sim_price = st.number_input("Prezzo Sottostante Ipotetico", value=float(strike_short), step=10.0)
            
            # Logica calcolo puntuale
            if sim_price >= strike_short:
                pnl_sim = total_max_profit
                status = "Profitto Massimo 🏆"
                color_box = "#d4edda" # Verde chiaro
                text_color = "#155724"
            elif sim_price <= strike_long:
                pnl_sim = -total_max_loss
                status = "Perdita Massima 🛡️ (Tappata)"
                color_box = "#f8d7da" # Rosso chiaro
                text_color = "#721c24"
            else:
                # Siamo nel mezzo dello spread
                loss_per_share = (strike_short - sim_price) - net_credit_unit
                pnl_sim = -(loss_per_share * n_lotti * moltiplicatore)
                # Potrebbe essere profitto o perdita a seconda del break even
                if pnl_sim > 0:
                    status = "Profitto Parziale ⚠️"
                    color_box = "#fff3cd" # Giallo
                    text_color = "#856404"
                else:
                    status = "Perdita Parziale ⚠️"
                    color_box = "#fff3cd"
                    text_color = "#856404"

            st.markdown(f"""
            <div style="background-color:{color_box}; color:{text_color}; padding: 15px; border-radius: 5px; text-align: center;">
                <h3 style="margin:0;">€ {pnl_sim:,.2f}</h3>
                <p style="margin:0;">{status}</p>
            </div>
            """, unsafe_allow_html=True)

        with sim_col2:
            st.markdown("**Tabella di Sintesi (Che succede se...?)**")
            data_scenari = {
                "Scenario": ["Mercato Sale o Stabile (> Strike Venduto)", "Mercato Scende un po' (Al Break-Even)", "Crollo Totale (Sotto Protezione)"],
                "Prezzo Sottostante": [f"> {strike_short:,.0f}", f"{breakeven:,.2f}", f"< {strike_long:,.0f}"],
                "Risultato (P&L)": [f"€ {total_max_profit:,.2f} (Max Win)", "€ 0.00 (Pareggio)", f"€ -{total_max_loss:,.2f} (Max Loss)"]
            }
            df_scenari = pd.DataFrame(data_scenari)
            st.table(df_scenari)

# --- CONFIGURAZIONE PAGINA E MAIN LOOP ---
st.set_page_config(page_title="Trading Opzioni", layout="wide", page_icon="📈")
st.title(":chart_with_upwards_trend: Trading in opzioni")

# Inizializza session state
inizializza_stato()

# --- 1. SEZIONE CALCOLO SPREAD (NUOVA) ---
# La inseriamo per prima o dopo l'analisi base, a tua scelta. Qui la metto in evidenza.
calcolatore_bull_put_numerico()

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
