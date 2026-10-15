import sqlite3
from datetime import datetime

def assegna_attrezzatura(codice_identificativo, id_dipendente, cantiere):
    """Assegna un'attrezzatura a un dipendente registrando il movimento."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    # 1. Verifica lo stato attuale dell'attrezzatura
    cursor.execute('SELECT id, stato FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    risultato = cursor.fetchone()

    if not risultato:
        print(f"❌ Errore: Attrezzatura con codice {codice_identificativo} non trovata.")
        conn.close()
        return False

    id_attrezzatura, stato_attuale = risultato

    if stato_attuale != 'Disponibile':
        print(f"❌ Attenzione: L'attrezzatura {codice_identificativo} non è disponibile (Stato attuale: {stato_attuale}).")
        conn.close()
        return False

    # 2. Registra il movimento di consegna
    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO movimenti (id_attrezzatura, id_dipendente, tipo_operazione, cantiere_destinazione, data_ora)
        VALUES (?, ?, 'Consegna', ?, ?)
    ''', (id_attrezzatura, id_dipendente, cantiere, data_ora))

    # 3. Aggiorna lo stato e l'ubicazione dell'attrezzatura
    cursor.execute('''
        UPDATE attrezzature 
        SET stato = 'Assegnata', ubicazione = ? 
        WHERE id = ?
    ''', (cantiere, id_attrezzatura))

    conn.commit()
    conn.close()
    print(f"✅ Successo: Attrezzatura {codice_identificativo} consegnata al dipendente ID {id_dipendente} presso {cantiere}.")
    return True


def restituisci_attrezzatura(codice_identificativo):
    """Registra la restituzione di un'attrezzatura in magazzino."""
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, stato FROM attrezzature WHERE codice_identificativo = ?', (codice_identificativo,))
    risultato = cursor.fetchone()

    if not risultato:
        print(f"❌ Errore: Attrezzatura con codice {codice_identificativo} non trovata.")
        conn.close()
        return False

    id_attrezzatura, stato_attuale = risultato

    if stato_attuale != 'Assegnata':
        print(f"❌ Attenzione: L'attrezzatura {codice_identificativo} non risulta attualmente assegnata.")
        conn.close()
        return False

    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Registra il movimento di restituzione
    cursor.execute('''
        INSERT INTO movimenti (id_attrezzatura, tipo_operazione, cantiere_destinazione, data_ora)
        VALUES (?, 'Restituzione', 'Magazzino', ?)
    ''', (id_attrezzatura, data_ora))

    # Aggiorna lo stato e l'ubicazione
    cursor.execute('''
        UPDATE attrezzature 
        SET stato = 'Disponibile', ubicazione = 'Magazzino' 
        WHERE id = ?
    ''', (id_attrezzatura,))

    conn.commit()
    conn.close()
    print(f"✅ Successo: Attrezzatura {codice_identificativo} restituita in Magazzino e resa disponibile.")
    return True


if __name__ == '__main__':
    # Test rapido delle funzioni
    print("Test operazione di consegna...")
    assegna_attrezzatura("EQ-001", 1, "Cantiere Nord")
    
    print("\nTest operazione di restituzione...")
    restituisci_attrezzatura("EQ-001")