import streamlit as st
import math

# --- FUNZIONI MATEMATICHE ORIGINALI DEL MASANIELLO ---
def combinazioni(n, k):
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)

def calcola_peso_combinazione(n, k, quota_media):
    """Calcola il divisore binomiale (panni totali iniziali)"""
    p = 1 / quota_media
    somma = 0
    for i in range(k, n + 1):
        somma += combinazioni(n, i) * (p**i) * ((1-p)**(n-i))
    return somma

def calcola_quota_panno_corrente(n_tot, k_tot, v_correnti, p_correnti):
    """Calcola quante combinazioni vincenti ci sono nello stato attuale"""
    n_residui = n_tot - (v_correnti + p_correnti)
    k_residui = k_tot - v_correnti
    
    if k_residui <= 0:
        return 1.0
    if k_residui > n_residui:
        return 0.0
        
    comb_totali = sum(combinazioni(n_residui, i) for i in range(k_residui, n_residui + 1))
    comb_se_vinco = sum(combinazioni(n_residui - 1, i) for i in range(k_residui - 1, n_residui))
    
    if comb_totali == 0:
        return 0.0
    return comb_totali / comb_se_vinco

# --- CONFIGURAZIONE INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Masaniello BigStake Clone", layout="wide", page_icon="🎯")
st.title("🎯 Masaniello Money Manager (Matematica Certificata)")
st.write("Sviluppato secondo le formule standard di scomposizione e bilanciamento dei panni d'orizzonte.")

# --- INIZIALIZZAZIONE ---
if 'inizializzato' not in st.session_state:
    st.session_state.inizializzato = False
    st.session_state.cassa_iniziale = 50.0
    st.session_state.cassa_attuale = 50.0
    st.session_state.n_tot = 10
    st.session_state.k_tot = 4
    st.session_state.quota_media = 1.50
    st.session_state.vincite = 0
    st.session_state.perdite = 0
    st.session_state.target_finale = 0.0
    st.session_state.storico = []
    st.session_state.stato_ciclo = "In corso"

# --- SIDEBAR DI CONFIGURAZIONE ---
with st.sidebar:
    st.header("⚙️ Impostazioni Iniziali")
    disabilitato = st.session_state.inizializzato
    
    input_budget = st.number_input("Cassa Totale (€)", value=50.0, step=5.0, disabled=disabilitato)
    input_n = st.number_input("Numero Eventi Totali (N)", value=10, step=1, min_value=1, disabled=disabilitato)
    input_k = st.number_input("Eventi richiesti (K)", value=4, step=1, min_value=1, max_value=input_n, disabled=disabilitato)
    input_q = st.number_input("Quota Media di Riferimento", value=1.50, step=0.05, min_value=1.01, disabled=disabilitato)
    
    if not st.session_state.inizializzato:
        if st.button("🚀 Avvia Ciclo", type="primary"):
            # Calcolo del Moltiplicatore Fisso basato sui parametri iniziali
            peso_iniziale = calcola_peso_combinazione(input_n, input_k, input_q)
            
            st.session_state.cassa_iniziale = input_budget
            st.session_state.cassa_attuale = input_budget
            st.session_state.n_tot = input_n
            st.session_state.k_tot = input_k
            st.session_state.quota_media = input_q
            st.session_state.target_finale = input_budget / peso_iniziale
            st.session_state.inizializzato = True
            st.rerun()
    else:
        if st.button("🔄 Resetta e Cancella", type="secondary"):
            st.session_state.inizializzato = False
            st.session_state.vincite = 0
            st.session_state.perdite = 0
            st.session_state.storico = []
            st.session_state.stato_ciclo = "In corso"
            st.rerun()

# --- TABELLONE PRINCIPALE ---
if not st.session_state.inizializzato:
    st.info("Configura la cassa, gli eventi e la quota media nella sidebar, poi clicca su 'Avvia Ciclo'.")
else:
    n_residui = st.session_state.n_tot - (st.session_state.vincite + st.session_state.perdite)
    k_residui = st.session_state.k_tot - st.session_state.vincite

    # Aggiornamento stato del ciclo
    if k_residui <= 0:
        st.session_state.stato_ciclo = "Vinto"
    elif k_residui > n_residui:
        st.session_state.stato_ciclo = "Perso"

    # Grafica delle metriche (Uguale a BigStake)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cassa Attuale", f"€ {st.session_state.cassa_attuale:.2f}")
    col2.metric("Target Atteso a Fine Ciclo", f"€ {st.session_state.target_finale:.2f}")
    col3.metric("Profitto Netto Previsto", f"€ {(st.session_state.target_finale - st.session_state.cassa_iniziale):.2f}")
    col4.metric("Progresso Vincite", f"{st.session_state.vincite} / {st.session_state.k_tot} W")

    st.markdown("---")

    if st.session_state.stato_ciclo == "In corso":
        st.subheader(f"Step {len(st.session_state.storico) + 1}")
        
        # Inserimento della quota del bookmaker per questo specifico evento
        quota_reale = st.number_input("Quota REALE dell'evento corrente:", value=st.session_state.quota_media, step=0.05, min_value=1.01)
        
        # FORMULA CORE MASANIELLO (Ancorata al Target Finale)
        # Calcoliamo il valore del panno attuale rispetto al traguardo fisso
        n_res = st.session_state.n_tot - (st.session_state.vincite + st.session_state.perdite)
        k_res = st.session_state.k_tot - st.session_state.vincite
        
        c_attuali = sum(combinazioni(n_res, i) for i in range(k_res, n_res + 1))
        c_vittoria = sum(combinazioni(n_res - 1, i) for i in range(k_res - 1, n_res))
        
        # Calcolo dello stake perfetto legato al Payout Atteso
        # Formula: (Valore se vinco - Valore attuale) / (Quota - 1) modificata per l'orizzonte dei panni
        q_passo = c_attuali / c_vittoria
        
        # Lo stake necessario per non perdere terreno rispetto al Target Finale
        quota_iniziale_media = st.session_state.quota_media
        
        # Algoritmo BigStake / Excel standard per lo stake del passo:
        prossimo_stake = (st.session_state.cassa_attuale / q_passo) / quota_reale
        
        # Per riflettere esattamente il bilanciamento a quote variabili sul target fisso:
        # Se la quota reale si abbassa, lo stake deve alzarsi per garantire che la vincita porti la cassa al livello corretto.
        frazione_orizzonte = c_vittoria / sum(combinazioni(st.session_state.n_tot, i) for i in range(st.session_state.k_tot, st.session_state.n_tot + 1))
        
        # Formula standard di ricalcolo dinamico dello stake ancorato
        prossimo_stake = (st.session_state.target_finale * (c_vittoria / c_attuali) - st.session_state.cassa_attuale) / (quota_reale - 1)
        
        if prossimo_stake < 0.01:
            # Protezione se siamo talmente avanti che basterebbe un centesimo
            prossimo_stake = 0.01
            
        st.metric("Puntata da effettuare (Stake)", f"€ {prossimo_stake:.2f}")

        col_v, col_p = st.columns(2)
        with col_v:
            if st.button("✅ SEGNA COME VINTO", use_container_width=True, type="primary"):
                profitto = prossimo_stake * (quota_reale - 1)
                st.session_state.cassa_attuale += profitto
                st.session_state.vincite += 1
                st.session_state.storico.append({
                    "Step": len(st.session_state.storico) + 1,
                    "Quota": quota_reale,
                    "Stake": round(prossimo_stake, 2),
                    "Esito": "Vinto",
                    "Bilancio (€)": round(st.session_state.cassa_attuale, 2)
                })
                st.rerun()
                
        with col_p:
            if st.button("❌ SEGNA COME PERSO", use_container_width=True):
                st.session_state.cassa_attuale -= prossimo_stake
                st.session_state.perdite += 1
                st.session_state.storico.append({
                    "Step": len(st.session_state.storico) + 1,
                    "Quota": quota_reale,
                    "Stake": round(prossimo_stake, 2),
                    "Esito": "Perso",
                    "Bilancio (€)": round(st.session_state.cassa_attuale, 2)
                })
                st.rerun()

    elif st.session_state.stato_ciclo == "Vinto":
        st.balloons()
        st.success(f"🎉 CICLO CHIUSO! Target raggiunto con successo. Cassa Finale: € {st.session_state.cassa_attuale:.2f} (Target iniziale stimato: € {st.session_state.target_finale:.2f})")
    else:
        st.error(f"💥 CICLO FALLITO! Numero massimo di perdite superato. Cassa salvata e recuperata: € {st.session_state.cassa_attuale:.2f}")

    if st.session_state.storico:
        st.subheader("📋 Registro delle Giocate Effettuate")
        st.table(st.session_state.storico)
