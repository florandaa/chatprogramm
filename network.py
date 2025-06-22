##
# @file network.py
# @brief Netzwerk-Utilities für das Chatprogramm.
#
# Stellt Funktionen für das Senden und Empfangen von UDP- und TCP-Nachrichten, 
# Laden der Konfiguration und Hilfsfunktionen bereit.
##

import socket
import threading
import toml
import os

## 
# @var debug_mode
# @brief Schaltet zusätzliche Debug-Ausgaben im Netzwerkmodul ein/aus.
debug_mode = False

##
# @brief Lädt die Konfiguration aus einer TOML-Datei.
# @param path Pfad zur TOML-Datei (Default: "config.toml").
# @return Dictionary mit Konfigurationsdaten.
def load_config(path="config.toml"):
    return toml.load(os.path.abspath(path))

##
# @brief Startet einen UDP-Listener, der eingehende Nachrichten verarbeitet.
#
# Erstellt einen UDP-Socket, lauscht auf dem angegebenen Port und 
# ruft optional ein Callback für jede eingehende Nachricht auf.
#
# @param port Port, auf dem gelauscht werden soll.
# @param callback Funktion, die aufgerufen wird, wenn eine Nachricht empfangen wird (message, addr).
def udp_listener(port, callback=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", port))
   
    if debug_mode:
        print(f"[DEBUG] UDP-Listener auf Port {port}")
   
    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode().strip()
        if debug_mode:
            print(f"[DEBUG] UDP empfangen von {addr}: {message}")
        if callback:
            callback(message, addr)

##
# @brief Sendet eine UDP-Nachricht an eine gegebene IP und Port.
#
# Öffnet einen neuen UDP-Socket, setzt Broadcast (falls nötig) und sendet die Nachricht.
# Gibt im Fehlerfall eine Fehlermeldung aus.
#
# @param message Zu sendende Nachricht (String)
# @param ip Ziel-IP-Adresse (z. B. "255.255.255.255" für Broadcast)
# @param port Ziel-Port (z. B. 4000)
def udp_send(message, ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # WICHTIG für Broadcast
   
    if debug_mode:
        print(f"[DEBUG] UDP senden an {ip}:{port} → {message}")
   
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if ip.endswith(".255"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        sock.sendto(message.encode(), (ip, port))
    except Exception as e:
        print(f"[FEHLER] UDP-Senden: {e}")
    finally:
        sock.close()

##
# @brief Startet einen TCP-Server, der auf eingehende Verbindungen wartet.
#
# Lauscht auf dem gegebenen Port, nimmt eingehende TCP-Verbindungen entgegen und 
# ruft optional ein Callback mit den empfangenen Daten auf.
#
# @param port Port für den TCP-Server.
# @param callback Funktion, die für jede Nachricht aufgerufen wird (data).
def tcp_server(port, callback=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen()
    print(f"[TCP] Server auf Port {port}")
   
    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024).decode("utf-8")
        if debug_mode:
            print(f"[DEBUG] TCP empfangen von {addr}: {data}")
        if callback:
            callback(data)
        conn.close()

##
# @var MAX_MSG_LENGTH
# @brief Maximale Länge einer Textnachricht (Zeichen).
MAX_MSG_LENGTH = 512  # Oberes Limit für Nachrichtenlänge

##
# @brief Sendet eine Nachricht via TCP (Text oder Binärdaten).
#
# Baut eine TCP-Verbindung auf, prüft die Nachrichtenlänge (für Text), 
# sendet die Nachricht (Text oder Binärdaten) und schließt die Verbindung.
#
# @param message Die zu sendende Nachricht (String oder bytes)
# @param ip Ziel-IP-Adresse (Empfänger)
# @param port Ziel-Port (Empfänger)
# @param binary True, wenn Binärdaten gesendet werden, sonst False (Text)
def tcp_send(message, ip, port, binary=False):
    # Prüft für Textnachrichten die maximale Länge (Protokoll-Anforderung)
    if not binary and len(message) > MAX_MSG_LENGTH:
        raise ValueError(f"Nachricht zu lang ({len(message)} > {MAX_MSG_LENGTH} Zeichen)")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)  # Timeout für Verbindung
    try:
        sock.connect((ip, port))
        if binary:
            sock.sendall(message)
        else:
            sock.sendall(message.encode())
        if debug_mode:
            print(f"[DEBUG] TCP gesendet an {ip}:{port} → {message[:50] if not binary else '[BINÄRDATEN]'}")
    except Exception as e:
        print(f"[FEHLER] TCP: {e}")
    finally:
        sock.close()

##
# @brief Ermittelt die eigene (lokale) IP-Adresse.
#
# Öffnet eine Dummy-Verbindung zu einer externen IP (Google DNS) und gibt die lokale IP zurück.
# Falls nicht möglich, wird "127.0.0.1" zurückgegeben.
#
# @return Eigene IP-Adresse (String)
def get_own_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"
