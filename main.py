import threading 
import time
import atexit 
import socket
from network import load_config, udp_listener, tcp_server, udp_send
from cli import start_cli 

# @file main.py
# @brief Einstiegspunkt des Chatprogramms. Startet Netzwerkdienste und meldet den Client im lokalen Netzwerk an.

# === Konfiguration laden ===
cfg = load_config()
tcp_port = cfg["port"][0]
udp_port = cfg["port"][1]
handle = cfg["handle"]
whoisport = cfg["whoisport"]

# # === Lokale IP ermitteln (Debug/Info-Zwecke) ===
def get_own_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"

local_ip = get_own_ip()
print(f"[INFO] {handle} ist erreichbar unter {local_ip}:{tcp_port}")

# === LEAVE-Nachricht beim Beenden senden ===
def clean_exit():
    udp_send(f"LEAVE {handle}", "255.255.255.255", whoisport)

atexit.register(clean_exit)

# === Listener und Server starten ===
threading.Thread(target=udp_listener, args=(whoisport,), daemon=True).start()  # Discovery (JOIN/WHO/LEAVE)
threading.Thread(target=udp_listener, args=(udp_port,), daemon=True).start()   # Nachrichten-Empfang via UDP
threading.Thread(target=tcp_server, args=(tcp_port,), daemon=True).start()     # TCP-Empfang (MSG, IMG)

# === Beitritt zum Netzwerk (JOIN) und Anfrage nach Teilnehmern (WHO) ===
time.sleep(1) # Warten, damit Listener bereit sind
udp_send(f"JOIN {handle} {tcp_port}", "255.255.255.255", whoisport)

time.sleep(1)
udp_send("WHO", "255.255.255.255", whoisport)

# === CLI starten (z. B. mit /msg, /verlauf, /nutzer etc.) ===
try:
    start_cli()
except Exception as e:
    print(f"[WARNUNG] CLI nicht gefunden oder Fehler: {e}")
    print("[INFO] Programm bleibt im Leerlauf aktiv.")
    while True:
        time.sleep(1)