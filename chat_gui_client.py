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
        self.broadcast_ip = config.get("broadcast_ip", "255.255.255.255")
        self.abwesend = False

        self.master = master
        self.master.title("ChA12Room")

        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        self.frame = ttk.Frame(master, padding=15)
        self.frame.grid(row=0, column=0,  sticky='nsew')
        # Linker Bereich: Chatbereich
        self.left_area = ttk.Frame(self.frame)
        self.left_area.grid(row=0, column=0, sticky='nsew')

        # Rechter Bereich: Nutzerliste 
        #self.right_area = ttk.Frame(self.frame, width=200)
        #self.right_area.grid(row=0, column=1, sticky='ns', padx=(15, 0))

        #Grid-Anpassungen
        self.frame.columnconfigure(0, weight=3) # Chatbereich  wächst ein wenig stärker
        self.frame.columnconfigure(1, weight=1) # Nutzerliste bleibt schmaler
        self.frame.rowconfigure(0, weight=1) 

        self.master.configure(bg="#e6e6e6")

        self.style = ttk.Style()
        self.style.theme_use("clam")  # Verwende das "clam" Theme für bessere Kompatibilität
        self.style.configure("TFrame", background="#f5f7fa")

        self.style.configure("TButton", 
                            background="#4CAF50", foreground="white",
                            font=("Segoe UI", 10, "bold"),
                            padding=6, borderwidth=0)
        self.style.map("TButton",
                        background=[('active', '#2f6cd1'), 
                                    ('disabled', '#cccccc')]) 
        
        self.style.configure("TEntry",
                            font=("Segoe UI", 10),
                            padding=5)

        # Neuer Frame links für die Nutzerliste
        self.nutzer_frame = ttk.Frame(self.frame, padding=10)
        self.nutzer_frame.grid(row=0, column=1, rowspan=4, padx=(10, 0), pady=10, sticky='ns')

        self.nutzer_label = tk.Label(self.nutzer_frame, text="Online Nutzer:", font=("Segoe UI", 12, "bold"),
        fg="#4CAF50", bg="#f5f7fa",anchor="center",justify="center")
        self.nutzer_label.pack(anchor="center", pady=(5, 10))

        self.nutzer_listbox = tk.Listbox(self.nutzer_frame, width=18, height=20, bg="#ffffff", fg="#333333", highlightthickness=1,
                                        relief="solid", selectbackground="#cce5ff", selectforeground="#000000",)
        self.nutzer_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        self.nutzer_listbox.pack(fill=tk.BOTH, expand=True)
        

        self.handle = simpledialog.askstring("Name", "Dein Benutzername:")
       
        #Zuerst einen freien Port suchen
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_socket:
            temp_socket.bind(('', 0))
            self.empfangs_port = temp_socket.getsockname()[1]  # Dynamisch einen freien Port       
        self.port_label = ttk.Label(self.left_area, text=f"Empfangsport: {self.empfangs_port}")
        self.port_label.grid(row=4, column=2, columnspan=2, sticky='e', pady=(5, 0))
       
        self.discovery_thread = threading.Thread(
            target=udp_listener,
            args=(self.whoisport, self.verarbeitete_udp_nachricht),
            daemon=True
        )   
        self.discovery_thread.start()

        #Frühzeitig JOIN senden, damit andere Nutzer dich sehen können
        time.sleep(1)  # Warten, damit Listener bereit sind
        udp_send(f"JOIN {self.handle} {self.empfangs_port}", self.broadcast_ip, self.whoisport)  

        udp_send("WHO", self.broadcast_ip, self.whoisport)  # Sende WHO-Nachricht beim Start
 
        

        self.ziel = tk.StringVar(value="(niemand)")  # Standardwert für Empfänger
        self.chatbox = scrolledtext.ScrolledText(self.left_area, wrap=tk.WORD, state='disabled', width=60, height=20, 
                                                          bg="#ffffff", fg="#333333", font=("Segoe UI", 10), 
                                                          bd=0, relief="flat", padx=10, pady=10)
        self.chatbox.grid(row=0, column=0, columnspan=4, pady=(0, 15), padx=(0, 10), sticky='nsew')

        self.entry = ttk.Entry(self.left_area, width=40)
        self.entry.grid(row=1, column=0, columnspan=2, pady=(0, 10),padx=(0, 5), sticky='we')
        self.entry.bind("<Return>", self.sende_nachricht)

        self.send_button = ttk.Button(self.left_area, text="Senden", command=self.sende_nachricht)
        self.send_button.grid(row=1, column=2, pady=(0, 10), padx=5, sticky='we')

        self.image_button = ttk.Button(self.left_area, text="Bild senden", command=self.bild_senden)
        self.image_button.grid(row=1, column=3, pady=(0, 10), padx=5, sticky='we')

        self.ziel_label = ttk.Label(self.left_area, text="Empfänger:")
        self.ziel_label.grid(row=2, column=0, sticky='w', padx=(0, 5))

        initial_choices = list(bekannte_nutzer.keys()) or["(niemand)"]
        self.ziel.set(initial_choices[0])  # Setze Standardwert

        self.ziel_menu = ttk.OptionMenu(self.left_area, self.ziel, *initial_choices)
        self.ziel_menu.grid(row=2, column=1, sticky='w', padx=(0, 5))

        self.name_button = ttk.Button(self.left_area, text="Name ändern", command=self.name_aendern)
        self.name_button.grid(row=2, column=2, pady=(0, 10),padx=(0, 5), sticky='we')

        self.exit_button = ttk.Button(self.left_area, text="Verlassen", command=self.beenden)
        self.exit_button.grid(row=2, column=3, pady=(0, 10), sticky='we')

        self.verlauf_button = ttk.Button(self.left_area, text="Verlauf speichern", command=self.speichere_verlauf)
        self.verlauf_button.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        self.ip_label = ttk.Label(self.left_area, text=f"Deine IP: {get_own_ip()}")
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
        udp_send(f"JOIN {self.handle} {self.empfangs_port}", self.broadcast_ip, self.whoisport)
        time.sleep(1)
        udp_send("WHO", self.broadcast_ip, self.whoisport)

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
            self.schreibe_chat(f"[INFO] Nutzerliste aktualisiert: {list(bekannte_nutzer.keys())}")
            
            # Antwort mit eigener Nutzertaabelle an den neuen CLient senden'
            antwort = "KNOWUSERS " + ", ".join([f"{h} {ip} {port}" for h, (ip, port) in bekannte_nutzer.items()])
            udp_send(antwort, addr[0], self.whoisport)

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
                self.update_ziel_menu()
               
    
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
        self.ziel_menu = ttk.OptionMenu(self.left_area, self.ziel, *bekannte_nutzer.keys())
        self.ziel_menu.grid(row=2, column=1, sticky='w', padx=(0, 5))


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
        udp_send(f"LEAVE {self.handle}", self.broadcast_ip, self.whoisport)


    def empfange_tcp(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            try:
                server.bind(("0.0.0.0", self.empfangs_port))
                print(f"TCP-Server gestartet auf Port {self.empfangs_port}")
            except Exception as e:
                print(f"[FEHLER] Konnte TCP-Port {self.empfangs_port} nicht binden: {e}")
                self.schreibe_chat(f"[FEHLER] TCP-Port {self.empfangs_port} blockiert- bitte firewall prüfen.")
                return
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