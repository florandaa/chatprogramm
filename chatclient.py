
import socket
import threading

def empfangen(sock):
    while True:
        try:
            daten = sock.recv(1024).decode()
            if daten:
                print("\n" + daten)
        except:
            print("Verbindung wurde unterbrochen.")
            break

def senden(sock, benutzername):
    while True:
        nachricht = input()
        if nachricht.lower() == "exit":
            sock.send("exit".encode())
            break
        sock.send(nachricht.encode())

def start_client(server_ip='127.0.0.1', port=12345):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, port))

    benutzername = input("Benutzername: ")
    sock.send(benutzername.encode())

    threading.Thread(target=empfangen, args=(sock,), daemon=True).start()
    senden(sock, benutzername)

    sock.close()
    print("Verbindung geschlossen.")

if __name__ == "__main__":
    start_client()
