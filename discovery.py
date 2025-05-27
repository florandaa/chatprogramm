import toml
import threading

config = toml.load('config.toml')
handle = config['handle']
tcp_port = config['port'][0]
udp_port = config['port'][1]
whoisport = config['whoisport']

import socket

socket1 =socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

socket1.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)

socket1.bind(('',whoisport))

participants = {}

def discovery_loop():
    while True:
        data, addr = socket1.recvfrom(1024)
        message = data.decode('utf-8').strip()
        parts = message.split()

        if not parts:
            continue
        command = parts[0]

        if command == "JOIN" and len(parts) == 3:
            handle = parts[1]
            port = int(parts[2])
            ip = addr[0]
            participants[handle] = (ip, port)
            if handle not in participants:
                print(f"[JOIN] {handle} hinzugefügt: {ip, port}")
            else:
                print(f"[JOIN] {handle} bereits vorhanden, aktualisiere Eintrag.")

        elif command == "WHO":
            print(f"[WHO] Anfrage erhalten von {addr[0]}")
            entries = [f"{h} {ip} {p}" for h, (ip, p) in participants.items()]
            response = "KNOWUSERS " + ", ".join(entries)
            socket1.sendto(response.encode('utf-8'), (addr[0], 5000))

        elif command == "LEAVE" and len(parts) == 2:
            handle = parts[1]
            if handle in participants:
                del participants[handle]
                print(f"[LEAVE] {handle} wurde entfernt. ")
            else:
                print(f"[LEAVE] {handle} nicht gefunden. ")

threading.Thread(target=discovery_loop, daemon=True).start()

import time
while True:
    time.sleep(1)
