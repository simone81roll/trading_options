import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione Pagina
st.set_page_config(
    page_title="Options Edge Finder v2",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizzato
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .status-card {
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        color: white;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #0066cc;
        margin-bottom: 15px;
    }
    .metric-label { font-size: 13px; color: #6c757d; font-weight: 500; text-transform: uppercase; }
    .metric-value { font-size: 22px; color: #1c1c1c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Options Edge Finder — Regime Analysis & Spread Calculator")
st.markdown("Questo modulo analizza l'efficacia del **Credit Put Spread** separando i dati storici in base alla posizione del prezzo rispetto alla **Media Mobile a 200 periodi (SMA 200)**.")

# SIDEBAR PARAMETRI
st.sidebar.header("⚙️ Parametri di Configurazione")
ticker_symbol = "SPY"

dte_opzioni = st.sidebar.slider("Giorni alla scadenza (DTE)", min_value=15, max_value=60, value=30, step=5)
giorni_lavorativi = int(np.round(dte_opzioni * (5/7)))

st.sidebar.subheader("🎯 Definizione degli Strike")
strike_venduto_pct = st.sidebar.slider("Distanza Strike VENDUTO (%)", min_value=-15.0, max_value=-1.0, value=-5.0, step=0.5) / 100
ampiezza_spread_pct = st.sidebar.slider("Ampiezza dello Spread (%)", min_value=1.0, max_value=10.0, value=2.0, step=0.5) / 100

# CARICAMENTO DATI
@st.cache_data(ttl=86400)
def carica_dati_completi(symbol):
    data = yf.download(symbol, start="2000-01-01") # Dal 2000 per prendere Bolla DotCom, 2008 e 2020
    df_puro = data[['Adj Close']].copy()
    df_puro.columns = ['Close']
    return df_puro

try:
    with st.spinner("Analisi dello storico S&P 500 in corso..."):
        df = carica_dati_completi(ticker_symbol)
        
    # Calcolo indicatori strutturali
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['Prezzo_Futuro'] = df['Close'].shift(-giorni_lavorativi)
    df['Rendimento_Periodo'] = (df['Prezzo_Futuro'] - df['Close']) / df['Close']
    
    # Determina il regime di mercato ALL'INGRESSO della posizione
    df['Regime'] = np.where(df['Close'] >= df['SMA_200'], 'Toro (Sopra SMA 200)', 'Orso (Sotto SMA 200)')
    
    df_analisi = df.dropna().copy()
    
    # Prezzo attuale per calcoli in tempo reale
    prezzo_corrente = float(df['Close'].iloc[-1])
    regime_attuale = df_analisi['Regime'].iloc[-1]
    sma_200_attuale = float(df['SMA_200'].iloc[-1])
    
    # Calcolo Strike Operativi Reali
    valore_strike_venduto = np.round(prezzo_corrente * (1 + strike_venduto_pct), 2)
    # Lo strike comprato si calcola SOTTO lo strike venduto in base all'ampiezza percentuale scelta
    valore_strike_comprato = np.round(valore_strike_venduto * (1 - ampiezza_spread_pct), 2)
    distanza_totale_comprato_pct = ((valore_strike_comprato - prezzo_corrente) / prezzo_corrente) * 100

    # STATISTICA AGGREGATA VS CONDIZIONATA
    def calcola_statistiche(dataframe, short_pct, long_pct):
        totale = len(dataframe)
        if totale == 0: return 0, 0, 0
        # Scenario di perdita parziale: il mercato scende sotto lo strike venduto
        violazioni_short = len(dataframe[dataframe['Rendimento_Periodo'] < short_pct])
        # Scenario di perdita MASSIMA: il mercato abbatte anche la protezione (strike comprato)
        # Nota: nel passato il rendimento calcolato è (Prezzo_Futuro - Prezzo_Ingresso)/Prezzo_Ingresso.
        # Lo strike comprato è posizionato a: Prezzo_Ingresso * (1 + short_pct) * (1 - long_pct) - 1 per trovare la % equivalente dal prezzo d'ingresso
        pct_equivalente_comprato = (1 + short_pct) * (1 - long_pct) - 1
        violazioni_massime = len(dataframe[dataframe['Rendimento_Periodo'] < pct_equivalente_comprato])
        
        prob_successo = ((totale - violazioni_short) / totale) * 100
        prob_perdita_massima = (violazioni_massime / totale) * 100
        return prob_successo, prob_perdita_massima, totale

    prob_tot_succ, prob_tot_loss, n_tot = calcola_statistiche(df_analisi, strike_venduto_pct, ampiezza_spread_pct)
    
    df_toro = df_analisi[df_analisi['Regime'] == 'Toro (Sopra SMA 200)']
    prob_toro_succ, prob_toro_loss, n_toro = calcola_statistiche(df_toro, strike_venduto_pct, ampiezza_spread_pct)
    
    df_orso = df_analisi[df_analisi['Regime'] == 'Orso (Sotto SMA 200)']
    prob_orso_succ, prob_orso_loss, n_orso = calcola_statistiche(df_orso, strike_venduto_pct, ampiezza_spread_pct)

    # INTERFACCIA: STATO ATTUALE DEL MERCATO
    st.subheader("🚨 Stato del Mercato in Tempo Reale")
    col_st1, col_st2, col_st3 = st.columns(3)
    
    with col_st1:
        st.metric("Prezzo Corrente SPY", f"${prezzo_corrente:.2f}")
    with col_st2:
        st.metric("Media Mobile 200gg (SMA 200)", f"${sma_200_attuale:.2f}")
    with col_st3:
        if regime_attuale == 'Toro (Sopra SMA 200)':
            st.markdown('<div class="status-card" style="background-color: #28a745; text-align:center;"><b>REGIME ATTUALE: TORO</b><br>Prezzo sopra la SMA 200</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-card" style="background-color: #dc3545; text-align:center;"><b>REGIME ATTUALE: ORSO</b><br>Prezzo sotto la SMA 200 (Attenzione!)</div>', unsafe_allow_html=True)

    # INTERFACCIA: SEGNALE OPERATIVO DELLO SPREAD
    st.subheader("📋 Configurazione del Credit Put Spread Consigliato")
    st.markdown("In base ai tuoi parametri di rischio sulla distanza, ecco i livelli esatti da impostare sulla piattaforma di trading:")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.error(f"🔴 VENDI (Short Put)\n**Strike: ${valore_strike_venduto:.2f}**\nDistanza attuale: {strike_venduto_pct*100:.1f}%")
    with col_c2:
        st.success(f"🟢 COMPRA (Long Put - Protezione)\n**Strike: ${valore_strike_comprato:.2f}**\nDistanza attuale: {distanza_totale_comprato_pct:.1f}%")
    with col_c3:
        ampiezza_punti = np.round(valore_strike_venduto - valore_strike_comprato, 2)
        st.warning(f"🛡️ STRUTTURA SPREAD\n**Ampiezza: {ampiezza_punti} punti**\nRischio Massimo: ${ampiezza_punti*100:.2f} per contratto")

    # CONFRONTO STATISTICO TRA REGIMI
    st.subheader("📊 Impatto della SMA 200 sulle Probabilità Storiche")
    st.markdown("Nota come cambiano radicalmente le probabilità di successo se apri l'operazione quando il mercato è in un trend rialzista rispetto a un trend ribassista.")

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(f"""
            <div class="metric-card" style="border-left-color: #6c757d;">
                <div class="metric-label">Storico Totale (Tutti i giorni)</div>
                <div class="metric-value">Prob. Successo: {prob_tot_succ:.1f}%</div>
                <div style="font-size:12px; color:#dc3545;">Prob. Perdita Massima: {prob_tot_loss:.1f}%</div>
                <div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_tot} scenari mensili totali</div>
            </div>
        """, unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"""
            <div class="metric-card" style="border-left-color: #28a745;">
                <div class="metric-label">Quando il mercato è SOPRA la SMA 200</div>
                <div class="metric-value" style="color: #28a745;">Prob. Successo: {prob_toro_succ:.1f}%</div>
                <div style="font-size:12px; color:#dc3545;">Prob. Perdita Massima: {prob_toro_loss:.1f}%</div>
                <div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_toro} scenari (Mercato Sano)</div>
            </div>
        """, unsafe_allow_html=True)
    with col_m3:
        border_color = "#dc3545" if prob_orso_succ < prob_toro_succ else "#ffc107"
        st.markdown(f"""
            <div class="metric-card" style="border-left-color: {border_color};">
                <div class="metric-label">Quando il mercato è SOTTO la SMA 200</div>
                <div class="metric-value" style="color: #dc3545;">Prob. Successo: {prob_orso_succ:.1f}%</div>
                <div style="font-size:12px; color:#dc3545;">Prob. Perdita Massima: {prob_orso_loss:.1f}%</div>
                <div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_orso} scenari (Mercato Pericoloso)</div>
            </div>
        """, unsafe_allow_html=True)

    # GRAFICO VISIVO DEI REGIMI
    st.subheader("📈 Visualizzazione dei Rendimenti Storici per Regime")
    
    fig = go.Figure()
    fig.add_trace(go.Box(y=df_toro['Rendimento_Periodo'] * 100, name="Sopra SMA 200 (Toro)", marker_color='#28a745'))
    fig.add_trace(go.Box(y=df_orso['Rendimento_Periodo'] * 100, name="Sotto SMA 200 (Orso)", marker_color='#dc3545'))
    
    fig.add_hline(y=strike_venduto_pct * 100, line_color="red", line_dash="dash", line_width=2, annotation_text="Livello Strike Venduto")
    
    fig.update_layout(
        yaxis_title="Rendimento a 30gg (%)",
        template="plotly_white",
        height=400,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Errore durante l'esecuzione del modello: {e}")
