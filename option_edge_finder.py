import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione Pagina
st.set_page_config(
    page_title="Options Edge Finder — Dynamic Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizzato per massima leggibilità
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .status-card { padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px; text-align: center; font-weight: bold; }
    .metric-card { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #0066cc; }
    .card-title { font-size: 13px; color: #6c757d; font-weight: 500; text-transform: uppercase; margin-bottom: 10px; }
    .card-value { font-size: 24px; color: #1c1c1c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Options Edge Finder — Volatility Assistant")
st.markdown("Questo strumento analizza la volatilità recente dell'S&P 500 e calcola matematicamente lo strike più sicuro per il tuo Credit Put Spread.")

# SIDEBAR SEMPLIFICATA
st.sidebar.header("⚙️ Impostazioni Opzione")
dte_opzioni = st.sidebar.slider("Giorni alla scadenza (DTE)", min_value=15, max_value=60, value=30, step=5)
giorni_lavorativi = int(np.round(dte_opzioni * (5/7)))

st.sidebar.subheader("🛡️ Livello di Protezione")
livello_sicurezza = st.sidebar.select_slider(
    "Profilo di Rischio",
    options=["Aggressivo (1.0 Sigma)", "Bilanciato (1.5 Sigma)", "Prudente (2.0 Sigma)", "Ultra-Sicuro (2.5 Sigma)"],
    value="Prudente (2.0 Sigma)"
)

# Mappatura del valore Sigma scelto
mappa_sigma = {"Aggressivo (1.0 Sigma)": 1.0, "Bilanciato (1.5 Sigma)": 1.5, "Prudente (2.0 Sigma)": 2.0, "Ultra-Sicuro (2.5 Sigma)": 2.5}
sigma_scelto = mappa_sigma[livello_sicurezza]

ampiezza_spread_pct = st.sidebar.slider("Ampiezza dello Spread (%)", min_value=1.0, max_value=5.0, value=2.0, step=0.5) / 100

# CARICAMENTO DATI LOCALI CSV
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
        colonna_target = 'Adj Close' if 'Adj Close' in df_puro.columns else 'Close'
        df_finale = pd.DataFrame(df_puro[colonna_target]).copy()
        df_finale.columns = ['Close']
        df_finale = df_finale.sort_index()
        df_finale['Close'] = pd.to_numeric(df_finale['Close'], errors='coerce').dropna()
        return df_finale
    except Exception as e:
        st.error(f"⚠️ Errore nel caricamento del file CSV: {e}")
        return pd.DataFrame()

df = carica_dati_locali()

if not df.empty:
    # Calcolo Volatilità Storica Rolling
    df['Rendimento_Giornaliero'] = df['Close'].pct_change()
    df['Volatila_Rolling'] = df['Rendimento_Giornaliero'].rolling(window=20).std() * np.sqrt(giorni_lavorativi)
    
    # Calcolo dello storico delle scadenze
    df['Prezzo_Futuro'] = df['Close'].shift(-giorni_lavorativi)
    df['Rendimento_Effettivo'] = (df['Prezzo_Futuro'] - df['Close']) / df['Close']
    
    # Calcolo Strike Dinamico Storico
    df['Distanza_Dinamica_Pct'] = - (sigma_scelto * df['Volatila_Rolling'])
    df['Strike_Venduto_Dinamico'] = df['Close'] * (1 + df['Distanza_Dinamica_Pct'])
    df['Successo_Dinamico'] = df['Rendimento_Effettivo'] >= df['Distanza_Dinamica_Pct']
    
    df_analisi = df.dropna().copy()
    
    # Estrazione Dati per OGGI (Ultimo record del file)
    prezzo_corrente = float(df['Close'].iloc[-1])
    volatila_attuale_pct = float(df_analisi['Volatila_Rolling'].iloc[-1]) * 100
    distanza_attuale_pct = float(df_analisi['Distanza_Dinamica_Pct'].iloc[-1]) * 100
    
    valore_strike_venduto = np.round(prezzo_corrente * (1 + (distanza_attuale_pct/100)), 2)
    valore_strike_comprato = np.round(valore_strike_venduto * (1 - ampiezza_spread_pct), 2)
    ampiezza_punti = np.round(valore_strike_venduto - valore_strike_comprato, 2)

    # 1. LIVELLO OPERATIVO IMMEDIATO
    st.subheader("🎯 Consiglio Operativo per Oggi")
    st.info(f"In base alla volatilità attuale del mercato ({volatila_attuale_pct:.2f}%), per mantenere un profilo **{livello_sicurezza}** l'algoritmo ti consiglia di posizionare lo strike a una distanza minima del **{distanza_attuale_pct:.1f}%** dal prezzo corrente.")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.markdown(f'<div class="metric-card" style="border-left-color: #dc3545;"><div class="card-title">🔴 Vendi (Short Put)</div><div class="card-value">Strike ${valore_strike_venduto:.2f}</div><div style="font-size:12px; color:#6c757d; margin-top:5px;">Distanza dal prezzo: {distanza_attuale_pct:.1f}%</div></div>', unsafe_allow_html=True)
    with col_c2:
        st.markdown(f'<div class="metric-card" style="border-left-color: #28a745;"><div class="card-title">🟢 Compra (Long Put)</div><div class="card-value">Strike ${valore_strike_comprato:.2f}</div><div style="font-size:12px; color:#6c757d; margin-top:5px;">Livello di protezione spread</div></div>', unsafe_allow_html=True)
    with col_c3:
        st.markdown(f'<div class="metric-card" style="border-left-color: #ffc107;"><div class="card-title">🛡️ Gestione del Rischio</div><div class="card-value">Ampiezza: {ampiezza_punti} pt</div><div style="font-size:12px; color:#6c757d; margin-top:5px;">Perdita Max: ${ampiezza_punti*100:.2f} a lotto</div></div>', unsafe_allow_html=True)

    # 2. STATISTICHE DI SUCCESSO DEL MODELLO
    st.subheader("📊 Affidabilità Storica di questa impostazione")
    win_rate_storico = (df_analisi['Successo_Dinamico'].sum() / len(df_analisi)) * 100
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.metric("Percentuale di Successo Storica (Win Rate)", f"{win_rate_storico:.1f}%")
    with col_w2:
        if win_rate_storico >= 95:
            st.markdown('<div class="status-card" style="background-color: #28a745; color: white;">LIVELLO DI SICUREZZA ECCEZIONALE</div>', unsafe_allow_html=True)
        elif win_rate_storico >= 90:
            st.markdown('<div class="status-card" style="background-color: #0066cc; color: white;">LIVELLO DI SICUREZZA STANDARD OTTIMALE</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-card" style="background-color: #ffc107; color: #1c1c1c;">ATTENZIONE: ADATTA I PARAMETRI NELLA SIDEBAR</div>', unsafe_allow_html=True)

    # 3. GRAFICO VISIVO DI VERIFICA (Ultimi 3 anni per non appesantire)
    st.subheader("📈 Grafico Visivo dell'Andamento dello Strike")
    st.markdown("Questo grafico mostra come lo strike consigliato (linea rossa) si sposta da solo per rimanere sempre a distanza di sicurezza sotto il prezzo di mercato (linea blu).")
    
    df_recent = df_analisi.tail(750) # Ultimi 3 anni circa
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_recent.index, y=df_recent['Close'], name="Prezzo SPY", line=dict(color='#0066cc', width=2)))
    fig.add_trace(go.Scatter(x=df_recent.index, y=df_recent['Strike_Venduto_Dinamico'], name="Strike Consigliato (Dinamico)", line=dict(color='#dc3545', width=1.5, dash='dash')))
    
    fig.update_layout(template="plotly_white", height=450, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
