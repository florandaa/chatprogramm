import threading 
import time
import atexit 
import signal
import socket
import sys
from network import load_config, udp_listener, tcp_server, udp_send
from cli import start_cli, chat_verlauf, parse_args  # parse_args importiert


# @file main.py
# @brief Einstiegspunkt des Chatprogramms. Startet Netzwerkdienste und meldet den Client im lokalen Netzwerk an.

# === CLI-Argumente lesen ===
args = parse_args()

# === Konfiguration laden ===
config_path = getattr(args, "config", "config.toml")
config = load_config(config_path)

# === CLI-Overrides anwenden ===
if args.handle:
    config["handle"] = args.handle
if args.port:
    config["port"] = args.port
if args.autoreply:
    config["autoreply"] = args.autoreply
if args.whoisport:
    config["whoisport"] = args.whoisport
if args.broadcast_ip:
    config["broadcast_ip"] = args.broadcast_ip

# === Konfig-Werte extrahieren ===
broadcast_ip = config.get("broadcast_ip", "255.255.255.255")
tcp_port = config["port"][0]
udp_port = config["port"][1]
handle = config["handle"]
whoisport = config["whoisport"]
benutzername = config.get("handle", "Benutzer")  # Fehler behoben

known_users = {}  # Globale Nutzerliste

# === UDP-Handler (JOIN) ===
def handle_udp_message(message, addr):
    parts = message.strip().split()
    if parts[0] == "JOIN" and len(parts) == 3:
        user_handle = parts[1]
        user_port = int(parts[2])
        sender_ip = addr[0]
        known_users[user_handle] = (sender_ip, user_port)
        print(f"[INFO] Neuer Nutzer bekannt: {user_handle} @ {sender_ip}:{user_port}")

# === TCP-Handler (MSG etc.) ===
def handle_tcp_message(message):
    print(f"[MSG] {message}")
    chat_verlauf.append(message)

# === Debug-Ausgabe ===
print(f"[DEBUG] Geladene Konfigurationsdatei: {config_path}")
print("[DEBUG] Aktive Konfiguration:")
for key, value in config.items():
    print(f"{key} = {value}")

# === Lokale IP ermitteln ===
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
    udp_send(f"LEAVE {handle}", broadcast_ip, whoisport)

atexit.register(clean_exit)

# === Listener starten ===
if config_path != "config2.toml":
    threading.Thread(target=udp_listener, args=(whoisport, handle_udp_message), daemon=True).start()
threading.Thread(target=udp_listener, args=(udp_port, handle_udp_message), daemon=True).start()
threading.Thread(target=tcp_server, args=(tcp_port, handle_tcp_message), daemon=True).start()

# === Netzwerkbeitritt ===
time.sleep(1)
udp_send(f"JOIN {handle} {tcp_port}", broadcast_ip, whoisport)

time.sleep(1)
udp_send("WHO", broadcast_ip, whoisport)


# === CLI starten ===
try:
    start_cli(known_users)  # known_users statt []
except Exception as e:
    print(f"[WARNUNG] CLI nicht gefunden oder Fehler: {e}")
    print("[INFO] Programm bleibt im Leerlauf aktiv.")
    while True:
        time.sleep(1)

# === STRG+C behandeln ===
def handle_sigint(signum, frame):
    clean_exit()
    print("[INFO] Programm wurde beendet.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)


# === Testdaten(vor der Abgabe entfernen CLI schnell testen) ===
known_users["Sara"] = ("10.54.143.52", 5001)
known_users["Floranda"] = ("10.55.140.182", 5002)
