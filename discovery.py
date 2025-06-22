##
# @file discovery_service.py
# @brief Implementiert den Discovery-Service zur Teilnehmererkennung und Verwaltung im Chatnetzwerk.
#
# Diese Datei enthält die Klasse DiscoveryService, die über UDP Nachrichten verarbeitet,
# neue Teilnehmer im Chatnetzwerk registriert, bekannte Nutzer verteilt und Teilnehmer-Listen verwaltet.
# Der Service erlaubt es Clients, sich zu verbinden, abzumelden und die aktuelle Teilnehmerliste abzufragen.
#

import socket
import threading
from datetime import datetime

##
# @class DiscoveryService
# @brief Realisiert einen Discovery-Dienst für die Verwaltung und Verteilung von Chat-Teilnehmern.
#
# Die DiscoveryService-Klasse stellt Methoden bereit, um
# - Beitrittsanfragen ("JOIN") von Clients entgegenzunehmen,
# - Teilnehmer abzumelden ("LEAVE"),
# - Anfragen nach bekannten Nutzern ("WHO") zu beantworten
# und verteilt aktuelle Nutzerlisten per Broadcast.
#
class DiscoveryService:
    ##
    # @brief Initialisiert den Discovery-Service.
    # @param port UDP-Port für den Discovery-Dienst (Standard: 4000)
    #
    # Initialisiert die Teilnehmerliste, Lock-Objekt für Thread-Sicherheit und steuert die Ausführung.
    #
    def __init__(self, port=4000):
        self.port = port
        self.participants = {}
        self.lock = threading.Lock()
        self.running = True
        
    ##
    # @brief Verarbeitet eingehende UDP-Anfragen von Clients.
    # @param data Empfangene UDP-Daten (Bytes)
    # @param addr Absenderadresse als Tupel (IP, Port)
    #
    # Erkennt und verarbeitet die Befehle JOIN, WHO und LEAVE:
    # - JOIN: Registriert neuen Nutzer und verteilt aktuelle Teilnehmerliste.
    # - WHO: Sendet aktuelle Teilnehmerliste an den anfragenden Client.
    # - LEAVE: Entfernt Nutzer aus der Teilnehmerliste.
    #
    def handle_request(self, data, addr):
        try:
            msg = data.decode("utf-8").strip()
            print(f"[DISCOVERY] {datetime.now().strftime('%H:%M:%S')} - Received from {addr}: {msg}")

            if msg.startswith("JOIN"):
                parts = msg.split()
                if len(parts) >= 4:
                    handle = parts[1]
                    chat_port = int(parts[2])
                    file_port = int(parts[3]) if len(parts) > 3 else None
                    with self.lock:
                        self.participants[handle] = {
                            'ip': addr[0],
                            'chat_port': chat_port,
                            'file_port': file_port
                        }
                    print(f"[JOIN] {handle} @ {addr[0]}:{chat_port}")
                    self.broadcast_participants()

            elif msg == "WHO":
                self.send_participants(addr)

            elif msg.startswith("LEAVE"):
                handle = msg.split()[1]
                with self.lock:
                    if handle in self.participants:
                        del self.participants[handle]
                        print(f"[DISCOVERY] {handle} left the chat")

        except Exception as e:
            print(f"[DISCOVERY ERROR] {e}")

    ##
    # @brief Sendet die aktuelle Teilnehmerliste als Broadcast-Nachricht an alle Clients im Netzwerk.
    #
    # Erstellt eine KNOWNUSERS-Nachricht mit allen aktuellen Teilnehmern und verschickt sie per UDP-Broadcast.
    #
    def broadcast_participants(self):
        with self.lock:
            msg = "KNOWNUSERS " + " ".join(
                f"{h} {d['ip']} {d['chat_port']}"
                for h, d in self.participants.items()
            )

        self.send_message(msg, '255.255.255.255', self.port)

    ##
    # @brief Sendet die aktuelle Teilnehmerliste an eine spezifische Adresse (Antwort auf WHO).
    # @param addr Zieladresse (IP, Port)
    #
    def send_participants(self, addr):
        with self.lock:
            msg = "KNOWNUSERS " + " ".join(
                f"{h} {d['ip']} {d['chat_port']}"
                for h, d in self.participants.items()
            )

        self.send_message(msg, addr[0], addr[1])

    ##
    # @brief Versendet eine UDP-Nachricht an eine bestimmte IP und Port.
    # @param msg Zu sendende Nachricht (String)
    # @param ip Ziel-IP-Adresse
    # @param port Ziel-Port
    #
    @staticmethod
    def send_message(msg, ip, port):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(msg.encode("utf-8"), (ip, port))

    ##
    # @brief Startet den Discovery-Service und verarbeitet fortlaufend UDP-Nachrichten.
    #
    # Bindet den UDP-Socket an den konfigurierten Port und verarbeitet jede eingehende Nachricht
    # in einem eigenen Thread. Läuft solange self.running True ist.
    #
    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", self.port))
        
        print(f"[DISCOVERY] Service started on port {self.port}")
        try:
            while self.running:
                data, addr = sock.recvfrom(1024)
                threading.Thread(target=self.handle_request, args=(data, addr)).start()
        finally:
            sock.close()

##
# @brief Startet den Discovery-Service über die Kommandozeile.
#
# Liest einen optionalen Port aus den Kommandozeilenargumenten und startet die DiscoveryService-Instanz.
#
def start_discovery():
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    service = DiscoveryService(port)
    service.start()

if __name__ == "__main__":
    start_discovery()
