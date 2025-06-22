# @file chat_gui_client_final.py
# @brief Finale Version der Chat-GUI mit Dark Mode, Bildversand, Discovery-Integration und Bugfixes

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

BG_COLOR = "#f0f0f0"
TEXT_BG = "#ffffff"
BUTTON_COLOR = "#4a90e2"
FONT = ("Helvetica", 10)
MAX_MSG_LENGTH = 512

class ChatGUI:
    def __init__(self, master, config):
        self.master = master
        self.config = config
        self.running = True

        self.handle = config["handle"]
        self.udp_port = config["port"][0]
        self.tcp_port = config["port"][1]
        self.whoisport = config["whoisport"]
        self.imagepath = config.get("imagepath", "./received_images")
        self.autoreply = config.get("autoreply", "Ich bin nicht verf\u00fcgbar")

        self.known_users = {}
        self.chat_queue = queue.Queue()
        self.last_autoreply = {}
        self.chat_display_refs = []

        os.makedirs(self.imagepath, exist_ok=True)

        self.setup_gui()
        self.start_network()

        self.send_join()
        threading.Thread(target=self.listen_for_joins, daemon=True).start()
        threading.Thread(target=self.send_who, daemon=True).start()

        self.master.after(100, self.process_queue)

    def setup_gui(self):
        self.dark_mode = tk.BooleanVar(value=False)
        self.master.title(f"ChA12Room - {self.handle}")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        menubar = tk.Menu(self.master)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(label="Dunkelmodus", variable=self.dark_mode, command=self.toggle_theme)
        menubar.add_cascade(label="Ansicht", menu=view_menu)
        self.master.config(menu=menubar)

        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.chat_display = scrolledtext.ScrolledText(main_frame, width=60, height=20, wrap=tk.WORD, bg=TEXT_BG, font=FONT)
        self.chat_display.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.chat_display.config(state=tk.DISABLED)

        self.user_listbox = tk.Listbox(main_frame, height=20, width=20, bg=TEXT_BG, font=FONT)
        self.user_listbox.grid(row=0, column=2, padx=5, pady=5, sticky="ns")

        self.message_entry = ttk.Entry(main_frame, width=50, font=FONT)
        self.message_entry.grid(row=1, column=0, padx=5, pady=5, sticky="we")
        self.message_entry.bind("<Return>", self.send_message)

        self.recipient_var = tk.StringVar()
        self.recipient_menu = ttk.Combobox(main_frame, textvariable=self.recipient_var, state="readonly", width=15, font=FONT)
        self.recipient_menu.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        self.recipient_menu["values"] = ["(Broadcast)"]
        self.recipient_menu.current(0)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=5, sticky="we")

        self.send_button = ttk.Button(button_frame, text="Senden", command=self.send_message, style="Accent.TButton")
        self.send_button.pack(side=tk.LEFT, padx=2)

        self.image_button = ttk.Button(button_frame, text="Bild senden", command=self.send_image_dialog)
        self.image_button.pack(side=tk.LEFT, padx=2)

        self.abwesend_var = tk.BooleanVar()
        self.abwesend_check = ttk.Checkbutton(button_frame, text="Abwesend", variable=self.abwesend_var)
        self.abwesend_check.pack(side=tk.LEFT, padx=2)

        self.leave_button = ttk.Button(button_frame, text="Verlassen", command=self.on_close, style="Danger.TButton")
        self.leave_button.pack(side=tk.RIGHT, padx=2)

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.layout("Accent.TButton", style.layout("TButton"))
        style.configure("Accent.TButton", background=BUTTON_COLOR, foreground="white", font=FONT)
        style.layout("Danger.TButton", style.layout("TButton"))
        style.configure("Danger.TButton", background="#e74c3c", foreground="white", font=FONT)

    def start_network(self):
        self.join_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.join_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.join_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            self.join_socket.bind(("", self.whoisport))
            threading.Thread(target=self.listen_for_joins, daemon=True).start()
        except OSError:
            self.queue_update("[Info] JOIN-Empfang deaktiviert (Discovery l\u00e4uft bereits)")

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(("", 0))

        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.tcp_socket.bind(("0.0.0.0", self.tcp_port))
        except OSError:
            self.tcp_socket.bind(("0.0.0.0", 0))
            self.tcp_port = self.tcp_socket.getsockname()[1]
            self.queue_update(f"[Info] TCP-Port automatisch gewechselt auf {self.tcp_port}")
        self.tcp_socket.listen()

        threading.Thread(target=self.tcp_listener, daemon=True).start()
        threading.Thread(target=self.udp_knownusers_listener, daemon=True).start()

    def tcp_listener(self):
        while self.running:
            try:
                conn, addr = self.tcp_socket.accept()
                threading.Thread(target=self.handle_tcp_connection, args=(conn, addr), daemon=True).start()
            except:
                pass

    def handle_tcp_connection(self, conn, addr):
        try:
            data = conn.recv(1024)
            if data.startswith(b"MSG"):
                parts = data.decode().split(maxsplit=2)
                if len(parts) == 3:
                    _, sender, text = parts
                    self.queue_update(f"{sender}: {text}")
                    if self.abwesend_var.get() and sender != self.handle:
                        now = time.time()
                        if now - self.last_autoreply.get(sender, 0) > 30:
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
        message = f"JOIN {self.handle} {self.tcp_port}"
        self.udp_socket.sendto(message.encode(), ("255.255.255.255", self.whoisport))

    def send_who(self):
        time.sleep(1)
        self.udp_socket.sendto(b"WHO", ("255.255.255.255", self.whoisport))

    def send_message(self, event=None):
        text = self.message_entry.get().strip()
        if not text or len(text.encode("utf-8")) > MAX_MSG_LENGTH:
            self.queue_update("[Fehler] Nachricht zu lang oder leer.")
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
        if recipient in self.known_users:
            ip, port = self.known_users[recipient]
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect((ip, port))
                    s.sendall(f"MSG {self.handle} {text}".encode())
            except:
                self.queue_update(f"[Fehler] Nachricht an {recipient} fehlgeschlagen")

    def send_image_dialog(self):
        filepath = filedialog.askopenfilename(title="Bild ausw\u00e4hlen", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg")])
        if not filepath:
            return
        recipient = self.recipient_var.get()
        if recipient == "(Broadcast)":
            messagebox.showerror("Fehler", "Bilder k\u00f6nnen nicht an alle gesendet werden")
            return
        if recipient not in self.known_users:
            messagebox.showerror("Fehler", "Empf\u00e4nger nicht gefunden")
            return
        try:
            with open(filepath, "rb") as f:
                img_data = f.read()
            ip, port = self.known_users[recipient]
            header = f"IMG {self.handle} {len(img_data)} {os.path.basename(filepath)}"
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((ip, port))
                s.sendall(header.encode() + b"\n" + img_data)
            self.queue_update(f"Bild an {recipient} gesendet: {os.path.basename(filepath)}")
        except Exception as e:
            self.queue_update(f"[Fehler] Bildsendung: {str(e)}")

    def queue_update(self, message, image_path=None):
        self.chat_queue.put((message, image_path))

    def process_queue(self):
        try:
            while True:
                message, image_path = self.chat_queue.get_nowait()
                self.update_chat_display(message, image_path)
                self.update_user_list()
        except queue.Empty:
            pass
        self.master.after(100, self.process_queue)

    def update_chat_display(self, message, image_path=None):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n")
        if image_path:
            try:
                img = Image.open(image_path)
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                self.chat_display.image_create(tk.END, image=photo)
                self.chat_display.insert(tk.END, "\n")
                self.chat_display_refs.append(photo)  # Verhindert GC
            except Exception as e:
                self.chat_display.insert(tk.END, f"[Fehler beim Bildanzeigen: {str(e)}]\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def listen_for_joins(self):
        while self.running:
            try:
                data, addr = self.join_socket.recvfrom(1024)
                message = data.decode().strip()
                if message.startswith("JOIN"):
                    parts = message.split()
                    if len(parts) == 3:
                        handle, port = parts[1], int(parts[2])
                        if handle != self.handle:
                            self.known_users[handle] = (addr[0], port)
                            self.queue_update(f"[System] {handle} ist dem Chat beigetreten")
            except:
                pass

    def udp_knownusers_listener(self):
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                message = data.decode().strip()
                if message.startswith("KNOWNUSERS"):
                    users_raw = message[len("KNOWNUSERS "):].strip()
                    parts = users_raw.split()
                    for i in range(0, len(parts), 3):
                        if i + 2 < len(parts):
                            handle, ip, port = parts[i], parts[i + 1], int(parts[i + 2])
                            if handle != self.handle:
                                self.known_users[handle] = (ip, port)
                    self.queue_update("[System] Nutzerliste aktualisiert")
            except:
                pass

    def update_user_list(self):
        current_users = sorted(self.known_users.keys())
        if self.handle not in current_users:
            self.known_users[self.handle] = ("127.0.0.1", self.tcp_port)
            current_users.append(self.handle)
        current_recipients = ["(Broadcast)"] + [u for u in current_users if u != self.handle]
        self.user_listbox.delete(0, tk.END)
        for user in current_users:
            self.user_listbox.insert(tk.END, user)
        current_selection = self.recipient_var.get()
        self.recipient_menu["values"] = current_recipients
        if current_selection not in current_recipients:
            self.recipient_var.set("(Broadcast)")

    def toggle_theme(self):
        style = ttk.Style()
        if self.dark_mode.get():
            style.configure("TEntry", fieldbackground="#2e2e2e", foreground="#f0f0f0")
            self.chat_display.config(bg="#1e1e1e", fg="#f0f0f0")
            self.user_listbox.config(bg="#1e1e1e", fg="#f0f0f0")
            self.message_entry.configure(background="#2e2e2e", foreground="#f0f0f0")
        else:
            style.configure("TEntry", fieldbackground=TEXT_BG, foreground="black")
            self.chat_display.config(bg=TEXT_BG, fg="black")
            self.user_listbox.config(bg=TEXT_BG, fg="black")
            self.message_entry.configure(background=TEXT_BG, foreground="black")

    def on_close(self):
        if self.running:
            self.running = False
            self.udp_socket.sendto(f"LEAVE {self.handle}".encode(), ("255.255.255.255", self.whoisport))
            self.udp_socket.close()
            self.tcp_socket.close()
            self.master.destroy()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle", required=True)
    parser.add_argument("--port", nargs=2, type=int, required=True)
    parser.add_argument("--whoisport", type=int, required=True)
    args = parser.parse_args()

    config = {
        "handle": args.handle,
        "port": args.port,
        "whoisport": args.whoisport,
        "imagepath": "./received_images",
        "autoreply": "Ich bin nicht verf\u00fcgbar"
    }

    root = tk.Tk()
    ChatGUI(root, config)
    root.mainloop()
