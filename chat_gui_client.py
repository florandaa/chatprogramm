import tkinter as tk
from tkinter import scrolledtext, simpledialog, filedialog
import threading
import time
import socket
import os
import tkinter.ttk as ttk
from network import load_config, tcp_send,udp_send,udp_listener
from cli import get_own_ip

bekannte_nutzer = {}  # Globale Variable für bekannte Nutzer
chat_verlauf = []  # Chatverlauf zur Anzeige und Speicherung
# @file chat_gui_client.py

class ChatGUI:
    def __init__(self, master):
        config = load_config()
        self.whoisport = config.get('whoisport', 4000)  # Port für Discovery
        self.autoreply_text = config.get("autoreply", "Ich bin gerade abwesend")
        self.abwesend = False

        self.master = master
        self.master.title("Chat GUI")
        self.frame = tk.Frame(master, bg="#f2f2f2", padx=15, pady=15)
        self.frame.grid(row=0, column=0,  sticky='nsew')
        self.master.configure(bg="#e6e6e6")


        # Neuer Frame links für die Nutzerliste
        self.nutzer_frame = tk.Frame(self.frame, bg="#ffffff", relief="solid")
        self.nutzer_frame.grid(row=0, column=4, rowspan=4, padx=(15, 0), pady=10, sticky='ns')

        self.nutzer_label = tk.Label(self.nutzer_frame, text="Online Nutzer:", bg="#ffffff", font=("Segoe UI", 10, "bold"))
        self.nutzer_label.pack(anchor="nw", padx=10, pady=5)

        self.nutzer_listbox = tk.Listbox(self.nutzer_frame, width=20, height=20, bg="#f9f9f9", fg="#000", bd=0, highlightthickness=0)
        self.nutzer_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        self.nutzer_listbox.pack(fill=tk.BOTH, expand=True)
        

        self.handle = simpledialog.askstring("Name", "Dein Benutzername:")

        udp_send("WHO", "255.255.255.255", self.whoisport)  # Sende WHO-Nachricht beim Start

        # Setze dynamisch den Empfangsport je nach Benutzername
        if self.handle == "Sara":

            self.empfangs_port = 5001
        elif self.handle == "Floranda":

            self.empfangs_port = 5002
        else:
            self.empfangs_port = 5560  # Backup-Port für neue Namen

        self.ziel = tk.StringVar(value="(niemand)")  # Standardwert für Empfänger
        self.chatbox = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, state='disabled', width=60, height=20, 
                                                          bg="#ffffff", fg="#000000", font=("Segoe UI", 10), bd=1, relief="solid")
        self.chatbox.grid(row=0, column=0, columnspan=4, pady=(0, 10))

        self.entry = tk.Entry(self.frame, width=40)
        self.entry.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky='we')
        self.entry.bind("<Return>", self.sende_nachricht)

        self.send_button = ttk.Button(self.frame, text="Senden", command=self.sende_nachricht)
        self.send_button.grid(row=1, column=2, pady=(0, 10), sticky='we')

        self.image_button = ttk.Button(self.frame, text="Bild senden", command=self.bild_senden)
        self.image_button.grid(row=1, column=3, pady=(0, 10), sticky='we')

        self.ziel_label = ttk.Label(self.frame, text="Empfänger:")
        self.ziel_label.grid(row=2, column=0, sticky='w')

        initial_choices = list(bekannte_nutzer.keys()) or["(niemand)"]
        self.ziel.set(initial_choices[0])  # Setze Standardwert

        self.ziel_menu = ttk.OptionMenu(self.frame, self.ziel, *initial_choices)
        self.ziel_menu.grid(row=2, column=1, sticky='w')

        self.name_button = ttk.Button(self.frame, text="Name ändern", command=self.name_aendern)
        self.name_button.grid(row=2, column=2, pady=(0, 10), sticky='we')

        self.exit_button = ttk.Button(self.frame, text="Verlassen", command=self.beenden)
        self.exit_button.grid(row=2, column=3, pady=(0, 10), sticky='we')

        self.verlauf_button = ttk.Button(self.frame, text="Verlauf speichern", command=self.speichere_verlauf)
        self.verlauf_button.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        self.ip_label = tk.Label(self.frame, text=f"Deine IP: {get_own_ip()}")
        self.ip_label.grid(row=3, column=2, columnspan=2, pady=(10, 0), sticky='e')

        self.empfang_thread = threading.Thread(target=self.empfange_tcp, daemon=True)
        self.empfang_thread.start()
        
        self.discovery_thread = threading.Thread(
            target=udp_listener,
            args=(self.whoisport, self.verarbeitete_udp_nachricht),
            daemon=True
        )
        self.discovery_thread.start()

        # Join + WHO-Nachrichten senden
        time.sleep(1)  # Warten, damit Listener bereit sind
        udp_send(f"JOIN {self.handle} {self.empfangs_port}", "255.255.255.255", self.whoisport)
        time.sleep(1)
        udp_send("WHO", "255.255.255.255", self.whoisport)

    def verarbeitete_udp_nachricht(self, message, addr):
        teile = message.strip().split()   
        if not teile:
            return
        cmd = teile[0]
        
        if cmd == "JOIN" and len(teile) == 3:
            handle = teile[1]
            port = int(teile[2])
            ip = addr[0]
            
            bekannte_nutzer[handle] = (ip, port)
            self.schreibe_chat(f"[JOIN] Neuer Nutzer: {handle} @ {ip}:{port}")
            self.update_ziel_menu()

        elif cmd == "KNOWUSERS":
            eintraege = " ".join(teile[1:]).split(", ")
            for eintrag in eintraege:
                try:
                    handle, ip, port = eintrag.split()
                    bekannte_nutzer[handle] = (ip, int(port))
                except:
                    continue
            self.update_ziel_menu() 

        elif cmd == "LEAVE" and len(teile) == 2:
            handle = teile[1]
            if handle in bekannte_nutzer:
                del bekannte_nutzer[handle]
                self.schreibe_chat(f"[LEAVE] Nutzer {handle} hat den Chat verlassen.")
               
    
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
        self.entry.delete(0, tk.END) # Leere das Eingabefeld sofort nach dem Senden
        ziel = self.ziel.get()
        if ziel in bekannte_nutzer:
            ip, port = bekannte_nutzer[ziel]
            try:
                tcp_send(f"MSG {self.handle} {nachricht}", ip, port)
                self.schreibe_chat(f"(an {ziel}) {self.handle}: {nachricht}")
            except Exception as e:
                self.schreibe_chat(f"[FEHLER] Nachricht nicht gesendet: {e}")
            threading.Thread(target=senden, daemon=True).start()
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

    def update_ziel_menu(self):
        aktuelle_auswahl = self.ziel.get()

        # Aktualisiere die Nutzerliste in der Listbox
        self.nutzer_listbox.delete(0, 'end')
        for name in bekannte_nutzer.keys():
            self.nutzer_listbox.insert(tk.END, name)

        # Menü komplett neu aufbauen
        self.ziel_menu.destroy()
        self.ziel_menu = ttk.OptionMenu(self.frame, self.ziel, None, *bekannte_nutzer.keys())
        self.ziel_menu.grid(row=2, column=1, sticky='w')


        #Empfänger automatisch auf den ersten Eintrag setzen, wenn nichts ausgewählt ist oder der Eintrag nicht mehr existiert
        if aktuelle_auswahl == "(niemand)" or aktuelle_auswahl not in bekannte_nutzer:
            if bekannte_nutzer:
                neuer_empfaenger = list(bekannte_nutzer.keys())[-1]  # Letzter Eintrag in der Liste
                self.ziel.set(neuer_empfaenger)
            else:
                self.ziel.set("(niemand)")


    def beenden(self):
        self.speichere_verlauf()
        self.master.destroy()
        udp_send(f"LEAVE {self.handle}", "255.255.255.255", self.whoisport)


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

                        if self.abwesend and text.startswith("MSG"):
                            try:
                                teile = text.split()
                                absender = teile [1]
                                if absender != self.handle:
                                    ip = addr [0]
                                    antwort = f"MSG {self.handle} {self.autoreply_text}"
                                    tcp_send(antwort, ip, self.empfangs_port)
                                    self.schreibe_chat(f"(Auto-Reply an {absender}) {self.autoreply_text}")
                            except Exception as e:
                                print("[Auto-Reply Fehler]", e)     
                    except UnicodeDecodeError:
                        dateiname = f"empfangenes_bild_{int(time.time())}.jpg"
                        with open(dateiname, "wb") as f:
                            f.write(daten)
                        self.schreibe_chat(f"[Bild empfangen von {addr[0]}] Gespeichert als {dateiname}")

if __name__ == "__main__":
    root = tk.Tk()
    gui = ChatGUI(root)
    root.mainloop()