import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image
from pyzbar.pyzbar import decode
from operazioni import assegna_attrezzatura, restituisci_attrezzatura

def ottieni_statistiche():
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM attrezzature')
    totali = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attrezzature WHERE stato = 'Disponibile'")
    disponibili = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attrezzature WHERE stato = 'Assegnata'")
    assegnate = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attrezzature WHERE stato = 'Danneggiata'")
    danneggiate = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attrezzature WHERE stato = 'Smarrita'")
    smarrite = cursor.fetchone()[0]
    conn.close()
    return totali, disponibili, assegnate, danneggiate, smarrite

def ottieni_liste_db():
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()
    cursor.execute('SELECT codice_identificativo, descrizione FROM attrezzature')
    attrezzature = cursor.fetchall()
    cursor.execute('SELECT id, nome, cognome FROM dipendenti')
    dipendenti = cursor.fetchall()
    conn.close()
    return attrezzature, dipendenti

def ottieni_storico_movimenti():
    conn = sqlite3.connect('pigozzi_tech.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.id, m.id_attrezzatura, d.nome || ' ' || d.cognome, m.tipo_operazione, m.cantiere_destinazione, m.data_ora
        FROM movimenti m
        JOIN dipendenti d ON m.id_dipendente = d.id
        ORDER BY m.id DESC
    ''')
    righe = cursor.fetchall()
    conn.close()
    return righe

class ApplicazionePigozzi:
    def __init__(self, root):
        self.root = root
        self.root.title("Pigozzi Tech - Gestione Attrezzature")
        self.root.geometry("800x700")
        
        titolo = tk.Label(root, text="Pigozzi Tech S.R.L. - Dashboard Attrezzature", font=("Arial", 16, "bold"))
        titolo.pack(pady=5)
        
        # --- FRAME DASHBOARD ---
        frame_dash = tk.LabelFrame(root, text=" Riepilogo Stato Attrezzature ", font=("Arial", 10))
        frame_dash.pack(fill="x", padx=15, pady=5)
        
        self.lbl_tot = tk.Label(frame_dash, text="", font=("Arial", 9))
        self.lbl_tot.pack(anchor="w", padx=10, pady=1)
        self.lbl_disp = tk.Label(frame_dash, text="", font=("Arial", 9), fg="green")
        self.lbl_disp.pack(anchor="w", padx=10, pady=1)
        self.lbl_ass = tk.Label(frame_dash, text="", font=("Arial", 9), fg="blue")
        self.lbl_ass.pack(anchor="w", padx=10, pady=1)
        self.lbl_dann = tk.Label(frame_dash, text="", font=("Arial", 9), fg="orange")
        self.lbl_dann.pack(anchor="w", padx=10, pady=1)
        self.lbl_smar = tk.Label(frame_dash, text="", font=("Arial", 9), fg="red")
        self.lbl_smar.pack(anchor="w", padx=10, pady=1)
        
        self.aggiorna_etichette_dashboard()

        # --- FRAME OPERAZIONI ---
        frame_ops = tk.LabelFrame(root, text=" Gestione Movimenti & QR Code ", font=("Arial", 10))
        frame_ops.pack(fill="x", padx=15, pady=5)

        tk.Label(frame_ops, text="Attrezzatura:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.combo_attrezzature = ttk.Combobox(frame_ops, width=35, state="readonly")
        self.combo_attrezzature.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_ops, text="Dipendente:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.combo_dipendenti = ttk.Combobox(frame_ops, width=35, state="readonly")
        self.combo_dipendenti.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame_ops, text="Cantiere / Ubicazione:", font=("Arial", 9)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.entry_cantiere = tk.Entry(frame_ops, width=37)
        self.entry_cantiere.grid(row=2, column=1, padx=5, pady=5)

        frame_btn = tk.Frame(frame_ops)
        frame_btn.grid(row=3, column=0, columnspan=2, pady=8)

        btn_assegna = tk.Button(frame_btn, text="Registra Consegna", bg="#d1e7dd", font=("Arial", 9, "bold"), command=self.esegui_consegna)
        btn_assegna.pack(side="left", padx=5)

        btn_restituisci = tk.Button(frame_btn, text="Registra Restituzione", bg="#f8d7da", font=("Arial", 9, "bold"), command=self.esegui_restituzione)
        btn_restituisci.pack(side="left", padx=5)

        btn_scansiona = tk.Button(frame_btn, text="Scansiona con Webcam", bg="#cff4fc", font=("Arial", 9, "bold"), command=self.scansiona_con_webcam)
        btn_scansiona.pack(side="left", padx=5)

        # --- FRAME STORICO MOVIMENTI ---
        frame_storico = tk.LabelFrame(root, text=" Storico Movimenti ", font=("Arial", 10))
        frame_storico.pack(fill="both", expand=True, padx=15, pady=5)

        columns = ("ID", "Attrezzatura", "Dipendente", "Operazione", "Cantiere", "Data/Ora")
        self.tree_storico = ttk.Treeview(frame_storico, columns=columns, show="headings", height=6)
        
        for col in columns:
            self.tree_storico.heading(col, text=col)
            self.tree_storico.column(col, width=110, anchor="center")

        scrollbar = ttk.Scrollbar(frame_storico, orient="vertical", command=self.tree_storico.yview)
        self.tree_storico.configure(yscrollcommand=scrollbar.set)
        
        self.tree_storico.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        self.popola_dropdown()
        self.aggiorna_tabella_storico()

    def aggiorna_etichette_dashboard(self):
        tot, disp, ass, dann, smar = ottieni_statistiche()
        self.lbl_tot.config(text=f"Totale Attrezzature: {tot}")
        self.lbl_disp.config(text=f"Disponibili in Magazzino: {disp}")
        self.lbl_ass.config(text=f"Assegnate nei Cantieri: {ass}")
        self.lbl_dann.config(text=f"Danneggiate: {dann}")
        self.lbl_smar.config(text=f"Smarrite: {smar}")

    def popola_dropdown(self):
        attrezzature, dipendenti = ottieni_liste_db()
        self.combo_attrezzature['values'] = [f"{eq[0]} - {eq[1]}" for eq in attrezzature]
        self.combo_dipendenti['values'] = [f"{d[0]} - {d[1]} {d[2]}" for d in dipendenti]

    def aggiorna_tabella_storico(self):
        for row in self.tree_storico.get_children():
            self.tree_storico.delete(row)
        for mov in ottieni_storico_movimenti():
            self.tree_storico.insert("", "end", values=mov)

    def esegui_consegna(self):
        sel_att = self.combo_attrezzature.get()
        sel_dip = self.combo_dipendenti.get()
        cantiere = self.entry_cantiere.get().strip()

        if not sel_att or not sel_dip or not cantiere:
            messagebox.showerror("Errore", "Compila tutti i campi per registrare la consegna.")
            return

        codice_eq = sel_att.split(" - ")[0]
        id_dip = int(sel_dip.split(" - ")[0])

        successo = assegna_attrezzatura(codice_eq, id_dip, cantiere)
        if successo:
            messagebox.showinfo("Successo", f"Attrezzatura {codice_eq} consegnata correttamente!")
            self.aggiorna_etichette_dashboard()
            self.aggiorna_tabella_storico()
            self.entry_cantiere.delete(0, tk.END)
        else:
            messagebox.showerror("Errore", "Impossibile completare la consegna. Controlla lo stato dell'attrezzatura.")

    def esegui_restituzione(self):
        sel_att = self.combo_attrezzature.get()
        if not sel_att:
            messagebox.showerror("Errore", "Seleziona un'attrezzatura da restituire.")
            return

        codice_eq = sel_att.split(" - ")[0]
        successo = restituisci_attrezzatura(codice_eq)
        if successo:
            messagebox.showinfo("Successo", f"Attrezzatura {codice_eq} restituita in magazzino!")
            self.aggiorna_etichette_dashboard()
            self.aggiorna_tabella_storico()
        else:
            messagebox.showerror("Errore", "Impossibile restituire l'attrezzatura. Potrebbe non essere assegnata.")

    def scansiona_con_webcam(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Errore", "Impossibile accedere alla webcam del PC.")
            return

        messagebox.info_scand = messagebox.showinfo("Webcam", "Inquadra il QR code con la webcam.\nPremi 'Q' sulla tastiera per annullare.")
        
        codice_trovato = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            risultati = decode(frame)
            if risultati:
                codice_trovato = risultati[0].data.decode('utf-8').strip()
                if codice_trovato.upper().startswith("ID:"):
                    codice_trovato = codice_trovato[3:].strip()
                break
                
            cv2.imshow("Scanner QR Code - Pigozzi Tech (Premi 'q' per uscire)", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()
        
        if codice_trovato:
            trovato = False
            for item in self.combo_attrezzature['values']:
                codice_item = item.split(" - ")[0].strip()
                if codice_item.lower() == codice_trovato.lower():
                    self.combo_attrezzature.set(item)
                    trovato = True
                    messagebox.showinfo("QR Scansionato", f"Attrezzatura identificata con successo: {codice_trovato}")
                    break
                    
            if not trovato:
                messagebox.showwarning("Attenzione", f"Codice '{codice_trovato}' letto dal QR ma non presente nel database.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ApplicazionePigozzi(root)
    root.mainloop()