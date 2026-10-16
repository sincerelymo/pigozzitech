import sqlite3
from datetime import datetime

def inizializza_db_azzzerato():
    """Crea o resetta il database con tabelle per quantità e tracciamento rigoroso."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    # Tabella Attrezzature/Articoli di base
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attrezzature (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codice_identificativo TEXT UNIQUE,
            descrizione TEXT
        )
    ''')

    # Tabella per la gestione delle quantità in tempo reale per ogni articolo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS giacenze (
            id_attrezzatura INTEGER PRIMARY KEY,
            totale INTEGER DEFAULT 0,
            disponibili INTEGER DEFAULT 0,
            assegnate INTEGER DEFAULT 0,
            danneggiate INTEGER DEFAULT 0,
            smarrite INTEGER DEFAULT 0,
            FOREIGN KEY (id_attrezzatura) REFERENCES attrezzature(id)
        )
    ''')

    # Tabella Dipendenti
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dipendenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cognome TEXT
        )
    ''')

    # Tabella Movimenti
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimenti (
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
    """Aggiunge o resetta un articolo con una quantità iniziale definita."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice,))
    res = cursor.fetchone()

    if not res:
        cursor.execute('INSERT INTO attrezzature (codice_identificativo, descrizione) VALUES (?, ?)', (codice, descrizione))
        id_attrezzatura = cursor.lastrowid
        # Inizializziamo con tutto disponibile
        cursor.execute('''
            INSERT INTO giacenze (id_attrezzatura, totale, disponibili, assegnate, danneggiate, smarrite)
            VALUES (?, ?, ?, 0, 0, 0)
        ''', (id_attrezzatura, quantita_totale, quantita_totale))
    else:
        id_attrezzatura = res[0]
        # Aggiorna reset quantitativi
        cursor.execute('''
            UPDATE giacenze SET totale = ?, disponibili = ?, assegnate = 0, danneggiate = 0, smarrite = 0
            WHERE id_attrezzatura = ?
        ''', (quantita_totale, quantita_totale, id_attrezzatura))

    conn.commit()
    conn.close()


def assegna_attrezzatura(codice_identificativo, id_dipendente, cantiere, quantita):
    """Consegna attrezzatura verificando che ci siano abbastanza pezzi disponibili."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "Articolo non trovato."
    id_attrezzatura = res[0]

    cursor.execute('SELECT disponibili, totale FROM giacenze WHERE id_attrezzatura = ?', (id_attrezzatura,))
    g = cursor.fetchone()
    if not g:
        conn.close()
        return False, "Giacenza non configurata per questo articolo."

    disponibili, totale = g

    if quantita > disponibili:
        conn.close()
        return False, f"Quantità non disponibile! Disponibili in magazzino: {disponibili}."

    # Aggiorna giacenze
    new_disp = disponibili - quantita
    new_ass = (totale - new_disp) - (g[2] - disponibili) # ricalcolo corretto assegnate
    # Semplificazione calcolo assegnate:
    cursor.execute('SELECT assegnate FROM giacenze WHERE id_attrezzatura = ?', (id_attrezzatura,))
    vecchie_assegnate = cursor.fetchone()[0]
    
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
    """Restituisce attrezzatura verificando che non si restituisca più del consegnato."""
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
    """Segnala merce come Danneggiata o Smarrita scalandola dalle assegnate o disponibili."""
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

    # Per sicurezza verifichiamo che ci siano abbastanza pezzi totali movimentabili
    if quantita > (ass + disp):
        conn.close()
        return False, "Quantità non valida rispetto allo stock attuale."

    colonna_target = 'danneggiate' if tipo == 'Danneggiata' else 'smarrite'

    # Sottraiamo prioritariamente dalle assegnate o disponibili
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