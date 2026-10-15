import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
from pyzbar.pyzbar import decode
from operazioni import assegna_attrezzatura, restituisci_attrezzatura

st.set_page_config(page_title="Pigozzi Tech - Gestione Attrezzature", layout="wide")

st.title("🛠️ Pigozzi Tech S.R.L. - Gestione Attrezzature")

# Funzioni database
def ottieni_statistiche():
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM attrezzature')
    totali = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attrezzature WHERE stato = 'Disponibile'")
    disponibili = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attrezzature WHERE stato = 'Assegnata'")
    assegnate = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attrezzature WHERE stato = 'Danneggiata'")
    danneggiate = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attrezzature WHERE stato = 'Smarrita'")
    smarrite = cursor.fetchone()[0]
    conn.close()
    return totali, disponibili, assegnate, danneggiate, smarrite

def ottieni_liste_db():
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()
    cursor.execute('SELECT codice_identificativo, descrizione FROM attrezzature')
    attrezzature = cursor.fetchall()
    cursor.execute('SELECT id, nome, cognome FROM dipendenti')
    dipendenti = cursor.fetchall()
    conn.close()
    return attrezzature, dipendenti

def ottieni_storico_movimenti():
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.id, m.id_attrezzatura, d.nome || ' ' || d.cognome, m.tipo_operazione, m.cantiere_destinazione, m.data_ora
        FROM movimenti m
        JOIN dipendenti d ON m.id_dipendente = d.id
        ORDER BY m.id DESC
    ''')
    righe = cursor.fetchall()
    conn.close()
    return righe

# --- DASHBOARD METRICS ---
tot, disp, ass, dann, smar = ottieni_statistiche()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Totale", tot)
col2.metric("Disponibili", disp)
col3.metric("Assegnate", ass)
col4.metric("Danneggiate", dann)
col5.metric("Smarrite", smar)

st.divider()

# --- GESTIONE STATO / INDEX PER LA WEBCAM ---
attrezzature, dipendenti = ottieni_liste_db()
lista_eq = [f"{eq[0]} - {eq[1]}" for eq in attrezzature]
lista_dip = [f"{d[0]} - {d[1]} {d[2]}" for d in dipendenti]

# --- SEZIONE WEBCAM & OPERAZIONI ---
col_web, col_op = st.columns([1, 1])

with col_web:
    st.subheader("📷 Scansione QR con Webcam")
    camera_file = st.camera_input("Inquadra il QR code")
    
    codice_scansionato = None
    if camera_file is not None:
        try:
            immagine = Image.open(camera_file)
            risultati = decode(immagine)
            if risultati:
                codice_scansionato = risultati[0].data.decode('utf-8').strip()
                if codice_scansionato.upper().startswith("ID:"):
                    codice_scansionato = codice_scansionato[3:].strip()
                st.success(f"QR Riconosciuto: **{codice_scansionato}**")
            else:
                st.warning("Nessun QR code rilevato nello scatto.")
        except Exception as e:
            st.error(f"Errore nella decodifica: {e}")

with col_op:
    st.subheader("📦 Registrazione Movimento")
    
    # Seleziona automaticamente l'indice se è arrivato un codice dalla webcam
    indice_preozionato = 0
    if codice_scansionato:
        for idx, item in enumerate(lista_eq):
            if codice_scansionato.lower() in item.lower():
                indice_preozionato = idx
                break

    with st.form("form_movimenti"):
        sel_attrezzatura = st.selectbox("Seleziona Attrezzatura", lista_eq, index=indice_preozionato)
        sel_dipendente = st.selectbox("Seleziona Dipendente", lista_dip)
        cantiere = st.text_input("Cantiere / Ubicazione di destinazione")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted_consegna = st.form_submit_button("Registra Consegna 🚀", use_container_width=True)
        with col_btn2:
            submitted_restituzione = st.form_submit_button("Registra Restituzione 📥", use_container_width=True)

        if submitted_consegna:
            if not cantiere:
                st.error("Inserisci il cantiere di destinazione.")
            else:
                codice_eq = sel_attrezzatura.split(" - ")[0]
                id_dip = int(sel_dipendente.split(" - ")[0])
                successo = assegna_attrezzatura(codice_eq, id_dip, cantiere)
                if successo:
                    st.success(f"Attrezzatura {codice_eq} consegnata con successo!")
                    st.rerun()
                else:
                    st.error("Errore durante la consegna. Controlla lo stato dell'attrezzatura.")

        if submitted_restituzione:
            codice_eq = sel_attrezzatura.split(" - ")[0]
            successo = restituisci_attrezzatura(codice_eq)
            if successo:
                st.success(f"Attrezzatura {codice_eq} restituita in magazzino!")
                st.rerun()
            else:
                st.error("Errore durante la restituzione.")

st.divider()

# --- STORICO MOVIMENTI ---
st.subheader("📜 Storico Movimenti Completo")
storico = ottieni_storico_movimenti()

if storico:
    df_storico = pd.DataFrame(storico, columns=["ID", "Attrezzatura", "Dipendente", "Operazione", "Cantiere", "Data/Ora"])
    st.dataframe(df_storico, use_container_width=True)
else:
    st.write("Nessun movimento registrato finora.")