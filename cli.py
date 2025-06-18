# @file cli.py
# @brief Kommandozeilen-Schnittstelle für den Chat-Client

import argparse
import threading
from network import tcp_send, udp_send, udp_listener, load_config
import socket

chat_verlauf = []  # Gespeicherte Nachrichten lokal (für Verlauf & Export)
benutzername = "Benutzer"  # Standardname, wird in main.py ggf. überschrieben
bekannte_nutzer = {}       # Wird durch main.py gesetzt
config = {}


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


# === CLI-Argumente für Konfig-Überschreibung ===
def parse_args():
    parser = argparse.ArgumentParser(description="Chatprogramm starten mit optionaler Konfig-Überschreibung")
    parser.add_argument("--handle", help="Benutzername")
    parser.add_argument("--port", nargs=2, type=int, metavar=("UDP1", "UDP2"), help="Portbereich")
    parser.add_argument("--autoreply", help="Text für automatische Antwort")
    parser.add_argument("--whoisport", type=int, help="Discovery-Port")
    parser.add_argument("--broadcast_ip", help="Broadcast-Adresse")
    return parser.parse_args()


# === Discovery Callback ===
def discovery_callback(msg, addr):
    global bekannte_nutzer
    print(f"[CALLBACK] empfangen: {msg} von {addr}")

    if msg.startswith("KNOWNUSERS"):
        teile = msg.split()[1:]  # ohne "KNOWNUSERS"
        for i in range(0, len(teile), 3):
            try:
                handle = teile[i]
                ip = teile[i + 1]
                port = int(teile[i + 2])
                bekannte_nutzer[handle] = (ip, port)
            except IndexError:
                continue
        print(f"[DEBUG] aktuelle bekannte_nutzer: {bekannte_nutzer}")

    elif msg.startswith("JOIN "):
        teile = msg.split()
        if len(teile) == 3:
            handle, port = teile[1], int(teile[2])
            ip = addr[0]
            bekannte_nutzer[handle] = (ip, port)
            print(f"[JOIN] Neuer Nutzer entdeckt: {handle} @ {ip}:{port}")

            # Antwort senden mit allen bekannten Nutzern
            daten = []
            for h, (ip, p) in bekannte_nutzer.items():
                daten.extend([h, ip, str(p)])
            antwort = "KNOWNUSERS " + " ".join(daten)
            udp_send(antwort, ip, config["whoisport"])

    elif msg.startswith("WHO"):
        ip = addr[0]
        daten = []
        for h, (ip, p) in bekannte_nutzer.items():
            daten.extend([h, ip, str(p)])
        antwort = "KNOWNUSERS " + " ".join(daten)
        udp_send(antwort, ip, config["whoisport"])

# === TCP-Nachrichten empfangen (MSG)
def empfange_tcp(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen()
    print(f"[TCP] Server läuft auf Port {port}")
    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024).decode("utf-8")
        if data.startswith("MSG "):
            teile = data.split(" ", 2)
            if len(teile) == 3:
                sender, nachricht = teile[1], teile[2]
                chat_verlauf.append(f"{sender}: {nachricht}")
                print(f"\n{sender}: {nachricht}\n{benutzername}: ", end="")
        conn.close()

# === Verlauf speichern ===
def speichere_verlauf():
    with open("chat_verlauf.txt", "w", encoding="utf-8") as datei:
        for nachricht in chat_verlauf:
            datei.write(nachricht + "\n")
    print("Chatverlauf gespeichert in 'chat_verlauf.txt'.")

# === Lokale IP-Adresse ermitteln ===
def get_own_ip():
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"


# === Hauptfunktion CLI
def start_cli():
    global benutzername

    print("Willkommen zum Chat!")
    print("Verfügbare Befehle: /hilfe, /name, /verlauf, /nutzer, /msg, /ip, exit\n")

    while True:
        eingabe = input(f"{benutzername}: ").strip()

        if eingabe == "exit":
            speichere_verlauf()
            print("Chat wird beendet.")
            break

        elif eingabe.startswith("/hilfe"):
            zeige_hilfe()

        elif eingabe.startswith("/name "):
            neuer_name = eingabe.split(" ", 1)[1]
            print(f"Name geändert: {benutzername} → {neuer_name}")
            benutzername = neuer_name

        elif eingabe == "/verlauf":
            for msg in chat_verlauf:
                print(msg)

        elif eingabe == "/nutzer":
            print(f"[DEBUG] aktuelle bekannte_nutzer: {bekannte_nutzer}")
            if bekannte_nutzer:
                for name, (ip, port) in bekannte_nutzer.items():
                    print(f"- {name} @ {ip}:{port}")
            else:
                print("Noch keine bekannten Nutzer.")

        elif eingabe.startswith("/msg "):
            teile = eingabe.split(" ", 2)
            if len(teile) < 3:
                print("Nutze: /msg [handle] [Nachricht]")
                continue
            ziel, text = teile[1], teile[2]
            if ziel in bekannte_nutzer:
                ip, port = bekannte_nutzer[ziel]
                tcp_send(f"MSG {benutzername} {text}", ip, port)
                chat_verlauf.append(f"(an {ziel}) {benutzername}: {text}")
            else:
                print(f"Unbekannter Nutzer: {ziel}")

        elif eingabe == "/ip":
            print("Deine IP:", get_own_ip())

        else:
            if eingabe:
                print("Nur Kommandos erlaubt. Tippe /hilfe für Hilfe.")


# === Startpunkt
if __name__ == "__main__":
    config = load_config()
    args = parse_args()

    # Argumente überschreiben config
    if args.handle:
        config["handle"] = args.handle
    if args.port:
        config["port"] = args.port
    if args.whoisport is not None:
        config["whoisport"] = args.whoisport
    if args.autoreply:
        config["autoreply"] = args.autoreply
    if args.broadcast_ip:
        config["broadcast_ip"] = args.broadcast_ip

    benutzername = config.get("handle", "Benutzer")
    whoisport = config.get("whoisport", 4000)
    broadcast_ip = config.get("broadcast_ip", "255.255.255.255")
    empfangs_port = config["port"][1]

    # JOIN senden
    udp_send(f"JOIN {benutzername} {empfangs_port}", broadcast_ip, whoisport)

    # Listener starten
    threading.Thread(target=udp_listener, args=(whoisport, discovery_callback), daemon=True).start()
    threading.Thread(target=empfange_tcp, args=(empfangs_port,), daemon=True).start()

    # Regelmäßig WHO senden
    def wiederhole_who():
        udp_send("WHO", broadcast_ip, whoisport)
        threading.Timer(10, wiederhole_who).start()
    wiederhole_who()

    start_cli()
