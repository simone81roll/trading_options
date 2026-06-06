import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione Pagina
st.set_page_config(
    page_title="Options Edge v12 — Institutional",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizzato
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .metric-card { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #ff9900; margin-bottom: 15px; }
    .card-title { font-size: 13px; color: #6c757d; font-weight: 500; text-transform: uppercase; margin-bottom: 5px; }
    .card-value { font-size: 24px; color: #1c1c1c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ Options Edge Finder — Institutional Confluence")
st.markdown("Filtro quantitativo multi-livello: Velocità di prezzo, Greche (Delta), Open Interest e Indice VIX.")

# --- SIDEBAR: DATI IN TEMPO REALE E PARAMETRI ---
st.sidebar.header("🚀 1. Input Dati di Mercato (Live)")
live_mode = st.sidebar.checkbox("Attiva Input Manuale Live", value=True)
prezzo_manuale = st.sidebar.number_input("Prezzo S&P 500 Corrente", min_value=1.0, value=6000.0, step=0.5)
sma_manuale = st.sidebar.number_input("Valore SMA 200", min_value=1.0, value=5600.0, step=0.5)

st.sidebar.header("⚙️ 2. Struttura dell'Opzione")
dte_opzioni = st.sidebar.slider("Giorni alla scadenza (DTE)", min_value=15, max_value=60, value=30, step=5)
delta_target = st.sidebar.slider("Delta Max Strike Venduto", min_value=0.05, max_value=0.30, value=0.15, step=0.01)

# --- NUOVA SIDEBAR: DATI ISTITUZIONALI ---
st.sidebar.header("🛡️ 3. Filtri Istituzionali (VIX & OI)")
vix_corrente = st.sidebar.number_input("Valore VIX Corrente", min_value=9.0, max_value=100.0, value=15.0, step=0.1)

st.sidebar.markdown("**Muri di Opzioni (Open Interest):**")
oi_strike = st.sidebar.number_input("Open Interest (OI) del tuo Strike", min_value=0, value=15000, step=100, help="Quanti contratti aperti ci sono sullo strike che vuoi vendere?")
oi_medio = st.sidebar.number_input("OI Medio degli strike vicini", min_value=1, value=3000, step=100, help="Una media a occhio dei volumi sugli strike adiacenti.")

# CARICAMENTO CSV STORICO (Invariato)
@st.cache_data
def carica_dati_locali():
    try:
        df_puro = pd.read_csv("spy_history.csv")
        df_puro.columns = [col.strip() for col in df_puro.columns]
        if 'Date' in df_puro.columns:
            df_puro['Date'] = pd.to_datetime(df_puro['Date'])
            df_puro.set_index('Date', inplace=True)
        elif 'Date' in df_puro.index.names:
            df_puro.index = pd.to_datetime(df_puro.index)
        col_target = 'Adj Close' if 'Adj Close' in df_puro.columns else 'Close'
        df_finale = pd.DataFrame(df_puro[col_target]).copy()
        df_finale.columns = ['Close']
        df_finale = df_finale.sort_index()
        df_finale['Close'] = pd.to_numeric(df_finale['Close'], errors='coerce').dropna()
        return df_finale
    except Exception as e:
        st.error(f"⚠️ Errore CSV: {e}")
        return pd.DataFrame()

df = carica_dati_locali()

if not df.empty:
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['Estensione_SMA200_Pct'] = ((df['Close'] - df['SMA_200']) / df['SMA_200']) * 100
    df_analisi = df.dropna().copy()
    
    # 1. RILEVAZIONE STATO PREZZI
    if live_mode:
        prezzo_corrente = prezzo_manuale
        sma_200_attuale = sma_manuale
    else:
        prezzo_corrente = float(df_analisi['Close'].iloc[-1])
        sma_200_attuale = float(df_analisi['SMA_200'].iloc[-1])
        
    estensione_attuale = ((prezzo_corrente - sma_200_attuale) / sma_200_attuale) * 100
    
    st.subheader("🚨 1. Motore dei Prezzi e Distanza (Time to Touch)")
    col_st1, col_st2, col_st3 = st.columns(3)
    with col_st1: st.metric("Prezzo Sottostante", f"${prezzo_corrente:.2f}")
    with col_st2: st.metric("Media Mobile 200gg", f"${sma_200_attuale:.2f}")
    with col_st3: st.metric("Estensione Attuale", f"{estensione_attuale:.2f}%")
    
    # ALGORITMO BACKTEST
    tolleranza = 0.5
    min_filtro, max_filtro = estensione_attuale - tolleranza, estensione_attuale + tolleranza
    giorni_simili = df_analisi[(df_analisi['Estensione_SMA200_Pct'] >= min_filtro) & (df_analisi['Estensione_SMA200_Pct'] <= max_filtro)].copy()
    
    prob_sopravvivenza_dte = 0.0 # Valore di default
    
    if len(giorni_simili) >= 5:
        lista_tempi_tocco = []
        toccati_entro_dte = 0
        
        for data_inizio, riga in giorni_simili.iterrows():
            liv_target = riga['SMA_200']
            cond_tocco = df_analisi.loc[data_inizio:]['Close'] <= liv_target
            if cond_tocco.any():
                data_tocco = cond_tocco.idxmax()
                giorni_passati = len(df_analisi.loc[data_inizio:data_tocco]) - 1
                lista_tempi_tocco.append(giorni_passati)
                if giorni_passati <= dte_opzioni: toccati_entro_dte += 1
                    
        if lista_tempi_tocco:
            tempo_minimo = min(lista_tempi_tocco)
            prob_sopravvivenza_dte = ((len(giorni_simili) - toccati_entro_dte) / len(giorni_simili)) * 100
            
            st.info(f"**Storico Estensione:** Da questo livello (+/- {tolleranza}%), il crollo più rapido mai registrato ha richiesto **{tempo_minimo} giorni** per toccare la media. Probabilità base del trade (tempo scaduto prima del crollo): **{prob_sopravvivenza_dte:.1f}%**.")
    else:
        st.warning("Pochi dati storici esatti per questa specifica estensione.")

    st.divider()

    # 2. SEZIONE ANALISI ISTITUZIONALE
    st.subheader("🏛️ 2. Confluenza Istituzionale (Greche, Volumi e VIX)")
    st.markdown("Valutazione dei parametri di liquidità e paura del mercato per approvare l'ingresso a mercato.")

    col_i1, col_i2, col_i3 = st.columns(3)

    # A) VALUTAZIONE DELTA (Probabilità teorica del mercato)
    with col_i1:
        prob_teorica = (1 - delta_target) * 100
        if delta_target <= 0.16:
            st.markdown(f'<div class="metric-card" style="border-left-color: #28a745;"><div class="card-title">1️⃣ Edge del Delta</div><div class="card-value" style="color: #28a745;">{delta_target:.2f} (Sicuro)</div><div style="font-size:12px; color:#6c757d; margin-top:5px;">Prob. Mercato: {prob_teorica:.1f}%</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="metric-card" style="border-left-color: #dc3545;"><div class="card-title">1️⃣ Edge del Delta</div><div class="card-value" style="color: #dc3545;">{delta_target:.2f} (Aggressivo)</div><div style="font-size:12px; color:#6c757d; margin-top:5px;">Rischio ITM elevato</div></div>', unsafe_allow_html=True)

    # B) VALUTAZIONE OPEN INTEREST (I Muri)
    with col_i2:
        rapporto_oi = oi_strike / oi_medio if oi_medio > 0 else 1
        if rapporto_oi >= 3.0:
            colore_oi, testo_oi, sub_oi = "#28a745", f"{rapporto_oi:.1f}x", "Muro Istituzionale Solido"
        elif rapporto_oi >= 1.5:
            colore_oi, testo_oi, sub_oi = "#0066cc", f"{rapporto_oi:.1f}x", "Supporto Standard"
        else:
            colore_oi, testo_oi, sub_oi = "#dc3545", f"{rapporto_oi:.1f}x", "Strike Vulnerabile / Poco liquido"
            
        st.markdown(f'<div class="metric-card" style="border-left-color: {colore_oi};"><div class="card-title">2️⃣ Scudo Open Interest</div><div class="card-value" style="color: {colore_oi};">{testo_oi} OI Medio</div><div style="font-size:12px; color:#6c757d; margin-top:5px;">{sub_oi}</div></div>', unsafe_allow_html=True)

    # C) VALUTAZIONE VIX (Indice Paura)
    with col_i3:
        if vix_corrente < 13.0:
            colore_vix, testo_vix, sub_vix = "#dc3545", f"{vix_corrente}", "Premi troppo bassi. Rischio espansione."
        elif 13.0 <= vix_corrente <= 18.0:
            colore_vix, testo_vix, sub_vix = "#0066cc", f"{vix_corrente}", "Volatilità Neutrale. Premi equi."
        else:
            colore_vix, testo_vix, sub_vix = "#28a745", f"{vix_corrente}", "Alta Volatilità. Edge a favore del venditore."
            
        st.markdown(f'<div class="metric-card" style="border-left-color: {colore_vix};"><div class="card-title">3️⃣ Valore VIX (Paura)</div><div class="card-value" style="color: {colore_vix};">{testo_vix}</div><div style="font-size:12px; color:#6c757d; margin-top:5px;">{sub_vix}</div></div>', unsafe_allow_html=True)

    # 3. VERDETTO FINALE COMBINATO
    st.divider()
    st.subheader("🎯 Semaforo Operativo Finale")
    
    punteggio = 0
    if prob_sopravvivenza_dte >= 85: punteggio += 1
    if delta_target <= 0.16: punteggio += 1
    if rapporto_oi >= 2.0: punteggio += 1
    if vix_corrente >= 13.0: punteggio += 1

    if punteggio == 4:
        st.success("🟢 **VIA LIBERA (CONFLUENZA TOTALE):** Tutte le metriche (Storico, Greche, Volumi e VIX) sono allineate a tuo favore. Il rischio statistico è minimizzato al massimo livello possibile per questo Trade.")
    elif punteggio == 3:
        st.info("🟡 **APPROVATO CON CAUTELA:** Hai 3 fattori a favore su 4. Il setup è buono, ma c'è un elemento (es. VIX basso o OI debole) che non offre la massima copertura. Gestisci con attenzione l'ampiezza dello spread.")
    else:
        st.error(f"🔴 **TRADE SCONSIGLIATO (Punteggio {punteggio}/4):** Troppi parametri non allineati. Le probabilità non giocano nettamente a tuo favore o i premi non giustificano il rischio strutturale preso.")
