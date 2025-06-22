"""
@file chat_gui_client.py
@brief GUI-Client für das P2P-Chatsystem

Diese Implementierung erfüllt alle Projektanforderungen:
- SLCP-Protokoll (JOIN, WHO, KNOWNUSERS, MSG, IMG, LEAVE)
- Peer-to-Peer ohne zentralen Server
- Kombination aus UDP (Discovery) und TCP (Nachrichten/Bilder)
- Konfiguration über config.toml
"""

import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import tkinter.ttk as ttk
import threading
import socket
import os
import sys
import time
import queue
from network import load_config
from PIL import Image, ImageTk
from io import BytesIO

# Farben und Stile
BG_COLOR = "#f0f0f0"
TEXT_BG = "#ffffff"
BUTTON_COLOR = "#4a90e2"
FONT = ("Helvetica", 10)

class ChatGUI:
    def __init__(self, master, config):
        """
        @brief Initialisiert die Chat-GUI
        @param master: Tkinter Root-Window
        @param config: Konfigurationsdictionary aus config.toml
        """
        self.master = master
        self.config = config
        self.running = True
        
        # Netzwerkparameter
        self.handle = config["handle"]
        self.udp_port = config["port"][0]
        self.tcp_port = config["port"][1]
        self.whoisport = config["whoisport"]
        self.imagepath = config.get("imagepath", "./received_images")
        self.autoreply = config.get("autoreply", "Ich bin nicht verfügbar")
        
        # Datenstrukturen
        self.known_users = {}  # {handle: (ip, port)}
        self.chat_queue = queue.Queue()
        self.last_autoreply = {}
        
        # Verzeichnis für Bilder erstellen
        os.makedirs(self.imagepath, exist_ok=True)
        
        # GUI initialisieren
        self.setup_gui()
        
        # Netzwerk starten
        self.start_network()
        
        # Initiale Nachrichten senden
        self.send_join()
        threading.Thread(target=self.send_who, daemon=True).start()
        
        # Queue-Processing starten
        self.master.after(100, self.process_queue)

    def setup_gui(self):
        """@brief Erstellt alle GUI-Komponenten"""
        self.master.title(f"ChA12Room - {self.handle}")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Hauptframe
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Chat-Anzeige
        self.chat_display = scrolledtext.ScrolledText(
            main_frame, 
            width=60, 
            height=20,
            wrap=tk.WORD,
            bg=TEXT_BG,
            font=FONT
        )
        self.chat_display.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.chat_display.config(state=tk.DISABLED)
        
        # Nutzerliste
        self.user_listbox = tk.Listbox(
            main_frame,
            height=20,
            width=20,
            bg=TEXT_BG,
            font=FONT
        )
        self.user_listbox.grid(row=0, column=2, padx=5, pady=5, sticky="ns")
        
        # Nachrichteneingabe
        self.message_entry = ttk.Entry(main_frame, width=50, font=FONT)
        self.message_entry.grid(row=1, column=0, padx=5, pady=5, sticky="we")
        self.message_entry.bind("<Return>", self.send_message)
        
        # Empfänger-Auswahl
        self.recipient_var = tk.StringVar()
        self.recipient_menu = ttk.Combobox(
            main_frame,
            textvariable=self.recipient_var,
            state="readonly",
            width=15,
            font=FONT
        )
        self.recipient_menu.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        self.recipient_menu["values"] = ["(Broadcast)"]
        self.recipient_menu.current(0)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=5, sticky="we")
        
        self.send_button = ttk.Button(
            button_frame,
            text="Senden",
            command=self.send_message,
            style="Accent.TButton"
        )
        self.send_button.pack(side=tk.LEFT, padx=2)
        
        self.image_button = ttk.Button(
            button_frame,
            text="Bild senden",
            command=self.send_image_dialog
        )
        self.image_button.pack(side=tk.LEFT, padx=2)
        
        self.abwesend_var = tk.BooleanVar()
        self.abwesend_check = ttk.Checkbutton(
            button_frame,
            text="Abwesend",
            variable=self.abwesend_var
        )
        self.abwesend_check.pack(side=tk.LEFT, padx=2)
        
        self.leave_button = ttk.Button(
            button_frame,
            text="Verlassen",
            command=self.on_close,
            style="Danger.TButton"
        )
        self.leave_button.pack(side=tk.RIGHT, padx=2)
        
        # Layout anpassen
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Stile
        style = ttk.Style()
        style.configure("Accent.TButton", background=BUTTON_COLOR, foreground="white")
        style.configure("Danger.TButton", background="#e74c3c", foreground="white")

    def start_network(self):
        """Startet Netzwerkkomponenten – nutzt externen Discovery-Dienst"""
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # NICHT BINDEN – Discovery läuft extern!
        # self.udp_socket.bind(("0.0.0.0", self.whoisport))  ← RAUS!

        # TCP Server
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.tcp_socket.bind(("0.0.0.0", self.tcp_port))
        except OSError as e:
            self.tcp_socket.bind(("0.0.0.0", 0))
            self.tcp_port = self.tcp_socket.getsockname()[1]
            self.queue_update(f"[System] Verwende Port {self.tcp_port}")
        
        self.tcp_socket.listen()
        threading.Thread(target=self.tcp_listener, daemon=True).start()


    def udp_listener(self):
        """@brief Hört auf UDP-Nachrichten (JOIN, WHO, LEAVE)"""
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                message = data.decode().strip()
                
                if message.startswith("JOIN") and len(message.split()) == 3:
                    _, handle, port = message.split()
                    self.known_users[handle] = (addr[0], int(port))
                    self.queue_update(f"[System] {handle} ist dem Chat beigetreten")
                    
                elif message == "WHO":
                    known_users_str = " ".join(
                        [f"{h} {ip} {p}" for h, (ip, p) in self.known_users.items()]
                    )
                    response = f"KNOWNUSERS {known_users_str}"
                    self.udp_socket.sendto(response.encode(), addr)
                    
                elif message.startswith("KNOWNUSERS"):
                    users = message.split()[1:]
                    for i in range(0, len(users), 3):
                        if i+2 < len(users):
                            handle, ip, port = users[i], users[i+1], users[i+2]
                            if handle != self.handle:
                                self.known_users[handle] = (ip, int(port))
                    self.queue_update("[System] Nutzerliste aktualisiert")
                    
                elif message.startswith("LEAVE") and len(message.split()) == 2:
                    handle = message.split()[1]
                    if handle in self.known_users:
                        del self.known_users[handle]
                        self.queue_update(f"[System] {handle} hat den Chat verlassen")
                        
            except Exception as e:
                self.queue_update(f"[Fehler] UDP: {str(e)}")

    def tcp_listener(self):
        """@brief Hört auf TCP-Nachrichten (MSG, IMG)"""
        while self.running:
            try:
                conn, addr = self.tcp_socket.accept()
                threading.Thread(
                    target=self.handle_tcp_connection,
                    args=(conn, addr),
                    daemon=True
                ).start()
            except Exception as e:
                self.queue_update(f"[Fehler] TCP: {str(e)}")

    def handle_tcp_connection(self, conn, addr):
        """@brief Verarbeitet eine einzelne TCP-Verbindung"""
        try:
            data = conn.recv(1024)
            if not data:
                return
                
            if data.startswith(b"MSG"):
                parts = data.decode().split(maxsplit=2)
                if len(parts) == 3:
                    _, sender, text = parts
                    self.queue_update(f"{sender}: {text}")
                    
                    # Autoreply wenn abwesend
                    if self.abwesend_var.get() and sender != self.handle:
                        now = time.time()
                        if now - self.last_autoreply.get(sender, 0) > 30:  # 30s Cooldown
                            self.send_message_to(sender, self.autoreply)
                            self.last_autoreply[sender] = now
                            
            elif data.startswith(b"IMG"):
                try:
                    header, img_data = data.split(b"\n", 1)
                    parts = header.decode().split()
                    if len(parts) >= 3:
                        _, sender, size = parts[:3]
                        filename = f"img_{int(time.time())}.png"
                        filepath = os.path.join(self.imagepath, filename)
                        
                        with open(filepath, "wb") as f:
                            f.write(img_data)
                            
                        self.queue_update(f"{sender} hat ein Bild gesendet", filepath)
                except Exception as e:
                    self.queue_update(f"[Fehler] Bildempfang: {str(e)}")
                    
        finally:
            conn.close()

    def send_join(self):
        """@brief Sendet JOIN-Nachricht an alle"""
        message = f"JOIN {self.handle} {self.tcp_port}"
        self.udp_socket.sendto(
            message.encode(),
            ("255.255.255.255", self.whoisport)
        )

        # Eigener Nutzer zur known_users-Liste hinzufügen 👇
        try:
            eigene_ip = socket.gethostbyname(socket.gethostname())
            self.known_users[self.handle] = (eigene_ip, self.tcp_port)
        except Exception as e:
            self.queue_update(f"[Fehler] Eigene IP konnte nicht ermittelt werden: {e}")


    def send_who(self):
        """@brief Sendet WHO-Nachricht an alle"""
        time.sleep(1)  # Warten bis JOIN verarbeitet wurde
        self.udp_socket.sendto(
            b"WHO",
            ("255.255.255.255", self.whoisport)
        )

    def send_message(self, event=None):
        """@brief Sendet eine Textnachricht"""
        text = self.message_entry.get().strip()
        if not text:
            return
            
        recipient = self.recipient_var.get()
        self.message_entry.delete(0, tk.END)
        
        if recipient == "(Broadcast)":
            for user, (ip, port) in self.known_users.items():
                if user != self.handle:
                    self.send_message_to(user, text)
            self.queue_update(f"(An alle) {self.handle}: {text}")
        else:
            self.send_message_to(recipient, text)
            self.queue_update(f"(An {recipient}) {self.handle}: {text}")

    def send_message_to(self, recipient, text):
        """@brief Sendet Nachricht an bestimmten Nutzer"""
        if recipient in self.known_users:
            ip, port = self.known_users[recipient]
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    s.sendall(f"MSG {self.handle} {text}".encode())
            except Exception as e:
                self.queue_update(f"[Fehler] Nachricht an {recipient}: {str(e)}")

    def send_image_dialog(self):
        """@brief Öffnet Dialog zum Senden eines Bildes"""
        filepath = filedialog.askopenfilename(
            title="Bild auswählen",
            filetypes=[("Bilder", "*.png;*.jpg;*.jpeg;*.gif")]
        )
        if not filepath:
            return
            
        recipient = self.recipient_var.get()
        if recipient == "(Broadcast)":
            messagebox.showerror("Fehler", "Bilder können nicht an alle gesendet werden")
            return
            
        if recipient not in self.known_users:
            messagebox.showerror("Fehler", "Empfänger nicht gefunden")
            return
            
        try:
            with open(filepath, "rb") as f:
                img_data = f.read()
                
            ip, port = self.known_users[recipient]
            header = f"IMG {self.handle} {len(img_data)} {os.path.basename(filepath)}"
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.sendall(header.encode() + b"\n" + img_data)
                
            self.queue_update(f"Bild an {recipient} gesendet: {os.path.basename(filepath)}")
        except Exception as e:
            self.queue_update(f"[Fehler] Bildsendung: {str(e)}")

    def queue_update(self, message, image_path=None):
        """@brief Fügt Nachricht/Bild zur Verarbeitung in die Queue ein"""
        self.chat_queue.put((message, image_path))

    def process_queue(self):
        """@brief Verarbeitet Nachrichten aus der Queue (im Hauptthread)"""
        try:
            while True:
                message, image_path = self.chat_queue.get_nowait()
                self.update_chat_display(message, image_path)
                self.update_user_list()
        except queue.Empty:
            pass
            
        self.master.after(100, self.process_queue)

    def update_chat_display(self, message, image_path=None):
        """@brief Aktualisiert die Chat-Anzeige"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n")
        
        if image_path:
            try:
                img = Image.open(image_path)
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                
                # Bild in Textwidget einfügen
                self.chat_display.image_create(tk.END, image=photo)
                self.chat_display.insert(tk.END, "\n")
                
                # Referenz behalten
                self.chat_display.image = photo
            except Exception as e:
                self.chat_display.insert(tk.END, f"[Fehler beim Bildanzeigen: {str(e)}]\n")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def update_user_list(self):
        """@brief Aktualisiert die Nutzerliste"""
        current_users = sorted(self.known_users.keys())
        current_recipients = ["(Broadcast)"] + [u for u in current_users if u != self.handle]
        
        # Nutzerliste aktualisieren
        self.user_listbox.delete(0, tk.END)
        for user in current_users:
            self.user_listbox.insert(tk.END, user)
            
        # Empfänger-Menü aktualisieren
        current_selection = self.recipient_var.get()
        self.recipient_menu["values"] = current_recipients
        
        if current_selection not in current_recipients:
            self.recipient_var.set("(Broadcast)")

    def on_close(self):
        """@brief Behandelt das Schließen der GUI"""
        if self.running:
            self.running = False
            self.udp_socket.sendto(
                f"LEAVE {self.handle}".encode(),
                ("255.255.255.255", self.whoisport)
            )
            self.udp_socket.close()
            self.tcp_socket.close()
            self.master.destroy()

def start_gui(config):
    """@brief Startet die GUI mit gegebener Konfiguration"""
    root = tk.Tk()
    try:
        ChatGUI(root, config)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fehler", f"Kritischer Fehler: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    # Argumentparser für direkte GUI-Nutzung
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle", required=True)
    parser.add_argument("--port", nargs=2, type=int, required=True)
    parser.add_argument("--whoisport", type=int, required=True)
    args = parser.parse_args()
    
    # Konfiguration erstellen
    config = {
        "handle": args.handle,
        "port": args.port,
        "whoisport": args.whoisport,
        "imagepath": "./received_images",
        "autoreply": "Ich bin nicht verfügbar"
    }
    
    # GUI starten
    root = tk.Tk()
    ChatGUI(root, config)
    root.mainloop()