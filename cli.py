import socket
import threading
import time
import re
import sys
from datetime import datetime
from network import get_own_ip


# Farbcodes für die Konsolenausgabe
class colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

# Konfiguration
IP_BROADCAST = "255.255.255.255"
chat_verlauf = []
bekannte_nutzer = {}

def format_timestamp():
    return f"{colors.BLUE}[{datetime.now().strftime('%H:%M:%S')}]{colors.END}"

def print_system(msg):
    print(f"{format_timestamp()} {colors.YELLOW}⚙️ {msg}{colors.END}")

def print_message(sender, msg):
    print(f"\n{format_timestamp()} {colors.GREEN}✉️ {sender}: {msg}{colors.END}")
    print(f"load.config[handle] ", end="", flush=True)

def print_error(msg):
    print(f"{format_timestamp()} {colors.RED}❌ {msg}{colors.END}")

def print_success(msg):
    print(f"{format_timestamp()} {colors.GREEN}✅ {msg}{colors.END}")

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

def udp_empfaenger(whoisport, handle):
    global bekannte_nutzer
    print_system(f"UDP-Empfänger gestartet mit handle={handle} auf Port {whoisport}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("0.0.0.0", whoisport))
    except OSError:
        print_error(f"UDP-Port {whoisport} belegt – Discovery-Dienst läuft wahrscheinlich schon.")
        print_system("Versuche stattdessen auf zufälligem freien Port zu lauschen...")
        try:
            sock.bind(("0.0.0.0", 0))  # Betriebssystem gibt freien Port
            print_system(f"UDP-Empfang läuft auf Port {sock.getsockname()[1]}")
        except Exception as e:
            print_error(f"Konnte keinen alternativen Port öffnen: {e}")
            return


    
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            msg = data.decode().strip()
            
            if msg.startswith("KNOWNUSERS"):
                neue_nutzer = {}
                teile = msg.split()[1:]
                for i in range(0, len(teile), 3):
                    if i + 2 < len(teile):
                        name, ip, port = teile[i], teile[i + 1], int(teile[i + 2])
                        if name != handle:  # <== Eigener Nutzer wird nicht gespeichert
                            neue_nutzer[name] = (ip, port)
                bekannte_nutzer.update(neue_nutzer)

                if neue_nutzer:
                    print_system(f"Nutzerliste aktualisiert: {', '.join(neue_nutzer.keys())}")
                else:
                    print_system("Keine neuen Nutzer empfangen.")

        except Exception as e:
            print_error(f"UDP Fehler: {e}")

def start_cli(handle, port, whoisport):
    # Listener starten
    threading.Thread(target=empfange_tcp, args=(port,), daemon=True).start()
    threading.Thread(target=udp_empfaenger, args=(whoisport, handle), daemon=True).start()
    
    # JOIN senden
    eigene_ip = get_own_ip()
    join_msg = f"JOIN {handle} {eigene_ip} {port}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(join_msg.encode(), (IP_BROADCAST, whoisport))
    print_system(f"JOIN Nachricht gesendet")
    
    # WHO senden
    time.sleep(0.5)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b"WHO", (IP_BROADCAST, whoisport))
    
    # Hauptloop
    try:
        while True:
            cmd = input(f"{handle}> ").strip()
            
            if cmd == "/hilfe":
                print("Befehle:\n/nutzer - Liste aller Nutzer\n/msg <Name> \"Text\" - Nachricht senden\n/exit - Beenden")
            
            elif cmd == "/nutzer":
                print("🟢 Aktive Nutzer:")
                for name, (ip, port) in bekannte_nutzer.items():
                    if name != handle:
                        print(f"- {name} @ {ip}:{port}")
                if len(bekannte_nutzer) <= 1:
                    print("Keine anderen Nutzer online")
            
            elif cmd.startswith("/msg "):
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
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.sendto(f"LEAVE {handle}".encode(), (IP_BROADCAST, whoisport))
                break
                
    except KeyboardInterrupt:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(f"LEAVE {handle}".encode(), (IP_BROADCAST, whoisport))
        print("\nChat beendet")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 cli.py <handle> <port> <whoisport>")
        sys.exit(1)
        
    start_cli(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))