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
 
def tcp_server(port, callback=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen()
    print(f"[TCP] Server auf Port {port}")
   
    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024).decode("utf-8")
        if debug_mode:
            print(f"[DEBUG] TCP empfangen von {addr}: {data}")
        if callback:
            callback(data)
        conn.close()
 
def tcp_send(message, ip, port, binary=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)  # Timeout hinzugefügt
    try:
        sock.connect((ip, port))
        if binary:
            sock.sendall(message)
        else:
            sock.sendall(message.encode())
        if debug_mode:
            print(f"[DEBUG] TCP gesendet an {ip}:{port} → {message[:50] if not binary else '[BINÄRDATEN]'}")
    except Exception as e:
        print(f"[FEHLER] TCP: {e}")
    finally:
        sock.close()
 
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
 
def tcp_server(port, callback=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen()
    print(f"[TCP] Server auf Port {port}")
   
    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024).decode("utf-8")
        if debug_mode:
            print(f"[DEBUG] TCP empfangen von {addr}: {data}")
        if callback:
            callback(data)
        conn.close()
 
def get_own_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"
 