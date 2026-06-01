"""
ai_assistant.py

Modulo separato per integrare una valutazione AI nella app Streamlit
"Trading in opzioni - AI Lab".

Questo file NON prende decisioni operative di trading.
Produce una checklist ragionata sulla base dei dati calcolati dall'app.
"""

import json
from typing import Any, Dict

import streamlit as st
from openai import OpenAI


def _get_openai_client() -> OpenAI:
    """
    Crea il client OpenAI leggendo la chiave da Streamlit secrets.

    Atteso in .streamlit/secrets.toml:

    OPENAI_API_KEY = "la-tua-chiave"
    """

    api_key = st.secrets.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY non trovata. "
            "Aggiungila nel file .streamlit/secrets.toml"
        )

    return OpenAI(api_key=api_key)


def valuta_strategia_prudente_ai(dati_ai: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valuta la Strategia Prudente - Analisi Multi-Rischio.

    Input:
        dati_ai: dizionario generato da option_app_v4_ai.py

    Output:
        dizionario con esito, rischio, punti positivi, criticità e checklist.
    """

    client = _get_openai_client()

    system_prompt = """
Sei un assistente di analisi del rischio per strategie in opzioni.

Regole fondamentali:
- Non fornire consulenza finanziaria.
- Non dire mai "compra", "vendi", "apri la posizione" o "non aprire la posizione".
- Non dare raccomandazioni operative definitive.
- Valuta solo la coerenza della strategia rispetto ai dati forniti.
- Evidenzia rischi, punti positivi e controlli da fare prima di una decisione autonoma dell'utente.
- Rispondi sempre in italiano.
- Restituisci esclusivamente JSON valido, senza testo prima o dopo.
"""

    user_prompt = f"""
Analizza questa strategia di opzioni di tipo Bull Put Spread prudente.

Dati calcolati dall'app:
{json.dumps(dati_ai, indent=2, ensure_ascii=False)}

Restituisci un JSON con questa struttura esatta:

{{
  "esito": "OK | DA_VALUTARE | CRITICO",
  "livello_rischio": "BASSO | MEDIO | ALTO | MOLTO_ALTO",
  "sintesi": "breve sintesi della situazione",
  "punti_positivi": [
    "punto positivo 1",
    "punto positivo 2"
  ],
  "criticita": [
    "criticità 1",
    "criticità 2"
  ],
  "controlli_prima_di_valutare": [
    "controllo 1",
    "controllo 2"
  ],
  "nota_finale": "nota finale prudente, senza raccomandazioni operative"
}}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
    )

    testo = response.output_text.strip()

    try:
        return json.loads(testo)
    except json.JSONDecodeError:
        return {
            "esito": "DA_VALUTARE",
            "livello_rischio": "NON_DETERMINATO",
            "sintesi": testo,
            "punti_positivi": [],
            "criticita": [
                "La risposta AI non era in formato JSON valido."
            ],
            "controlli_prima_di_valutare": [
                "Verificare manualmente i dati della strategia."
            ],
            "nota_finale": (
                "La valutazione automatica non è stata interpretata correttamente. "
                "Usare solo come supporto e non come decisione operativa."
            ),
        }
