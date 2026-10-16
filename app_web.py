import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
from pyzbar.pyzbar import decode
import qrcode
import io
from operazioni import (
    inizializza_db_azzzerato, 
    inserisci_articolo_iniziale, 
    assegna_attrezzatura, 
    restituisci_attrezzatura, 
    segnala_danneggiata_o_persa,
    modifica_quantita_totale,
    azzera_articolo_specifico,
    azzera_storico_movimenti,
    aggiungi_nuovo_articolo_anagrafica,
    elimina_articolo_definitivo
)

st.set_page_config(page_title="Pigozzi Tech - Gestione Attrezzature", layout="wide")
st.title("🛠️ Pigozzi Tech S.R.L. - Gestione Attrezzature")

# Controllo esistenza database e popolamento 20 articoli
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
    
    conn_dip = sqlite3.connect('pigozzi_tech.db')
    c_dip = conn_dip.cursor()
    c_dip.execute("INSERT INTO dipendenti (nome, cognome) VALUES ('Mario', 'Rossi')")
    c_dip.execute("INSERT INTO dipendenti (nome, cognome) VALUES ('Luigi', 'Verdi')")
    c_dip.execute("INSERT INTO dipendenti (nome, cognome) VALUES ('Giovanni', 'Bianchi')")
    conn_dip.commit()
    conn_dip.close()

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

def ottieni_storico_avanzato(codice_articolo=None, filtro_soggetto=None):
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()
    query = '''
        SELECT m.id, a.codice_identificativo || ' - ' || a.descrizione, COALESCE(d.nome || ' ' || d.cognome, 'Magazzino/Sistema'), 
               m.tipo_operazione, m.quantita, m.cantiere_destinazione, m.data_ora
        FROM movimenti m
        JOIN attrezzature a ON m.id_attrezzatura = a.id
        LEFT JOIN dipendenti d ON m.id_dipendente = d.id
        WHERE 1=1
    '''
    params = []
    if codice_articolo and codice_articolo != "Tutti":
        query += " AND a.codice_identificativo = ?"
        params.append(codice_articolo)
        
    if filtro_soggetto == "Magazzino / Sistema":
        query += " AND m.id_dipendente IS NULL"
    elif filtro_soggetto and filtro_soggetto != "Tutti":
        id_dip = int(filtro_soggetto.split(" - ")[0])
        query += " AND d.id = ?"
        params.append(id_dip)
        
    query += " ORDER BY m.id DESC"
    cursor.execute(query, params)
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
scelta_filtro_articolo = st.selectbox("Filtra metriche per articolo:", ["Tutti"] + lista_eq)

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

# --- OPZIONI DI GESTIONE ANAGRAFICA, ARTICOLI E QR CODE ---
with st.expander("⚙️ Gestione Anagrafica Articoli, Modifiche & QR Code"):
    tab_nuovo, tab_elimina, tab_mod, tab_azz, tab_qr = st.tabs([
        "➕ Nuovo Articolo", "🗑️ Elimina Articolo", "Modifica Totale", "Azzera Articolo", "Genera QR Code 🖨️"
    ])
    
    with tab_nuovo:
        with st.form("form_nuovo_articolo"):
            st.write("Aggiungi un nuovo articolo da zero nel magazzino:")
            nuovo_codice = st.text_input("Codice Identificativo (es. EQ-021)")
            nuova_desc = st.text_input("Descrizione Articolo (es. Martello Pneumatico)")
            nuova_qta_iniziale = st.number_input("Quantità Iniziale", min_value=1, max_value=200, value=5)
            btn_crea_articolo = st.form_submit_button("Crea Articolo & Genera 🚀")

            if btn_crea_articolo:
                if not nuovo_codice or not nuova_desc:
                    st.error("Inserisci sia il codice identificativo che la descrizione.")
                else:
                    ok, msg = aggiungi_nuovo_articolo_anagrafica(nuovo_codice.upper().strip(), nuova_desc, nuova_qta_iniziale)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with tab_elimina:
        with st.form("form_elimina_articolo"):
            st.warning("⚠️ Attenzione: Rimuovere un articolo lo cancellerà completamente insieme al suo storico e alle sue giacenze.")
            articolo_da_eliminare = st.selectbox("Seleziona Articolo da Rimuovere", lista_eq, key="del_art")
            btn_conferma_elimina = st.form_submit_button("Elimina Definitivamente ❌")

            if btn_conferma_elimina:
                codice_del = articolo_da_eliminare.split(" - ")[0]
                ok, msg = elimina_articolo_definitivo(codice_del)
                if ok:
                    st.error(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with tab_mod:
        with st.form("form_modifica_totale"):
            articolo_da_modificare = st.selectbox("Articolo da Aggiornare", lista_eq, key="mod_tot")
            nuovo_valore_totale = st.number_input("Nuova Quantità Totale Reale", min_value=1, max_value=500, value=10, step=1)
            btn_aggiorna_totale = st.form_submit_button("Aggiorna Totale Magazzino 🔄")

            if btn_aggiorna_totale:
                codice_mod = articolo_da_modificare.split(" - ")[0]
                ok, msg = modifica_quantita_totale(codice_mod, nuovo_valore_totale)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
                    
    with tab_azz:
        with st.form("form_azzera_articolo"):
            articolo_da_azzerare = st.selectbox("Articolo da Azzerare completamente", lista_eq, key="azz_art")
            st.warning("⚠️ Questa opzione porterà a 0 tutti i valori (Totale, Disponibili, Assegnate, ecc.) dell'articolo selezionato.")
            btn_conferma_azzera = st.form_submit_button("Azzera Articolo Selezionato ❌")

            if btn_conferma_azzera:
                codice_azz = articolo_da_azzerare.split(" - ")[0]
                ok, msg = azzera_articolo_specifico(codice_azz)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
                    
    with tab_qr:
        st.write("Genera in tempo reale il QR code per qualsiasi articolo registrato:")
        articolo_qr = st.selectbox("Seleziona Articolo per QR", lista_eq, key="qr_art")
        codice_da_codificare = articolo_qr.split(" - ")[0]
        
        img_qr = qrcode.make(codice_da_codificare)
        buf = io.BytesIO()
        img_qr.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        st.image(byte_im, width=200, caption=f"QR Code per {articolo_qr}")
        st.download_button(
            label="Scarica QR Code in PNG 📥",
            data=byte_im,
            file_name=f"QR_{codice_da_codificare}.png",
            mime="image/png"
        )

st.divider()

# --- STORICO MOVIMENTI E FILTRI AVANZATI ---
col_storico_titolo, col_storico_btn = st.columns([3, 1])
with col_storico_titolo:
    st.subheader("📜 Storico Movimenti e Filtri")

with col_storico_btn:
    with st.popover("🗑️ Azzera Storico"):
        st.write("Sei sicuro di voler cancellare tutto lo storico dei movimenti registrati?")
        if st.button("Conferma Azzeramento", type="primary"):
            ok, msg = azzera_storico_movimenti()
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

col_f1, col_f2 = st.columns(2)
with col_f1:
    filtro_storico_articolo = st.selectbox("Filtra storico per Articolo:", ["Tutti"] + lista_eq, key="fil_art")
with col_f2:
    opzioni_soggetto = ["Tutti", "Magazzino / Sistema"] + lista_dip
    filtro_storico_soggetto = st.selectbox("Filtra storico per Soggetto (Dipendente o Magazzino):", opzioni_soggetto, key="fil_sogg")

codice_storico_art = None
if filtro_storico_articolo != "Tutti":
    codice_storico_art = filtro_storico_articolo.split(" - ")[0]

storico_dati = ottieni_storico_avanzato(codice_storico_art, filtro_storico_soggetto)

if storico_dati:
    df_storico = pd.DataFrame(storico_dati, columns=["ID", "Articolo", "Soggetto", "Operazione", "Quantità", "Cantiere/Stato", "Data/Ora"])
    st.dataframe(df_storico, use_container_width=True)
else:
    st.info("Nessun movimento trovato per i criteri selezionati.")