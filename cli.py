# @file cli.py
# @brief Kommandozeilen-Schnittstelle für den Chat-Client

import argparse
import toml
from network import tcp_send, load_config

chat_verlauf = []  # Gespeicherte Nachrichten lokal (für Verlauf & Export)
benutzername = None  # Standardname beim Start

# Liste aller bekannten Nutzer – gefüllt nach WHO/KNOWUSERS
bekannte_nutzer = {}  # Wird aus main.py gesetzt

# === Hilfetext anzeigen ===
def zeige_hilfe():
    print("Befehle:")
    print("/hilfe              - Zeigt diese Hilfe an")
    print("/name [name]        - Ändert deinen Namen")
    print("/verlauf            - Zeigt alle gesendeten Nachrichten")
    print("/nutzer             - Zeigt bekannte Nutzer (KNOWUSERS)")
    print("/msg [name] [text]  - Sendet eine Nachricht an Nutzer")
    print("/ip                 - Zeigt deine aktuelle IP-Adresse")
    print("exit                - Beendet den Chat")


def parse_args():
    parser = argparse.ArgumentParser(description="Chatprogramm starten mit optionaler Konfig-Überschreibung")
    parser.add_argument("--handle", help="Benutzername")
    parser.add_argument("--port", nargs=2, type=int, metavar=("UDP1", "UDP2"), help="Portbereich")
    parser.add_argument("--autoreply", help="Text für automatische Antwort")
    parser.add_argument("--whoisport", type=int, help="Discovery-Port")
    parser.add_argument("--broadcast_ip", help="Broadcast-Adresse")
    return parser.parse_args()

# === Verlauf als Datei speichern ===
def speichere_verlauf():
    with open("chat_verlauf.txt", "w", encoding="utf-8") as datei:
        for nachricht in chat_verlauf:
            datei.write(nachricht + "\n")
    print("Chatverlauf gespeichert in 'chat_verlauf.txt'.")


# === Eigene IP ermitteln (lokal, IPv4) ===
def get_own_ip():
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Verbindet sich "scheinbar" nach außen
            return s.getsockname()[0]  # Gibt lokale IP zurück
    except:
        return "127.0.0.1"  # Fallback im Fehlerfall


# === Hauptfunktion zur Ausführung der CLI ===
def start_cli(known_users_ref=None):
    global benutzername 
    global bekannte_nutzer
    bekannte_nutzer = known_users_ref
    print("Willkommen zum Chat!")
    print("Verfügbare Befehle: /hilfe, /name, /verlauf, /nutzer, /msg, /ip, exit\n")

    while True:
        eingabe = input(f"{benutzername}: ").strip()

        # === Programm beenden ===
        if eingabe.lower() == "exit":
            speichere_verlauf()
            print("Chat wird beendet.")
            break

        # === Hilfe anzeigen ===
        elif eingabe.lower() == "/hilfe":
            zeige_hilfe()

        # === Benutzername ändern ===
        elif eingabe.lower().startswith("/name "):
            teile = eingabe.split(" ", 1)
            if len(teile) == 2 and teile[1].strip():
                neuer_name = teile[1].strip()
                print(f"Benutzername wird geändert von {benutzername} zu {neuer_name}")
                benutzername = neuer_name
            else:
                print("Fehler: Ungültiger Befehl. Beispiel: /name Mo")

        # === Gespeicherte Nachrichten anzeigen ===
        elif eingabe.lower() == "/verlauf":
            if not chat_verlauf:
                print("Noch keine Nachrichten gespeichert.")
            else:
                print("Gespeicherte Nachrichten:")
                for nachricht in chat_verlauf:
                    print(nachricht)

        # === Bekannte Nutzer anzeigen ===
        elif eingabe.lower() == "/nutzer":
            if not bekannte_nutzer:
                print("Noch keine bekannten Nutzer.")
            else:
                print("Bekannte Nutzer:")
                for handle, (ip, port) in bekannte_nutzer.items():
                    print(f"- {handle} @ {ip}:{port}")

        # === Sendet Nachricht an Nutzer  ===
        elif eingabe.lower().startswith("/msg "):
            teile = eingabe.split(" ", 2)
            if len(teile) < 3:
                print("Fehler: Benutze /msg [handle] [Nachricht]")
            else:
                ziel, nachricht = teile[1], teile[2]
                if ziel in bekannte_nutzer:
                    ip, port = bekannte_nutzer[ziel]
                    tcp_send(f"MSG {benutzername} {nachricht}", ip, port)
                    print(f"[SEND] Nachricht an {ziel} gesendet: {nachricht}")
                    chat_verlauf.append(f"(an {ziel}) {benutzername}: {nachricht}")
                else:
                    print(f"Unbekannter Nutzer: {ziel}")
           
        # === Eigene IP anzeigen lassen ===
        elif eingabe.lower() == "/ip":
            print(f"Deine IP-Adresse: {get_own_ip()}")

        # === Normale Nachricht (nicht an andere gesendet!) ===
        else:
            if eingabe:
                nachricht = f"{benutzername}: {eingabe}"
                chat_verlauf.append(nachricht)
                print("Nachricht gesendet:", nachricht)
            else:
                print("Fehler: Nachricht darf nicht leer sein.")

if __name__ == "__main__":
    from network import load_config
    config = load_config()
    start_cli(config)
