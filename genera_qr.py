# --- IMPORTANTE: Prima di eseguire, installa le librerie con: ---
# pip install qrcode pillow

import sqlite3
import qrcode
import os

def genera_qr_code():
    # 1. Crea una cartella per salvare i QR code se non esiste
    cartella_qr = "qr_codes"
    os.makedirs(cartella_qr, exist_ok=True)

    # 2. Connessione al database SQLite
    conn = None
    try:
        conn = sqlite3.connect('pigozzi_tech.db')
        cursor = conn.cursor()

        # 3. Preleva tutte le attrezzature (codice univoco, descrizione)
        cursor.execute('SELECT codice_identificativo, descrizione FROM attrezzature')
        attrezzature = cursor.fetchall()

        if not attrezzature:
            print("Nessuna attrezzatura trovata nel database.")
            return

        print(f"Trovate {len(attrezzature)} attrezzature. Inizio generazione QR...")

        # 4. Itera su ogni attrezzatura e genera il QR
        for eq in attrezzature:
            codice = eq[0]
            descrizione = eq[1]

            # Dati da codificare nel QR code (il codice identificativo univoco)
            dati_qr = f"ID:{codice}"

            # Configurazione del QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(dati_qr)
            qr.make(fit=True)

            # Genera l'immagine (bianco e nero)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Salvataggio dell'immagine nella cartella 'qr_codes'
            percorso_file = os.path.join(cartella_qr, f"{codice}.png")
            img.save(percorso_file)
            print(f"QR code generato per: {codice} ({descrizione}) -> {percorso_file}")

        print(f"\n✅ Tutti i {len(attrezzature)} QR code sono stati salvati nella cartella '{cartella_qr}'.")

    except sqlite3.Error as e:
        print(f"Errore del database: {e}")
    except Exception as e:
        print(f"Errore generico: {e}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    genera_qr_code()