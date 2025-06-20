# @file discovery.py
# @brief Discovery-Dienst für ein Peer-to-Peer-Netzwerk
# @details Verwaltet Teilnehmerinformationen über UDP-Nachrichten, verarbeitet JOIN, WHO und LEAVE Befehle.

import socket
import threading
import toml
import os
import time


## Verwendung der Konfiguration aus der config.toml Datei
config = toml.load(os.path.abspath("config.toml"))## Lädt die Konfiguration aus der config.toml Datei
handle = config['handle']
tcp_port = config['port'][0]
udp_port = config['port'][1]
whoisport = config['whoisport']
debug_mode = True

# === Socket einrichten (UDP + Broadcast) ===

## Erstellen eines UDP Sockets
socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
## Erlauben, dass der Socket die Adresse wiederverwendet
socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
## Erlauben, dass der Socket Broadcast-Nachrichten sendet
socket1.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
##Verbindung des Sockets mit dem Port
socket1.bind(('', whoisport))

## Dictionary zur Speicherung der Teilnehmer 
participants = {}  # Format: {handle: (ip, port)}

# === Discovery-Dienst starten ===
## @brief Eine Endlosschleife, die auf eingehende Nachrichten wartet(Sie empfängt dauerhaft UDP-Nachrichten)
def discovery_loop():
    while True:
        try:
            data, addr = socket1.recvfrom(1024)
            ## data=Inhalt, addr=(IP,Port des Absenders)-Empfangen von Daten (max. 1024 Bytes)
            message = data.decode('utf-8').strip()
            ## Dekodieren der empfangenen Daten von Bytes in Text/String. 
            ## strip() entfernt führende und nachfolgende Leerzeichen
            if debug_mode:
                    print(f"[DEBUG] Empfangen von {addr}: {message}")
            
            parts = message.split()
            ##Zerlegen der Nachricht in Teile, getrennt durch Leerzeichen

            if not parts:
                continue
                ##Wenn die Nachricht leer ist, überspringe den Rest der Schleife

            command = parts[0]
            ## Liest den ersten Teil der Nachricht als Befehl(zb. JOIN,WHO,LEAVe)

            # --- JOIN-Befehl ---
            if command == "JOIN" and len(parts) == 3:
                ## Überprüfen, ob der Befehl "JOIN" ist. len(parts) == 3 stellt sicher, dass genau 3 Teile vorhanden sind
                handle = parts[1] ## Name
                port = int(parts[2])## Portnummer
                participants[handle] = (addr[0], port)
                print(f"[JOIN] {handle} registriert bei {addr[0]}:{port}")

            # --- WHO-Befehl ---
            elif command == "WHO":
                print(f"[WHO] Anfrage erhalten von {addr[0]}")
                entries = [f"{h} {ip} {p}" for h, (ip, p) in participants.items()]
                ## Erstellen einer Liste von Einträgen "Handle IP Port"
                response = "KNOWUSERS " + ", ".join(entries)
                ## Zusammenfügen der Einträge zu einer Antwort
                socket1.sendto(response.encode('utf-8'), addr)
                ## Senden der Antwort an die IP-Adresse des Absenders 
                if debug_mode:
                        print(f"[DEBUG] Sende an {addr}: {response}")

            # --- LEAVE-Befehl ---
            elif command == "LEAVE" and len(parts) == 2:
                handle = parts[1] ## Name des Teilnehmers, der den Raum verlassen möchte
                if handle in participants:
                    ## Überprüft, ob der Teilnehmer im Dictionary vorhanden ist
                    del participants[handle]## Entfernen des Teilnehmers aus dem Dictionary
                    print(f"[LEAVE] {handle} wurde entfernt.")
                else:
                    print(f"[LEAVE] {handle} nicht gefunden.")
        
        except Exception as e:
                print(f"[FEHLER] Discovery-Fehler: {e}")

    
## Schleife damit es im Hintergrund läuft
threading.Thread(target=discovery_loop, daemon=True).start()

# === Endlosschleife für Programmlebensdauer ===
while True:
    time.sleep(1)
