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
import os  # Wichtig: os für Dateipfad-Operationen
from network import load_config, udp_send, udp_listener, get_own_ip

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

def main():
    args = parse_args()
    config = load_config()
   
    # Merge config with arguments
    config.update({
        "handle": args.handle,
        "port": args.port,
        "whoisport": args.whoisport,
        "autoreply": args.autoreply if args.autoreply else config.get("autoreply", "")
    })

    # Start discovery service if not running
    if not discovery_running(config["whoisport"]):
        print("Starting discovery service...")
        subprocess.Popen([sys.executable, "discovery.py"])
        time.sleep(1)  # Ensure discovery is ready

    # Send initial messages
    def send_initial_messages():
        join_msg = f"JOIN {config['handle']} {config['port'][1]}"
        udp_send(join_msg, "255.255.255.255", config["whoisport"])
        time.sleep(0.5)
        udp_send("WHO", "255.255.255.255", config["whoisport"])

    send_initial_messages()

    # User interface selection
    while True:
        print("\n1) Command Line Interface (CLI)")
        print("2) Graphical User Interface (GUI)")
        choice = input("Please choose (1/2): ").strip()
        
        if choice == "1":
            from cli import start_cli
            start_cli(
                handle=config["handle"],
                port=config["port"][1],
                whoisport=config["whoisport"]
            )
            break
            
        elif choice == "2":
            gui_file = "chat_gui_client_verbessert.py"  # Korrekter Dateiname
            if not os.path.exists(gui_file):
                print(f"Error: GUI file '{gui_file}' not found in {os.getcwd()}!")
                print("Please ensure the file exists or use CLI instead.")
                continue
                
            try:
                subprocess.Popen([
                    sys.executable,
                    gui_file,
                    "--handle", config["handle"],
                    "--port", str(config["port"][0]), str(config["port"][1]),
                    "--whoisport", str(config["whoisport"])
                ])
                break
            except Exception as e:
                print(f"Failed to start GUI: {str(e)}")
                continue
                
        else:
            print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()