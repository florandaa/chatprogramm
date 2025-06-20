import tkinter as tk
from tkinter import scrolledtext, simpledialog, filedialog
import threading 
import time
import json
import socket
import os
import sys
import queue
import tkinter.ttk as ttk
from network import load_config, tcp_send, udp_send, udp_listener
from cli import get_own_ip

bekannte_nutzer = {}  # Globale Variable für bekannte Nutzer
chat_verlauf = []  # Chatverlauf zur Anzeige und Speicherung

# @file chat_gui_client.py

class ChatGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("ChA12Room")

        config = load_config()
        self.config = config
        self.broadcast_ip = self.config.get("broadcast_ip") or "192.168.2.255"


        # CLI-Overrides
        args = sys.argv[1:]

        def get_arg(name, count=1, default=None, cast=str):
            if name in args:
                i = args.index(name)
                try:
                    if count == 1:
                        return cast(args[i + 1])
                    else:
                        return [cast(arg) for arg in args[i + 1:i + 1 + count]]
                except (IndexError, ValueError):
                    print(f"[WARNUNG] Ungültiges Argument für {name}, Standard wird verwendet.")
            return default

        config["handle"] = get_arg("--handle", 1, self.config.get("handle"), str)
        config["whoisport"] = get_arg("--whoisport", 1, config.get("whoisport"), int)
        config["port"] = get_arg("--port", 2, config.get("port"), int)
        config["autoreply"] = get_arg("--autoreply", 1, config.get("autoreply"), str)
        config["broadcast_ip"] = get_arg("--broadcast_ip", 1, config.get("broadcast_ip"), str)
        config["imagepath"] = get_arg("--imagepath", 1, config.get("imagepath"), str)

        self.whoisport = self.config.get("whoisport")
        if self.whoisport == 0:
            print("[INFO] UDP-Discovery deaktiviert.")
        else:
            print(f"[UDP] Wartet auf Port {self.whoisport}...")
            self.discovery_thread = threading.Thread(
                target=udp_listener,
                args=(self.whoisport, self.verarbeitete_udp_nachricht),
                daemon=True
            )
            self.discovery_thread.start()
        self.autoreply_text = self.config.get("autoreply", "Ich bin gerade abwesend")
        self.abwesend = False

        self.letzte_autoreply = {}  # Speichert die letzte Autoreply-Nachricht pro Nutzer
        self.autoreply_cooldown = 30  # Cooldown-Zeit für Autoreplies in Sekunden

        self.running = True  # Flag, um den Hauptthread zu steuern
        
        
        self.gui_queue = queue.Queue()  # Queue für GUI-Updates
        self.master.after(100, self.verarbeitete_gui_queue)  # Starte Queue-Verarbeitung
        
        # NEU: Lokale Peer-Datei einlesen bei whoisport == 0
        if self.whoisport == 0:
            try:
                with open("peer_info.json", "r") as f:
                    info = json.load(f)
                    bekannte_nutzer[info["handle"]] = (info["ip"], info["port"])
                    self.gui_queue.put((self.update_ziel_menu, ()))
                    print(f"[INFO] Lokale Peer-Info geladen: {info}")
            except Exception as e:
                print(f"[WARNUNG] Konnte peer_info.json nicht laden: {e}")

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
        

        self.handle = get_arg("--handle", 1, None, str) 
        if not self.handle:
            self.handle = simpledialog.askstring("Name", "Bitte gib deinen Benutzernamen ein:")
        config["handle"] = self.handle # Sicherstellen, dass der Handle in der Konfiguration gespeichert wird
        #Zuerst einen freien Port suchen
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_socket:
            temp_socket.bind(('', 0))
            self.empfangs_port = temp_socket.getsockname()[1]  # Dynamisch einen freien Port       
        

        # Wenn Discovery aktiv ist, speichere eigene Info für lokale Fallbacks
        if self.whoisport > 0:
            with open("peer_info.json", "w") as f:
                json.dump({"handle": self.handle, "ip": get_own_ip(), "port": self.empfangs_port}, f)
       
       
        if self.whoisport > 0:
            self.discovery_thread = threading.Thread(
                target=udp_listener,
                args=(self.whoisport, self.verarbeitete_udp_nachricht),
                daemon=True
            )
            self.discovery_thread.start()



        #Frühzeitig JOIN senden, damit andere Nutzer dich sehen können
        if self.whoisport > 0:
            time.sleep(1)  # Warten, damit Listener bereit sind
            eigene_ip = get_own_ip()
            join_msg = f"JOIN {self.handle} {eigene_ip} {self.empfangs_port}"
            udp_send(join_msg, self.broadcast_ip, self.whoisport)

            # Zusatz: sende JOIN direkt an localhost für lokalen Empfang
            udp_send(join_msg, "127.0.0.1", self.whoisport)

            bekannte_nutzer[self.handle] = (get_own_ip(), self.empfangs_port)  # Füge dich selbst hinzu
            self.gui_queue.put((self.update_ziel_menu, ()))  # Aktualisiere die Nutzerliste

            # Zusätzlicher WHO-Send nur, wenn UDP erlaubt ist
        if self.whoisport > 0:
            time.sleep(1)  # Warten, damit andere Nutzer dich sehen können
            udp_send("WHO", self.broadcast_ip, self.whoisport)  # Sende WHO-Nachricht beim Start
 
        # # Als Notlösung: füge Sara manuell zu Ilirjons bekannte_nutzer hinzu
        # if self.whoisport == 0:
        #     print("[INFO] Fallback: füge Sara lokal hinzu")
        #     bekannte_nutzer["Sara"] = ("127.0.0.1", 51588)
        

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

        self.abwesen_button = ttk.Button(self.left_area, text="Abwesenheit: AUS", command=self.toggle_abwesenheit)
        self.abwesen_button.grid(row=4, column=0, columnspan=2, pady=(5, 0), sticky='we')


        self.status_label = ttk.Label(self.left_area, text="", anchor="w", font=("Segoe UI", 9, "italic"))
        self.status_label.grid(row=5, column=0, columnspan=4, sticky='w', pady=(5, 0))
                                      

        self.empfang_thread = threading.Thread(target=self.empfange_tcp, daemon=True)
        self.empfang_thread.start()
        
        self.server_socket = None

        self.aktualisiere_status()


    def verarbeitete_udp_nachricht(self, message, addr):
        teile = message.strip().split()   
        if not teile:
            return
        
        cmd = teile[0]
        
        if cmd == "JOIN" and len(teile) == 4:
            handle = teile[1]
            ip = teile[2]
            port = int(teile[3])


            # # Wenn Nutzer schon bekannt und IP+Port gleich sind überspringen 
            # if handle in bekannte_nutzer:
            #     gespeicherte_ip, gespeicherter_port = bekannte_nutzer[handle]
            #     if gespeicherte_ip == ip and gespeicherter_port == port:
            #         return
        
            bekannte_nutzer[handle] = (ip, port)
            self.gui_queue.put((self.schreibe_chat, (f"[JOIN] Neuer Nutzer: {handle} @ {ip}:{port}",)))
            self.gui_queue.put((self.update_ziel_menu, ()))
            self.gui_queue.put((self.schreibe_chat, (f"[INFO] Nutzerliste aktualisiert: {list(bekannte_nutzer.keys())}",)))
            
            # # Antwort mit eigener Nutzertabelle an den neuen CLient senden'
            # antwort = "KNOWUSERS " + " ".join([f"{h} {ip} {port}" for h, (ip, port) in bekannte_nutzer.items()])
            # udp_send(antwort, ip, self.whoisport)

            # Sende eigenen JOIN zurück, aber nur wenn der ander Name ungleich ich ist
            if handle != self.handle:
                join_msg = f"JOIN {self.handle} {self.empfangs_port}"
                for _ in range(2): # 2x Zuverlässigkeit
                    udp_send(join_msg, ip, self.whoisport)
                    time.sleep(0.2)
            
            # Sende auch Knowusers mehrfach
            antwort = "KNOWUSERS " + " ".join([f"{h} {ip} {port}" for h, (ip, port) in bekannte_nutzer.items()])
            for _ in range(2):
                udp_send(antwort, ip, self.whoisport)
                time.sleep(0.2)
           
            # for _ in range(2):
            #     udp_send(antwort, ip, self.whoisport)
            #     time.sleep(0.15)


        elif cmd == "KNOWUSERS":
            daten = teile[1:]
            print(f"[DEBUG] KNOWUSERS empfangen von {addr}: {daten}")

            for i in range(0, len(daten), 3):
                try:
                    handle = daten[i]
                    ip = daten[i + 1]
                    port = int(daten[i +2])
                    # # Nur hinzufügen wenn noch nicht vorhanden
                    # if handle not in bekannte_nutzer:
                    bekannte_nutzer[handle] = (ip, port)
                except IndexError:
                    continue

            self.gui_queue.put((self.update_ziel_menu,()))
            self.gui_queue.put((self.schreibe_chat, (f"[INFO] Nutzerliste aktualisiert: {list(bekannte_nutzer.keys())}",)))

            
            
            # eintraege = " ".join(teile[1:]).split(", ")
            # for eintrag in eintraege:
            #     try:
            #         handle, ip, port = eintrag.split()
            #         bekannte_nutzer[handle] = (ip, int(port))
            #     except:
            #         continue
            # self.gui_queue.put((self.schreibe_chat, (f"[INFO] Nutzerliste aktualisiert: {list(bekannte_nutzer.keys())}",)))
            # self.gui_queue.put((self.update_ziel_menu, ()))
            

        elif cmd == "LEAVE" and len(teile) == 2:
            handle = teile[1]
            if handle in bekannte_nutzer:
                del bekannte_nutzer[handle]
                self.gui_queue.put((self.schreibe_chat, (f"[LEAVE] Nutzer {handle} hat den Chat verlassen.",)))
                self.gui_queue.put((self.update_ziel_menu, ()))
                
               
    def verarbeitete_gui_queue(self):
        try:
            while True:
                func, args = self.gui_queue.get_nowait()
                func(*args)
        except queue.Empty:
            pass
        self.master.after(100, self.verarbeitete_gui_queue)  # Weiterverarbeiten
    def schreibe_chat(self, text):
        def gui_action(text):
            self.chatbox.configure(state='normal')
            self.chatbox.insert(tk.END, text + "\n")
            self.chatbox.configure(state='disabled')
            self.chatbox.yview(tk.END)
            chat_verlauf.append(text)
        self.gui_queue.put((gui_action, (text,)))  # Argument wird korrekt übergeben
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
        pfad = filedialog.askopenfilename(
            title="Bild auswählen",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg"), ("JPEG", "*.jpeg"), ("GIF", "*.gif"), ("Alle Dateien", "*.*")]
        )
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
        neue_liste = list(sorted(bekannte_nutzer.keys()))
        if neue_liste == getattr(self, "aktuelle_nutzer_liste", []):
            return # Keine Änderung, also nichts tun
        self.alte_nutzer_liste = neue_liste # Speichere die alte Liste für zukünftige Vergleiche

        print("[DEBUG] Zielmenü aktualisiert:", list(bekannte_nutzer.keys()))

        def gui_action():
            aktuelle_auswahl = self.ziel.get()

            self.nutzer_listbox.delete(0, 'end')
            for name in bekannte_nutzer.keys():
                self.nutzer_listbox.insert(tk.END, name)

            # Aktualisiere die Nutzerliste im Listbox-Widget   
            self.ziel_menu.destroy()
            self.ziel_menu = ttk.OptionMenu(self.left_area, self.ziel, *bekannte_nutzer.keys())
            self.ziel_menu.grid(row=2, column=1, sticky='w', padx=(0, 5))
            
            # Wenn die aktuelle Auswahl nicht mehr existiert, setze sie auf "(niemand)"
            if aktuelle_auswahl not in neue_liste:
                if neue_liste:
                    self.ziel.set(neue_liste[-1])
                else:
                    self.ziel.set("(niemand)")
           
        self.gui_queue.put((gui_action, (),))  # Füge die Aktion der Queue hinzu

    def toggle_abwesenheit(self):
        self.abwesend = not self.abwesend
        status = "EIN" if self.abwesend else "AUS"
        self.abwesen_button.config(text=f"Abwesenheit: {status}")
        self.schreibe_chat(f"[INFO] Abwesenheitsmodus ist jetzt {status}.")
        self.aktualisiere_status()

    def beenden(self):
        self.running = False  # Stoppe TCP-Schleife
        if self.whoisport > 0:
            udp_send(f"LEAVE {self.handle}", self.broadcast_ip, self.whoisport)
            self.speichere_verlauf()
            if self.server_socket:
                try:
                    self.server_socket.close()  # Schließe den TCP-Server-Socket
                    print("[INFO] TCP-Server geschlossen.")
                except Exception as e:
                    print(f"[WARNUNG] Fehler beim Schließen des TCP-Servers: {e}")
            self.master.destroy()

    def aktualisiere_status(self):
        status_text = f"IP: {get_own_ip()} | Port: {self.empfangs_port} | "
        status_text += "Abwesend" if self.abwesend else "Aktiv"
        self.status_label.config(text=status_text)
        self.master.after(3000, self.aktualisiere_status)  # Aktualisiere alle 3 Sekunden

    def empfange_tcp(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket = server
        try:
            server.bind(("0.0.0.0", self.empfangs_port))
            print(f"TCP-Server gestartet auf Port {self.empfangs_port}")
        except Exception as e:
            print(f"[FEHLER] Konnte TCP-Port {self.empfangs_port} nicht binden: {e}")
            self.schreibe_chat(f"[FEHLER] TCP-Port {self.empfangs_port} blockiert- bitte firewall prüfen.")
            return
        server.listen()
        server.settimeout(1)  # Setze Timeout für accept
        while self.running:
            try:
                conn, addr = server.accept()
                with conn:
                    daten = b""
                    while True:
                        packet = conn.recv(1024)
                        if not packet:
                            break
                        daten += packet
                    try:
                        text = daten.decode()
                        self.gui_queue.put((self.schreibe_chat, (f"[Empfangen von {addr[0]}] {text}",)))
                    


                        if self.abwesend and text.startswith("MSG"):
                            try:
                                teile = text.split()
                                absender = teile[1]
                                if absender != self.handle:
                                    ip = addr[0]

                                    # Prüfe Cooldown
                                    jetzt = time.time()
                                    zuletzt = self.letzte_autoreply.get(absender, 0)

                                    if jetzt - zuletzt >= self.autoreply_cooldown:
                                        antwort = f"MSG {self.handle} {self.autoreply_text}"
                                        tcp_send(antwort, ip, self.empfangs_port)
                                        self.letzte_autoreply[absender] = jetzt
                                        self.gui_queue.put((self.schreibe_chat, (f"(Auto-Reply an {absender}) {self.autoreply_text}",)))
                                    else:
                                        print(f"[Auto-Reply] Cooldown aktiv für {absender}, warte noch {self.autoreply_cooldown - (jetzt - zuletzt):.1f} Sekunden.")

                            except Exception as e:
                                print("[Auto-Reply Fehler]", e)
    
                    except UnicodeDecodeError:
                        pfad = os.path.expanduser(self.config.get("imagepath", "."))
                        os.makedirs(pfad, exist_ok=True)
                        dateiname = os.path.join(pfad, f"empfangenes_bild_{int(time.time())}.jpg")
                        with open(dateiname, "wb") as f:
                            f.write(daten)
                        self.gui_queue.put((self.schreibe_chat, (f"[Bild empfangen von {addr[0]}] Gespeichert als {dateiname}",)))
            except socket.timeout:
                continue  




if __name__ == "__main__":
    root = tk.Tk()
    gui = ChatGUI(root)
    root.mainloop()    
      