import tkinter as tk
from tkinter import scrolledtext, simpledialog, filedialog
import threading
import time
import socket
import os
from network import tcp_send
from cli import get_own_ip

# Beispielhafte bekannte Nutzer – für lokale Tests mit sich selbst
bekannte_nutzer = {
    "Sara": ("127.0.0.1", 5555),
    "TestHost": ("127.0.0.1", 5556)
}

chat_verlauf = []  # Chatverlauf zur Anzeige und Speicherung

class ChatGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat GUI")

        self.frame = tk.Frame(master)
        self.frame.pack(padx=10, pady=10)

        self.handle = simpledialog.askstring("Name", "Dein Benutzername:")
        self.ziel = tk.StringVar(value="Sara")

        self.chatbox = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, state='disabled', width=60, height=20)
        self.chatbox.grid(row=0, column=0, columnspan=4, pady=(0, 10))

        self.entry = tk.Entry(self.frame, width=40)
        self.entry.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky='we')
        self.entry.bind("<Return>", self.sende_nachricht)

        self.send_button = tk.Button(self.frame, text="Senden", command=self.sende_nachricht)
        self.send_button.grid(row=1, column=2, pady=(0, 10), sticky='we')

        self.image_button = tk.Button(self.frame, text="Bild senden", command=self.bild_senden)
        self.image_button.grid(row=1, column=3, pady=(0, 10), sticky='we')

        self.ziel_label = tk.Label(self.frame, text="Ziel:")
        self.ziel_label.grid(row=2, column=0, sticky='w')

        self.ziel_menu = tk.OptionMenu(self.frame, self.ziel, *bekannte_nutzer.keys())
        self.ziel_menu.grid(row=2, column=1, sticky='w')

        self.name_button = tk.Button(self.frame, text="Name ändern", command=self.name_aendern)
        self.name_button.grid(row=2, column=2, pady=(0, 10), sticky='we')

        self.exit_button = tk.Button(self.frame, text="Beenden", command=self.beenden)
        self.exit_button.grid(row=2, column=3, pady=(0, 10), sticky='we')

        self.verlauf_button = tk.Button(self.frame, text="Verlauf speichern", command=self.speichere_verlauf)
        self.verlauf_button.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        self.ip_label = tk.Label(self.frame, text=f"Deine IP: {get_own_ip()}")
        self.ip_label.grid(row=3, column=2, columnspan=2, pady=(10, 0), sticky='e')

        self.empfang_thread = threading.Thread(target=self.empfange_tcp, daemon=True)
        self.empfang_thread.start()
        
        self.empfangs_port = 5555 if self.handle == "Sara" else 5556

    def schreibe_chat(self, text):
        self.chatbox.configure(state='normal')
        self.chatbox.insert(tk.END, text + "\n")
        self.chatbox.configure(state='disabled')
        self.chatbox.yview(tk.END)
        chat_verlauf.append(text)

    def sende_nachricht(self, event=None):
        nachricht = self.entry.get().strip()
        if not nachricht:
            return
        ziel = self.ziel.get()
        if ziel in bekannte_nutzer:
            ip, port = bekannte_nutzer[ziel]
            try:
                tcp_send(f"MSG {self.handle} {nachricht}", ip, port)
                self.schreibe_chat(f"(an {ziel}) {self.handle}: {nachricht}")
            except Exception as e:
                self.schreibe_chat(f"[FEHLER] Nachricht nicht gesendet: {e}")
            self.entry.delete(0, tk.END)
        else:
            self.schreibe_chat(f"[FEHLER] Unbekannter Nutzer: {ziel}")

    def bild_senden(self):
        pfad = filedialog.askopenfilename(title="Bild auswählen", filetypes=[("Bilddateien", "*.png;*.jpg;*.jpeg;*.gif")])
        if not pfad:
            return
        ziel = self.ziel.get()
        if ziel in bekannte_nutzer:
            ip, port = bekannte_nutzer[ziel]
            try:
                with open(pfad, "rb") as f:
                    bilddaten = f.read()
                tcp_send(bilddaten, ip, port, binary=True)
                self.schreibe_chat(f"(an {ziel}) [Bild gesendet: {os.path.basename(pfad)}]")
            except Exception as e:
                self.schreibe_chat(f"[FEHLER] Bild nicht gesendet: {e}")
        else:
            self.schreibe_chat(f"[FEHLER] Unbekannter Nutzer: {ziel}")

    def speichere_verlauf(self):
        with open("chat_gui_verlauf.txt", "w", encoding="utf-8") as f:
            for zeile in chat_verlauf:
                f.write(zeile + "\n")
        self.schreibe_chat("[INFO] Verlauf gespeichert.")

    def name_aendern(self):
        neuer_name = simpledialog.askstring("Name ändern", "Neuer Benutzername:")
        if neuer_name:
            self.handle = neuer_name
            self.schreibe_chat(f"[INFO] Benutzername geändert zu {self.handle}")

    def beenden(self):
        self.speichere_verlauf()
        self.master.destroy()


    def empfange_tcp(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("0.0.0.0", self.empfangs_port))
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