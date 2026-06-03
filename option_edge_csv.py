import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione Pagina
st.set_page_config(
    page_title="Options Edge Finder v6",
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

st.title("🛡️ Options Edge Finder — Local Data Engine")
st.markdown("Analisi statistica del **Credit Put Spread** basata su archivio storico locale protetto da Rate Limiting.")

# SIDEBAR PARAMETRI
st.sidebar.header("⚙️ Parametri di Configurazione")

dte_opzioni = st.sidebar.slider("Giorni alla scadenza (DTE)", min_value=15, max_value=60, value=30, step=5)
# Convertiamo i DTE in giorni lavorativi effettivi (circa i 5/7 del tempo solare)
giorni_lavorativi = int(np.round(dte_opzioni * (5/7)))

st.sidebar.subheader("🎯 Definizione degli Strike")
strike_venduto_pct = st.sidebar.slider("Distanza Strike VENDUTO (%)", min_value=-15.0, max_value=-1.0, value=-5.0, step=0.5) / 100
ampiezza_spread_pct = st.sidebar.slider("Ampiezza dello Spread (%)", min_value=1.0, max_value=10.0, value=2.0, step=0.5) / 100

# CARICAMENTO DATI DA FILE LOCALE CSV (Sicuro e Immediato)
@st.cache_data
def carica_dati_locali():
    try:
        # Legge il file CSV caricato dentro la repository GitHub
        df_puro = pd.read_csv("spy_history.csv")
        
        # Gestione flessibile dei nomi delle colonne generati da Yahoo o piattaforme esterne
        df_puro.columns = [col.strip() for col in df_puro.columns]
        
        if 'Date' in df_puro.columns:
            df_puro['Date'] = pd.to_datetime(df_puro['Date'])
            df_puro.set_index('Date', inplace=True)
        elif 'Date' in df_puro.index.names:
            df_puro.index = pd.to_datetime(df_puro.index)
            
        # Scegliamo la colonna del prezzo di chiusura corretta
        colonna_target = 'Adj Close' if 'Adj Close' in df_puro.columns else 'Close'
        
        df_finale = pd.DataFrame(df_puro[colonna_target]).copy()
        df_finale.columns = ['Close']
        
        # Ordiniamo le date in modo cronologico crescente per le medie mobili
        df_finale = df_finale.sort_index()
        df_finale['Close'] = pd.to_numeric(df_finale['Close'], errors='coerce')
        df_finale = df_finale.dropna()
        
        return df_finale
    except Exception as e:
        st.error(f"⚠️ Errore nel caricamento del file 'spy_history.csv' locale: {e}")
        st.info("Verifica che il file si trovi esattamente nella stessa cartella dello script su GitHub.")
        return pd.DataFrame()

df = carica_dati_locali()

if not df.empty:
    try:
        # Calcolo indicatori matematici su dati storici giornalieri stabili
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['Prezzo_Futuro'] = df['Close'].shift(-giorni_lavorativi)
        df['Rendimento_Periodo'] = (df['Prezzo_Futuro'] - df['Close']) / df['Close']
        
        df['Regime'] = np.where(df['Close'] >= df['SMA_200'], 'Toro (Sopra SMA 200)', 'Orso (Sotto SMA 200)')
        df_analisi = df.dropna().copy()
        
        # Estrazione degli ultimi dati reali inseriti nel file
        prezzo_corrente = float(df['Close'].iloc[-1])
        sma_200_attuale = float(df['SMA_200'].iloc[-1])
        regime_attuale = str(df_analisi['Regime'].iloc[-1])
        
        # Calcolo degli Strike Operativi Reali basati sull'ultimo record
        valore_strike_venduto = np.round(prezzo_corrente * (1 + strike_venduto_pct), 2)
        valore_strike_comprato = np.round(valore_strike_venduto * (1 - ampiezza_spread_pct), 2)
        distanza_totale_comprato_pct = ((valore_strike_comprato - prezzo_corrente) / prezzo_corrente) * 100

        # INTERFACCIA REALE
        st.subheader("🚨 Ultimo Stato Rilevato dell'Indice SPY")
        col_st1, col_st2, col_st3 = st.columns(3)
        
        with col_st1:
            st.metric("Ultimo Prezzo di Chiusura", f"${prezzo_corrente:.2f}")
        with col_st2:
            st.metric("Media Mobile 200gg (SMA 200)", f"${sma_200_attuale:.2f}")
        with col_st3:
            if 'Toro' in regime_attuale:
                st.markdown('<div class="status-card" style="background-color: #28a745; text-align:center;"><b>REGIME: TORO</b><br>Prezzo sopra la SMA 200</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-card" style="background-color: #dc3545; text-align:center;"><b>REGIME: ORSO</b><br>Prezzo sotto la SMA 200 (Attenzione Risk!)</div>', unsafe_allow_html=True)

        # CONFIGURAZIONE STRUTTURA DEL CREDIT PUT SPREAD
        st.subheader("📋 Livelli di Input per il Credit Put Spread")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.error(f"🔴 VENDI (Short Put)\n**Strike: ${valore_strike_venduto:.2f}**\nDistanza: {strike_venduto_pct*100:.1f}%")
        with col_c2:
            st.success(f"🟢 COMPRA (Long Put - Protezione)\n**Strike: ${valore_strike_comprato:.2f}**\nDistanza: {distanza_totale_comprato_pct:.1f}%")
        with col_c3:
            ampiezza_punti = np.round(valore_strike_venduto - valore_strike_comprato, 2)
            st.warning(f"🛡️ PARAMETRI DI CONTROLLO\n**Ampiezza Spread: {ampiezza_punti} punti**\nRischio Massimo: ${ampiezza_punti*100:.2f} per contratto")

        # TENTATIVO CARICAMENTO MODULO AI ASSISTANT
        try:
            from ai_assistant import valuta_strategia_prudente_ai
            st.subheader("🤖 Suggerimento Operativo dell'AI Assistant")
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

        # FUNZIONE DI CALCOLO QUANTITATIVO DELLE STATISTICHE
        def calcola_statistiche(dataframe, short_pct, long_pct):
            totale = len(dataframe)
            if totale == 0: return 0.0, 0.0, 0
            
            # Violazioni dello strike corto (Perdita iniziale)
            violazioni_short = len(dataframe[dataframe['Rendimento_Periodo'] < short_pct])
            
            # Violazioni dello strike lungo di protezione (Perdita massima o Max Loss)
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

        # CRUSCOTTO METRICHE SULLO SCHERMO
        st.subheader("📊 Impatto della SMA 200 sulle Probabilità Storiche")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #6c757d;">
                    <div class="metric-label">Storico Totale (Tutti i giorni)</div>
                    <div class="metric-value">Prob. Successo: {prob_tot_succ:.1f}%</div>
                    <div style="font-size:12px; color:#dc3545;">Prob. Perdita Max: {prob_tot_loss:.1f}%</div>
                    <div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_tot} scenari analizzati</div>
                </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #28a745;">
                    <div class="metric-label">Quando il mercato è SOPRA la SMA 200</div>
                    <div class="metric-value" style="color: #28a745;">Prob. Successo: {prob_toro_succ:.1f}%</div>
                    <div style="font-size:12px; color:#dc3545;">Prob. Perdita Max: {prob_toro_loss:.1f}%</div>
                    <div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_toro} giorni di trend rialzista</div>
                </div>
            """, unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #dc3545;">
                    <div class="metric-label">Quando il mercato è SOTTO la SMA 200</div>
                    <div class="metric-value" style="color: #dc3545;">Prob. Successo: {prob_orso_succ:.1f}%</div>
                    <div style="font-size:12px; color:#dc3545;">Prob. Perdita Max: {prob_orso_loss:.1f}%</div>
                    <div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_orso} giorni di trend ribassista</div>
                </div>
            """, unsafe_allow_html=True)

        # BOXPLOT RENDIMENTI CON SOGLIA
        st.subheader("📈 Distribuzione dei Rendimenti a Scadenza per Regime")
        fig = go.Figure()
        fig.add_trace(go.Box(y=df_toro['Rendimento_Periodo'] * 100, name="Sopra SMA 200 (Toro)", marker_color='#28a745'))
        fig.add_trace(go.Box(y=df_orso['Rendimento_Periodo'] * 100, name="Sotto SMA 200 (Orso)", marker_color='#dc3545'))
        fig.add_hline(y=strike_venduto_pct * 100, line_color="red", line_dash="dash", line_width=2, annotation_text="Livello Short Put")
        fig.update_layout(yaxis_title="Rendimento del periodo (%)", template="plotly_white", height=400, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    except Exception as runtime_err:
        st.error(f"Errore nell'elaborazione matematica dei vettori: {runtime_err}")
