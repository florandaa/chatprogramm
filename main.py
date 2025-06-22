##
# @file main.py
# @brief Einstiegspunkt des Chatprogramms.
#
# Dieses Skript lädt die Konfiguration, verarbeitet Kommandozeilenargumente, 
# und bietet die Wahl zwischen CLI und GUI.
# Hinweis: Der Discovery-Service MUSS separat laufen!
##

import sys
import socket
import argparse
import os  # Für Dateipfad-Operationen
import time
from network import load_config, udp_send

##
# @brief Verarbeitet Kommandozeilenargumente für das Chatprogramm.
# @return Parsed Argumente (Namespace)
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle", help="Dein Benutzername")
    parser.add_argument("--port", nargs=2, type=int, help="UDP- und TCP-Ports (z. B. 5000 5001)")
    parser.add_argument("--whoisport", type=int, help="Discovery-Dienst-Port")
    parser.add_argument("--autoreply", help="Automatische Antwortnachricht")
    return parser.parse_args()

##
# @brief Prüft, ob der Discovery-Dienst bereits läuft (ob Port belegt ist).
# @param port WHOIS-Port für Discovery
# @return True falls Discovery läuft (Port belegt), sonst False
def discovery_running(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", port))
        s.close()
        return False  # Port frei -> Discovery läuft NICHT
    except:
        return True   # Port belegt -> Discovery läuft

##
# @brief Hauptfunktion: Programmstart, Konfiguration, UI-Auswahl
def main():
    # Konfiguration laden
    config = load_config()
    args = parse_args()

    # Überschreibe Konfig mit Kommandozeilenparametern
    if args.handle:
        config["handle"] = args.handle
    if args.port:
        config["port"] = args.port
    if args.whoisport:
        config["whoisport"] = args.whoisport
    if args.autoreply:
        config["autoreply"] = args.autoreply

    ##
    # @section DiscoveryCheck Discovery-Service prüfen
    # Discovery muss als separater Prozess laufen!
    if not discovery_running(config["whoisport"]):
        print("❗ Discovery-Service läuft NICHT. Bitte zuerst 'python3 discovery.py' in einem anderen Terminal starten!")
        sys.exit(1)
    else:
        print(f"Verbinde zu Discovery-Service auf Port {config['whoisport']} ...")

    ##
    # @section InitialMessages Sende JOIN und WHO automatisch (Pflicht)
    def send_initial_messages():
        join_msg = f"JOIN {config['handle']} {config['port'][1]}"
        udp_send(join_msg, "255.255.255.255", config["whoisport"])
        time.sleep(0.5)
        udp_send("WHO", "255.255.255.255", config["whoisport"])
    send_initial_messages()

    ##
    # @section UI Auswahl: CLI oder GUI
    while True:
        print("\n1) Command Line Interface (CLI)")
        print("2) Graphical User Interface (GUI)")
        choice = input("Please choose (1/2): ").strip()
        
        if choice == "1":
            # Starte CLI
            from cli import start_cli
            start_cli(
                handle=config["handle"],
                port=config["port"][1],
                whoisport=config["whoisport"]
            )
            break
            
        elif choice == "2":
            # Starte GUI (optional)
            gui_file = "chat_gui_client_verbessert.py"
            if not os.path.exists(gui_file):
                print(f"Error: GUI file '{gui_file}' not found in {os.getcwd()}!")
                print("Please ensure the file exists or use CLI instead.")
                continue
            try:
                import subprocess
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

##
# @brief Einstiegspunkt des Programms.
if __name__ == "__main__":
    main()
