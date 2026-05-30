import streamlit as st
import math

# --- MOTORE MATEMATICO ---

def calcola_target_teorico(cassa, n_tot, k_tot, q_media):
    """Calcola il target teorico iniziale usando la matrice delle probabilità (Metodo BigStake)"""
    # Matrice U[n][k]
    U = [[0.0 for _ in range(k_tot + 1)] for _ in range(n_tot + 1)]
    
    # Se k=0 (zero vittorie richieste), il target è già raggiunto
    for i in range(n_tot + 1):
        U[i][0] = 1.0
        
    for n in range(1, n_tot + 1):
        for k in range(1, k_tot + 1):
            if k > n:
                U[n][k] = 0.0
            else:
                U[n][k] = (U[n-1][k-1] + U[n-1][k] * (q_media - 1)) / q_media
                
    rendimento = U[n_tot][k_tot]
    if rendimento == 0:
        return 0
    return cassa / rendimento

def calcola_stake_dinamico(cassa_attuale, n_tot, k_tot, v_correnti, p_correnti, quota_reale):
    """
    Formula Infallibile a Panni Variabili.
    Bilancia perfettamente la cassa attuale su tutti i percorsi rimanenti.
    """
    n_res = n_tot - (v_correnti + p_correnti)
    k_res = k_tot - v_correnti

    if k_res <= 0 or k_res > n_res:
        return 0.0

    # Combinazioni esatte (se vinco il prossimo e poi arrivo al target esatto)
    c_esatte = math.comb(n_res - 1, k_res - 1)
    
    # Combinazioni se perdo il prossimo ma riesco comunque a chiudere il ciclo
    c_perdita = sum(math.comb(n_res - 1, i) for i in range(k_res, n_res))

    denominatore = (quota_reale * c_perdita) + c_esatte

    if denominatore == 0:
        return 0.0

    stake = cassa_attuale * (c_esatte / denominatore)
    return round(stake, 2)


# --- INTERFACCIA STREAMLIT ---

st.set_page_config(page_title="Masaniello Pro", layout="wide", page_icon="📊")
st.title("📊 Masaniello (Motore Dinamico)")

if 'inizializzato' not in st.session_state:
    st.session_state.inizializzato = False
    st.session_state.cassa_iniziale = 50.0
    st.session_state.cassa_attuale = 50.0
    st.session_state.n_tot = 10
    st.session_state.k_tot = 4
    st.session_state.quota_media = 1.50
    st.session_state.target_teorico = 0.0
    st.session_state.vincite = 0
    st.session_state.perdite = 0
    st.session_state.storico = []
    st.session_state.stato_ciclo = "In corso"

with st.sidebar:
    st.header("⚙️ Impostazioni")
    disabilitato = st.session_state.inizializzato
    
    input_budget = st.number_input("Cassa Totale (€)", value=50.0, step=5.0, disabled=disabilitato)
    input_n = st.number_input("Numero Eventi Totali (N)", value=10, step=1, min_value=1, disabled=disabilitato)
    input_k = st.number_input("Eventi richiesti (K)", value=4, step=1, min_value=1, max_value=input_n, disabled=disabilitato)
    input_q = st.number_input("Quota Media Stimata", value=1.50, step=0.05, min_value=1.01, disabled=disabilitato)
    
    if not st.session_state.inizializzato:
        if st.button("🚀 Avvia Ciclo", type="primary"):
            st.session_state.cassa_iniziale = input_budget
            st.session_state.cassa_attuale = input_budget
            st.session_state.n_tot = input_n
            st.session_state.k_tot = input_k
            st.session_state.quota_media = input_q
            st.session_state.target_teorico = calcola_target_teorico(input_budget, input_n, input_k, input_q)
            st.session_state.inizializzato = True
            st.rerun()
    else:
        if st.button("🔄 Resetta e Riavvia", type="secondary"):
            st.session_state.inizializzato = False
            st.session_state.vincite = 0
            st.session_state.perdite = 0
            st.session_state.storico = []
            st.session_state.stato_ciclo = "In corso"
            st.rerun()

if not st.session_state.inizializzato:
    st.info("Imposta i parametri a sinistra e clicca su 'Avvia Ciclo'.")
else:
    n_residui = st.session_state.n_tot - (st.session_state.vincite + st.session_state.perdite)
    k_residui = st.session_state.k_tot - st.session_state.vincite

    if k_residui <= 0:
        st.session_state.stato_ciclo = "Vinto"
    elif k_residui > n_residui:
        st.session_state.stato_ciclo = "Perso"

    col1, col2, col3 = st.columns(3)
    col1.metric("Cassa Attuale", f"€ {st.session_state.cassa_attuale:.2f}")
    col2.metric("Target Teorico Iniziale", f"€ {st.session_state.target_teorico:.2f}")
    col3.metric("Progresso Vincite", f"{st.session_state.vincite} / {st.session_state.k_tot} W")

    st.markdown("---")

    if st.session_state.stato_ciclo == "In corso":
        st.subheader(f"Giocata {len(st.session_state.storico) + 1}")
        
        quota_reale = st.number_input("Quota REALE da giocare:", value=st.session_state.quota_media, step=0.05, min_value=1.01)
        
        prossimo_stake = calcola_stake_dinamico(
            st.session_state.cassa_attuale,
            st.session_state.n_tot,
            st.session_state.k_tot,
            st.session_state.vincite,
            st.session_state.perdite,
            quota_reale
        )
        
        st.metric("Puntata Esatta (Stake)", f"€ {prossimo_stake:.2f}")

        col_v, col_p = st.columns(2)
        with col_v:
            if st.button("✅ Vinto", use_container_width=True, type="primary"):
                profitto = prossimo_stake * (quota_reale - 1)
                st.session_state.cassa_attuale += profitto
                st.session_state.vincite += 1
                st.session_state.storico.append({
                    "Step": len(st.session_state.storico) + 1,
                    "Quota": quota_reale,
                    "Stake": prossimo_stake,
                    "Esito": "Vinto",
                    "Cassa": round(st.session_state.cassa_attuale, 2)
                })
                st.rerun()
                
        with col_p:
            if st.button("❌ Perso", use_container_width=True):
                st.session_state.cassa_attuale -= prossimo_stake
                st.session_state.perdite += 1
                st.session_state.storico.append({
                    "Step": len(st.session_state.storico) + 1,
                    "Quota": quota_reale,
                    "Stake": prossimo_stake,
                    "Esito": "Perso",
                    "Cassa": round(st.session_state.cassa_attuale, 2)
                })
                st.rerun()

    elif st.session_state.stato_ciclo == "Vinto":
        st.balloons()
        st.success(f"🎉 Ciclo Vinto! Cassa finale: € {st.session_state.cassa_attuale:.2f}")
    else:
        st.error(f"💥 Ciclo Perso. Cassa rimanente: € {st.session_state.cassa_attuale:.2f}")

    if st.session_state.storico:
        st.table(st.session_state.storico)
