# chat_gui_client.py
import tkinter as tk
from tkinter import scrolledtext, filedialog
import tkinter.ttk as ttk
import threading, socket, os, sys, time, queue
from network import load_config, udp_send, tcp_send, udp_listener, tcp_server
from cli import get_own_ip

bekannte_nutzer = {}
chat_verlauf = []

class ChatGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("ChA12Room")
        self.running = True

        config = load_config()
        args = sys.argv[1:]
        def get_arg(name, count=1, default=None, cast=str):
            if name in args:
                try:
                    idx = args.index(name)
                    if count == 1:
                        return cast(args[idx + 1])
                    else:
                        return [cast(x) for x in args[idx + 1:idx + 1 + count]]
                except: return default
            return default

        self.config = config
        self.handle = get_arg("--handle", 1, config.get("handle", "Gast"), str)
        self.ports = get_arg("--port", 2, config.get("port", [5000, 5001]), int)
        self.whoisport = get_arg("--whoisport", 1, config.get("whoisport", 4000), int)
        self.autoreply_text = get_arg("--autoreply", 1, config.get("autoreply", "Bin gerade nicht da"), str)
        self.broadcast_ip = get_arg("--broadcast_ip", 1, config.get("broadcast_ip", "255.255.255.255"), str)
        self.abwesend = False
        self.letzte_autoreply = {}
        self.verlauf_datei = f"chatverlauf_{self.handle}.txt"
        self.join_gesendet = False

        self.chat_queue = queue.Queue()
        self.master.after(100, self.verarbeite_gui_queue)

        self.port1, self.port2 = self.ports
        self.ip = get_own_ip()
        bekannte_nutzer[self.handle] = (self.ip, self.port2)

        self.build_gui()

        threading.Thread(target=udp_listener, args=(self.whoisport, self.handle, self.chat_queue), daemon=True).start()
        threading.Thread(target=tcp_server, args=(self.port2, self.chat_queue, self.handle), daemon=True).start()

        self.sende_join()

    def build_gui(self):
        self.chatbox = scrolledtext.ScrolledText(self.master, state='disabled', width=60, height=20)
        self.chatbox.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        self.nutzer_listbox = tk.Listbox(self.master, height=20, width=20)
        self.nutzer_listbox.grid(row=0, column=3, padx=(0,10), pady=10, sticky='ns')

        self.eingabe = tk.Entry(self.master, width=50)
        self.eingabe.grid(row=1, column=0, padx=10, sticky='we')
        self.eingabe.bind("<Return>", self.sende_nachricht)

        self.send_button = ttk.Button(self.master, text="Senden", command=self.sende_nachricht)
        self.send_button.grid(row=1, column=1)

        self.img_button = ttk.Button(self.master, text="Bild senden", command=self.bild_senden)
        self.img_button.grid(row=1, column=2)

        self.leave_button = ttk.Button(self.master, text="Verlassen", command=self.beenden)
        self.leave_button.grid(row=1, column=3)

        self.abwesend_var = tk.BooleanVar()
        self.abwesend_check = tk.Checkbutton(self.master, text="Abwesenheit", variable=self.abwesend_var, command=self.toggle_abwesenheit)
        self.abwesend_check.grid(row=2, column=3, sticky="w", padx=10)

        self.ziel_var = tk.StringVar()
        self.ziel_menu = ttk.Combobox(self.master, textvariable=self.ziel_var, state="readonly")
        self.ziel_menu.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="we")
        self.ziel_menu['values'] = ["(alle)"]
        self.ziel_menu.set("(alle)")

    def toggle_abwesenheit(self):
        self.abwesend = self.abwesend_var.get()

    def sende_join(self):
        if self.join_gesendet:
            return
        self.join_gesendet = True
        msg = f"JOIN {self.handle} {self.port2}"
        for _ in range(2):
            udp_send(msg, self.broadcast_ip, self.whoisport)
            time.sleep(0.2)
        udp_send("WHO", self.broadcast_ip, self.whoisport)

    def sende_nachricht(self, event=None):
        text = self.eingabe.get().strip()
        if not text: return
        self.eingabe.delete(0, tk.END)
        ziel = self.ziel_var.get()

        if ziel == "(alle)":
            for name, (ip, port) in bekannte_nutzer.items():
                if name != self.handle:
                    tcp_send(f"MSG {self.handle} {text}", ip, port)
            self.chat_queue.put((lambda: self.schreibe_chat(f"(an alle) {self.handle}: {text}"), ()))
        elif ziel in bekannte_nutzer:
            ip, port = bekannte_nutzer[ziel]
            tcp_send(f"MSG {self.handle} {text}", ip, port)
            self.chat_queue.put((lambda: self.schreibe_chat(f"(an {ziel}) {self.handle}: {text}"), ()))

    def bild_senden(self):
        pfad = filedialog.askopenfilename(filetypes=[("Bilder", "*.png;*.jpg;*.jpeg;*.gif")])
        if not pfad: return
        ziel = self.ziel_var.get()
        try:
            with open(pfad, "rb") as f:
                inhalt = f.read()
            dateiname = os.path.basename(pfad)
            nachricht = f"IMG {self.handle} {dateiname}"
            datenpaket = nachricht.encode() + b"\n" + inhalt
            if ziel == "(alle)":
                for name, (ip, port) in bekannte_nutzer.items():
                    if name != self.handle:
                        tcp_send(datenpaket, ip, port, binary=True)
            elif ziel in bekannte_nutzer:
                ip, port = bekannte_nutzer[ziel]
                tcp_send(datenpaket, ip, port, binary=True)
            self.chat_queue.put((lambda: self.schreibe_chat(f"[Bild gesendet an {ziel}]: {dateiname}"), ()))
        except Exception as e:
            self.chat_queue.put((lambda: self.schreibe_chat(f"[Fehler beim Bildversand: {e}]"), ()))

    def schreibe_chat(self, text):
        self.chatbox.config(state='normal')
        self.chatbox.insert(tk.END, text + "\n")
        self.chatbox.config(state='disabled')
        self.chatbox.yview(tk.END)
        chat_verlauf.append(text)
        self.speichere_zeile(text)

    def speichere_zeile(self, text):
        try:
            with open(self.verlauf_datei, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception as e:
            print(f"[Fehler beim Speichern]: {e}")

    def update_online_nutzer(self):
        self.nutzer_listbox.delete(0, tk.END)
        nutzer = sorted(bekannte_nutzer.keys())
        for name in nutzer:
            self.nutzer_listbox.insert(tk.END, name)
        self.ziel_menu['values'] = ["(alle)"] + [n for n in nutzer if n != self.handle]
        if self.ziel_var.get() not in self.ziel_menu['values']:
            self.ziel_var.set("(alle)")

    def verarbeite_gui_queue(self):
        try:
            while True:
                func, args = self.chat_queue.get_nowait()
                func(*args)
        except queue.Empty:
            pass
        self.master.after(100, self.verarbeite_gui_queue)

    def beenden(self):
        if self.whoisport > 0:
            udp_send(f"LEAVE {self.handle}", self.broadcast_ip, self.whoisport)
        bekannte_nutzer.pop(self.handle, None)
        self.chat_queue.put((lambda: self.update_online_nutzer(), ()))
        self.running = False
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    gui = ChatGUI(root)
    root.mainloop()
