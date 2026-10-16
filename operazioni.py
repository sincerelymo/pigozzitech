import sqlite3
from datetime import datetime

def inizializza_db_azzzerato():
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


def aggiungi_nuovo_articolo_anagrafica(codice, descrizione, quantita_iniziale):
    """Aggiunge un nuovo articolo nell'anagrafica con relativo stock iniziale."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice,))
    res = cursor.fetchone()
    if res:
        conn.close()
        return False, f"Errore: Esiste già un articolo con il codice {codice}!"

    try:
        cursor.execute('INSERT INTO attrezzature (codice_identificativo, descrizione) VALUES (?, ?)', (codice, descrizione))
        id_attrezzatura = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO giacenze (id_attrezzatura, totale, disponibili, assegnate, danneggiate, smarrite)
            VALUES (?, ?, ?, 0, 0, 0)
        ''', (id_attrezzatura, quantita_iniziale, quantita_iniziale))

        data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO movimenti (id_attrezzatura, tipo_operazione, quantita, cantiere_destinazione, data_ora)
            VALUES (?, 'Nuovo Articolo', ?, 'Magazzino', ?)
        ''', (id_attrezzatura, quantita_iniziale, data_ora))

        conn.commit()
        conn.close()
        return True, f"Articolo {codice} aggiunto con successo!"
    except Exception as e:
        conn.close()
        return False, f"Errore durante l'inserimento: {e}"


def elimina_articolo_definitivo(codice_identificativo):
    """Elimina completamente un articolo, le sue giacenze e lo storico collegato."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "Articolo non trovato."

    id_attrezzatura = res[0]

    # Elimina movimenti, giacenze e articolo per evitare problemi di chiavi esterne
    cursor.execute('DELETE FROM movimenti WHERE id_attrezzatura = ?', (id_attrezzatura,))
    cursor.execute('DELETE FROM giacenze WHERE id_attrezzatura = ?', (id_attrezzatura,))
    cursor.execute('DELETE FROM attrezzature WHERE id = ?', (id_attrezzatura,))

    conn.commit()
    conn.close()
    return True, f"Articolo {codice_identificativo} rimosso definitivamente dall'inventario."


def modifica_quantita_totale(codice_identificativo, nuovo_totale):
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


def azzera_articolo_specifico(codice_identificativo):
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "Articolo non trovato."
    
    id_attrezzatura = res[0]
    cursor.execute('''
        UPDATE giacenze 
        SET totale = 0, disponibili = 0, assegnate = 0, danneggiate = 0, smarrite = 0
        WHERE id_attrezzatura = ?
    ''', (id_attrezzatura,))

    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO movimenti (id_attrezzatura, tipo_operazione, quantita, cantiere_destinazione, data_ora)
        VALUES (?, 'Azzeramento Articolo', 0, 'Magazzino', ?)
    ''', (id_attrezzatura, data_ora))

    conn.commit()
    conn.close()
    return True, f"Articolo {codice_identificativo} azzerato con successo!"


def azzera_storico_movimenti():
    try:
        conn = sqlite3.connect('pigozzi_tech.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM movimenti')
        conn.commit()
        conn.close()
        return True, "Storico dei movimenti azzerato con successo!"
    except Exception as e:
        return False, f"Errore durante l'azzeramento dello storico: {e}"


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