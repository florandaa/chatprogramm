import threading
from network.network import load_config, udp_listener, tcp_server, udp_send, tcp_send
import time
import socket

cfg = load_config()

tcp_port = cfg["port"][0]
udp_port = cfg["port"][1]
handle = cfg["handle"]

threading.Thread(target=udp_listener, args=(udp_port,), daemon=True).start()
threading.Thread(target=tcp_server, args=(tcp_port,), daemon=True).start()

udp_send(f"{handle} sagt hallo über UDP", "127.0.0.1", udp_port)
tcp_send("Hallo über TCP", "127.0.0.1", tcp_port)
