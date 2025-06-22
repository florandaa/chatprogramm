import socket
import threading
import toml
import os

debug_mode = False
 
def load_config(path="config.toml"):
    return toml.load(os.path.abspath(path))
 
def udp_listener(port, callback=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", port))
   
    if debug_mode:
        print(f"[DEBUG] UDP-Listener auf Port {port}")
   
    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode().strip()
        if debug_mode:
            print(f"[DEBUG] UDP empfangen von {addr}: {message}")
        if callback:
            callback(message, addr)
 
def udp_send(message, ip, port):
   
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # WICHTIG
   
    if debug_mode:
        print(f"[DEBUG] UDP senden an {ip}:{port} → {message}")
   
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if ip.endswith(".255"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        sock.sendto(message.encode(), (ip, port))
    except Exception as e:
        print(f"[FEHLER] UDP-Senden: {e}")
    finally:
        sock.close()
 
