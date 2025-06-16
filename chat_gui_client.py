import tkinter as tk
from tkinter import scrolledtext, simpledialog, filedialog
import threading
import time
import socket
from network import tcp_send
from cli import get_own_ip
import os

# Beispielhafte bekannte Nutzer – diese sollten im echten Projekt dynamisch verwaltet werden
bekannte_nutzer = {
    "Sara": ("192.168.2.164", 5001),
    "TestHost": ("192.168.2.164", 5002)
}

chat_verlauf = []  # Zum Speichern des gesamten Chatverlaufs

class ChatGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat GUI")
        self.master.configure(bg="#f0f0f0")

        self.frame = tk.Frame(master, bg="#f0f0f0")
        self.frame.pack(padx=10, pady=10)

        # Benutzername abfragen
        self.handle = simpledialog.askstring("Name", "Dein Benutzername:")
        self.ziel = tk.StringVar(value="Sara")  # Standardzielnutzer

        # Chatverlauf-Anzeige mit Scrollfunktion
        self.chatbox = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, state='disabled', width=60, height=20, bg="white")
        self.chatbox.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Texteingabefeld für Nachrichten
        self.entry = tk.Entry(self.frame, width=40)
        self.entry.grid(row=1, column=0, pady=(0, 10), padx=(0, 5))
        self.entry.bind("<Return>", self.sende_nachricht)

        # Senden-Button
        self.send_button = tk.Button(self.frame, text="Senden", bg="#4caf50", fg="white", command=self.sende_nachricht)
        self.send_button.grid(row=1, column=1, pady=(0, 10))

        # Bild senden Button
        self.image_button = tk.Button(self.frame, text="Bild senden", bg="#2196f3", fg="white", command=self.bild_senden)
        self.image_button.grid(row=1, column=2, pady=(0, 10), padx=(5, 0))

        # Zielauswahl nebeneinander
        ziel_frame = tk.Frame(self.frame, bg="#f0f0f0")
        ziel_frame.grid(row=2, column=0, columnspan=3, sticky='w', pady=(0, 10))
        
        self.ziel_label = tk.Label(ziel_frame, text="Ziel:", bg="#f0f0f0")
        self.ziel_label.pack(side=tk.LEFT)

        self.ziel_menu = tk.OptionMenu(ziel_frame, self.ziel, *bekannte_nutzer.keys())
        self.ziel_menu.config(bg="white")
        self.ziel_menu.pack(side=tk.LEFT, padx=(5, 0))

        # Verlauf speichern Button
        self.verlauf_button = tk.Button(self.frame, text="Verlauf speichern", command=self.speichere_verlauf)
        self.verlauf_button.grid(row=3, column=0, columnspan=3, pady=(0, 10))

        # Anzeige der eigenen IP-Adresse
        self.ip_label = tk.Label(self.frame, text=f"Deine IP: {get_own_ip()}", bg="#f0f0f0")
        self.ip_label.grid(row=4, column=0, columnspan=3, pady=(5, 0))

        # Empfangsthread für eingehende Nachrichten starten
        self.empfang_thread = threading.Thread(target=self.empfange_tcp, daemon=True)
        self.empfang_thread.start()

    def schreibe_chat(self, text):
        """Fügt neue Zeile im Chatverlauf ein."""
        self.chatbox.configure(state='normal')
        self.chatbox.insert(tk.END, text + "\n")
        self.chatbox.configure(state='disabled')
        self.chatbox.yview(tk.END)
        chat_verlauf.append(text)

    def sende_nachricht(self, event=None):
        """Sendet Textnachricht an ausgewählten Nutzer."""
        nachricht = self.entry.get().strip()
        if not nachricht:
            return
        ziel = self.ziel.get()
        if ziel in bekannte_nutzer:
            ip, port = bekannte_nutzer[ziel]
            tcp_send(f"MSG {self.handle} {nachricht}", ip, port)
            self.schreibe_chat(f"(an {ziel}) {self.handle}: {nachricht}")
            self.entry.delete(0, tk.END)
        else:
            self.schreibe_chat(f"[FEHLER] Unbekannter Nutzer: {ziel}")

    def bild_senden(self):
        """Öffnet Dateidialog zum Senden eines Bildes."""
        pfad = filedialog.askopenfilename(title="Bild auswählen", filetypes=[("Bilddateien", "*.png;*.jpg;*.jpeg;*.gif")])
        if not pfad:
            return
        ziel = self.ziel.get()
        if ziel in bekannte_nutzer:
            ip, port = bekannte_nutzer[ziel]
            with open(pfad, "rb") as f:
                bilddaten = f.read()
            tcp_send(bilddaten, ip, port, binary=True)
            self.schreibe_chat(f"(an {ziel}) [Bild gesendet: {os.path.basename(pfad)}]")
        else:
            self.schreibe_chat(f"[FEHLER] Unbekannter Nutzer: {ziel}")

    def speichere_verlauf(self):
        """Speichert den Chatverlauf als Textdatei."""
        with open("chat_gui_verlauf.txt", "w", encoding="utf-8") as f:
            for zeile in chat_verlauf:
                f.write(zeile + "\n")
        self.schreibe_chat("[INFO] Verlauf gespeichert.")

    def empfange_tcp(self):
        """Einfacher TCP-Server zum Empfangen von Nachrichten oder Bildern."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("0.0.0.0", 5555))
            server.listen()
            while True:
                conn, addr = server.accept()
                with conn:
                    daten = conn.recv(1024)
                    try:
                        text = daten.decode()
                        self.schreibe_chat(f"[Empfangen von {addr[0]}] {text}")
                    except UnicodeDecodeError:
                        dateiname = f"empfangenes_bild_{int(time.time())}.jpg"
                        with open(dateiname, "wb") as f:
                            f.write(daten)
                        self.schreibe_chat(f"[Bild empfangen von {addr[0]}] Gespeichert als {dateiname}")

if __name__ == "__main__":
    root = tk.Tk()
    gui = ChatGUI(root)
    root.mainloop()