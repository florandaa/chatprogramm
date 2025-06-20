# @file cli.py
# @brief Kommandozeilen-Schnittstelle für den Chat-Client

import argparse
import threading
import socket
from network import tcp_send, udp_send, udp_listener, load_config

chat_verlauf = []  # Gespeicherte Nachrichten lokal (für Verlauf & Export)
benutzername = "Benutzer"  # Standardname, wird in main.py ggf. überschrieben
bekannte_nutzer = {}       # Wird durch main.py gesetzt
config = {}
debug_mode = False

# === CLI-Argumente ===
def parse_args():
    parser = argparse.ArgumentParser(description="Chatprogramm starten")
    parser.add_argument("--handle", help="Benutzername")
    parser.add_argument("--port", nargs=2, type=int, metavar=("UDP", "TCP"), help="UDP- & TCP-Port")
    parser.add_argument("--autoreply", help="Automatische Abwesenheitsnachricht")
    parser.add_argument("--whoisport", type=int, help="Port für Discovery (UDP)")
    parser.add_argument("--broadcast_ip", help="Broadcast-Adresse")
    parser.add_argument("--debug", action="store_true", help="Aktiviere Debug-Ausgaben")
    return parser.parse_args()


# === Discovery-Callback ===
def discovery_callback(msg, addr):
    if debug_mode:
        print(f"[DEBUG] Discovery empfangen: {msg} von {addr}")

    teile = msg.split()

    if teile[0] == "KNOWNUSERS":
        daten = teile[1:]
        for i in range(0, len(daten), 3):
            try:
                h, ip, p = daten[i], daten[i+1], int(daten[i+2])
                bekannte_nutzer[h] = (ip, p)
            except IndexError:
                continue
        if debug_mode:
            print(f"[DEBUG] Nutzerliste aktualisiert: {bekannte_nutzer}")

    elif teile[0] == "JOIN" and len(teile) == 3:
        h, port = teile[1], int(teile[2])
        bekannte_nutzer[h] = (addr[0], port)
        print(f"[INFO] Neuer Nutzer: {h} @ {addr[0]}:{port}")

        daten = []
        for h, (ip, p) in bekannte_nutzer.items():
            daten.extend([h, ip, str(p)])
        antwort = "KNOWNUSERS " + " ".join(daten)
        udp_send(antwort, addr[0], config["whoisport"])

    elif teile[0] == "WHO":
        daten = []
        for h, (ip, p) in bekannte_nutzer.items():
            daten.extend([h, ip, str(p)])
        antwort = "KNOWNUSERS " + " ".join(daten)
        udp_send(antwort, addr[0], config["whoisport"])

# === TCP-Nachrichten empfangen ===
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


# === Lokale IP-Adresse ermitteln ===
def get_own_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Nutze einen echten Zielhost, der im Netzwerk erreichbar ist
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.clos()

# === Verlauf speichern ===
def speichere_verlauf():
    with open("chat_verlauf.txt", "w", encoding="utf-8") as datei:
        for nachricht in chat_verlauf:
            datei.write(nachricht + "\n")
    print("Chatverlauf gespeichert in 'chat_verlauf.txt'.")

# === Hilfe anzeigen ===
def zeige_hilfe():
    print("Befehle:")
    print("/hilfe           - Hilfe anzeigen")
    print("/name [Name]     - Namen ändern")
    print("/verlauf         - Nachrichtenverlauf anzeigen")
    print("/nutzer          - Bekannte Nutzer zeigen")
    print("/msg [Name] [Text] - Nachricht senden")
    print("/ip              - Eigene IP anzeigen")
    print("exit             - Beenden")

# === Hauptfunktion CLI
def start_cli():
    global benutzername

    print("Willkommen zum Chat! Tippe /hilfe für Optionen.")

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
                print("Keine Nutzer bekannt.")
            if debug_mode:
                print(f"[DEBUG] bekannte_nutzer: {bekannte_nutzer}")

        elif eingabe.startswith("/msg "):
            teile = eingabe.split(" ", 2)
            if len(teile) < 3:
                print("Nutze: /msg [Name] [Text]")
                continue
            ziel, text = teile[1], teile[2]
            if ziel in bekannte_nutzer:
                ip, port = bekannte_nutzer[ziel]
                tcp_send(f"MSG {benutzername} {text}", ip, port)
                chat_verlauf.append(f"(an {ziel}) {benutzername}: {text}")
            else:
                print("Unbekannter Nutzer.")

        elif eingabe == "/ip":
            print("Deine IP:", get_own_ip())

        elif eingabe:
            print("Unbekannter Befehl. Tippe /hilfe.")


# === Startpunkt
if __name__ == "__main__":
    args = parse_args()
    debug_mode = args.debug
    config = load_config()

    # Config-Overrides
    if args.handle: config["handle"] = args.handle
    if args.port: config["port"] = args.port
    if args.autoreply: config["autoreply"] = args.autoreply
    if args.whoisport: config["whoisport"] = args.whoisport
    if args.broadcast_ip: config["broadcast_ip"] = args.broadcast_ip

    benutzername = config.get("handle", "Benutzer")
    whoisport = config.get("whoisport", 4000)
    broadcast_ip = config.get("broadcast_ip", "255.255.255.255")
    udp_port, tcp_port = config["port"]

    # JOIN & Listener
    udp_send(f"JOIN {benutzername} {tcp_port}", broadcast_ip, whoisport)
    threading.Thread(target=udp_listener, args=(whoisport, discovery_callback), daemon=True).start()
    threading.Thread(target=empfange_tcp, args=(tcp_port,), daemon=True).start()

    # Regelmäßig WHO senden
    def wiederhole_who():
        udp_send("WHO", broadcast_ip, whoisport)
        threading.Timer(10, wiederhole_who).start()
    wiederhole_who()

    start_cli()
