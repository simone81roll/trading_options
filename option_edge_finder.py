import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione Pagina
st.set_page_config(
    page_title="Options Edge Finder v8 — Dynamic Strike",
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

st.title("🛡️ Options Edge Finder — Dynamic Volatility Engine")
st.markdown("Analisi con **Strike Dinamico** regolato sulla Volatilità Storica corrente e sui Regimi di Mercato.")

# SIDEBAR PARAMETRI DI VOLATILITÀ
st.sidebar.header("⚙️ Configurazione Dinamica")
dte_opzioni = st.sidebar.slider("Giorni alla scadenza (DTE)", min_value=15, max_value=60, value=30, step=5)
giorni_lavorativi = int(np.round(dte_opzioni * (5/7)))

st.sidebar.subheader("📊 Parametri di Volatilità (Bande)")
# Al posto della percentuale fissa, usiamo le Deviazioni Standard (Sigma)
moltiplicatore_sigma = st.sidebar.slider(
    "Moltiplicatore Deviazioni Standard (N Sigma)", 
    min_value=1.0, max_value=3.0, value=1.5, step=0.1,
    help="Un valore più alto allontana lo strike aumentando la sicurezza, ma riduce il premio incassato."
)

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
    # 1. Calcolo Volatilità Storica Rolling a 20 giorni (Rendimenti Logaritmici o Percentuali)
    df['Rendimento_Giornaliero'] = df['Close'].pct_change()
    # Volatilità periodale basata sui giorni lavorativi del DTE scelto
    df['Volatila_Rolling'] = df['Rendimento_Giornaliero'].rolling(window=20).std() * np.sqrt(giorni_lavorativi)
    
    # 2. Indicatori Strutturali
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['Prezzo_Futuro'] = df['Close'].shift(-giorni_lavorativi)
    df['Rendimento_Effettivo_Periodo'] = (df['Prezzo_Futuro'] - df['Close']) / df['Close']
    df['Regime'] = np.where(df['Close'] >= df['SMA_200'], 'Toro (Sopra SMA 200)', 'Orso (Sotto SMA 200)')
    
    # 3. 🗓️ Calcolo Strike Dinamico Storico Giorno per Giorno
    # Distanza dinamica calcolata in base alla volatilità di quel preciso giorno
    df['Distanza_Dinamica_Short_Pct'] = - (moltiplicatore_sigma * df['Volatila_Rolling'])
    df['Strike_Venduto_Dinamico'] = df['Close'] * (1 + df['Distanza_Dinamica_Short_Pct'])
    
    df['Mese_Num'] = df.index.month
    nomi_mesi = {1: 'Gen', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mag', 6: 'Giu', 7: 'Lug', 8: 'Ago', 9: 'Set', 10: 'Ott', 11: 'Nov', 12: 'Dic'}
    df['Mese'] = df['Mese_Num'].map(nomi_mesi)
    
    df_analisi = df.dropna().copy()
    
    # Estrazione Dati Correnti (Ultima Riga del File)
    prezzo_corrente = float(df['Close'].iloc[-1])
    sma_200_attuale = float(df['SMA_200'].iloc[-1])
    regime_attuale = str(df_analisi['Regime'].iloc[-1])
    volatila_attuale_pct = float(df_analisi['Volatila_Rolling'].iloc[-1]) * 100
    
    # CONCORDANZA SUGGERIMENTO DINAMICO ATTUALE
    distanza_consigliata_pct = float(df_analisi['Distanza_Dinamica_Short_Pct'].iloc[-1])
    valore_strike_venduto = np.round(prezzo_corrente * (1 + distanza_consigliata_pct), 2)
    valore_strike_comprato = np.round(valore_strike_venduto * (1 - ampiezza_spread_pct), 2)
    distanza_totale_comprato_pct = ((valore_strike_comprato - prezzo_corrente) / prezzo_corrente) * 100

    # INTERFACCIA REALE
    st.subheader("🚨 Dashboard Analisi Volatilità e Stato di Mercato")
    col_st1, col_st2, col_st3, col_st4 = st.columns(4)
    with col_st1: st.metric("Prezzo SPY Corrente", f"${prezzo_corrente:.2f}")
    with col_st2: st.metric("Media Mobile 200gg", f"${sma_200_attuale:.2f}")
    with col_st4: st.metric(f"Volatilità Attuale ({dte_opzioni} DTE)", f"{volatila_attuale_pct:.2f}%")
    with col_st3:
        if 'Toro' in regime_attuale:
            st.markdown('<div class="status-card" style="background-color: #28a745; text-align:center; padding:12px;"><b>REGIME: TORO</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-card" style="background-color: #dc3545; text-align:center; padding:12px;"><b>REGIME: ORSO</b></div>', unsafe_allow_html=True)

    # OUTPUT STRIKE DINAMICI CONSIGLIATI
    st.subheader("🤖 Algoritmo di Calcolo: Strike Consigliati per il Momento Attuale")
    st.info(f"L'algoritmo ha analizzato la volatilità recente. Per coprire **{moltiplicatore_sigma} Deviazioni Standard** ad un orizzonte di {dte_opzioni} giorni, ti consiglia una distanza minima di sicurezza dello **{distanza_consigliata_pct * 100:.2f}%**.")

    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1: st.error(f"🔴 APRI SHORT PUT (Vendi)\n**Strike Consigliato: ${valore_strike_venduto:.2f}**\nDistanza Dinamica: {distanza_consigliata_pct*100:.1f}%")
    with col_c2: st.success(f"🟢 APRI LONG PUT (Compra)\n**Strike Consigliato: ${valore_strike_comprato:.2f}**\nDistanza di Protezione: {distanza_totale_comprato_pct:.1f}%")
    with col_c3:
        ampiezza = np.round(valore_strike_venduto - valore_strike_comprato, 2)
        st.warning(f"🛡️ CONFIGURAZIONE RISK\n**Ampiezza Spread: {ampiezza} punti**\nRischio Massimo: ${ampiezza*100:.2f} per contratto")

    # --- ANALISI STORICA DEL MODELLO DINAMICO ---
    st.subheader("📊 Validazione Storica: Come si è comportato lo Strike Dinamico nei Mesi dell'Anno?")
    st.markdown("A differenza di prima, lo strike si è spostato nel tempo inseguendo il mercato. Vediamo il Win Rate storico reale di questo approccio dinamico:")

    # Calcolo statistiche con Strike Dinamico Variabile riga per riga
    # Un successo si ha quando il rendimento effettivo del periodo è superiore alla distanza dinamica calcolata in quel preciso giorno
    df_analisi['Successo_Dinamico'] = df_analisi['Rendimento_Effettivo_Periodo'] >= df_analisi['Distanza_Dinamica_Short_Pct']
    
    # Calcolo violazione della max loss dinamica
    pct_max_loss_dinamica = (1 + df_analisi['Distanza_Dinamica_Short_Pct']) * (1 - ampiezza_spread_pct) - 1
    df_analisi['Max_Loss_Dinamica'] = df_analisi['Rendimento_Effettivo_Periodo'] < pct_max_loss_dinamica

    stat_mesi_dinamici = []
    ordine_mesi = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']

    for m in ordine_mesi:
        sub_df = df_analisi[df_analisi['Mese'] == m]
        tot = len(sub_df)
        if tot > 0:
            win_rate = (sub_df['Successo_Dinamico'].sum() / tot) * 100
            max_loss_rate = (sub_df['Max_Loss_Dinamica'].sum() / tot) * 100
            
            stat_mesi_dinamici.append({
                'Mese': m,
                'Win Rate Dinamico (%)': np.round(win_rate, 1),
                'Max Loss Prob (%)': np.round(max_loss_rate, 1),
                'Scenari': tot
            })

    df_stat_mesi_dinamici = pd.DataFrame(stat_mesi_dinamici)

    # GRAFICO WIN RATE DINAMICO
    fig_bar = go.Figure()
    colori_barre = ['#28a745' if wr >= 92 else '#ffc107' if wr >= 88 else '#dc3545' for wr in df_stat_mesi_dinamici['Win Rate Dinamico (%)']]
    
    fig_bar.add_trace(go.Bar(
        x=df_stat_mesi_dinamici['Mese'],
        y=df_stat_mesi_dinamici['Win Rate Dinamico (%)'],
        text=df_stat_mesi_dinamici['Win Rate Dinamico (%)'].astype(str) + '%',
        textposition='auto',
        marker_color=colori_barre,
    ))
    fig_bar.add_hline(y=90.0, line_color="black", line_dash="dot", annotation_text="Soglia Target (90%)")
    fig_bar.update_layout(
        title="Win Rate Storico Modello Dinamico (Regolato sulla Volatilità del Giorno di Ingresso)",
        yaxis=dict(title="Probabilità di Successo (%)", range=[75, 105]),
        template="plotly_white", height=400
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # CONFRONTO REGIME CON APPROCCIO DINAMICO
    st.subheader("📈 Performance Dinamica condizionata alla SMA 200")
    
    tot_scenari = len(df_analisi)
    win_tot = (df_analisi['Successo_Dinamico'].sum() / tot_scenari) * 100
    loss_tot = (df_analisi['Max_Loss_Dinamica'].sum() / tot_scenari) * 100
    
    df_toro = df_analisi[df_analisi['Regime'] == 'Toro (Sopra SMA 200)']
    win_toro = (df_toro['Successo_Dinamico'].sum() / len(df_toro)) * 100 if len(df_toro) > 0 else 0
    loss_toro = (df_toro['Max_Loss_Dinamica'].sum() / len(df_toro)) * 100 if len(df_toro) > 0 else 0
    
    df_orso = df_analisi[df_analisi['Regime'] == 'Orso (Sotto SMA 200)']
    win_orso = (df_orso['Successo_Dinamico'].sum() / len(df_orso)) * 100 if len(df_orso) > 0 else 0
    loss_orso = (df_orso['Max_Loss_Dinamica'].sum() / len(df_orso)) * 100 if len(df_orso) > 0 else 0

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(f'<div class="metric-card" style="border-left-color: #6c757d;"><div class="metric-label">Totale Storico Dinamico</div><div class="metric-value">Win Rate: {win_tot:.1f}%</div><div style="font-size:12px; color:#dc3545;">Prob. Max Loss: {loss_tot:.1f}%</div></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="metric-card" style="border-left-color: #28a745;"><div class="metric-label">In Regime Toro (Dinamico)</div><div class="metric-value" style="color: #28a745;">Win Rate: {win_toro:.1f}%</div><div style="font-size:12px; color:#dc3545;">Prob. Max Loss: {loss_toro:.1f}%</div></div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown(f'<div class="metric-card" style="border-left-color: #dc3545;"><div class="metric-label">In Regime Orso (Dinamico)</div><div class="metric-value" style="color: #dc3545;">Win Rate: {win_orso:.1f}%</div><div style="font-size:12px; color:#dc3545;">Prob. Max Loss: {loss_orso:.1f}%</div></div>', unsafe_allow_html=True)
