# main.py - Vollständig korrigierte Version
import sys
import socket
import subprocess
import threading
import time
import argparse
from network import load_config, udp_send, udp_listener, get_own_ip
 
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle", required=True, help="Dein Benutzername")
    parser.add_argument("--port", nargs=2, type=int, required=True,
                       help="UDP- und TCP-Ports (z. B. 5000 5001)")
    parser.add_argument("--whoisport", type=int, required=True,
                       help="Discovery-Dienst-Port")
    parser.add_argument("--autoreply", help="Automatische Antwortnachricht")
    return parser.parse_args()
 
def discovery_running(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", port))
        s.close()
        return False
    except:
        return True
 
def main():
    args = parse_args()
    config = load_config()
   
    # Merge args with config
    config["handle"] = args.handle
    config["port"] = args.port
    config["whoisport"] = args.whoisport
    if args.autoreply:
        config["autoreply"] = args.autoreply
 
    # Start discovery if not running
    if not discovery_running(config["whoisport"]):
        print("Starte Discovery-Dienst...")
        subprocess.Popen([sys.executable, "discovery.py"])
        time.sleep(1)  # Wait for discovery to start
 
    # Send initial messages
    join_msg = f"JOIN {config['handle']} {config['port'][1]}"
    udp_send(join_msg, "255.255.255.255", config["whoisport"])
    time.sleep(0.5)
    udp_send("WHO", "255.255.255.255", config["whoisport"])
 
    # Start CLI/GUI
    print("1) CLI\n2) GUI")
    choice = input("> ").strip()
   
    if choice == "1":
        from cli import start_cli
        start_cli(
            handle=config["handle"],
            port=config["port"][1],  # TCP port
            whoisport=config["whoisport"]
        )
    elif choice == "2":
        subprocess.Popen([
            sys.executable,
            "chat_gui_client_verbessert.py",
            "--handle", config["handle"],
            "--port", str(config["port"][0]), str(config["port"][1]),
            "--whoisport", str(config["whoisport"])
        ])
 
if __name__ == "__main__":
    main()
