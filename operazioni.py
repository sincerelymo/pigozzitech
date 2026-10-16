import sqlite3
from datetime import datetime

def assegna_attrezzatura(codice_identificativo, id_dipendente, cantiere, quantita=1):
    """Assegna o consegna una quantità di attrezzatura a un dipendente."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, stato FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    risultato = cursor.fetchone()

    if not risultato:
        print(f"❌ Errore: Attrezzatura con codice {codice_identificativo} non trovata.")
        conn.close()
        return False

    id_attrezzatura, stato_attuale = risultato

    # Registra il movimento di consegna con la quantità scelta
    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO movimenti (id_attrezzatura, id_dipendente, tipo_operazione, cantiere_destinazione, data_ora)
        VALUES (?, ?, ?, ?, ?)
    ''', (id_attrezzatura, id_dipendente, f"Consegna (Q.tà: {quantita})", cantiere, data_ora))

    # Aggiorna lo stato a Assegnata indipendentemente dallo stato precedente per evitare blocchi
    cursor.execute('''
        UPDATE attrezzature 
        SET stato = 'Assegnata', ubicazione = ? 
        WHERE id = ?
    ''', (cantiere, id_attrezzatura))

    conn.commit()
    conn.close()
    return True


def restituisci_attrezzatura(codice_identificativo, quantita=1):
    """Registra la restituzione di una quantità di attrezzatura in magazzino."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    risultato = cursor.fetchone()

    if not risultato:
        print(f"❌ Errore: Attrezzatura con codice {codice_identificativo} non trovata.")
        conn.close()
        return False

    id_attrezzatura = risultato[0]
    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Registra il movimento di restituzione
    cursor.execute('''
        INSERT INTO movimenti (id_attrezzatura, tipo_operazione, cantiere_destinazione, data_ora)
        VALUES (?, ?, 'Magazzino', ?)
    ''', (id_attrezzatura, f"Restituzione (Q.tà: {quantita})", data_ora))

    # Riporta l'attrezzatura come disponibile in magazzino
    cursor.execute('''
        UPDATE attrezzature 
        SET stato = 'Disponibile', ubicazione = 'Magazzino' 
        WHERE id = ?
    ''', (id_attrezzatura,))

    conn.commit()
    conn.close()
    return True


def segnala_danneggiata_db(codice_identificativo, quantita=1):
    """Segnala l'attrezzatura come danneggiata."""
    try:
        conn = sqlite3.connect('pigozzi_tech.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
        risultato = cursor.fetchone()
        if not risultato:
            conn.close()
            return False
            
        id_attrezzatura = risultato[0]
        data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
            INSERT INTO movimenti (id_attrezzatura, tipo_operazione, cantiere_destinazione, data_ora)
            VALUES (?, ?, 'Magazzino/Riparazione', ?)
        ''', (id_attrezzatura, f"Danneggiata (Q.tà: {quantita})", data_ora))

        cursor.execute("UPDATE attrezzature SET stato = 'Danneggiata' WHERE id = ?", (id_attrezzatura,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False