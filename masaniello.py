import streamlit as st
import math

# --- FUNZIONI MATEMATICHE CORE ---
def combinazioni(n, k):
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)

def calcola_quota_riferimento(n, k, quota_media):
    """Calcola il coefficiente del pacchetto combinatorio iniziale"""
    p = 1 / quota_media
    somma = 0
    for i in range(k, n + 1):
        somma += combinazioni(n, i) * (p**i) * ((1-p)**(n-i))
    return somma

def calcola_stake(budget_iniziale, n_tot, k_tot, v_correnti, p_correnti, quota_corrente):
    """
    Calcola lo stake per il prossimo evento basandosi sulle combinazioni residue.
    Formula basata sul peso delle sequenze vincenti rimaste.
    """
    n_residui = n_tot - (v_correnti + p_correnti)
    k_residui = k_tot - v_correnti

    # Verifiche di fine ciclo o anomalie
    if k_residui <= 0:
        return 0.0  # Obiettivo già raggiunto
    if k_residui > n_residui:
        return 0.0  # Impossibile raggiungere l'obiettivo

    # Combinazioni totali residue che portano al successo
    comb_totali_residue = sum(combinazioni(n_residui, i) for i in range(k_residui, n_residui + 1))
    
    # Combinazioni residue nell'ipotesi che il prossimo evento sia VINCENTE (k_residui si riduce di 1)
    comb_se_vinco = sum(combinazioni(n_residui - 1, i) for i in range(k_residui - 1, n_residui))

    if comb_totali_residue == 0:
        return 0.0

    # Quota teorica interna del passo
    quota_passo = comb_totali_residue / comb_se_vinco
    
    # Lo stake è frazione della cassa attuale basata sul rapporto tra quota reale e quota del passo
    # Per il Masaniello classico a quota fissa, quota_corrente e quota_passo si allineano.
    # Con quote variabili, usiamo la proporzione sul rendimento atteso.
    passo = (1 / quota_passo) / quota_corrente
    
    # Nota: Nelle implementazioni reali, il calcolo dello stake usa il bilanciamento delle masse
    # Qui usiamo la formula standard ricorsiva del Masaniello
    quota_fissa_iniziale = st.session_state.iniziale_quota_media
    rendimento_atteso = 1 / calcola_quota_riferimento(n_tot, k_tot, quota_fissa_iniziale)
    
    # Calcolo dello stake esatto tramite scomposizione dei panni (metodo dei coefficienti)
    c_attuali = sum(combinazioni(n_residui, i) for i in range(k_residui, n_residui + 1))
    c_vittoria = sum(combinazioni(n_residui - 1, i) for i in range(k_residui - 1, n_residui))
    
    if c_attuali == 0: return 0
    
    # Quota del pacchetto residuo
    stake = st.session_state.cassa_attuale * (c_vittoria / c_attuali) / quota_corrente
    return round(max(stake, 0.0), 2)


# --- CONFIGURAZIONE INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Masaniello Dashboard", layout="wide", page_icon="📊")
st.title("📊 Sistema Masaniello Professionale")
st.write("Un gestore di cassa ad orizzonte chiuso con ricalcolo dinamico.")

# --- INIZIALIZZAZIONE DELLO STATO (SESSION STATE) ---
if 'inizializzato' not in st.session_state:
    st.session_state.inizializzato = False
    st.session_state.cassa_iniziale = 100.0
    st.session_state.cassa_attuale = 100.0
    st.session_state.n_tot = 10
    st.session_state.k_tot = 6
    st.session_state.iniziale_quota_media = 2.0
    st.session_state.vincite = 0
    st.session_state.perdite = 0
    st.session_state.storico = []
    st.session_state.stato_ciclo = "In corso" # "Vinto", "Perso", "In corso"

# --- SIDEBAR: PARAMETRI DI CONFIGURAZIONE ---
with st.sidebar:
    st.header("⚙️ Impostazioni Ciclo")
    
    # Disabilitiamo gli input se il ciclo è già partito per evitare crash matematici
    disabilitato = st.session_state.inizializzato
    
    input_budget = st.number_input("Cassa Totale (€)", value=100.0, step=10.0, disabled=disabilitato)
    input_n = st.number_input("Numero Eventi Totali (N)", value=10, step=1, min_value=1, disabled=disabilitato)
    input_k = st.number_input("Eventi da Indovinare (K)", value=6, step=1, min_value=1, max_value=input_n, disabled=disabilitato)
    input_quota = st.number_input("Quota Media Stimata", value=2.0, step=0.1, min_value=1.01, disabled=disabilitato)
    
    if not st.session_state.inizializzato:
        if st.button("🚀 Avvia Masaniello", type="primary"):
            st.session_state.cassa_iniziale = input_budget
            st.session_state.cassa_attuale = input_budget
            st.session_state.n_tot = input_n
            st.session_state.k_tot = input_k
            st.session_state.iniziale_quota_media = input_quota
            st.session_state.inizializzato = True
            st.rerun()
    else:
        if st.button("🔄 Resetta e Crea Nuovo Ciclo", type="secondary"):
            st.session_state.inizializzato = False
            st.session_state.vincite = 0
            st.session_state.perdite = 0
            st.session_state.storico = []
            st.session_state.stato_ciclo = "In corso"
            st.rerun()

# --- CORPO PRINCIPALE ---
if not st.session_state.inizializzato:
    st.info("Configura i parametri nella barra laterale a sinistra e clicca su 'Avvia Masaniello' per iniziare.")
else:
    # Calcolo metriche generali iniziali
    prob_successo = calcola_quota_riferimento(st.session_state.n_tot, st.session_state.k_tot, st.session_state.iniziale_quota_media)
    if prob_successo > 0:
        payout_finale = st.session_state.cassa_iniziale / prob_successo
        roi = ((payout_finale - st.session_state.cassa_iniziale) / st.session_state.cassa_iniziale) * 100
    else:
        payout_finale = 0
        roi = 0

    # Layout a colonne per le KPI superiori
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cassa Attuale", f"€ {st.session_state.cassa_attuale:.2f}")
    col2.metric("Target Finale (Se Vincita)", f"€ {payout_finale:.2f}")
    col3.metric("ROI Potenziale", f"{roi:.1f}%")
    col4.metric("Progresso Obiettivo", f"{st.session_state.vincite} / {st.session_state.k_tot} W")

    st.markdown("---")

    # Controlli sullo stato del ciclo
    n_residui = st.session_state.n_tot - (st.session_state.vincite + st.session_state.perdite)
    k_residui = st.session_state.k_tot - st.session_state.vincite

    if k_residui <= 0:
        st.session_state.stato_ciclo = "Vinto"
    elif k_residui > n_residui:
        st.session_state.stato_ciclo = "Perso"

    if st.session_state.stato_ciclo == "In corso":
        # Form per la giocata corrente
        st.subheader(f"Next Step: Giocata del Turno {len(st.session_state.storico) + 1}")
        
        col_q, col_st = st.columns(2)
        with col_q:
            quota_corrente = st.number_input("Inserisci la quota REALE del prossimo evento:", value=st.session_state.iniziale_quota_media, step=0.05, min_value=1.01)
        
        # Calcolo dello stake dinamico
        prossimo_stake = calcola_stake(
            st.session_state.cassa_iniziale, 
            st.session_state.n_tot, 
            st.session_state.k_tot, 
            st.session_state.vincite, 
            st.session_state.perdite, 
            quota_corrente
        )
        
        with col_st:
            st.metric("Puntata Consigliata (Stake)", f"€ {prossimo_stake:.2f}")

        # Pulsanti di esito
        col_v, col_p = st.columns(2)
        with col_v:
            if st.button("✅ Segna come VINTO", use_container_width=True, type="primary"):
                profitto = prossimo_stake * (quota_corrente - 1)
                st.session_state.cassa_attuale += profitto
                st.session_state.vincite += 1
                st.session_state.storico.append({
                    "Step": len(st.session_state.storico) + 1,
                    "Quota": quota_corrente,
                    "Stake": prossimo_stake,
                    "Esito": "Vinto",
                    "Bilancio (€)": round(st.session_state.cassa_attuale, 2)
                })
                st.rerun()
                
        with col_p:
            if st.button("❌ Segna come PERSO", use_container_width=True):
                st.session_state.cassa_attuale -= prossimo_stake
                st.session_state.perdite += 1
                st.session_state.storico.append({
                    "Step": len(st.session_state.storico) + 1,
                    "Quota": quota_corrente,
                    "Stake": prossimo_stake,
                    "Esito": "Perso",
                    "Bilancio (€)": round(st.session_state.cassa_attuale, 2)
                })
                st.rerun()

    elif st.session_state.stato_ciclo == "Vinto":
        st.balloons()
        st.success(f"🎉 COMPLIMENTI! Ciclo chiuso in profitto. Cassa finale: € {st.session_state.cassa_attuale:.2f}")
    else:
        st.error(f"💥 CASSA PERSA! Non è più possibile raggiungere l'obiettivo di {st.session_state.k_tot} vincite. Cassa residua: € {st.session_state.cassa_attuale:.2f}")

    # --- TABELLA DELLO STORICO ---
    if st.session_state.storico:
        st.subheader("📋 Registro delle Giocate Effettuate")
        st.table(st.session_state.storico)
