import sqlite3
from datetime import datetime

def inizializza_db_azzzerato():
    """Crea o resetta completamente il database con tabelle per quantità e tracciamento."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS movimenti')
    cursor.execute('DROP TABLE IF EXISTS giacenze')
    cursor.execute('DROP TABLE IF EXISTS attrezzature')
    cursor.execute('DROP TABLE IF EXISTS dipendenti')

    cursor.execute('''
        CREATE TABLE attrezzature (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codice_identificativo TEXT UNIQUE,
            descrizione TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE giacenze (
            id_attrezzatura INTEGER PRIMARY KEY,
            totale INTEGER DEFAULT 0,
            disponibili INTEGER DEFAULT 0,
            assegnate INTEGER DEFAULT 0,
            danneggiate INTEGER DEFAULT 0,
            smarrite INTEGER DEFAULT 0,
            FOREIGN KEY (id_attrezzatura) REFERENCES attrezzature(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE dipendenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cognome TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE movimenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_attrezzatura INTEGER,
            id_dipendente INTEGER,
            tipo_operazione TEXT,
            quantita INTEGER,
            cantiere_destinazione TEXT,
            data_ora TEXT,
            FOREIGN KEY (id_attrezzatura) REFERENCES attrezzature(id),
            FOREIGN KEY (id_dipendente) REFERENCES dipendenti(id)
        )
    ''')

    conn.commit()
    conn.close()


def inserisci_articolo_iniziale(codice, descrizione, quantita_totale=10):
    """Aggiunge un articolo con una quantità iniziale di magazzino."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice,))
    res = cursor.fetchone()

    if not res:
        cursor.execute('INSERT INTO attrezzature (codice_identificativo, descrizione) VALUES (?, ?)', (codice, descrizione))
        id_attrezzatura = cursor.lastrowid
        cursor.execute('''
            INSERT INTO giacenze (id_attrezzatura, totale, disponibili, assegnate, danneggiate, smarrite)
            VALUES (?, ?, ?, 0, 0, 0)
        ''', (id_attrezzatura, quantita_totale, quantita_totale))

    conn.commit()
    conn.close()


def modifica_quantita_totale(codice_identificativo, nuovo_totale):
    """Modifica la quantità totale di un articolo e adegua i disponibili di conseguenza."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "Articolo non trovato."
    
    id_attrezzatura = res[0]
    cursor.execute('SELECT totale, disponibili, assegnate FROM giacenze WHERE id_attrezzatura = ?', (id_attrezzatura,))
    g = cursor.fetchone()
    if not g:
        conn.close()
        return False, "Giacenza non trovata."

    vecchio_totale, disponibili, assegnate = g

    # Calcoliamo la differenza per aggiornare i pezzi disponibili senza toccare quelli già assegnati
    differenza = nuovo_totale - vecchio_totale
    nuovo_disponibili = disponibili + differenza

    if nuovo_disponibili < 0:
        conn.close()
        return False, f"Impossibile impostare questo totale: risulterebbero disponibili quantità negative (Assegnati attuali: {assegnate})."

    cursor.execute('''
        UPDATE giacenze 
        SET totale = ?, disponibili = ?
        WHERE id_attrezzatura = ?
    ''', (nuovo_totale, nuovo_disponibili, id_attrezzatura))

    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO movimenti (id_attrezzatura, tipo_operazione, quantita, cantiere_destinazione, data_ora)
        VALUES (?, 'Modifica Totale', ?, 'Magazzino (Inventario)', ?)
    ''', (id_attrezzatura, nuovo_totale, data_ora))

    conn.commit()
    conn.close()
    return True, f"Quantità totale aggiornata a {nuovo_totale} con successo!"


def assegna_attrezzatura(codice_identificativo, id_dipendente, cantiere, quantita):
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "Articolo non trovato."
    id_attrezzatura = res[0]

    cursor.execute('SELECT disponibili, totale, assegnate FROM giacenze WHERE id_attrezzatura = ?', (id_attrezzatura,))
    g = cursor.fetchone()
    if not g:
        conn.close()
        return False, "Giacenza non configurata per questo articolo."

    disponibili, totale, assegnate = g

    if quantita > disponibili:
        conn.close()
        return False, f"Quantità non disponibile! Disponibili in magazzino: {disponibili}."

    cursor.execute('''
        UPDATE giacenze 
        SET disponibili = disponibili - ?, assegnate = assegnate + ?
        WHERE id_attrezzatura = ?
    ''', (quantita, quantita, id_attrezzatura))

    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO movimenti (id_attrezzatura, id_dipendente, tipo_operazione, quantita, cantiere_destinazione, data_ora)
        VALUES (?, ?, 'Consegna', ?, ?, ?)
    ''', (id_attrezzatura, id_dipendente, quantita, cantiere, data_ora))

    conn.commit()
    conn.close()
    return True, "Consegna registrata con successo!"


def restituisci_attrezzatura(codice_identificativo, quantita):
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "Articolo non trovato."
    id_attrezzatura = res[0]

    cursor.execute('SELECT assegnate FROM giacenze WHERE id_attrezzatura = ?', (id_attrezzatura,))
    assegnate = cursor.fetchone()[0]

    if quantita > assegnate:
        conn.close()
        return False, f"Errore: Stai tentando di restituire {quantita} pezzi, ma risultano assegnati solo {assegnate} pezzi!"

    cursor.execute('''
        UPDATE giacenze 
        SET assegnate = assegnate - ?, disponibili = disponibili + ?
        WHERE id_attrezzatura = ?
    ''', (quantita, quantita, id_attrezzatura))

    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO movimenti (id_attrezzatura, tipo_operazione, quantita, cantiere_destinazione, data_ora)
        VALUES (?, 'Restituzione', ?, 'Magazzino', ?)
    ''', (id_attrezzatura, quantita, data_ora))

    conn.commit()
    conn.close()
    return True, "Restituzione registrata con successo!"


def segnala_danneggiata_o_persa(codice_identificativo, quantita, tipo="Danneggiata"):
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "Articolo non trovato."
    id_attrezzatura = res[0]

    cursor.execute('SELECT assegnate, disponibili FROM giacenze WHERE id_attrezzatura = ?', (id_attrezzatura,))
    ass, disp = cursor.fetchone()

    if quantita > (ass + disp):
        conn.close()
        return False, "Quantità non valida rispetto allo stock attuale."

    colonna_target = 'danneggiate' if tipo == 'Danneggiata' else 'smarrite'

    cursor.execute(f'''
        UPDATE giacenze 
        SET {colonna_target} = {colonna_target} + ?, totale = totale - ?
        WHERE id_attrezzatura = ?
    ''', (quantita, quantita, id_attrezzatura))

    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO movimenti (id_attrezzatura, tipo_operazione, quantita, cantiere_destinazione, data_ora)
        VALUES (?, ?, ?, 'Magazzino/Revisione', ?)
    ''', (id_attrezzatura, tipo, quantita, data_ora))

    conn.commit()
    conn.close()
    return True, f"Segnalato come {tipo} con successo!"