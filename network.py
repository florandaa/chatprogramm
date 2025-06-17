# @file network.py
# @brief Netzwerkmodul für SLCP: UDP & TCP Kommunikation, Konfiguration laden 

import socket # Für Netzwerk-Kommunikation (UDP und TCP)
import threading  # Um Server/Listener im Hintergrund laufen zu lassen
import toml # Zum Einlesen der Konfigurationsdatei (.toml)
import os

#Arbeitsverzeichnis anzeigen (kann beim Debuggen helfen, aber ist optional)
print("Arbeitsverzeichnis:", os.getcwd())

#Pfad zur config.toml berechnen
pfad = os.path.abspath("config.toml") 

def load_config(path = "config.toml"):  # config.toml laden um in main.py ports und benutzernamen zu laden
    import toml
    with open(os.path.abspath(path), "r") as f:
        return toml.load(f)

 ##Wartet auf Nachrichten auf einem bestimmten Port 
def udp_listener(port, callback=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP-Socket erstellen
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Erlaubt das Wiederverwenden der Adresse
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Erlaubt Broadcast-
    sock.bind(("0.0.0.0", port)) # An allen IPs dieses Rechners auf Port lauschen
    print(f"[UDP] Wartet auf Port {port}...")
    while True:
        data, addr = sock.recvfrom(1024)  # Wartet auf eingehende Nachrichten
        message = data.decode().strip()
        print(f"[UDP] Von {addr}: {message}")  # Nachricht ausgeben
        if callback:
            callback(message, addr)  # Weiterleiten, z. B. an main.py oder CLI

##Sendet eine UDP-Nachricht an eine bestimmte IP-Adresse und Port (JOIN, WHO, etc.)
def udp_send(message, ip, port): 
    print(f"[DEBUG] Sende UDP an {ip}:{port} mit: {message}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Wenn Broadcast-Adresse → Broadcast aktivieren
    if ip.endswith(".255"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        sock.sendto(message.encode(), (ip, port))
    except PermissionError as e:
        print(f"[FEHLER] Keine Berechtigung beim UDP-Senden an {ip}:{port}: {e}")
    except Exception as e:
        print(f"[FEHLER] UDP-Senden fehlgeschlagen: {e}")
    finally:
        sock.close()

## TCP-Server: wartet auf eingehende TCP-Verbindungen (z. B. MSG, IMG)
def tcp_server(port, callback=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP-Socket
    sock.bind(("0.0.0.0", port))  # Lauscht auf allen Netzwerkschnittstellen
    sock.listen()  # Verbindungen akzeptieren
    print(f"[TCP] Server läuft auf Port {port}")
    while True:
        conn, addr = sock.accept()  # Wartet auf eingehende Verbindung
        data = conn.recv(1024).decode("utf-8")  # Liest Nachricht
        if callback:
            callback(data)
        else:
            print(f"[TCP] Nachricht empfangen: {data}")
        conn.close()

## für Kommunikation zwischen zwei Teilnehmern (z. B. MSG)
def tcp_send(message, ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP-Socket
    try:
        sock.connect((ip, port))  # Verbindung zum Server aufbauen
        sock.sendall(message.encode())  # Nachricht senden
        response = sock.recv(1024)  # Antwort empfangen
        print("Antwort:", response.decode())  # Antwort anzeigen
    except Exception as e:
        print(f"[FEHLER] TCP-Verbindung zu {ip}:{port} fehlgeschlagen:", e)
    finally:
        sock.close()  # Verbindung schließen

## Listener für mehrere Ports gleichzeitig starten (optional)
def start_all_listeners(udp_ports, tcp_port, callback=None):
    for port in udp_ports:
        threading.Thread(target=udp_listener, args=(port, callback), daemon=True).start()
    threading.Thread(target=tcp_server, args=(tcp_port, callback), daemon=True).start()