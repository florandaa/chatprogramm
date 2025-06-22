import socket
import threading
import time
 
participants = {}
whoisport = 4000  # Standard-Port für Discovery
 
def handle_request(data, addr):
    msg = data.decode().strip()
    print(f"[DISCOVERY] Empfangen von {addr}: {msg}")  # Debug
   
    if msg.startswith("JOIN") and len(msg.split()) == 3:
        handle, port = msg.split()[1], int(msg.split()[2])
        participants[handle] = (addr[0], port)
        print(f"[JOIN] {handle} @ {addr[0]}:{port}")
 
        # KNOWNUSERS an ALLE senden (Broadcast)
        antwort = "KNOWNUSERS " + " ".join([f"{h} {ip} {p}" for h, (ip, p) in participants.items()])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(antwort.encode(), ('255.255.255.255', whoisport))
        print(f"[BROADCAST] Gesendet: {antwort}")
 
    elif msg == "WHO":
        antwort = "KNOWNUSERS " + " ".join([f"{h} {ip} {p}" for h, (ip, p) in participants.items()])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(antwort.encode(), addr)
        print(f"[UNICAST] Antwort an {addr}: {antwort}")
 
    elif msg.startswith("LEAVE"):
        handle = msg.split()[1]
        if handle in participants:
            del participants[handle]
            print(f"[LEAVE] {handle} hat den Chat verlassen")
 
def start_discovery():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", whoisport))
    print(f"🔍 Discovery-Dienst läuft auf Port {whoisport}")
   
    while True:
        data, addr = sock.recvfrom(1024)
        threading.Thread(target=handle_request, args=(data, addr)).start()
 
if __name__ == "__main__":
    start_discovery()
 