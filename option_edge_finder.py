import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione Pagina
st.set_page_config(
    page_title="Options Edge Finder v9 — SMA Distance",
    page_icon="🛡️",
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

st.title("🛡️ Options Edge Finder — SMA 200 Distance Analyzer")
st.markdown("Analisi dell'impatto dell'**estensione percentuale dalla SMA 200** sulle probabilità di successo dello spread.")

# SIDEBAR PARAMETRI
st.sidebar.header("⚙️ Parametri Generali")
dte_opzioni = st.sidebar.slider("Giorni alla scadenza (DTE)", min_value=15, max_value=60, value=30, step=5)
giorni_lavorativi = int(np.round(dte_opzioni * (5/7)))

moltiplicatore_sigma = st.sidebar.slider("Moltiplicatore Deviazioni Standard (N Sigma)", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
ampiezza_spread_pct = st.sidebar.slider("Ampiezza dello Spread (%)", min_value=1.0, max_value=10.0, value=2.0, step=0.5) / 100

# 📊 NUOVO FILTRO: DISTANZA DALLA SMA 200
st.sidebar.subheader("📐 Filtro Estensione SMA 200")
st.sidebar.markdown("Analizza lo storico filtrando solo i giorni in cui l'indice si trovava a una specifica distanza dalla media:")
filtro_distanza = st.sidebar.slider(
    "Prezzo rispetto alla SMA 200 (Soglia %)", 
    min_value=-15.0, max_value=15.0, value=0.0, step=0.5,
    help="Se imposti +5%, analizzerai l'efficacia dello spread solo nei giorni in cui il mercato era esteso verso l'alto di almeno il 5% rispetto alla sua media mobile."
)
tipo_confronto = st.sidebar.radio("Mostra giorni con estensione:", ["Maggiore o uguale alla soglia (>=)", "Minore o uguale alla soglia (<=)"])

# CARICAMENTO DATI LOCALI
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
    # Calcolo indicatori base e volatilità
    df['Rendimento_Giornaliero'] = df['Close'].pct_change()
    df['Volatila_Rolling'] = df['Rendimento_Giornaliero'].rolling(window=20).std() * np.sqrt(giorni_lavorativi)
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['Prezzo_Futuro'] = df['Close'].shift(-giorni_lavorativi)
    df['Rendimento_Effettivo_Periodo'] = (df['Prezzo_Futuro'] - df['Close']) / df['Close']
    
    # 📐 CALCOLO DELLA DISTANZA PERCENTUALE DALLA SMA 200
    df['Distanza_SMA200_Pct'] = ((df['Close'] - df['SMA_200']) / df['SMA_200']) * 100
    
    # Calcolo Strike Dinamico Storico
    df['Distanza_Dinamica_Short_Pct'] = - (moltiplicatore_sigma * df['Volatila_Rolling'])
    df['Successo_Dinamico'] = df['Rendimento_Effettivo_Periodo'] >= df['Distanza_Dinamica_Short_Pct']
    pct_max_loss_dinamica = (1 + df['Distanza_Dinamica_Short_Pct']) * (1 - ampiezza_spread_pct) - 1
    df['Max_Loss_Dinamica'] = df['Rendimento_Effettivo_Periodo'] < pct_max_loss_dinamica
    
    df['Mese_Num'] = df.index.month
    nomi_mesi = {1: 'Gen', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mag', 6: 'Giu', 7: 'Lug', 8: 'Ago', 9: 'Set', 10: 'Ott', 11: 'Nov', 12: 'Dic'}
    df['Mese'] = df['Mese_Num'].map(nomi_mesi)
    
    df_analisi_totale = df.dropna().copy()
    
    # Applicazione dinamica del filtro basato sull'estensione impostata nella sidebar
    if tipo_confronto == "Maggiore o uguale alla soglia (>=)":
        df_filtrato = df_analisi_totale[df_analisi_totale['Distanza_SMA200_Pct'] >= filtro_distanza]
    else:
        df_filtrato = df_analisi_totale[df_analisi_totale['Distanza_SMA200_Pct'] <= filtro_distanza]
        
    # Estrazione Dati Correnti
    prezzo_corrente = float(df['Close'].iloc[-1])
    sma_200_attuale = float(df['SMA_200'].iloc[-1])
    distanza_attuale_sma_pct = float(df_analisi_totale['Distanza_SMA200_Pct'].iloc[-1])
    volatila_attuale_pct = float(df_analisi_totale['Volatila_Rolling'].iloc[-1]) * 100
    distanza_consigliata_pct = float(df_analisi_totale['Distanza_Dinamica_Short_Pct'].iloc[-1])
    
    valore_strike_venduto = np.round(prezzo_corrente * (1 + distanza_consigliata_pct), 2)
    valore_strike_comprato = np.round(valore_strike_venduto * (1 - ampiezza_spread_pct), 2)

    # INTERFACCIA CRUSCOTTO REALE
    st.subheader("🚨 KPI di Mercato ed Estensione Attuale")
    col_st1, col_st2, col_st3, col_st4 = st.columns(4)
    with col_st1: st.metric("Prezzo SPY Corrente", f"${prezzo_corrente:.2f}")
    with col_st2: st.metric("Media Mobile 200gg", f"${sma_200_attuale:.2f}")
    with col_st3: st.metric("Distanza Attuale dalla SMA 200", f"{distanza_attuale_sma_pct:.2f}%")
    with col_st4: st.metric(f"Volatilità ({dte_opzioni} DTE)", f"{volatila_attuale_pct:.2f}%")

    # SEGNALE OPERATIVO ATTUALE
    st.subheader("🤖 Configurazione Algoritmica per Oggi")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1: st.error(f"🔴 SHORT PUT -> **Strike: ${valore_strike_venduto:.2f}** ({distanza_consigliata_pct*100:.1f}%)")
    with col_c2: st.success(f"🟢 LONG PUT -> **Strike: ${valore_strike_comprato:.2f}**")
    with col_c3: 
        ampiezza = np.round(valore_strike_venduto - valore_strike_comprato, 2)
        st.warning(f"🛡️ RISK CONTROL -> **Max Loss Contract: ${ampiezza*100:.2f}**")

    # --- VALIDAZIONE DELLO STUDIO DI ESTENSIONE ---
    st.subheader(f"📊 Risultati dello Studio di Impatto: Estensione {tipo_confronto[:8]} {filtro_distanza}%")
    
    if df_filtrato.empty:
        st.warning("⚠️ Nessun giorno nello storico soddisfa i criteri di estensione impostati. Prova ad ammorbidire i filtri nella sidebar.")
    else:
        tot_filtrato = len(df_filtrato)
        win_filtrato = (df_filtrato['Successo_Dinamico'].sum() / tot_filtrato) * 100
        loss_filtrato = (df_filtrato['Max_Loss_Dinamica'].sum() / tot_filtrato) * 100
        
        tot_globale = len(df_analisi_totale)
        win_globale = (df_analisi_totale['Successo_Dinamico'].sum() / tot_globale) * 100
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f'<div class="metric-card" style="border-left-color: #6c757d;"><div class="metric-label">Campione Filtrato Analizzato</div><div class="metric-value">{tot_filtrato} Giorni</div><div style="font-size:12px; color:#6c757d;">Rappresentano il {((tot_filtrato/tot_globale)*100):.1f}% dello storico</div></div>', unsafe_allow_html=True)
        with col_m2:
            colore_bordo = "#28a745" if win_filtrato >= win_globale else "#ffc107"
            st.markdown(f'<div class="metric-card" style="border-left-color: {colore_bordo};"><div class="metric-label">Win Rate nel Filtro Selezionato</div><div class="metric-value" style="color: {colore_bordo};">{win_filtrato:.1f}%</div><div style="font-size:12px; color:#dc3545;">Probabilità Max Loss: {loss_filtrato:.1f}%</div></div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown(f'<div class="metric-card" style="border-left-color: #0066cc;"><div class="metric-label">Win Rate Globale di Riferimento</div><div class="metric-value" style="color: #0066cc;">{win_globale:.1f}%</div><div style="font-size:12px; color:#6c757d;">Media benchmark senza filtri</div></div>', unsafe_allow_html=True)

        # STAGIONALITÀ SUL CAMPIONE FILTRATO
        stat_mesi_filtrati = []
        ordine_mesi = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
        for m in ordine_mesi:
            sub_df = df_filtrato[df_filtrato['Mese'] == m]
            tot = len(sub_df)
            if tot > 0:
                win_m = (sub_df['Successo_Dinamico'].sum() / tot) * 100
                stat_mesi_filtrati.append({'Mese': m, 'Win Rate (%)': np.round(win_m, 1), 'Scenari': tot})
        df_stat_filtrati = pd.DataFrame(stat_mesi_filtrati)

        # GRAFICO IMPATTO MENSILE SOTTO FILTRO
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df_stat_filtrati['Mese'], y=df_stat_filtrati['Win Rate (%)'],
            text=df_stat_filtrati['Win Rate (%)'].astype(str) + '%', textposition='auto',
            marker_color='#0066cc'
        ))
        fig_bar.add_hline(y=win_globale, line_color="red", line_dash="dash", annotation_text="Media Globale")
        fig_bar.update_layout(
            title="Performance dello Strike Dinamico condizionata al Filtro di Estensione scelto",
            yaxis=dict(title="Win Rate (%)", range=[75, 105]), template="plotly_white", height=380
        )
        st.plotly_chart(fig_bar, use_container_width=True)
