import streamlit as st
import math

# --- MOTORE MATEMATICO ESATTO (BINOMIAL SURVIVAL) ---

def p_win(n, k, q_m):
    """
    Calcola la probabilità binomiale di ottenere almeno k vittorie in n eventi,
    assumendo una quota media q_m (probabilità di singolo successo p = 1/q_m).
    """
    if k <= 0: return 1.0
    if k > n: return 0.0
    
    p = 1.0 / q_m
    prob = 0.0
    for i in range(k, n + 1):
        prob += math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    return prob

def calcola_stake_perfetto(cassa_attuale, n_res, k_res, q_m, q_reale):
    """
    Calcola lo stake usando il bilanciamento dei panni (Target Invariante).
    U_W = Probabilità residua se vinciamo il prossimo evento
    U_L = Probabilità residua se perdiamo il prossimo evento
    """
    if k_res <= 0 or k_res > n_res or n_res <= 0: 
        return 0.0

    U_W = p_win(n_res - 1, k_res - 1, q_m)
    U_L = p_win(n_res - 1, k_res, q_m)
    
    numeratore = U_W - U_L
    denominatore = U_L * (q_reale - 1.0) + U_W
    
    if denominatore == 0: 
        return 0.0
        
    stake = cassa_attuale * (numeratore / denominatore)
    return round(stake, 2)


# --- INTERFACCIA STREAMLIT ---

st.set_page_config(page_title="Masaniello Perfetto", layout="wide", page_icon="🎯")
st.title("🎯 Masaniello Algoritmo Matematico (Stile BigStake)")
st.write("Motore a Quote Variabili ricalibrato sulla distribuzione binomiale esatta.")

# --- INIZIALIZZAZIONE SESSIONE ---
if 'inizializzato' not in st.session_state:
    st.session_state.inizializzato = False
    st.session_state.cassa_iniziale = 50.0
    st.session_state.cassa_attuale = 50.0
    st.session_state.n_tot = 10
    st.session_state.k_tot = 4
    st.session_state.quota_media = 1.50
    st.session_state.vincite = 0
    st.session_state.perdite = 0
    st.session_state.storico = []
    st.session_state.stato_ciclo = "In corso"

# --- SIDEBAR CONFIGURAZIONE ---
with st.sidebar:
    st.header("⚙️ Creazione Ciclo")
    disabilitato = st.session_state.inizializzato
    
    input_budget = st.number_input("Cassa Totale (€)", value=50.0, step=10.0, disabled=disabilitato)
    input_n = st.number_input("Eventi Totali (N)", value=10, step=1, min_value=1, disabled=disabilitato)
    input_k = st.number_input("Vincite Richieste (K)", value=5, step=1, min_value=1, max_value=input_n, disabled=disabilitato)
    input_q = st.number_input("Quota Media Stimata", value=1.50, step=0.05, min_value=1.01, disabled=disabilitato)
    
    if not st.session_state.inizializzato:
        if st.button("🚀 Avvia Sistema", type="primary"):
            st.session_state.cassa_iniziale = input_budget
            st.session_state.cassa_attuale = input_budget
            st.session_state.n_tot = input_n
            st.session_state.k_tot = input_k
            st.session_state.quota_media = input_q
            st.session_state.inizializzato = True
            st.rerun()
    else:
        if st.button("🔄 Resetta e Crea Nuovo", type="secondary"):
            st.session_state.inizializzato = False
            st.session_state.vincite = 0
            st.session_state.perdite = 0
            st.session_state.storico = []
            st.session_state.stato_ciclo = "In corso"
            st.rerun()

# --- TABELLONE PRINCIPALE ---
if not st.session_state.inizializzato:
    st.info("Imposta i parametri nella sidebar a sinistra e clicca su 'Avvia Sistema'.")
else:
    # Parametri residui
    n_residui = st.session_state.n_tot - (st.session_state.vincite + st.session_state.perdite)
    k_residui = st.session_state.k_tot - st.session_state.vincite

    # Target Dinamico Calcolato (Cassa / Probabilità Residua)
    prob_attuale = p_win(n_residui, k_residui, st.session_state.quota_media)
    target_attuale = st.session_state.cassa_attuale / prob_attuale if prob_attuale > 0 else 0.0

    # Aggiornamento stato
    if k_residui <= 0:
        st.session_state.stato_ciclo = "Vinto"
    elif k_residui > n_residui:
        st.session_state.stato_ciclo = "Perso"

    # Metriche (Layout pulito a 4 colonne)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cassa Attuale", f"€ {st.session_state.cassa_attuale:.2f}")
    col2.metric("Target di Fine Ciclo", f"€ {target_attuale:.2f}")
    col3.metric("Profitto Netto Atteso", f"€ {(target_attuale - st.session_state.cassa_iniziale):.2f}")
    col4.metric("Progresso Obiettivo", f"{st.session_state.vincite} / {st.session_state.k_tot} W")

    st.markdown("---")

    if st.session_state.stato_ciclo == "In corso":
        st.subheader(f"➡️ Step Corrente: Giocata {len(st.session_state.storico) + 1}")
        
        # Inserimento della quota reale del momento
        quota_reale = st.number_input("Quota REALE da scommettere ora:", value=st.session_state.quota_media, step=0.05, min_value=1.01)
        
        # Motore che calcola lo stake
        prossimo_stake = calcola_stake_perfetto(
            st.session_state.cassa_attuale,
            n_residui,
            k_residui,
            st.session_state.quota_media,
            quota_reale
        )
        
        st.metric("Puntata Ideale (Stake)", f"€ {prossimo_stake:.2f}")

        col_v, col_p = st.columns(2)
        with col_v:
            if st.button("✅ SEGNA COME VINTO", use_container_width=True, type="primary"):
                st.session_state.cassa_attuale += prossimo_stake * (quota_reale - 1)
                st.session_state.vincite += 1
                st.session_state.storico.append({
                    "Step": len(st.session_state.storico) + 1,
                    "Quota": quota_reale,
                    "Stake": prossimo_stake,
                    "Esito": "Vinto",
                    "Cassa Aggiornata": round(st.session_state.cassa_attuale, 2)
                })
                st.rerun()
                
        with col_p:
            if st.button("❌ SEGNA COME PERSO", use_container_width=True):
                st.session_state.cassa_attuale -= prossimo_stake
                st.session_state.perdite += 1
                st.session_state.storico.append({
                    "Step": len(st.session_state.storico) + 1,
                    "Quota": quota_reale,
                    "Stake": prossimo_stake,
                    "Esito": "Perso",
                    "Cassa Aggiornata": round(st.session_state.cassa_attuale, 2)
                })
                st.rerun()

    elif st.session_state.stato_ciclo == "Vinto":
        st.balloons()
        st.success(f"🎉 OBIETTIVO RAGGIUNTO! Ciclo chiuso con successo. Cassa finale: € {st.session_state.cassa_attuale:.2f}")
    else:
        st.error(f"💥 CICLO INTERROTTO! Raggiunto il limite di errori. Cassa salvata residua: € {st.session_state.cassa_attuale:.2f}")

    if st.session_state.storico:
        st.subheader("📋 Registro Giocate")
        st.dataframe(st.session_state.storico, use_container_width=True)
