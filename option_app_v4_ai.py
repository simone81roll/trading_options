import streamlit as st
import numpy as np
import pandas as pd


# -----------------------------------------------------------------------------
# Stato sessione
# -----------------------------------------------------------------------------
def inizializza_stato():
    """Inizializza lo stato della sessione, se non è già presente."""
    if "rendimento_atteso" not in st.session_state:
        st.session_state["rendimento_atteso"] = 10.0


def update_from_slider():
    """Aggiorna lo stato della sessione quando lo slider cambia."""
    st.session_state["rendimento_atteso"] = st.session_state.rendimento_slider

    if st.session_state["rendimento_atteso"] > 100.0:
        st.session_state["rendimento_atteso"] = 100.0


def update_from_number_input():
    """Aggiorna lo stato della sessione quando l'input numerico cambia."""
    st.session_state["rendimento_atteso"] = st.session_state.rendimento_input

    if st.session_state["rendimento_atteso"] < 1.0:
        st.session_state["rendimento_atteso"] = 1.0
    elif st.session_state["rendimento_atteso"] > 100.0:
        st.session_state["rendimento_atteso"] = 100.0


# -----------------------------------------------------------------------------
# Funzioni di supporto
# -----------------------------------------------------------------------------
def get_risk_indicator(risk_point):
    """Restituisce un colore e un'etichetta di rischio in base al punteggio."""
    if risk_point > 270:
        return "#F90000", "Molto Alto"
    elif risk_point >= 170:
        return "#F99300", "Alto"
    elif risk_point >= 70:
        return "#00f900", "Medio"
    else:
        return "#008000", "Basso"


def get_distance_color(diff_percent):
    """Restituisce un'emoji per la distanza percentuale dallo strike."""
    if diff_percent < 4.50:
        return ""
    elif diff_percent <= 10.0:
        return ""
    else:
        return ""


def valuta_regole_strategia_prudente(dati_ai):
    """
    Valuta la Strategia Prudente secondo regole tecniche di base.

    Questa funzione non usa AI: serve come filtro deterministico prima di passare
    eventualmente i dati a un modello AI.
    """
    alert = []

    credito_netto = dati_ai.get("credito_netto_usd", 0)
    rischio_unitario = dati_ai.get("rischio_unitario_usd", 0)
    larghezza_spread = dati_ai.get("larghezza_spread", 0)
    prezzo_sottostante = dati_ai.get("prezzo_sottostante", 0)
    strike_venduto = dati_ai.get("strike_venduto", 0)

    rapporto_credito_rischio = credito_netto / rischio_unitario if rischio_unitario else 0
    distanza_strike = (
        ((prezzo_sottostante - strike_venduto) / prezzo_sottostante) * 100
        if prezzo_sottostante
        else 0
    )

    if credito_netto <= 0:
        alert.append("Credito netto nullo o negativo: la strategia non genera incasso iniziale.")

    if rapporto_credito_rischio < 0.03:
        alert.append("Credito netto molto basso rispetto al rischio unitario dello spread.")

    if distanza_strike < 5:
        alert.append("Strike venduto vicino al prezzo attuale rispetto alla logica prudente.")

    if larghezza_spread > 150:
        alert.append("Spread molto largo: rischio unitario elevato.")

    soluzione_50 = dati_ai.get("soluzione_rischio_50", {})
    soluzione_75 = dati_ai.get("soluzione_rischio_75", {})

    if soluzione_50.get("lotti_consigliati", 0) == 0:
        alert.append("Con rischio massimo 50% non risulta apribile alcun lotto.")

    if soluzione_75.get("lotti_consigliati", 0) == 0:
        alert.append("Con rischio massimo 75% non risulta apribile alcun lotto.")

    return alert


# -----------------------------------------------------------------------------
# Sezione Strategia Prudente - Analisi Multi-Rischio
# -----------------------------------------------------------------------------
def assistente_bull_put_multi_rischio():
    """
    Mostra la sezione Strategia Prudente e restituisce i dati da passare all'AI.
    """
    with st.container(border=True):
        st.subheader("🛡️ Strategia Prudente: Analisi Multi-Rischio")
        st.markdown(
            "Questa analisi calcola i lotti basandosi su uno "
            "**Strike consigliato al -5%** dal prezzo attuale."
        )

        # --- 1. INPUT DI BASE ---
        col_base1, col_base2, col_base3 = st.columns(3)

        with col_base1:
            prezzo_sottostante = st.number_input("Prezzo Attuale US500", value=6950.0, step=1.0)
            cambio_eurusd = st.number_input("Cambio EUR/USD", value=1.08, step=0.01)

        with col_base2:
            capitale_totale = st.number_input("Capitale Totale (€)", value=1000.0, step=100.0)

        with col_base3:
            distanza_strike_pct = (
                st.slider("Distanza Strike Consigliata (%)", 1.0, 10.0, 5.0) / 100
            )

        # --- 2. CONFIGURAZIONE DELLO SPREAD ---
        st.divider()
        col_spr1, col_spr2 = st.columns([2, 1])

        with col_spr1:
            strike_v = round((prezzo_sottostante * (1 - distanza_strike_pct)) / 5) * 5
            larghezza_spread = st.select_slider(
                "Larghezza Spread (Punti di distanza tra le due Put)",
                options=[25, 50, 75, 100, 150, 200],
                value=100,
                help=(
                    "100 punti è lo standard. Più è stretto, meno capitale blocchi "
                    "ma la protezione costa di più."
                ),
            )
            strike_p = strike_v - larghezza_spread
            st.info(f"**Configurazione:** Vendi Put **{strike_v}** | Compra Put **{strike_p}**")

        with col_spr2:
            p_venduta = st.number_input("Premio Put Venduta ($)", value=19.0)
            p_prot = st.number_input("Costo Put Prot. ($)", value=15.0)

        # --- 3. CALCOLI TECNICI ---
        credito_netto_usd = p_venduta - p_prot
        rischio_unit_usd = larghezza_spread - credito_netto_usd

        if rischio_unit_usd <= 0:
            st.error("Errore: il costo della protezione supera il premio incassato. Controlla i prezzi.")
            return {
                "tipo_analisi": "Strategia Prudente - Analisi Multi-Rischio",
                "errore": "Rischio unitario non valido",
                "prezzo_sottostante": prezzo_sottostante,
                "cambio_eurusd": cambio_eurusd,
                "capitale_totale_eur": capitale_totale,
                "distanza_strike_percentuale": distanza_strike_pct * 100,
                "strike_venduto": strike_v,
                "strike_comprato_protezione": strike_p,
                "larghezza_spread": larghezza_spread,
                "premio_put_venduta_usd": p_venduta,
                "costo_put_protezione_usd": p_prot,
                "credito_netto_usd": credito_netto_usd,
                "rischio_unitario_usd": rischio_unit_usd,
            }

        st.divider()

        # --- 4. CONFRONTO SOLUZIONI ---
        sol_50, sol_75 = st.columns(2)

        with sol_50:
            st.markdown("### Rischio Max 50%")
            limite_50_eur = capitale_totale * 0.50
            lotti_50 = int((limite_50_eur * cambio_eurusd) / rischio_unit_usd)
            guadagno_50_eur = (credito_netto_usd * lotti_50) / cambio_eurusd
            rischio_effettivo_50 = (rischio_unit_usd * lotti_50) / cambio_eurusd

            st.metric("Lotti Consigliati", lotti_50)
            st.metric("Vincita Max (€)", f"€ {guadagno_50_eur:.2f}")
            st.caption(f"Margine/Rischio: € {rischio_effettivo_50:.2f}")

        with sol_75:
            st.markdown("### Rischio Max 75%")
            limite_75_eur = capitale_totale * 0.75
            lotti_75 = int((limite_75_eur * cambio_eurusd) / rischio_unit_usd)
            guadagno_75_eur = (credito_netto_usd * lotti_75) / cambio_eurusd
            rischio_effettivo_75 = (rischio_unit_usd * lotti_75) / cambio_eurusd

            st.metric("Lotti Consigliati", lotti_75)
            st.metric("Vincita Max (€)", f"€ {guadagno_75_eur:.2f}")
            st.caption(f"Margine/Rischio: € {rischio_effettivo_75:.2f}")

        dati_strategia_prudente = {
            "tipo_analisi": "Strategia Prudente - Analisi Multi-Rischio",
            "prezzo_sottostante": prezzo_sottostante,
            "cambio_eurusd": cambio_eurusd,
            "capitale_totale_eur": capitale_totale,
            "distanza_strike_percentuale": distanza_strike_pct * 100,
            "strike_venduto": strike_v,
            "strike_comprato_protezione": strike_p,
            "larghezza_spread": larghezza_spread,
            "premio_put_venduta_usd": p_venduta,
            "costo_put_protezione_usd": p_prot,
            "credito_netto_usd": credito_netto_usd,
            "rischio_unitario_usd": rischio_unit_usd,
            "rapporto_credito_rischio": (
                credito_netto_usd / rischio_unit_usd if rischio_unit_usd else 0
            ),
            "soluzione_rischio_50": {
                "limite_rischio_eur": limite_50_eur,
                "lotti_consigliati": lotti_50,
                "guadagno_massimo_eur": guadagno_50_eur,
                "rischio_effettivo_eur": rischio_effettivo_50,
            },
            "soluzione_rischio_75": {
                "limite_rischio_eur": limite_75_eur,
                "lotti_consigliati": lotti_75,
                "guadagno_massimo_eur": guadagno_75_eur,
                "rischio_effettivo_eur": rischio_effettivo_75,
            },
        }

        return dati_strategia_prudente


# -----------------------------------------------------------------------------
# App principale
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide")
st.title(":robot_face: Trading in opzioni - AI Lab")

inizializza_stato()

# Questa è la sezione che dovrà alimentare l'AI.
dati_ai = assistente_bull_put_multi_rischio()

if dati_ai:
    alert_ai = valuta_regole_strategia_prudente(dati_ai)

    st.divider()

    with st.container(border=True):
        st.subheader("🧭 Controllo regole base - Strategia Prudente")

        if dati_ai.get("errore"):
            st.error(dati_ai["errore"])
        elif alert_ai:
            st.warning("Sono stati rilevati alcuni punti da verificare prima di valutare l'ingresso:")
            for alert in alert_ai:
                st.write(f"- {alert}")
        else:
            st.success("La strategia non presenta alert evidenti secondo le regole base impostate.")

    with st.expander("Dati letti dall'AI - Strategia Prudente"):
        st.json(dati_ai)


# -----------------------------------------------------------------------------
# Sezioni originali della V3 mantenute per confronto/manualità
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Calcolo dello Strike Price")

    sott, strike, var = st.columns([0.35, 0.35, 0.30])

    asset_price = sott.number_input("Prezzo Sottostante", min_value=0.0, value=6000.0, step=1.0, key="price")
    target_price = strike.number_input("Strike Price", min_value=0.0, value=6000.0, step=1.0, key="strike")

    diff_value = asset_price - target_price

    try:
        diff_percent = (diff_value / asset_price) * 100
    except ZeroDivisionError:
        diff_percent = 0.0

    emoji_distanza = get_distance_color(diff_percent)

    var.metric(
        label=f"Variazione dallo Strike {emoji_distanza}",
        value=f"{diff_percent:.2f} %",
        delta=f"Distanza Assoluta: {diff_value:.2f}",
    )


with st.container(border=True):
    st.subheader("Analisi")

    col3, col4, col5, col6 = st.columns([0.20, 0.35, 0.15, 0.30])

    with col3:
        capitale = st.number_input("Capitale Iniziale (€)", min_value=100, value=1000, step=100)

    with col4:
        st.slider(
            "Rendimento Atteso (%)",
            min_value=1.0,
            max_value=100.0,
            value=st.session_state.rendimento_atteso,
            step=0.1,
            format="%.2f%%",
            key="rendimento_slider",
            on_change=update_from_slider,
        )

    with col5:
        st.number_input(
            "(%)",
            min_value=1.0,
            max_value=100.0,
            value=st.session_state.rendimento_atteso,
            step=0.1,
            key="rendimento_input",
            on_change=update_from_number_input,
            format="%.2f",
            label_visibility="hidden",
        )

    progress_value = st.session_state.rendimento_atteso / 100.0
    premio = progress_value * capitale

    col6.metric(
        label="Premio Potenziale",
        value=f"€ {premio:.2f}",
    )

    risk, sic, color = st.columns([0.35, 0.35, 0.30])

    sicure_price = sic.number_input("Prezzo di Sicurezza", min_value=0.0, value=220.0, step=0.05)
    risk_point = risk.number_input("Punteggio di Rischio", min_value=1, max_value=400, value=60, step=1)

    prezzo_indicativo = (sicure_price * progress_value * 50 / risk_point) if risk_point != 0 else 0
    number_contract = (premio / prezzo_indicativo) if prezzo_indicativo != 0 else 0

    color_risk, label_risk = get_risk_indicator(risk_point)

    color.markdown(
        f"""
        <div style="background-color:{color_risk}; padding:10px; border-radius:8px; text-align:center; color:white; font-weight:bold;">
            Rischio: {label_risk} (Punteggio: {risk_point})
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.container(border=True):
    st.subheader("Ingresso a mercato")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Prezzo Indicativo per Contratto",
            value=f"€ {prezzo_indicativo:.2f}",
            help="Il prezzo stimato a cui aprire la posizione per raggiungere il rendimento atteso.",
        )

    with col2:
        st.metric(
            label="Numero Massimo Contratti",
            value=f"{number_contract:.2f}",
            help="Quanti contratti puoi acquistare con il premio calcolato.",
        )
