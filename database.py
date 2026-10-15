import sqlite3

def inizializza_database():
    # Connessione al database (verrà creato il file pigozzi_tech.db nella stessa cartella)
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()

    # 1. Tabella Dipendenti
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dipendenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            ruolo TEXT
        )
    ''')

    # 2. Tabella Attrezzature
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attrezzature (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codice_identificativo TEXT UNIQUE NOT NULL,
            descrizione TEXT NOT NULL,
            categoria TEXT NOT NULL,
            matricola TEXT,
            ubicazione TEXT NOT NULL,
            stato TEXT NOT NULL
        )
    ''')

    # 3. Tabella Movimenti (Consegne, Restituzioni, Trasferimenti)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_attrezzatura INTEGER,
            id_dipendente INTEGER,
            tipo_operazione TEXT NOT NULL,
            cantiere_destinazione TEXT,
            data_ora TEXT NOT NULL,
            FOREIGN KEY (id_attrezzatura) REFERENCES attrezzature (id),
            FOREIGN KEY (id_dipendente) REFERENCES dipendenti (id)
        )
    ''')

    # 4. Tabella Segnalazioni Anomalie
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS segnalazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_attrezzatura INTEGER,
            descrizione_problema TEXT NOT NULL,
            data_segnalazione TEXT NOT NULL,
            stato_risoluzione TEXT DEFAULT 'Aperta',
            FOREIGN KEY (id_attrezzatura) REFERENCES attrezzature (id)
        )
    ''')

    # Popolamento dati di prova se le tabelle sono vuote
    cursor.execute('SELECT COUNT(*) FROM attrezzature')
    if cursor.fetchone()[0] == 0:
        print("Inserimento dati di prova...")

        # Inserimento Dipendenti di prova
        dipendenti_prova = [
            ("Mario", "Rossi", "Elettricista"),
            ("Luca", "Bianchi", "Tecnico Reti"),
            ("Giulia", "Verdi", "Capo Cantiere"),
            ("Alessandro", "Neri", "Idraulico")
        ]
        cursor.executemany('INSERT INTO dipendenti (nome, cognome, ruolo) VALUES (?, ?, ?)', dipendenti_prova)

        # Inserimento 20 Attrezzature di prova richieste dal progetto
        attrezzature_prova = [
            ("EQ-001", "Trapano a percussione Bosch", "Elettroutensili", "TR-88321", "Magazzino", "Disponibile"),
            ("EQ-002", "Saldatrice Inverter", "Saldatura", "SL-44102", "Magazzino", "Disponibile"),
            ("EQ-003", "Multimetro digitale Fluke", "Strumentazione", "MT-11293", "Cantiere Nord", "Assegnata"),
            ("EQ-004", "Flessibile angolare Makita", "Elettroutensili", "FL-99382", "Magazzino", "Disponibile"),
            ("EQ-005", "Laser di livello rotativo", "Misurazione", "LS-55210", "Cantiere Sud", "Assegnata"),
            ("EQ-006", "Punte per trapano set completo", "Accessori", "PT-00192", "Magazzino", "Disponibile"),
            ("EQ-007", "Martello demolitore Hilti", "Elettroutensili", "MD-77312", "Magazzino", "Danneggiata"),
            ("EQ-008", "Scala telescopica alluminio 5m", "Attrezzatura minuta", "SC-33211", "Cantiere Nord", "Assegnata"),
            ("EQ-009", "Generatore di corrente 5kW", "Elettricità", "GEN-99120", "Magazzino", "Disponibile"),
            ("EQ-010", "Troncatrice radiale per legno", "Elettroutensili", "TRON-441", "Magazzino", "Disponibile"),
            ("EQ-011", "Termocamera infrarossi", "Strumentazione", "TC-88231", "Magazzino", "Smarrita"),
            ("EQ-012", "Idropulitrice professionale", "Pulizia", "IDR-11029", "Magazzino", "Disponibile"),
            ("EQ-013", "Avvitatore a impulsi a batteria", "Elettroutensili", "AV-66543", "Cantiere Centro", "Assegnata"),
            ("EQ-014", "Faretto LED da cantiere 50W", "Illuminazione", "FAR-22391", "Magazzino", "Disponibile"),
            ("EQ-015", "Carrello a mano per trasporto", "Movimentazione", "CAR-10293", "Magazzino", "Disponibile"),
            ("EQ-016", "Set chiavi inglesi complete", "Utensileria manuale", "CH-55432", "Magazzino", "Disponibile"),
            ("EQ-017", "Banco da lavoro portatile", "Attrezzatura minuta", "BN-99812", "Cantiere Nord", "Assegnata"),
            ("EQ-018", "Compressore d'aria 50L", "Pneumatica", "CMP-77612", "Magazzino", "Disponibile"),
            ("EQ-019", "Rilevatore di cavi e tubi", "Strumentazione", "RC-33412", "Magazzino", "Disponibile"),
            ("EQ-020", "Estintore portatile polvere 6kg", "Sicurezza", "EST-11234", "Cantiere Sud", "Assegnata")
        ]
        cursor.executemany('''
            INSERT INTO attrezzature (codice_identificativo, descrizione, categoria, matricola, ubicazione, stato)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', attrezzature_prova)

        print("Database creato e popolato con successo con 20 attrezzature!")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    inizializza_database()