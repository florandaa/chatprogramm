# @file network.py
# @brief Netzwerkmodul für SLCP: UDP & TCP Kommunikation, Konfiguration laden 

import socket # Für Netzwerk-Kommunikation (UDP und TCP)
import threading  # Um Server/Listener im Hintergrund laufen zu lassen
import toml # Zum Einlesen der Konfigurationsdatei (.toml)
import os

debug_mode = False  # Wird durch main.py oder cli.py gesetzt

# === Konfigurationsdatei laden ===
def load_config(path="config.toml"):
    return toml.load(os.path.abspath(path))

 ##Wartet auf Nachrichten auf einem bestimmten Port 
def udp_listener(port, callback=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP-Socket erstellen
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Erlaubt das Wiederverwenden der Adresse
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Erlaubt Broadcast-
    sock.bind(("0.0.0.0", port)) # An allen IPs dieses Rechners auf Port lauschen
    
    if debug_mode:
        print(f"[DEBUG] UDP-Listener auf Port {port} gestartet")
    
    while True:
        data, addr = sock.recvfrom(1024)  # Wartet auf eingehende Nachrichten
        message = data.decode().strip()
        if debug_mode:
            print(f"[DEBUG] UDP empfangen von {addr}: {message}")
        if callback:
            callback(message, addr)

##Sendet eine UDP-Nachricht an eine bestimmte IP-Adresse und Port (JOIN, WHO, etc.)
def udp_send(message, ip, port): 
    if debug_mode:
        print(f"[DEBUG] UDP senden an {ip}:{port} → {message}")
    
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
        if debug_mode:
            print(f"[DEBUG] TCP empfangen von {addr}: {data}")
        if callback:
            callback(data)
        else:
            print(f"[TCP] Nachricht empfangen: {data}")
        conn.close()

## für Kommunikation zwischen zwei Teilnehmern 
## binary für Text- und Bildversand
def tcp_send(message, ip, port, binary=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP-Socket
    try:
        sock.connect((ip, port))
        if binary:
            sock.sendall(message)
        else:
            sock.sendall(message.encode())
        if debug_mode:
            print(f"[DEBUG] TCP gesendet an {ip}:{port} → {message if not binary else '[BINÄRDATEN]'}")
        # Optional: auf Antwort warten
        # response = sock.recv(1024)
        # print("Antwort:", response.decode())
    except Exception as e:
        print(f"[FEHLER] TCP-Verbindung zu {ip}:{port} fehlgeschlagen:", e)
    finally:
        sock.close()  # Verbindung schließen

# === TCP-Listener (nur für GUI – ruft Callback auf)
def starte_tcp_listener(port, callback):
    def tcp_server():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", port))
        server.listen()
        if debug_mode:
            print(f"[DEBUG] TCP-Listener gestartet auf Port {port}")
        while True:
            conn, _ = server.accept()
            data = conn.recv(1024).decode("utf-8")
            if data:
                callback(data)
            conn.close()

    threading.Thread(target=tcp_server, daemon=True).start()

## Listener für mehrere Ports gleichzeitig starten (optional)
def start_all_listeners(udp_ports, tcp_port, callback=None):
    for port in udp_ports:
        threading.Thread(target=udp_listener, args=(port, callback), daemon=True).start()
    threading.Thread(target=tcp_server, args=(tcp_port, callback), daemon=True).start()