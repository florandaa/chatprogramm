##
# @file cli.py
# @brief Kommandozeilen-Client für das Peer-to-Peer-Chatprogramm (SLCP-Protokoll)
#
# Dieses Modul stellt eine textbasierte Benutzerschnittstelle bereit.
# Nutzer können sich mit dem Netzwerk verbinden, Nachrichten senden/empfangen
# und den Discovery-Mechanismus verwenden, um andere Teilnehmer zu erkennen.
#

import socket
import threading
import time
import re
import sys
from datetime import datetime

##
# @class colors
# @brief ANSI-Farbcodes für Konsolenausgabe.
class colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

##
# @var IP_BROADCAST
# @brief Standard-Broadcast-Adresse für UDP-Kommunikation.
IP_BROADCAST = "255.255.255.255"

##
# @var chat_verlauf
# @brief Liste zur Speicherung aller Chat-Nachrichten (lokal).
chat_verlauf = []

##
# @var bekannte_nutzer
# @brief Dictionary der bekannten Nutzer im Netzwerk (Name → (IP, Port)).
bekannte_nutzer = {}

##
# @brief Erzeugt einen Zeitstempel-String für Ausgaben.
# @return Zeitstempel als formatierter String
def format_timestamp():
    return f"{colors.BLUE}[{datetime.now().strftime('%H:%M:%S')}]{colors.END}"

##
# @brief Gibt Systemmeldungen farbig in der Konsole aus.
# @param msg Meldungstext
def print_system(msg):
    print(f"{format_timestamp()} {colors.YELLOW} {msg}{colors.END}")

##
# @brief Gibt empfangene Chatnachrichten aus.
# @param sender Absendername oder IP
# @param msg Nachrichtentext
def print_message(sender, msg):
    print(f"\n{format_timestamp()} {colors.GREEN} {sender}: {msg}{colors.END}")

##
# @brief Gibt Fehlermeldungen farbig in der Konsole aus.
# @param msg Fehlermeldung
def print_error(msg):
    print(f"{format_timestamp()} {colors.RED} {msg}{colors.END}")

##
# @brief Gibt Erfolgsmeldungen farbig in der Konsole aus.
# @param msg Erfolgsmeldung
def print_success(msg):
    print(f"{format_timestamp()} {colors.GREEN} {msg}{colors.END}")

##
# @brief Startet einen TCP-Server zur Annahme von Nachrichten.
# @param port TCP-Port, auf dem gehört wird
#
# Diese Funktion läuft in einem eigenen Thread und nimmt eingehende
# Verbindungen entgegen. Jede Nachricht wird direkt in der Konsole ausgegeben.
def empfange_tcp(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', port))
    sock.listen()
    print_system(f"TCP-Server gestartet auf Port {port}")
    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024).decode()
        print_message(addr[0], data)
        conn.close()

##
# @brief Startet den UDP-Empfänger für KNOWNUSERS-Nachrichten.
# @param my_udp_port Port, auf dem UDP gehört wird (eigener Listener-Port)
# @param handle Eigenes Handle (Name)
#
# Diese Funktion läuft in einem Thread und verarbeitet eintreffende UDP-Nachrichten.
# KNOWNUSERS-Antworten werden ausgewertet und die Nutzerliste aktualisiert.
def udp_empfaenger(my_udp_port, handle):
    global bekannte_nutzer
    print_system(f"UDP-Empfänger gestartet auf Port {my_udp_port} (handle={handle})")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        sock.bind(('0.0.0.0', my_udp_port))
    except OSError:
        print_error(f"UDP-Port {my_udp_port} belegt – Wähle anderen UDP-Port für diesen Nutzer!")
        sys.exit(1)

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            msg = data.decode().strip()
            # Erwartetes Format: KNOWNUSERS <Handle> <IP> <Port> ...
            if msg.startswith("KNOWNUSERS"):
                neue_nutzer = {}
                teile = msg.split()[1:]
                for i in range(0, len(teile), 3):
                    if i + 2 < len(teile):
                        name, ip, port = teile[i], teile[i + 1], int(teile[i + 2])
                        if name != handle:
                            neue_nutzer[name] = (ip, port)
                bekannte_nutzer.update(neue_nutzer)
                if neue_nutzer:
                    print_system(f"Nutzerliste aktualisiert: {', '.join(neue_nutzer.keys())}")
                else:
                    print_system("Keine neuen Nutzer empfangen.")
        except Exception as e:
            print_error(f"UDP Fehler: {e}")

##
# @brief Startet die Kommandozeilen-Benutzerschnittstelle (CLI) und alle Netzwerkthreads.
# @param handle Eigenes Handle (Name)
# @param tcp_port Port für TCP-Empfang (Nachrichten)
# @param my_udp_port Port für eigenen UDP-Empfänger (KNOWNUSERS)
#
# Stellt alle CLI-Befehle bereit: /hilfe, /nutzer, /msg, /exit.
def start_cli(handle, tcp_port, my_udp_port):
    # TCP- und UDP-Empfänger starten
    threading.Thread(target=empfange_tcp, args=(tcp_port,), daemon=True).start()
    threading.Thread(target=udp_empfaenger, args=(my_udp_port, handle), daemon=True).start()

    # JOIN-Nachricht senden (entweder an 4000 oder wie im Protokoll konfiguriert)
    join_msg = f"JOIN {handle} {tcp_port} {my_udp_port}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(join_msg.encode(), (IP_BROADCAST, 4000))
    print_system(f"JOIN Nachricht gesendet")

    # WHO-Anfrage senden, um aktuelle Nutzer zu erhalten
    time.sleep(0.5)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b"WHO", (IP_BROADCAST, 4000))

    # Benutzerbefehlsschleife
    try:
        while True:
            cmd = input(f"{handle}> ").strip()
            if cmd == "/hilfe":
                print("Befehle:\n/nutzer - Liste aller Nutzer\n/msg <Name> \"Text\" - Nachricht senden\n/exit - Beenden")
            elif cmd == "/nutzer":
                print("🟢 Aktive Nutzer:")
                found = False
                for name, (ip, port) in bekannte_nutzer.items():
                    if name != handle:
                        print(f"- {name} @ {ip}:{port}")
                        found = True
                if not found:
                    print("Keine anderen Nutzer online")
            elif cmd.startswith("/msg "):
                # Format: /msg <Name> "Text"
                match = re.match(r'/msg (\S+) "(.+)"', cmd)
                if match:
                    ziel, text = match.groups()
                    if ziel in bekannte_nutzer:
                        ip, port = bekannte_nutzer[ziel]
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.settimeout(2.0)
                                s.connect((ip, port))
                                s.sendall(f"{handle}: {text}".encode())
                                print_success(f"Nachricht an {ziel} gesendet")
                        except ConnectionRefusedError:
                            print_error(f"{ziel} ist nicht erreichbar (Port {port} geschlossen)")
                        except Exception as e:
                            print_error(f"Fehler: {e}")
                    else:
                        print_error(f"Nutzer '{ziel}' nicht gefunden")
            elif cmd == "/exit":
                # LEAVE an alle Discovery-Teilnehmer
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.sendto(f"LEAVE {handle}".encode(), (IP_BROADCAST, 4000))
                break
    except KeyboardInterrupt:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(f"LEAVE {handle}".encode(), (IP_BROADCAST, 4000))
        print("\nChat beendet")

##
# @brief Startpunkt für die CLI-Anwendung.
#
# Liest die drei Kommandozeilenargumente ein (Name, TCP-Port, UDP-Port) und startet das CLI.
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 cli.py <handle> <tcp_port> <my_udp_port>")
        sys.exit(1)
    start_cli(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
