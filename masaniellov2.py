import streamlit as st
import math

def combinazioni(n, k):
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)

def calcola_stake_variabile(cassa_attuale, n_tot, k_tot, v_correnti, p_correnti, quota_reale):
    """
    Calcola lo stake esatto bilanciato sulle quote reali.
    Versione Masaniello a panni variabili.
    """
    n_residui = n_tot - (v_correnti + p_correnti)
    k_residui = k_tot - v_correnti

    if k_residui <= 0 or k_residui > n_residui or n_residui <= 0:
        return 0.0

    # Combinazioni totali rimaste per vincere il ciclo
    comb_totali = sum(combinazioni(n_residui, i) for i in range(k_residui, n_residui + 1))
    # Combinazioni rimaste se l'evento corrente risulta vincente
    comb_se_vinco = sum(combinazioni(n_residui - 1, i) for i in range(k_residui - 1, n_residui))

    if comb_totali == 0:
        return 0.0

    # Formula pura del Masaniello Variabile
    frazione_cassa = comb_se_vinco / comb_totali
    stake = (cassa_attuale * frazione_cassa) / quota_reale
    
    return round(max(stake, 0.01), 2)

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="Masaniello Variabile", layout="wide", page_icon="📊")
st.title("📊 Masaniello a Quote Variabili Puro")
st.write("Questo algoritmo si bilancia dinamicamente in base alle quote reali inserite a ogni step.")

if 'inizializzato' not in st.session_state:
    st.session_state.inizializzato = False
    st.session_state.cassa_iniziale = 50.0
    st.session_state.cassa_attuale = 50.0
    st.session_state.n_tot = 10
    st.session_state.k_tot = 4
    st.session_state.vincite = 0
    st.session_state.perdite = 0
    st.session_state.storico = []
    st.session_state.stato_ciclo = "In corso"

with st.sidebar:
    st.header("⚙️ Configurazione")
    disabilitato = st.session_state.inizializzato
    
    input_budget = st.number_input("Cassa Totale (€)", value=50.0, step=5.0, disabled=disabilitato)
    input_n = st.number_input("Numero Eventi Totali (N)", value=10, step=1, min_value=1, disabled=disabilitato)
    input_k = st.number_input("Eventi richiesti (K)", value=4, step=1, min_value=1, max_value=input_n, disabled=disabilitato)
    
    if not st.session_state.inizializzato:
        if st.button("🚀 Avvia Ciclo Bilanciato", type="primary"):
            st.session_state.cassa_iniziale = input_budget
            st.session_state.cassa_attuale = input_budget
            st.session_state.n_tot = input_n
            st.session_state.k_tot = input_k
            st.session_state.inizializzato = True
            st.rerun()
    else:
        if st.button("🔄 Resetta Sistema", type="secondary"):
            st.session_state.inizializzato = False
            st.session_state.vincite = 0
            st.session_state.perdite = 0
            st.session_state.storico = []
            st.session_state.stato_ciclo = "In corso"
            st.rerun()

if not st.session_state.inizializzato:
    st.info("Imposta i parametri a sinistra e avvia il ciclo. Non serve preoccuparsi di indovinare una quota media precisa.")
else:
    # Parametri residui
    n_residui = st.session_state.n_tot - (st.session_state.vincite + st.session_state.perdite)
    k_residui = st.session_state.k_tot - st.session_state.vincite

    # Controllo chiusura ciclo dello stato precedente
    if k_residui <= 0:
        st.session_state.stato_ciclo = "Vinto"
    elif k_residui > n_residui:
        st.session_state.stato_ciclo = "Perso"

    # Visualizzazione KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("Cassa Attuale", f"€ {st.session_state.cassa_attuale:.2f}")
    col2.metric("Progresso Vincite", f"{st.session_state.vincite} / {st.session_state.k_tot} W")
    col3.metric("Eventi Rimanenti nel Ciclo", f"{n_residui} su {st.session_state.n_tot}")

    st.markdown("---")

    if st.session_state.stato_ciclo == "In corso":
        st.subheader(f"Turno Corrente: Giocata numero {len(st.session_state.storico) + 1}")
        
        # Qui inserisci la quota reale del match che hai davanti agli occhi sul bookmaker
        quota_reale = st.number_input("Quota REALE del prossimo evento:", value=1.50, step=0.05, min_value=1.01)
        
        # Calcolo dello stake usando la quota reale corrente
        prossimo_stake = calcola_stake_variabile(
            st.session_state.cassa_attuale,
            st.session_state.n_tot,
            st.session_state.k_tot,
            st.session_state.vincite,
            st.session_state.perdite,
            quota_reale
        )
        
        st.metric("Puntata da effettuare (Stake Bilanciato)", f"€ {prossimo_stake:.2f}")

        col_v, col_p = st.columns(2)
        with col_v:
            if st.button("✅ VINTO", use_container_width=True, type="primary"):
                profitto = prossimo_stake * (quota_reale - 1)
                st.session_state.cassa_attuale += profitto
                st.session_state.vincite += 1
                st.session_state.storico.append({
                    "Step": len(st.session_state.storico) + 1,
                    "Quota Giocata": quota_reale,
                    "Stake Applicato": prossimo_stake,
                    "Esito": "Vinto",
                    "Cassa (€)": round(st.session_state.cassa_attuale, 2)
                })
                st.rerun()
                
        with col_p:
            if st.button("❌ PERSO", use_container_width=True):
                st.session_state.cassa_attuale -= prossimo_stake
                st.session_state.perdite += 1
                st.session_state.storico.append({
                    "Step": len(st.session_state.storico) + 1,
                    "Quota Giocata": quota_reale,
                    "Stake Applicato": prossimo_stake,
                    "Esito": "Perso",
                    "Cassa (€)": round(st.session_state.cassa_attuale, 2)
                })
                st.rerun()

    elif st.session_state.stato_ciclo == "Vinto":
        st.balloons()
        vincita_netta = st.session_state.cassa_attuale - st.session_state.cassa_iniziale
        if vincita_netta > 0:
            st.success(f"🎉 Obiettivo raggiunto! Ciclo chiuso in ATTIVO. Cassa finale: € {st.session_state.cassa_attuale:.2f} (Profitto netto: +€ {vincita_netta:.2f})")
        else:
            st.warning(f"⚠️ Ciclo chiuso. Le quote reali inserite erano troppo basse rispetto alla struttura combinatoria per generare un profitto elevato, ma la cassa è stata difesa: € {st.session_state.cassa_attuale:.2f}")
    else:
        st.error(f"💥 Ciclo interrotto. Impossibile raggiungere {st.session_state.k_tot} vittorie. Cassa salvata: € {st.session_state.cassa_attuale:.2f}")

    if st.session_state.storico:
        st.subheader("📋 Registro delle Giocate")
        st.table(st.session_state.storico)
