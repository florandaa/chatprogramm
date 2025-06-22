##
# @file main.py
# @brief Einstiegspunkt des Chatprogramms.
#
# Dieses Skript lädt die Konfiguration, verarbeitet Kommandozeilenargumente, 
# startet gff. den Discovery-Dienst und bietet die Wahl zwischen CLI und GUI.
#

import sys
import socket
import subprocess
import threading
import time
import argparse
from network import load_config, udp_send, udp_listener, get_own_ip
from chat_gui_client_verbessert import start_gui
##
# @brief Verarbeitet Kommandozeilenargumente.
#
# Diese Funktion liest CLI-Argumente wie Handle, Ports, WHOIS-Port und optionale Autoreply-Nachricht.
#
# @return args: Ein Namespace-Objekt mit den Argumentwerten.
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle", required=True, help="Dein Benutzername")
    parser.add_argument("--port", nargs=2, type=int, required=True,
                       help="UDP- und TCP-Ports (z. B. 5000 5001)")
    parser.add_argument("--whoisport", type=int, required=True,
                       help="Discovery-Dienst-Port")
    parser.add_argument("--autoreply", help="Automatische Antwortnachricht")
    return parser.parse_args()

##
# @brief Prüft, ob der Discovery-Dienst bereits läuft.
#
# Diese Funktion versucht, den WHOIS-Port zu binden. Falls das nicht möglich ist,
# läuft vermutlich bereits ein Discovery-Prozess.
# 
# @param port WHOIS-Port, auf dem der Discovery-Dienst laufen soll.
# @return True, wenn der Dienst schon läuft, sonst False. 
def discovery_running(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", port))
        s.close()
        return False
    except:
        return True
 
##
# @brief Hauptfunktion zum Starten des Programms.
#
# Diese Funktion führt die Konfigurations- und Startlogik aus:
# - Argumente lesen
# - Konfiguration mergen 
# - Discovery Dienst starten (falls nötig)
# - Auswahl zwischen CLI oder GUI starten
#
# @return None
def main():
    args = parse_args()
    config = load_config()
   
    # Argumente mit Konfigurationsdatei zusammenführen
    config["handle"] = args.handle
    config["port"] = args.port
    config["whoisport"] = args.whoisport
    if args.autoreply:
        config["autoreply"] = args.autoreply
 
    # Discovery-Dienst starten wenn es nicht läutf
    if not discovery_running(config["whoisport"]):
        print("Starte Discovery-Dienst...")
        subprocess.Popen([sys.executable, "discovery.py"])
        time.sleep(1)  # Wait for discovery to start
 
    # Initiale Nchrichten (JOIN, WHO) senden
    join_msg = f"JOIN {config['handle']} {config['port'][1]}"
    udp_send(join_msg, "255.255.255.255", config["whoisport"])
    time.sleep(0.5)
    udp_send("WHO", "255.255.255.255", config["whoisport"])
 
    # Start der Benutzeroberfläche (CLI/GUI)
    print("1) CLI\n2) GUI")
    choice = input("> ").strip()
   
    if choice == "1":
        from cli import start_cli
        start_cli(
            handle=config["handle"],
            port=config["port"][1],  # TCP port
            whoisport=config["whoisport"]
        )
    elif choice == "2":
        subprocess.Popen([
            sys.executable,
            "chat_gui_client_verbessert.py",
            "--handle", config["handle"],
            "--port", str(config["port"][0]), str(config["port"][1]),
            "--whoisport", str(config["whoisport"])
        ])
 
# Einstiegspunkt
if __name__ == "__main__":
    # Nur ausführen, wenn Parameter übergeben wurden
    if len(sys.argv) > 1:
        config = {
            "handle": sys.argv[sys.argv.index("--handle")+1],
            "port": [int(sys.argv[sys.argv.index("--port")+1]), 
                     int(sys.argv[sys.argv.index("--port")+2])],
            "whoisport": int(sys.argv[sys.argv.index("--whoisport")+1])
        }
        start_gui(config)
    else:
        print("Dieses Modul sollte über main.py gestartet werden")
        sys.exit(1)