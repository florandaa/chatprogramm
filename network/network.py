import socket # Für Netzwerk-Kommunikation (UDP und TCP)
import threading  # Um Server/Listener im Hintergrund laufen zu lassen
import toml # Zum Einlesen der Konfigurationsdatei (.toml)

def load_config(path="config/config.toml"): # config.toml laden um in main.py ports und benutzernamen zu laden
    with open(path, "r") as f:
        return toml.load(f)

def udp_listener(port): # wartet auf Nachrichten auf einem bestimmten Port 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP-Socket erstellen
    sock.bind(("0.0.0.0", port)) # An allen IPs dieses Rechners auf Port lauschen
    print(f"[UDP] Wartet auf Port {port}...")
    while True:
        data, addr = sock.recvfrom(1024) # Wartet auf eingehende Nachrichten
        print(f"[UDP] Von {addr}: {data.decode()}") # Nachricht ausgeben

def udp_send(message, ip, port): # Sendet eine UDP-Nachricht an eine bestimmte IP-Adresse und Port (JOIN, WHO, etc.)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP-Socket
    sock.sendto(message.encode(), (ip, port)) # Nachricht an Ziel-IP/Port senden

def tcp_server(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP-Socket
    sock.bind(("0.0.0.0", port)) # Lauscht auf allen Netzwerkschnittstellen
    sock.listen() # Verbindungen akzeptieren
    print(f"[TCP] Server läuft auf Port {port}") 
    while True:
        conn, addr = sock.accept()  # Wartet auf eingehende Verbindung
        data = conn.recv(1024) # Liest Nachricht
        print(f"[TCP] Von {addr}: {data.decode()}")
        conn.sendall(b"Empfangen") # Antwort senden
        conn.close() # Verbindung beenden

def tcp_send(message, ip, port): # für Kommunikation zwischen zwei Teilnehmern
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP-Socket
    sock.connect((ip, port)) # Verbindung zum Server aufbauen
    sock.sendall(message.encode()) # Nachricht senden
    response = sock.recv(1024) # Antwort empfangen
    print("Antwort:", response.decode()) # Antwort anzeigen
    sock.close() # Verbindung schließen
