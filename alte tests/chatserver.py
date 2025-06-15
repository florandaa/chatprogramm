
import socket
import threading

clients = []
usernames = {}

def empfangen(conn, addr):
    benutzername = conn.recv(1024).decode()
    usernames[conn] = benutzername
    print(f"[VERBUNDEN] {benutzername} aus {addr} ist beigetreten.")
    speichern(f"{benutzername} ist dem Chat beigetreten.")

    while True:
        try:
            nachricht = conn.recv(1024).decode()
            if nachricht.lower() == "exit":
                print(f"[TRENNUNG] {benutzername} hat den Chat verlassen.")
                speichern(f"{benutzername} hat den Chat verlassen.")
                break

            gesendet = f"{benutzername}: {nachricht}"
            print(gesendet)
            speichern(gesendet)
            sende_an_alle(gesendet, conn)
        except:
            break

    conn.close()
    clients.remove(conn)
    usernames.pop(conn, None)

def sende_an_alle(nachricht, sender_conn):
    for client in clients:
        if client != sender_conn:
            try:
                client.send(nachricht.encode())
            except:
                pass

def speichern(nachricht):
    with open("chat_verlauf.txt", "a", encoding="utf-8") as f:
        f.write(nachricht + "\n")

def start_server(host="0.0.0.0", port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"Server läuft auf {host}:{port}")

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        threading.Thread(target=empfangen, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
