import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
#options_edge_finder
# Gestione flessibile dell'importazione della libreria Nasdaq
try:
    import nasdaqdatastorage as ndl
except ImportError:
    try:
        import nasdaqdatalink as ndl
    except ImportError:
        st.error("⚠️ La libreria Nasdaq Data Link non è installata. Verifica il tuo file requirements.txt")

# Configurazione Pagina
st.set_page_config(
    page_title="Options Edge Finder v5",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizzato per l'interfaccia grafica
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

st.title("🛡️ Options Edge Finder — Nasdaq API Version")
st.markdown("Analisi statistica del **Credit Put Spread** sull'S&P 500 basata sui dati istituzionali del circuito Nasdaq.")

# SIDEBAR PARAMETRI
st.sidebar.header("⚙️ Parametri di Configurazione")

dte_opzioni = st.sidebar.slider("Giorni alla scadenza (DTE)", min_value=15, max_value=60, value=30, step=5)
# Approssimazione per dati mensili/storici strutturati
finestra_shift = int(np.round(dte_opzioni / 30)) if dte_opzioni >= 30 else 1

st.sidebar.subheader("🎯 Definizione degli Strike")
strike_venduto_pct = st.sidebar.slider("Distanza Strike VENDUTO (%)", min_value=-15.0, max_value=-1.0, value=-5.0, step=0.5) / 100
ampiezza_spread_pct = st.sidebar.slider("Ampiezza dello Spread (%)", min_value=1.0, max_value=10.0, value=2.0, step=0.5) / 100

# CARICAMENTO DATI DA NASDAQ DATA LINK
@st.cache_data(ttl=86400)
def carica_dati_completi_nasdaq():
    try:
        # Recupera l'indice S&P 500 ufficiale (Yale Shiller dataset gratuito su Nasdaq)
        data = ndl.get("MULTPL/SP500_REAL_PRICE_MONTH")
        if data.empty:
            return pd.DataFrame()
            
        df_puro = pd.DataFrame(data.iloc[:, 0]).copy()
        df_puro.columns = ['Close']
        df_puro.index = pd.to_datetime(df_puro.index)
        df_puro = df_puro.sort_index()
        return df_puro
    except Exception as e:
        st.sidebar.error(f"Errore di connessione API Nasdaq: {e}")
        return pd.DataFrame()

try:
    with st.spinner("Connessione ai server Nasdaq in corso..."):
        df = carica_dati_completi_nasdaq()
        
    if df is None or df.empty:
        st.error("⚠️ Impossibile ricevere i dati dall'API pubblica del Nasdaq.")
        st.info("Se riscontri problemi continui con le API esterne online, la soluzione definitiva è caricare un file 'spy_history.csv' locale nella tua repository.")
    else:
        # Calcolo indicatori su storico macro (Media Mobile a 12 mesi per dati mensili, equivalente alla SMA 200)
        df['SMA_200'] = df['Close'].rolling(window=12).mean()
        df['Prezzo_Futuro'] = df['Close'].shift(-finestra_shift)
        df['Rendimento_Periodo'] = (df['Prezzo_Futuro'] - df['Close']) / df['Close']
        
        df['Regime'] = np.where(df['Close'] >= df['SMA_200'], 'Toro (Sopra SMA 200)', 'Orso (Sotto SMA 200)')
        df_analisi = df.dropna().copy()
        
        # Estrazione dati correnti
        prezzo_corrente = float(df['Close'].iloc[-1])
        sma_200_attuale = float(df['SMA_200'].iloc[-1])
        regime_attuale = str(df_analisi['Regime'].iloc[-1])
        
        # Calcolo degli Strike Operativi
        valore_strike_venduto = np.round(prezzo_corrente * (1 + strike_venduto_pct), 2)
        valore_strike_comprato = np.round(valore_strike_venduto * (1 - ampiezza_spread_pct), 2)
        distanza_totale_comprato_pct = ((valore_strike_comprato - prezzo_corrente) / prezzo_corrente) * 100

        # INTERFACCIA REALE
        st.subheader("🚨 Stato dell'Indice S&P 500")
        col_st1, col_st2, col_st3 = st.columns(3)
        
        with col_st1:
            st.metric("Ultimo Prezzo Indice", f"${prezzo_corrente:.2f}")
        with col_st2:
            st.metric("Media Mobile di Lungo Periodo", f"${sma_200_attuale:.2f}")
        with col_st3:
            if 'Toro' in regime_attuale:
                st.markdown('<div class="status-card" style="background-color: #28a745; text-align:center;"><b>REGIME ATTUALE: TORO</b><br>Prezzo sopra la Media</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-card" style="background-color: #dc3545; text-align:center;"><b>REGIME ATTUALE: ORSO</b><br>Prezzo sotto la Media (Rischio Elevato)</div>', unsafe_allow_html=True)

        # SEGNALE OPERATIVO SPREAD
        st.subheader("📋 Struttura del Credit Put Spread")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.error(f"🔴 STRIKE VENDUTO (Short Put)\n**${valore_strike_venduto:.2f}**\nDistanza: {strike_venduto_pct*100:.1f}%")
        with col_c2:
            st.success(f"🟢 STRIKE COMPRATO (Long Put)\n**${valore_strike_comprato:.2f}**\nDistanza: {distanza_totale_comprato_pct:.1f}%")
        with col_c3:
            ampiezza_punti = np.round(valore_strike_venduto - valore_strike_comprato, 2)
            st.warning(f"🛡️ PARAMETRI RISK\n**Ampiezza: {ampiezza_punti} Punti**\nRischio Massimo: ${ampiezza_punti*100:.2f}")

        # TENTATIVO IMPORTAZIONE ASSISTENTE AI
        try:
            from ai_assistant import valuta_strategia_prudente_ai
            st.subheader("🤖 Analisi Predittiva AI Assistant")
            def calcola_prob_singola(dataframe, short_pct):
                tot = len(dataframe)
                if tot == 0: return 0.0
                violazioni = len(dataframe[dataframe['Rendimento_Periodo'] < short_pct])
                return ((tot - violazioni) / tot) * 100
            
            prob_regime_attuale = calcola_prob_singola(df_analisi[df_analisi['Regime'] == regime_attuale], strike_venduto_pct)
            ai_report = valuta_strategia_prudente_ai(regime_attuale, prob_regime_attuale, 0, valore_strike_venduto, valore_strike_comprato)
            st.info(f"**{ai_report.get('stato', '')}**\n\n{ai_report.get('nota', '')}")
        except Exception:
            pass

        # FUNZIONE STATISTICHE QUANTATIVE
        def calcola_statistiche(dataframe, short_pct, long_pct):
            totale = len(dataframe)
            if totale == 0: return 0.0, 0.0, 0
            violazioni_short = len(dataframe[dataframe['Rendimento_Periodo'] < short_pct])
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

        # OUTPUT METRICHE SULLO SCHERMO
        st.subheader("📊 Analisi Storica Comparata dei Regimi")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #6c757d;">
                    <div class="metric-label">Storico Aggregato</div>
                    <div class="metric-value">Successo: {prob_tot_succ:.1f}%</div>
                    <div style="font-size:12px; color:#dc3545;">Perdita Max: {prob_tot_loss:.1f}%</div>
                    <div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_tot} periodi campionati</div>
                </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #28a745;">
                    <div class="metric-label">In Regime Rialzista (Prezzo > Media)</div>
                    <div class="metric-value" style="color: #28a745;">Successo: {prob_toro_succ:.1f}%</div>
                    <div style="font-size:12px; color:#dc3545;">Perdita Max: {prob_toro_loss:.1f}%</div>
                    <div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_toro} periodi sani</div>
                </div>
            """, unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #dc3545;">
                    <div class="metric-label">In Regime Ribassista (Prezzo < Media)</div>
                    <div class="metric-value" style="color: #dc3545;">Successo: {prob_orso_succ:.1f}%</div>
                    <div style="font-size:12px; color:#dc3545;">Perdita Max: {prob_orso_loss:.1f}%</div>
                    <div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_orso} periodi instabili</div>
                </div>
            """, unsafe_allow_html=True)

        # BOXPLOT
        st.subheader("📈 Distribuzione Matematica dei Rendimenti")
        fig = go.Figure()
        fig.add_trace(go.Box(y=df_toro['Rendimento_Periodo'] * 100, name="Fase Toro", marker_color='#28a745'))
        fig.add_trace(go.Box(y=df_orso['Rendimento_Periodo'] * 100, name="Fase Orso", marker_color='#dc3545'))
        fig.add_hline(y=strike_venduto_pct * 100, line_color="red", line_dash="dash", line_width=2, annotation_text="Soglia Short Put")
        fig.update_layout(yaxis_title="Rendimento a termine (%)", template="plotly_white", height=400, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Errore generale: {e}")
