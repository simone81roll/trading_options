import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
# Funzione per inizializzare lo stato della sessione, se non è già presente
def inizializza_stato():
    if 'rendimento_atteso' not in st.session_state:
        st.session_state['rendimento_atteso'] = 10.0 # Valore predefinito iniziale

# Funzione di callback per aggiornare lo stato della sessione quando lo slider cambia
def update_from_slider():
    # 'rendimento_slider' è la chiave assegnata allo slider tramite l'argomento 'key'
    st.session_state['rendimento_atteso'] = st.session_state.rendimento_slider
    # Nota: Aggiungo un piccolo controllo per non superare il max_value, 
    # anche se lo slider già lo gestisce, è buona pratica.
    if st.session_state['rendimento_atteso'] > 100.0:
        st.session_state['rendimento_atteso'] = 100.0

# Funzione di callback per aggiornare lo stato della sessione quando l'input numerico cambia
def update_from_number_input():
    # 'rendimento_input' è la chiave assegnata all'input numerico
    st.session_state['rendimento_atteso'] = st.session_state.rendimento_input
    # Aggiungiamo controlli per i limiti min/max
    if st.session_state['rendimento_atteso'] < 1.0:
        st.session_state['rendimento_atteso'] = 1.0
    elif st.session_state['rendimento_atteso'] > 100.0:
        st.session_state['rendimento_atteso'] = 100.0

def get_risk_indicator(risk_point):
    """Restituisce un colore e un'etichetta di rischio in base al punteggio."""
    if risk_point > 270:
        return "#F90000", "Molto Alto"
    elif risk_point >= 170:
        return "#F99300", "Alto"
    elif risk_point >= 70:
        return "#00f900", "Medio"
    else:
        return "#008000", "Basso"

def get_distance_color(diff_percent):
    """Restituisce un'emoji per la distanza percentuale dallo strike."""
    if diff_percent < 4.50:
        return "🔴"
    elif diff_percent <= 10.0:
        return "🟢"
    else:
        return "🌟"


def bull_put_spread_calculator():
    st.title("🛡️ Calcolatore Bull Put Spread")
    st.markdown("Analisi del profilo di rischio: **Vendita Put (Naked)** vs **Bull Put Spread**")

    # --- 1. SEZIONE INPUT (SIDEBAR O COLONNE) ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Gamba Venduta (Short)")
        strike_short = st.number_input("Strike Put Venduta", value=6350.0, step=10.0, format="%.2f")
        price_short = st.number_input("Premio Incassato (Vendita)", value=25.42, step=0.1, format="%.2f")
    
    with col2:
        st.subheader("Gamba Acquistata (Long)")
        strike_long = st.number_input("Strike Put Protezione", value=6250.0, step=10.0, format="%.2f", help="Lo strike della Put che compri per proteggerti")
        price_long = st.number_input("Costo Protezione (Acquisto)", value=5.00, step=0.1, format="%.2f")

    with col3:
        st.subheader("Dettagli Ordine")
        n_lotti = st.number_input("Numero Lotti", value=12, step=1)
        moltiplicatore = st.number_input("Moltiplicatore (1 per AvaOptions)", value=1, help="Solitamente 1 per CFD su indici, 50 per futures ES")

    # --- 2. CALCOLI FONDAMENTALI ---
    # Credito Netto (Il massimo guadagno possibile)
    net_credit_unit = price_short - price_long
    max_profit = net_credit_unit * n_lotti * moltiplicatore

    # Larghezza dello spread
    spread_width = strike_short - strike_long

    # Rischio Massimo (Larghezza spread - Credito netto)
    max_risk_unit = spread_width - net_credit_unit
    max_loss = max_risk_unit * n_lotti * moltiplicatore

    # Break-Even Point (Sopra questo valore sei in profitto)
    breakeven = strike_short - net_credit_unit

    # --- 3. VISUALIZZAZIONE KPI ---
    st.divider()
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    kpi1.metric("Massimo Profitto (Incasso)", f"${max_profit:,.2f}", delta_color="normal")
    kpi2.metric("Massima Perdita (Rischio)", f"-${max_loss:,.2f}", delta_color="inverse")
    kpi3.metric("Break-Even Point", f"{breakeven:,.2f}")
    kpi4.metric("Margine Stimato (Rischio)", f"${max_loss:,.2f}", help="In uno spread, il margine richiesto è solitamente pari alla massima perdita possibile.")

    # --- 4. GENERAZIONE DATI PER GRAFICO E TABELLA ---
    # Creiamo un range di prezzi ipotetici (dal 10% sotto lo strike long al 5% sopra lo strike short)
    min_chart_price = strike_long * 0.90
    max_chart_price = strike_short * 1.05
    price_range = np.linspace(min_chart_price, max_chart_price, 200)

    # Funzione Logica P&L vettorializzata
    def calculate_pnl(price):
        # Valore a scadenza delle opzioni
        # Short Put: Perde se prezzo < strike_short
        val_short = -np.maximum(0, strike_short - price)
        # Long Put: Guadagna se prezzo < strike_long
        val_long = np.maximum(0, strike_long - price)
        
        # P&L Totale = (Incasso Iniziale + Valore Short + Valore Long) * Lotti * Molt
        return (net_credit_unit + val_short + val_long) * n_lotti * moltiplicatore

    pnl_values = calculate_pnl(price_range)

    # --- 5. GRAFICO INTERATTIVO (PLOTLY) ---
    fig = go.Figure()

    # Linea del P&L
    fig.add_trace(go.Scatter(x=price_range, y=pnl_values, mode='lines', name='P&L a Scadenza', 
                             line=dict(color='blue', width=3)))

    # Area Verde (Profitto)
    fig.add_trace(go.Scatter(x=price_range, y=np.where(pnl_values >= 0, pnl_values, 0), 
                             fill='tozeroy', mode='none', fillcolor='rgba(0, 255, 0, 0.1)', name='Profitto'))

    # Area Rossa (Perdita)
    fig.add_trace(go.Scatter(x=price_range, y=np.where(pnl_values < 0, pnl_values, 0), 
                             fill='tozeroy', mode='none', fillcolor='rgba(255, 0, 0, 0.1)', name='Perdita'))

    # Linea dello zero
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    # Linee verticali per gli strike
    fig.add_vline(x=strike_short, line_dash="dot", line_color="green", annotation_text="Short Strike")
    fig.add_vline(x=strike_long, line_dash="dot", line_color="red", annotation_text="Protection Strike")

    fig.update_layout(title="Diagramma di Payoff a Scadenza", xaxis_title="Prezzo Sottostante (US500)", yaxis_title="Profitto/Perdita ($)")
    
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. SIMULATORE PREZZO PUNTUALE (Richiesta Excel) ---
    st.subheader("🔮 Simulatore Prezzo a Scadenza")
    sim_price = st.slider("Ipotizza un prezzo di chiusura:", 
                          min_value=float(int(min_chart_price)), 
                          max_value=float(int(max_chart_price)), 
                          value=float(breakeven))
    
    sim_pnl = calculate_pnl(sim_price)
    
    if sim_pnl > 0:
        st.success(f"Se il mercato chiude a **{sim_price}**, il tuo profitto sarà: **${sim_pnl:,.2f}**")
    else:
        st.error(f"Se il mercato chiude a **{sim_price}**, la tua perdita sarà: **${sim_pnl:,.2f}**")

# Esegui la funzione (se questo script è lanciato direttamente)
if __name__ == "__main__":
    bull_put_spread_calculator()
	
# --- IMPOSTAZIONI DELLA PAGINA ---
st.set_page_config(layout="wide")
st.title(":chart_with_upwards_trend: Trading in opzioni")


inizializza_stato()

# Usiamo un contenitore con bordo per raggruppare visivamente tutti gli input
with st.container(border=True):	
	st.subheader("🎯 Calcolo dello Strike Price")
		
	sott, strike, var =st.columns([0.35, 0.35, 0.30])
	asset_price = sott.number_input("Prezzo Sottostante", min_value=0.0, value=6000.0, step=1.0, key="price")
	target_price = strike.number_input("Strike Price", min_value=0.0, value=6000.0, step=1.0, key="strike")

	diff_value = asset_price - target_price
	try:
	    diff_percent = (diff_value / asset_price) * 100
	except ZeroDivisionError:
	    diff_percent = 0.0
	#st.divider()

	emoji_distanza = get_distance_color(diff_percent)
	var.metric(
	    label=f"Variazione dallo Strike {emoji_distanza}",
	    value=f"{diff_percent:.2f} %",
	    delta=f"Distanza Assoluta: {diff_value:.2f}"
	)

	
with st.container(border=True):
	st.subheader("💹 Analisi")

	col3, col4, col5, col6 = st.columns([0.20, 0.35, 0.15, 0.30])
	
	with col3:
		capitale = st.number_input("Capitale Iniziale (€)", min_value=100, value=1000, step=100)
		
	with col4:
	    st.slider(
	        "Rendimento Atteso (%)",
	        min_value=1.0,
	        max_value=100.0,
	        # Usiamo il valore dallo stato della sessione
	        value=st.session_state.rendimento_atteso, 
	        step=0.1,
	        format="%.2f%%",
	        key="rendimento_slider", # Chiave per accedere al suo valore nel callback
	        on_change=update_from_slider # Funzione da chiamare quando cambia
	    )

	# 2. Input Numerico (Sincronizzato)
	with col5:
	    st.number_input(
	        "(%)",
	        min_value=1.0,
	        max_value=100.0,
	        # Usiamo lo stesso valore dallo stato della sessione
	        value=st.session_state.rendimento_atteso,
	        step=0.1,
	        key="rendimento_input", # Chiave per accedere al suo valore nel callback
	        on_change=update_from_number_input, # Funzione da chiamare quando cambia
	        format="%.2f",
	        label_visibility="hidden"
	    )

	progress_value = st.session_state.rendimento_atteso / 100.0
	premio = progress_value * capitale

	col6.metric(
	    label="Premio Potenziale",
	    value=f"€ {premio:.2f}"
	)
	
	risk, sic, color =st.columns([0.35, 0.35, 0.30])
	#col6, col7 = st.columns(2)
	sicure_price = sic.number_input("Prezzo di Sicurezza", min_value=0.0, value=220.0, step=0.05)
	risk_point = risk.number_input("Punteggio di Rischio", min_value=1, max_value=400, value=60, step=1)
	
	prezzo_indicativo = (sicure_price * progress_value * 50 / risk_point) if risk_point != 0 else 0
	number_contract = (premio / prezzo_indicativo) if prezzo_indicativo != 0 else 0	

	color_risk, label_risk = get_risk_indicator(risk_point)				
	color.markdown(
        f"""
        <div style="background-color:{color_risk}; padding:10px; border-radius:10px; text-align:center; color:white; font-weight:bold;">
	        Rischio: {label_risk} (Punteggio: {risk_point})
        </div>
        """,
        unsafe_allow_html=True
	)


# Contenitore con bordo per mettere in risalto i risultati principali
with st.container(border=True):
    st.subheader("📉 Ingresso a mercato")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="Prezzo Indicativo per Contratto",
            value=f"€ {prezzo_indicativo:.2f}",
            help="Il prezzo stimato a cui aprire la posizione per raggiungere il rendimento atteso."
        )
    with col2:
        st.metric(
            label="Numero Massimo Contratti",
            value=f"{number_contract:.2f}",
            help="Quanti contratti puoi acquistare con il premio calcolato."
        )

