import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione Pagina
st.set_page_config(
    page_title="Options Edge Finder v7 — Seasonal Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizzato
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .status-card { padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px; color: white; }
    .metric-card { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #0066cc; margin-bottom: 15px; }
    .metric-label { font-size: 13px; color: #6c757d; font-weight: 500; text-transform: uppercase; }
    .metric-value { font-size: 22px; color: #1c1c1c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Options Edge Finder — Seasonal & Regime Engine")
st.markdown("Studio dinamico delle anomalie mensili e stagionali per strategie **Credit Put Spread** su SPY.")

# SIDEBAR PARAMETRI
st.sidebar.header("⚙️ Parametri di Configurazione")
dte_opzioni = st.sidebar.slider("Giorni alla scadenza (DTE)", min_value=15, max_value=60, value=30, step=5)
giorni_lavorativi = int(np.round(dte_opzioni * (5/7)))

st.sidebar.subheader("🎯 Definizione degli Strike")
strike_venduto_pct = st.sidebar.slider("Distanza Strike VENDUTO (%)", min_value=-15.0, max_value=-1.0, value=-5.0, step=0.5) / 100
ampiezza_spread_pct = st.sidebar.slider("Ampiezza dello Spread (%)", min_value=1.0, max_value=10.0, value=2.0, step=0.5) / 100

# CARICAMENTO DATI DA FILE LOCALE CSV
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
        df_finale['Close'] = pd.to_numeric(df_finale['Close'], errors='coerce')
        df_finale = df_finale.dropna()
        return df_finale
    except Exception as e:
        st.error(f"⚠️ Errore nel file CSV: {e}")
        return pd.DataFrame()

df = carica_dati_locali()

if not df.empty:
    # Calcolo indicatori strutturali
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['Prezzo_Futuro'] = df['Close'].shift(-giorni_lavorativi)
    df['Rendimento_Periodo'] = (df['Prezzo_Futuro'] - df['Close']) / df['Close']
    df['Regime'] = np.where(df['Close'] >= df['SMA_200'], 'Toro (Sopra SMA 200)', 'Orso (Sotto SMA 200)')
    
    # 🗓️ ESTRAZIONE DELLA STAGIONALITÀ MENSILE
    df['Mese_Num'] = df.index.month
    nomi_mesi = {1: 'Gen', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mag', 6: 'Giu', 7: 'Lug', 8: 'Ago', 9: 'Set', 10: 'Ott', 11: 'Nov', 12: 'Dic'}
    df['Mese'] = df['Mese_Num'].map(nomi_mesi)
    
    df_analisi = df.dropna().copy()
    
    # Dati correnti per l'interfaccia
    prezzo_corrente = float(df['Close'].iloc[-1])
    sma_200_attuale = float(df['SMA_200'].iloc[-1])
    regime_attuale = str(df_analisi['Regime'].iloc[-1])
    
    valore_strike_venduto = np.round(prezzo_corrente * (1 + strike_venduto_pct), 2)
    valore_strike_comprato = np.round(valore_strike_venduto * (1 - ampiezza_spread_pct), 2)
    distanza_totale_comprato_pct = ((valore_strike_comprato - prezzo_corrente) / prezzo_corrente) * 100

    # L'INTERFACCIA STATO ATTUALE (Invariata)
    st.subheader("🚨 Ultimo Stato Rilevato dell'Indice")
    col_st1, col_st2, col_st3 = st.columns(3)
    with col_st1: st.metric("Prezzo SPY", f"${prezzo_corrente:.2f}")
    with col_st2: st.metric("Media Mobile 200gg", f"${sma_200_attuale:.2f}")
    with col_st3:
        if 'Toro' in regime_attuale:
            st.markdown('<div class="status-card" style="background-color: #28a745; text-align:center;"><b>REGIME: TORO</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-card" style="background-color: #dc3545; text-align:center;"><b>REGIME: ORSO</b></div>', unsafe_allow_html=True)

    st.subheader("📋 Configurazione Livelli Operativi")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1: st.error(f"🔴 VENDI (Short Put) -> **Strike: ${valore_strike_venduto:.2f}** (-{abs(strike_venduto_pct*100):.1f}%)")
    with col_c2: st.success(f"🟢 COMPRA (Long Put) -> **Strike: ${valore_strike_comprato:.2f}** ({distanza_totale_comprato_pct:.1f}%)")
    with col_c3:
        ampiezza = np.round(valore_strike_venduto - valore_strike_comprato, 2)
        st.warning(f"🛡️ RISK PARAMETERS -> **Ampiezza: {ampiezza} punti** (Max Loss: ${ampiezza*100:.2f})")

    # --- NUOVA SEZIONE: ANALISI STAGIONALE AVANZATA ---
    st.subheader("🗓️ Studio di Stagionalità: Rendimenti e Win Rate per Mese dell'Anno")
    st.markdown("Questa sezione scompone i dati storici per verificare se esistono mesi intrinsecamente ostili o favorevoli alla strategia.")

    # Funzione di calcolo raggruppato per mese
    stat_mesi = []
    ordine_mesi = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
    
    # Calcolo della percentuale di perdita massima equivalente
    pct_equivalente_comprato = (1 + strike_venduto_pct) * (1 - ampiezza_spread_pct) - 1

    for m in ordine_mesi:
        sub_df = df_analisi[df_analisi['Mese'] == m]
        tot = len(sub_df)
        if tot > 0:
            violazioni_short = len(sub_df[sub_df['Rendimento_Periodo'] < strike_venduto_pct])
            violazioni_max = len(sub_df[sub_df['Rendimento_Periodo'] < pct_equivalente_comprato])
            
            win_rate = ((tot - violazioni_short) / tot) * 100
            loss_max_rate = (violazioni_max / tot) * 100
            rend_medio = sub_df['Rendimento_Periodo'].mean() * 100
            
            stat_mesi.append({
                'Mese': m,
                'Win Rate (%)': np.round(win_rate, 1),
                'Max Loss Prob (%)': np.round(loss_max_rate, 1),
                'Rendimento Medio (%)': np.round(rend_medio, 2),
                'Scenari': tot
            })

    df_stat_mesi = pd.DataFrame(stat_mesi)

    # GRAFICO 1: WIN RATE MENSILE STORICO (GRAFICO A BARRE)
    fig_bar = go.Figure()
    
    # Coloriamo in rosso i mesi storicamente più rischiosi (sotto il 90%) e in verde quelli ottimali
    colori_barre = ['#28a745' if wr >= 90 else '#ffc107' if wr >= 85 else '#dc3545' for wr in df_stat_mesi['Win Rate (%)']]
    
    fig_bar.add_trace(go.Bar(
        x=df_stat_mesi['Mese'],
        y=df_stat_mesi['Win Rate (%)'],
        text=df_stat_mesi['Win Rate (%)'].astype(str) + '%',
        textposition='auto',
        marker_color=colori_barre,
        name='Win Rate'
    ))
    
    fig_bar.add_hline(y=90.0, line_color="black", line_dash="dot", annotation_text="Target Standard (90%)")
    
    fig_bar.update_layout(
        title="Percentuale Storica di Successo (Win Rate) del Put Spread Mese per Mese",
        yaxis=dict(title="Probabilità di Successo (%)", range=[70, 105]),
        template="plotly_white",
        height=450
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # DIVISIONE IN DUE COLONNE PER APPROFONDIMENTI
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("### 📊 Tabella Metriche Stagionali")
        st.dataframe(df_stat_mesi.set_index('Mese'), use_container_width=True)
        st.caption("I dati mostrano il comportamento a scadenza della strategia diviso per il mese solare di INGRESSO a mercato.")

    with col_g2:
        st.markdown("### 💡 Cosa rivelano questi dati per il tuo trading?")
        
        # Identifichiamo dinamicamente il mese peggiore e quello migliore nel dataset
        mese_peggiore = df_stat_mesi.sort_values(by='Win Rate (%)').iloc[0]
        mese_migliore = df_stat_mesi.sort_values(by='Win Rate (%)', ascending=False).iloc[0]
        
        st.warning(f"⚠️ **Il Mese più critico:** Statisticamente è **{mese_peggiore['Mese']}**, con un Win Rate che scende al **{mese_peggiore['Win Rate (%)']}%**. In questo mese, il rischio di incorrere in una perdita massima (Max Loss) è storicamente del **{mese_peggiore['Max Loss Prob (%)']}%**.")
        st.success(f"🚀 **Il Mese d'oro:** Statisticamente è **{mese_migliore['Mese']}**, dove la strategia registra un tasso di successo eccezionale del **{mese_migliore['Win Rate (%)']}%**, supportato da un rendimento medio mensile del mercato pari a **{mese_migliore['Rendimento Medio (%)']}%**.")
        
        st.markdown("""
        **Consiglio Operativo per AvaOptions:**
        * Nelle finestre temporali associate ai mesi critici (tipicamente fine estate/inizio autunno), non aprire spread statici. Valuta di **allontanare lo strike venduto** (es. portandolo a -7% o -8%) o riduci la taglia dei tuoi lotti (*Position Sizing*).
        * Nei mesi caratterizzati da forte spinta rialzista storica (fine anno/primavera), puoi sfruttare l'alto Edge per incassare premi regolari con massima serenità, poiché i ritracciamenti violenti in grado di abbattere la barriera del 5% sono estremamente rari.
        """)

    # VECCHIO CONFRONTO REGIME (Mantenuto sotto come validazione strutturale)
    st.subheader("📈 Distribuzione dei Rendimenti e Regimi di Trend (SMA 200)")
    
    def calcola_statistiche(dataframe, short_pct, long_pct):
        totale = len(dataframe)
        if totale == 0: return 0.0, 0.0, 0
        violazioni_short = len(dataframe[dataframe['Rendimento_Periodo'] < short_pct])
        violazioni_massime = len(dataframe[dataframe['Rendimento_Periodo'] < pct_equivalente_comprato])
        prob_successo = ((totale - violazioni_short) / totale) * 100
        prob_perdita_massima = (violazioni_massime / totale) * 100
        return prob_successo, prob_perdita_massima, totale

    prob_tot_succ, prob_tot_loss, n_tot = calcola_statistiche(df_analisi, strike_venduto_pct, ampiezza_spread_pct)
    df_toro = df_analisi[df_analisi['Regime'] == 'Toro (Sopra SMA 200)']
    prob_toro_succ, prob_toro_loss, n_toro = calcola_statistiche(df_toro, strike_venduto_pct, ampiezza_spread_pct)
    df_orso = df_analisi[df_analisi['Regime'] == 'Orso (Sotto SMA 200)']
    prob_orso_succ, prob_orso_loss, n_orso = calcola_statistiche(df_orso, strike_venduto_pct, ampiezza_spread_pct)

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(f'<div class="metric-card" style="border-left-color: #6c757d;"><div class="metric-label">Storico Totale</div><div class="metric-value">Successo: {prob_tot_succ:.1f}%</div><div style="font-size:12px; color:#dc3545;">Perdita Max: {prob_tot_loss:.1f}%</div><div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_tot} scenari</div></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="metric-card" style="border-left-color: #28a745;"><div class="metric-label">Sopra SMA 200 (Toro)</div><div class="metric-value" style="color: #28a745;">Successo: {prob_toro_succ:.1f}%</div><div style="font-size:12px; color:#dc3545;">Perdita Max: {prob_toro_loss:.1f}%</div><div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_toro} scenari</div></div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown(f'<div class="metric-card" style="border-left-color: #dc3545;"><div class="metric-label">Sotto SMA 200 (Orso)</div><div class="metric-value" style="color: #dc3545;">Successo: {prob_orso_succ:.1f}%</div><div style="font-size:12px; color:#dc3545;">Perdita Max: {prob_orso_loss:.1f}%</div><div style="font-size:11px; color:#6c757d; margin-top:5px;">Su {n_orso} scenari</div></div>', unsafe_allow_html=True)
