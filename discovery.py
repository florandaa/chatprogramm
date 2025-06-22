import socket
import threading
from datetime import datetime

class DiscoveryService:
    def __init__(self, port=4000):
        self.port = port
        self.participants = {}
        self.lock = threading.Lock()
        self.running = True
        
    def handle_request(self, data, addr):
        try:
            msg = data.decode("utf-8").strip()
            print(f"[DISCOVERY] {datetime.now().strftime('%H:%M:%S')} - Received from {addr}: {msg}")

            if msg.startswith("JOIN"):
                parts = msg.split()
                if len(parts) >= 4:
                    handle = parts[1]
                    chat_port = int(parts[2])
                    file_port = int(parts[3]) if len(parts) > 3 else None
                    with self.lock:
                        self.participants[handle] = {
                            'ip': addr[0],
                            'chat_port': chat_port,
                            'file_port': file_port
                        }
                    print(f"[JOIN] {handle} @ {addr[0]}:{chat_port}")
                    self.broadcast_participants()


            elif msg == "WHO":
                self.send_participants(addr)

            elif msg.startswith("LEAVE"):
                handle = msg.split()[1]
                with self.lock:
                    if handle in self.participants:
                        del self.participants[handle]
                        print(f"[DISCOVERY] {handle} left the chat")

        except Exception as e:
            print(f"[DISCOVERY ERROR] {e}")

    def broadcast_participants(self):
        with self.lock:
            msg = "KNOWNUSERS " + " ".join(
                f"{h} {d['ip']} {d['chat_port']}"
                for h, d in self.participants.items()
            )

        self.send_message(msg, '255.255.255.255', self.port)

    def send_participants(self, addr):
        with self.lock:
            msg = "KNOWNUSERS " + " ".join(
                f"{h} {d['ip']} {d['chat_port']}"
                for h, d in self.participants.items()
            )

        self.send_message(msg, addr[0], addr[1])

    @staticmethod
    def send_message(msg, ip, port):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(msg.encode("utf-8"), (ip, port))

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", self.port))
        
        print(f"[DISCOVERY] Service started on port {self.port}")
        try:
            while self.running:
                data, addr = sock.recvfrom(1024)
                threading.Thread(target=self.handle_request, args=(data, addr)).start()
        finally:
            sock.close()

def start_discovery():
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    service = DiscoveryService(port)
    service.start()

if __name__ == "__main__":
    start_discovery()