from PIL import Image
from pyzbar.pyzbar import decode

def decodifica_qr(percorso_immagine):
    try:
        # Carica l'immagine del QR code
        immagine = Image.open(percorso_immagine)
        
        # Legge il QR code tramite pyzbar
        risultati = decode(immagine)
        
        if risultati:
            for qr in risultati:
                # Estrae il testo contenuto nel QR code (es. "EQ-001")
                codice_attrezzatura = qr.data.decode('utf-8')
                print(f"QR Code letto con successo! Codice attrezzatura: {codice_attrezzatura}")
                return codice_attrezzatura
        else:
            print("Nessun QR code trovato nell'immagine.")
            return None
            
    except Exception as e:
        print(f"Errore durante l'apertura dell'immagine: {e}")
        return None

if __name__ == "__main__":
    # Esempio di test puntando a uno dei QR code generati nella cartella
    decodifica_qr("qr_codes/EQ-001.png")