import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
from pyzbar.pyzbar import decode
from operazioni import (
    inizializza_db_azzzerato, 
    inserisci_articolo_iniziale, 
    assegna_attrezzatura, 
    restituisci_attrezzatura, 
    segnala_danneggiata_o_persa
)

st.set_page_config(page_title="Pigozzi Tech - Gestione Attrezzature", layout="wide")
st.title("🛠️ Pigozzi Tech S.R.L. - Gestione Attrezzature")

# Controlla se il database esiste già, altrimenti lo inizializza da zero
try:
    conn_chk = sqlite3.connect('pigozzi_tech.db')
    c_chk = conn_chk.cursor()
    c_chk.execute("SELECT COUNT(*) FROM attrezzature")
    esiste = c_chk.fetchone()[0]
    conn_chk.close()
except:
    esiste = 0

if esiste == 0:
    inizializza_db_azzzerato()
    
    # Popolamento con i 20 articoli da EQ-001 a EQ-020
    articoli_iniziali = [
        ("EQ-001", "Trapano a Percussione", 10),
        ("EQ-002", "Smerigliatrice Angolare", 8),
        ("EQ-003", "Saldatrice Inverter", 4),
        ("EQ-004", "Martello Demolitore", 5),
        ("EQ-005", "Avvitatore a Impulsi", 12),
        ("EQ-006", "Seghetto Alternativo", 6),
        ("EQ-007", "Laser di Livellamento", 3),
        ("EQ-008", "Troncatrice per Metalli", 4),
        ("EQ-009", "Pistola Termica", 10),
        ("EQ-010", "Flessibile Grande", 7),
        ("EQ-011", "Generatore di Corrente", 2),
        ("EQ-012", "Idropulitrice Alta Pressione", 5),
        ("EQ-013", "Murocotto / Miscelatore", 4),
        ("EQ-014", "Trabattello in Alluminio", 3),
        ("EQ-015", "Scala Telescopica", 8),
        ("EQ-016", "Faro LED Cantiere", 15),
        ("EQ-017", "Cavo Prolunga 50m", 20),
        ("EQ-018", "Compressore d'Aria 50L", 3),
        ("EQ-019", "Braccio Gru / Paranco", 2),
        ("EQ-020", "Kit DPI Completi", 25)
    ]

    for codice, desc, qta in articoli_iniziali:
        inserisci_articolo_iniziale(codice, desc, qta)
    
    # Dipendenti di test
    conn_dip = sqlite3.connect('pigozzi_tech.db')
    c_dip = conn_dip.cursor()
    c_dip.execute("INSERT INTO dipendenti (nome, cognome) VALUES ('Mario', 'Rossi')")
    c_dip.execute("INSERT INTO dipendenti (nome, cognome) VALUES ('Luigi', 'Verdi')")
    c_dip.execute("INSERT INTO dipendenti (nome, cognome) VALUES ('Giovanni', 'Bianchi')")
    conn_dip.commit()
    conn_dip.close()

# Funzioni di recupero dati
def ottieni_metriche(codice_articolo=None):
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()
    if codice_articolo and codice_articolo != "Tutti":
        cursor.execute('''
            SELECT g.totale, g.disponibili, g.assegnate, g.danneggiate, g.smarrite 
            FROM giacenze g 
            JOIN attrezzature a ON g.id_attrezzatura = a.id 
            WHERE a.codice_identificativo = ?
        ''', (codice_articolo,))
    else:
        cursor.execute('SELECT SUM(totale), SUM(disponibili), SUM(assegnate), SUM(danneggiate), SUM(smarrite) FROM giacenze')
    
    res = cursor.fetchone()
    conn.close()
    return [r if r is not None else 0 for r in res]

def ottieni_liste_db():
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()
    cursor.execute('SELECT codice_identificativo, descrizione FROM attrezzature')
    attrezzature = cursor.fetchall()
    cursor.execute('SELECT id, nome, cognome FROM dipendenti')
    dipendenti = cursor.fetchall()
    conn.close()
    return attrezzature, dipendenti

def ottieni_storico_per_articolo(codice_articolo=None):
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()
    query = '''
        SELECT m.id, a.codice_identificativo || ' - ' || a.descrizione, COALESCE(d.nome || ' ' || d.cognome, 'Magazzino/Sistema'), 
               m.tipo_operazione, m.quantita, m.cantiere_destinazione, m.data_ora
        FROM movimenti m
        JOIN attrezzature a ON m.id_attrezzatura = a.id
        LEFT JOIN dipendenti d ON m.id_dipendente = d.id
    '''
    if codice_articolo and codice_articolo != "Tutti":
        query += " WHERE a.codice_identificativo = ?"
        query += " ORDER BY m.id DESC"
        cursor.execute(query, (codice_articolo,))
    else:
        query += " ORDER BY m.id DESC"
        cursor.execute(query)
    
    righe = cursor.fetchall()
    conn.close()
    return righe

attrezzature, dipendenti = ottieni_liste_db()
lista_eq = [f"{eq[0]} - {eq[1]}" for eq in attrezzature]
lista_dip = [f"{d[0]} - {d[1]} {d[2]}" for d in dipendenti]

# --- SEZIONE WEBCAM & SELEZIONE ARTICOLO ---
col_web, col_op = st.columns([1, 1])

with col_web:
    st.subheader("📷 Scansione QR / Fotocamera")
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
                st.warning("Nessun QR code rilevato.")
        except Exception as e:
            st.error(f"Errore lettura: {e}")

with col_op:
    st.subheader("📦 Registrazione Movimento")
    
    indice_preozionato = 0
    if codice_scansionato:
        for idx, item in enumerate(lista_eq):
            if codice_scansionato.lower() in item.lower():
                indice_preozionato = idx
                break

    with st.form("form_operazioni"):
        sel_attrezzatura = st.selectbox("Seleziona Articolo", lista_eq, index=indice_preozionato)
        sel_dipendente = st.selectbox("Seleziona Dipendente", lista_dip)
        quantita = st.number_input("Quantità", min_value=1, max_value=50, value=1, step=1)
        cantiere = st.text_input("Cantiere di destinazione")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            btn_consegna = st.form_submit_button("Consegna 🚀")
        with c2:
            btn_restituzione = st.form_submit_button("Restituisci 📥")
        with c3:
            btn_danno = st.form_submit_button("Danneggiato ⚠️")
        with c4:
            btn_perso = st.form_submit_button("Smarrito ❌")

        codice_eq = sel_attrezzatura.split(" - ")[0]
        id_dip = int(sel_dipendente.split(" - ")[0])

        if btn_consegna:
            if not cantiere:
                st.error("Inserisci il cantiere.")
            else:
                ok, msg = assegna_attrezzatura(codice_eq, id_dip, cantiere, quantita)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        if btn_restituzione:
            ok, msg = restituisci_attrezzatura(codice_eq, quantita)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

        if btn_danno:
            ok, msg = segnala_danneggiata_o_persa(codice_eq, quantita, "Danneggiata")
            if ok:
                st.warning(msg)
                st.rerun()
            else:
                st.error(msg)

        if btn_perso:
            ok, msg = segnala_danneggiata_o_persa(codice_eq, quantita, "Smarrita")
            if ok:
                st.error(msg)
                st.rerun()
            else:
                st.error(msg)

st.divider()

# --- DASHBOARD DINAMICA IN BASE AL FILTRO ARTICOLO ---
st.subheader("📊 Stato Magazzino & Giacenze")
scelta_filtro_articolo = st.selectbox("Filtra metriche e storico per articolo:", ["Tutti"] + lista_eq)

codice_filtro = None
if scelta_filtro_articolo != "Tutti":
    codice_filtro = scelta_filtro_articolo.split(" - ")[0]

tot, disp, ass, dann, smar = ottieni_metriche(codice_filtro)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Totale", tot)
col2.metric("Disponibili", disp)
col3.metric("Assegnate", ass)
col4.metric("Danneggiate", dann)
col5.metric("Smarrite", smar)

st.divider()

# --- STORICO MOVIMENTI ---
st.subheader("📜 Storico Movimenti")
storico_dati = ottieni_storico_per_articolo(codice_filtro)

if storico_dati:
    df_storico = pd.DataFrame(storico_dati, columns=["ID", "Articolo", "Dipendente", "Operazione", "Quantità", "Cantiere/Stato", "Data/Ora"])
    st.dataframe(df_storico, use_container_width=True)
else:
    st.info("Nessun movimento trovato per i criteri selezionati.")