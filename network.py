import socket
import threading
import toml

def load_config(path="config.toml"):
    with open(path, "r") as f:
        return toml.load(f)

def udp_listener(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    print(f"[UDP] Wartet auf Port {port}...")
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"[UDP] Von {addr}: {data.decode()}")

def udp_send(message, ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (ip, port))

def tcp_server(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen()
    print(f"[TCP] Server läuft auf Port {port}")
    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024)
        print(f"[TCP] Von {addr}: {data.decode()}")
        conn.sendall(b"Empfangen")
        conn.close()

def tcp_send(message, ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    sock.sendall(message.encode())
    response = sock.recv(1024)
    print("Antwort:", response.decode())
    sock.close()
