# @file discovery.py
# @brief Discovery-Dienst für ein Peer-to-Peer-Netzwerk
# @details Verwaltet Teilnehmerinformationen über UDP-Nachrichten, verarbeitet JOIN, WHO und LEAVE Befehle.

import socket
import threading
import toml
import os
import time

# === Konfiguration laden ===
pfad = os.path.abspath("config.toml")
config = toml.load(pfad) 
handle = config['handle']
tcp_port = config['port'][0]
udp_port = config['port'][1]
whoisport = config['whoisport']

# === Socket einrichten (UDP + Broadcast) ===
socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
socket1.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
socket1.bind(('', whoisport))

# === Teilnehmerliste ===
participants = {}  # Format: {handle: (ip, port)}

# === Discovery-Dienst starten ===
## @brief Startet den Discovery-Dienst (JOIN, WHO, LEAVE)
## @details Wird in einem Thread ausgeführt, reagiert auf UDP-Nachrichten
def discovery_loop():
    while True:
        data, addr = socket1.recvfrom(1024)
        message = data.decode('utf-8').strip()
        parts = message.split()

        if not parts:
            continue

        command = parts[0]

        # --- JOIN-Befehl ---
        if command == "JOIN" and len(parts) == 3:
            handle = parts[1]
            port = int(parts[2])
            ip = addr[0]

            if handle not in participants:
                participants[handle] = (ip, port)
                print(f"[JOIN] {handle} hinzugefügt: {ip}:{port}")
            else:
                participants[handle] = (ip, port)
                print(f"[JOIN] {handle} bereits vorhanden, aktualisiere Eintrag.")

        # --- WHO-Befehl ---
        elif command == "WHO":
            print(f"[WHO] Anfrage erhalten von {addr[0]}")
            entries = [f"{h} {ip} {p}" for h, (ip, p) in participants.items()]
            response = "KNOWUSERS " + ", ".join(entries)
            socket1.sendto(response.encode('utf-8'), addr)

        # --- LEAVE-Befehl ---
        elif command == "LEAVE" and len(parts) == 2:
            handle = parts[1]
            if handle in participants:
                del participants[handle]
                print(f"[LEAVE] {handle} wurde entfernt.")
            else:
                print(f"[LEAVE] {handle} nicht gefunden.")

# === Discovery-Dienst im Hintergrund starten ===
threading.Thread(target=discovery_loop, daemon=True).start()

# === Endlosschleife für Programmlebensdauer ===
while True:
    time.sleep(1)
