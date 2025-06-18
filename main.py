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
debug_mode = getattr(args, "debug", False)

config_path = getattr(args, "config", "config.toml")
config = load_config(config_path)
globals()["config"] = config

# === CLI-Overrides anwenden ===
if args.handle: config["handle"] = args.handle
if args.port: config["port"] = args.port
if args.autoreply: config["autoreply"] = args.autoreply
if args.whoisport: config["whoisport"] = args.whoisport
if args.broadcast_ip: config["broadcast_ip"] = args.broadcast_ip

# === Konfig extrahieren ===
broadcast_ip = config.get("broadcast_ip", "255.255.255.255")
tcp_port, udp_port = config["port"]
handle = config["handle"]
whoisport = config["whoisport"]
known_users = {}

# === UDP-Nachrichten verarbeiten ===
def handle_udp_message(message, addr):
    if debug_mode:
        print(f"[DEBUG] UDP empfangen: {message} von {addr}")
    parts = message.strip().split()
    if parts[0] == "JOIN" and len(parts) == 3:
        user_handle = parts[1]
        user_port = int(parts[2])
        known_users[user_handle] = (addr[0], user_port)
        print(f"[INFO] Neuer Nutzer: {user_handle} @ {addr[0]}:{user_port}")


# === TCP-Nachrichten verarbeiten ===
def handle_tcp_message(message):
    if debug_mode:
        print(f"[DEBUG] TCP empfangen: {message}")
    print(f"[MSG] {message}")
    chat_verlauf.append(message)

# === Lokale IP anzeigen ===
def get_own_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"
if debug_mode:
    print(f"[DEBUG] Konfigurationsdatei: {config_path}")
    print("[DEBUG] Aktive Konfiguration:")
    for key, value in config.items():
        print(f"  {key} = {value}")

print(f"[INFO] {handle} erreichbar unter {get_own_ip()}:{tcp_port}")

# === Beenden-Handler ===
def clean_exit():
    udp_send(f"LEAVE {handle}", broadcast_ip, whoisport)
    print("[INFO] LEAVE gesendet.")

atexit.register(clean_exit)
signal.signal(signal.SIGINT, lambda s, f: (clean_exit(), sys.exit(0)))

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
    start_cli(known_users)
except Exception as e:
    print(f"[WARNUNG] CLI nicht verfügbar: {e}")
    while True:
        time.sleep(1)


