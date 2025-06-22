##
# @file network.py
# @brief Netzwerkfunktionen für UDP- und TCP-Kommunikation im Chatprogramm.
#
# Dieses Modul enthält Funktionen zum Senden und Emfangen von Nachrichten
# sowie zum Laden der Konfiguration und zur Ermittlung der eigenen IP-Adresse.
# Es unterstützt sowohl Broadcast- als auch Direktverbindungen.
#

import socket
import threading
import toml
import os

## Aktiviert den Debug-Modus (gibt Neztwerkaktivitäten in der Konsole aus)
debug_mode = False

##
# @brief Lädt die Konfiguration aus einer TOML-Datei.
# @param path Pfad zur Konfigurationsdatei (Standard: "config.toml")
# @return Ein Dictionary mit den geladenen Konfigurationswerten.
def load_config(path="config.toml"):
    return toml.load(os.path.abspath(path))

##
# @brief Starter einen UDP-Listener auf dem angegebenen Port.
#
# Der Listener empfängt eingehende UDP-Nachrichten und ruft eine Callback-Funktion auf,
# wenn eine Nachricht empfangen wird.
#
# @param port Port, auf dem gelauscht wird.
# @param callback Funktion, die bei Empfang aufgerufen wird: callback(nachricht, absender)
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
# @brief Sendet eine UDP-Nachricht an eine IP-Adresse und Port.
# 
# @param message Die zu sendende Nachricht (Text).
# @param ip Ziel-IP-Adresse (z. B. 255.255.255.255 für Broadcast).
# @param port Zielport.
def udp_send(message, ip, port):
   
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # WICHTIG
   
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
# @brief Startet einen TCP-Server, der eingehende Verbindungen verarbeitet.
#
# @param port Port, auf dem der Server lauscht.
# @param callback FUnktion, die aufgerufen wird, wenn eine Nachricht emfangen wird: callback(nachricht)
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
# @brief Sendet eine TCP-Nachricht an einen bestimmten Emfänger.
# 
# @param message Die zu sendende Nachricht (als Text oder Binärdaten).
# @param ip IP-Adresse des Empfängers.
# @param port Zielport.
# @param binary True, wenn es sich um Binärdaten handelt (z. B. Bilder); sonst False. 
def tcp_send(message, ip, port, binary=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)  # Timeout hinzugefügt
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
# @brief Ermittelt die eigene lokale IP-Adresse (nicht 127.0.0.1).
#
# @return Eigene IP-Adresse im lokalen Netzwerk.
def get_own_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"
 