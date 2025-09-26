import pandas as pd
import numpy as np
import streamlit as st

def get_custom_color(diff_percent):
    """Restituisce il codice colore in base alla logica di soglia."""
    if diff_percent > 10.0:
        return "#FFD700"  # GOLD
    elif diff_percent >= 4.50:
        return "#008000"  # GREEN (verde scuro)
    else:
        return "#FF0000"  # RED

st.title(":chart_with_upwards_trend: :blue[Trading in opzioni]")

with st.expander("**Calcolo dello Strike Price**", expanded=True):
	col1, col2 = st.columns(2)
	asset_price = col1.number_input(
		"Prezzo del sottostante",
		value = 6000,
		key = "price"
		)
	target_price = col2.number_input(
		"Strike Price",
		value = 6000,
		key = "strike"
		)
	diff_value = asset_price - target_price

	#calcolo della percentuale con con verifica divisione per 0

	try:
		diff_percent = (diff_value/asset_price) * 100
	except ZeroDivisionError:
		diff_percent = 0.0

	custom_color = get_custom_color(diff_percent)


	with col1.container(border=True):
		label_text = "Variazione Percentuale"
		value_text = f"{diff_percent:.2f} %"

		# --- RIMOZIONE DEI NEWLINE E USO DI SINGOLE VIRGOLETTE PER CSS ---
		# Manteniamo tutto su una singola riga o concatenato per evitare errori di spaziatura.
		html_code_compact = (
		    f"<p style='font-size: 14px; color: grey; margin-bottom: 0px;'>{label_text}</p>"
		    f"<p style='font-size: 28px; font-weight: bold; color: {custom_color}; margin-top: 0px;'>"
		    f"  {value_text}"
		    f"</p>"
		)
		st.write(html_code_compact, unsafe_allow_html=True)

	with col2.container(border=True):
		value_text = f"{diff_value}"
		label_text = "Distanza dallo strike price"

		html_code_compact = (
		    f"<p style='font-size: 14px; color: grey; margin-bottom: 0px;'>{label_text}</p>"
		    f"<p style='font-size: 28px; color: black; margin-top: 0px;'>"
		    f"  {value_text}"
		    f"</p>"
		)

		# --- INIEZIONE CON ST.WRITE ---
		# Usiamo st.write come alternativa a st.markdown
		st.write(html_code_compact, unsafe_allow_html=True)


with st.expander("**Analisi per l'ingresso a mercato**", expanded=True):
	col1, col2 = st.columns(2, vertical_alignment="top")
	capitale = col1.number_input(
	    "Capitale iniziale",
	    min_value=100,
	    max_value=100000,
	    value=1000,
	    step=1
	    )

	valore_selezionato = col2.number_input(
	    "Rendimento atteso (%)",
	    min_value=1.0,
	    max_value=100.0,
	    value=10.0,  # Valore di default
	    step=0.01,
	    format="%.2f",
	    key='2'
	)
	progress_value = valore_selezionato / 100.0

	st.progress(
		progress_value,
		text=f"Rendimento atteso: **{valore_selezionato:.2f}%**"
	)

	premio = (valore_selezionato / 100 * capitale)
	#valore_selezionato
	st.info(f"Premio potenziale: **{premio}** :heavy_dollar_sign:")

	col1, col2,col3 = st.columns([0.5,0.35,0.15])
	sicure_price = col1.number_input(
	    "Prezzo di sicurezza",
	    min_value=1.0,
	    max_value=1000.0,
	    value=220.0,
	    step=0.05
	    )

	risk_point = col2.number_input(
	    "Punteggio di rischio",
	    min_value=1,
	    max_value=400,
	    value=60,
	    step=1
	    )
	
	def get_color_risk(risk_point):
	    """Restituisce il codice colore in base alla logica di soglia."""
	    if risk_point > 270:
	        return "#F90000"  # GOLD
	    elif risk_point >= 170:
	        return "#F99300"
	    elif risk_point >= 70:
	        return "#00f900"  # GREEN (verde scuro)	    
	    else:
	        return "#008000"  # RED

	color_risk_custom = get_color_risk(risk_point)
	color_risk = col3.color_picker("Pick A Color", color_risk_custom, label_visibility="hidden")

	prezzo_indicativo = sicure_price*progress_value*50/risk_point

	text_price = f"{prezzo_indicativo:.2f}"

	label_text = "Prezzo indicativo di apertura della posizione"

	col1, col2 =st.columns(2)

	with col1.container(border=True):
		text_price = f"{prezzo_indicativo:.2f}"
		label_text = "Prezzo indicativo di apertura della posizione"
		html_code_compact = (
		    f"<p style='font-size: 14px; color: #5A5A5A; margin-bottom: 0px;'>{label_text}</p>"
		    f"<p style='font-size: 28px; color: black; margin-top: 0px;'>"
		    f"  {text_price}"
		    f"</p>"
		)

		st.write(html_code_compact, unsafe_allow_html=True)

	number_contract = premio / prezzo_indicativo

	with col2.container(border=True):
		text_price = f"{number_contract:.2f}"
		label_text = "Numeri massimo di contratti"
		html_code_compact = (
		    f"<p style='font-size: 14px; color: #5A5A5A; margin-bottom: 0px;'>{label_text}</p>"
		    f"<p style='font-size: 28px; color: black; margin-top: 0px;'>"
		    f"  {text_price}"
		    f"</p>"
		)

		st.write(html_code_compact, unsafe_allow_html=True)
