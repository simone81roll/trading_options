import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione Pagina
st.set_page_config(
    page_title="Options Edge Finder v10 — Time to Touch",
    page_icon="⏱️",
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

st.title("⏱️ Options Edge Finder — Time to Touch Engine")
st.markdown("Analisi della **velocità di riassorbimento**: quanto tempo impiega il prezzo a colmare la distanza dalla SMA 200?")

# SIDEBAR PARAMETRI
st.sidebar.header("⚙️ Orizzonte Temporale Opzione")
dte_opzioni = st.sidebar.slider("Giorni alla scadenza del tuo Spread (DTE)", min_value=15, max_value=60, value=30, step=5)

st.sidebar.subheader("🎯 Tolleranza Analisi")
tolleranza = st.sidebar.slider(
    "Flessibilità del filtro (%)", 
    min_value=0.2, max_value=2.0, value=0.5, step=0.1,
    help="Se l'estensione attuale è del 7%, una tolleranza dello 0.5% cercherà nello storico tutti i giorni con estensione compresa tra 6.5% e 7.5%."
)

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
    # Calcolo indicatori base
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    # Estensione percentuale attuale dalla media
    df['Estensione_SMA200_Pct'] = ((df['Close'] - df['SMA_200']) / df['SMA_200']) * 100
    df_analisi = df.dropna().copy()
    
    # 1. RILEVAZIONE STATO ATTUALE (Ultima riga del file)
    prezzo_corrente = float(df_analisi['Close'].iloc[-1])
    sma_200_attuale = float(df_analisi['SMA_200'].iloc[-1])
    estensione_attuale = float(df_analisi['Estensione_SMA200_Pct'].iloc[-1])
    
    st.subheader("🚨 Condizione di Mercato Odierna")
    col_st1, col_st2, col_st3 = st.columns(3)
    with col_st1: st.metric("Prezzo SPY Corrente", f"${prezzo_corrente:.2f}")
    with col_st2: st.metric("Media Mobile 200gg (SMA 200)", f"${sma_200_attuale:.2f}")
    with col_st3: st.metric("Estensione dalla SMA 200 (Distanza)", f"{estensione_attuale:.2f}%")
    
    # 2. ALGORITMO BACKTEST: CANCELLA I GIORNI DI CONFRONTO
    min_filtro = estensione_attuale - tolleranza
    max_filtro = estensione_attuale + tolleranza
    
    giorni_simili = df_analisi[(df_analisi['Estensione_SMA200_Pct'] >= min_filtro) & (df_analisi['Estensione_SMA200_Pct'] <= max_filtro)].copy()
    
    st.subheader(f"📊 Analisi Quantitativa: Finestre storiche con Estensione tra {min_filtro:.1f}% e {max_filtro:.1f}%")
    
    if len(giorni_simili) < 5:
        st.warning("⚠️ Ci sono troppi pochi campioni storici con questa estensione esatta per fare una statistica affidabile. Prova ad aumentare la 'Flessibilità del filtro' nella barra laterale.")
    else:
        lista_tempi_tocco = []
        scenari_totali = len(giorni_simili)
        toccati_entro_dte = 0
        
        # Per ogni giorno simile trovato nel passato, cronometriamo quanto ci ha messo il prezzo a scendere al livello della SMA 200 di quel giorno
        for data_inizio, riga in giorni_simili.iterrows():
            livello_target_prezzo = riga['SMA_200']
            
            # Guardiamo i dati successivi a quella data
            dati_futuri = df_analisi.loc[data_inizio:]
            
            # Troviamo il primo giorno in cui il prezzo di chiusura è diventato minore o uguale al target
            condizione_tocco = dati_futuri['Close'] <= livello_target_prezzo
            
            if condizione_tocco.any():
                data_tocco = condizione_tocco.idxmax()
                # Calcoliamo i giorni di borsa (giorni lavorativi) effettivi passati
                giorni_passati = len(df_analisi.loc[data_inizio:data_tocco]) - 1
                lista_tempi_tocco.append(giorni_passati)
                if giorni_passati <= dte_opzioni:
                    toccati_entro_dte += 1
            else:
                # Se non ha mai più toccato quel livello nella storia successiva
                pass

        # Calcolo metriche sui tempi di tocco
        if lista_tempi_tocco:
            tempo_minimo = min(lista_tempi_tocco)
            tempo_medio = int(np.mean(lista_tempi_tocco))
            prob_sopravvivenza_dte = ((scenari_totali - toccati_entro_dte) / scenari_totales) * 100
            
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.markdown(f'<div class="metric-card" style="border-left-color: #dc3545;"><div class="card-title">⚡ Crollo più Veloce della Storia</div><div class="card-value">{tempo_minimo} Giorni lavorativi</div><div style="font-size:12px; color:#6c757d; margin-top:5px;">Velocità massima di riassorbimento</div></div>', unsafe_allow_html=True)
            with col_m2:
                st.markdown(f'<div class="metric-card" style="border-left-color: #0066cc;"><div class="card-title">⏳ Tempo Medio di Ritorno alla Media</div><div class="card-value">{tempo_medio} Giorni lavorativi</div><div style="font-size:12px; color:#6c757d; margin-top:5px;">Velocità media di convergenza</div></div>', unsafe_allow_html=True)
            with col_m3:
                colore_wr = "#28a745" if prob_sopravvivenza_dte >= 90 else "#ffc107"
                st.markdown(f'<div class="metric-card" style="border-left-color: {colore_wr};"><div class="card-title">🎯 Probabilità di Successo a {dte_opzioni} DTE</div><div class="card-value" style="color: {colore_wr};">{prob_sopravvivenza_dte:.1f}%</div><div style="font-size:12px; color:#6c757d; margin-top:5px;">Scenari in cui il tempo è scaduto prima del tocco</div></div>', unsafe_allow_html=True)
            
            st.markdown(f"### 💡 Verdetto Statistico per il tuo Trading")
            if tempo_minimo > dte_opzioni:
                st.success(f"🔥 **Edge Clamoroso:** Nella storia dell'S&P 500, quando il mercato si è trovato a questa distanza dalla SMA 200, ci ha messo **almeno {tempo_minimo} giorni** per azzerare l'estensione. Vendendo una scadenza a **{dte_opzioni} giorni**, la matematica dice che il mercato non è mai stato così veloce da poterti colpire prima della scadenza dell'opzione!")
            else:
                st.warning(f"⚠️ **Attenzione al Criterio di Velocità:** Il crollo più rapido registrato da questo livello ha impiegato **{tempo_minimo} giorni** per toccare la media. Poiché il tuo DTE è di {dte_opzioni} giorni, ti trovi all'interno della finestra di pericolo. Storicamente, il livello è stato violato prima della scadenza nel **{(100 - prob_sopravvivenza_dte):.1f}%** dei casi.")

            # GRAFICO DI DISTRIBUZIONE DEI TEMPI DI TOCCO
            st.subheader("📊 Distribuzione dei tempi di colmamento del gap (in giorni)")
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=lista_tempi_tocco,
                name="Giorni impiegati",
                marker_color='#ff9900',
                xbins=dict(start=0, end=120, size=5)
            ))
            fig.add_vline(x=dte_opzioni, line_color="red", line_dash="dash", line_width=2, annotation_text=f"Scadenza della tua Opzione ({dte_opzioni} DTE)")
            fig.update_layout(
                template="plotly_white",
                xaxis=dict(title="Giorni di Borsa necessari per toccare la SMA 200"),
                yaxis=dict(title="Numero di casi storici rilevati"),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Nota: Le barre a SINISTRA della linea rossa indicano i casi storici in cui lo spread sarebbe andato in sofferenza prima della scadenza. Le barre a DESTRA rappresentano i trade vincenti.")
