import threading
from network import load_config, udp_listener, tcp_server, udp_send, tcp_send
import time
import socket



cfg = load_config()

tcp_port = cfg["port"][0]
udp_port = cfg["port"][1]
handle = cfg["handle"]
whoisport = cfg["whoisport"]

# Starte den WHOIS-Listener im Hintergrund
threading.Thread(target=udp_listener, args=(whoisport,), daemon=True).start()

# Starte UDP- und TCP-Server im Hintergrund
threading.Thread(target=udp_listener, args=(udp_port,), daemon=True).start()
threading.Thread(target=tcp_server, args=(tcp_port,), daemon=True).start()

# NEU: JOIN an Discovery senden
udp_send(f"JOIN {handle} {tcp_port}", "127.0.0.1", whoisport)

# Sende WHO und eine Nachricht an den Discovery-Dienst
time.sleep(1)
udp_send("WHO", "127.0.0.1", whoisport)

# Sende eine Nachricht über UDP und TCP
time.sleep(1)
udp_send(f"{handle} sagt hallo über UDP", "127.0.0.1", udp_port)
tcp_send("Hallo über TCP", "127.0.0.1", tcp_port)
