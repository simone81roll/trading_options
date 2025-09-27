import streamlit as st

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
