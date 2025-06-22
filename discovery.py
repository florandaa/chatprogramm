##
# @file discovery.py
# @brief Discovery-Service für Teilnehmererkennung im P2P-Chat
#
# Dieses Modul enthält den DiscoveryService, der über UDP Anfragen von Clients
# (JOIN, WHO, LEAVE) verarbeitet und die Teilnehmerliste verwaltet.
#

import socket
import threading
from datetime import datetime

##
# @class DiscoveryService
# @brief Discovery-Service verwaltet Teilnehmerliste und verarbeitet UDP-Anfragen.
#
# Der DiscoveryService nimmt JOIN-/WHO-/LEAVE-Nachrichten entgegen,
# verteilt die aktuelle Nutzerliste und sorgt dafür,
# dass alle Clients sich gegenseitig erkennen können.
#
class DiscoveryService:
    ##
    # @brief Konstruktor: Initialisiert Service und Datenstrukturen.
    # @param port UDP-Port für Discovery-Service (Standard: 4000)
    def __init__(self, port=4000):
        ##
        # @var port
        # @brief Port für eingehende UDP-Anfragen
        self.port = port
        ##
        # @var participants
        # @brief Dict der angemeldeten Nutzer: Handle → Daten (IP, chat_port, udp_port)
        self.participants = {}
        ##
        # @var lock
        # @brief Lock für Thread-Sicherheit beim Zugriff auf participants
        self.lock = threading.Lock()
        ##
        # @var running
        # @brief Steuerung, ob der Service weiterläuft
        self.running = True

    ##
    # @brief Verarbeitet eine eingehende UDP-Anfrage.
    # @param data Empfangene UDP-Daten (Bytes)
    # @param addr Absenderadresse (IP, Port)
    #
    # Erkennt JOIN, WHO und LEAVE und reagiert entsprechend.
    def handle_request(self, data, addr):
        try:
            msg = data.decode("utf-8").strip()
            print(f"[DISCOVERY] {datetime.now().strftime('%H:%M:%S')} - Received from {addr}: {msg}")

            # JOIN <Handle> <TCP-Port> <UDP-Port>
            if msg.startswith("JOIN"):
                parts = msg.split()
                if len(parts) == 4:
                    handle = parts[1]
                    chat_port = int(parts[2])
                    udp_port = int(parts[3])
                    with self.lock:
                        self.participants[handle] = {
                            'ip': addr[0],
                            'chat_port': chat_port,
                            'udp_port': udp_port
                        }
                    print(f"[JOIN] {handle} @ {addr[0]}:{chat_port} (UDP-Clientport: {udp_port})")
                    self.broadcast_participants()

            # WHO: Schickt aktuelle Nutzerliste an anfragenden Client
            elif msg == "WHO":
                self.send_participants(addr)

            # LEAVE <Handle>: Entfernt Nutzer aus Liste
            elif msg.startswith("LEAVE"):
                handle = msg.split()[1]
                with self.lock:
                    if handle in self.participants:
                        del self.participants[handle]
                        print(f"[DISCOVERY] {handle} left the chat")

        except Exception as e:
            print(f"[DISCOVERY ERROR] {e}")

    ##
    # @brief Sendet aktuelle Teilnehmerliste an alle bekannten Nutzer (UDP).
    #
    # Die Nachricht hat das Format: KNOWNUSERS <Name1> <IP1> <Port1> ...
    def broadcast_participants(self):
        with self.lock:
            msg = "KNOWNUSERS " + " ".join(
                f"{h} {d['ip']} {d['chat_port']}"
                for h, d in self.participants.items()
            )
        # Sende an jeden Client individuell auf seinen UDP-Listener
        for h, d in self.participants.items():
            self.send_message(msg, d['ip'], d['udp_port'])

    ##
    # @brief Antwortet gezielt auf eine WHO-Anfrage mit der Nutzerliste.
    # @param addr Zieladresse (IP, Port) des anfragenden Clients
    def send_participants(self, addr):
        with self.lock:
            msg = "KNOWNUSERS " + " ".join(
                f"{h} {d['ip']} {d['chat_port']}"
                for h, d in self.participants.items()
            )
        self.send_message(msg, addr[0], addr[1])

    ##
    # @brief Verschickt eine UDP-Nachricht an einen Client.
    # @param msg Nachrichtentext (String)
    # @param ip Ziel-IP
    # @param port Ziel-Port
    @staticmethod
    def send_message(msg, ip, port):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(msg.encode("utf-8"), (ip, port))

    ##
    # @brief Startet den Discovery-Service (UDP-Server), verarbeitet eingehende Nachrichten.
    #
    # Hauptschleife: wartet auf Daten, startet für jede Nachricht einen Thread zur Verarbeitung.
    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", self.port))
        print(f"[DISCOVERY] Service started on port {self.port}")
        try:
            while self.running:
                data, addr = sock.recvfrom(1024)
                threading.Thread(target=self.handle_request, args=(data, addr)).start()
        finally:
            sock.close()

##
# @brief Startet den Discovery-Service von der Kommandozeile aus.
def start_discovery():
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    service = DiscoveryService(port)
    service.start()

if __name__ == "__main__":
    start_discovery()
