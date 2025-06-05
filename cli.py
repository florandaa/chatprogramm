chat_verlauf = [] # Liste zum Speichern des Chatverlaufs
benutzername = "Benutzer" # Standard-Benutzername

def zeige_hilfe():# Funktion zum Anzeigen der Hilfe
    print("Befehle:")
    print("/hilfe   - Zeigt diese Hilfe an") 
    print("/name [name]  -  Ändert deinen Namen")
    print("/verlauf  -  Zeigt alle gesendeten Nachrichten ")
    print("exit - Beendet den Chat")

def speichere_verlauf(): # Funktion zum Speichern des Chatverlaufs in eine Datei
    with open("chat_verlauf.txt", "w", encoding="utf-8") as datei:
        for nachricht in chat_verlauf:
            datei.write(nachricht + "\n")
    print("Chatverlauf gespeichert in 'chat_verlauf.txt'.")
    
def start_cli(): # Funktion zum Starten der CLI
    global benutzername # Erlaubt veränderung des globalen Benutzernamens
    print("willkommen") 
    print("Verfügbare Befehle: /hilfe, /name [name], /verlauf, exit\n")

    while True: 
        eingabe = input(f"{benutzername}: ").strip() # Eingabeaufforderung für den Benutzer

        if eingabe.lower() == "exit": # Beenden des Chats
            speichere_verlauf() # Speichert den Verlauf vor dem Beenden
            print("Chat wird beendet.")
            break
        
        elif eingabe.lower() == "/hilfe": 
            zeige_hilfe()

        elif eingabe.lower().startswith("/name "):
            teile = eingabe.split(" ", 1)

            if len(teile) == 2 and teile[1].strip() != "":
                neuer_name = teile[1].strip()
                if neuer_name:  # Überprüfen, ob der neue Name nicht leer ist
                 print(f"Benutzername wird geändert von {benutzername} zu {neuer_name}")
                 benutzername = neuer_name
                else:
                print("Fehler: Bitte gib einen Namen an. Beispiel: /name Mo")
            else:
                print("Fehler: Ungültiger Befehl. Beispiel: /name Mo")
                
        elif eingabe.lower() == "/verlauf".strip():
            if not chat_verlauf:
                print("Noch keine Nachrichten gespeichert.")
            else:
                print("Gespeicherte Nachrichten:")
                for nachricht in chat_verlauf:
                    print(nachricht)

        else:
            # normale Nachricht
           if eingabe:
            nachricht = f"{benutzername}: {eingabe}"
            chat_verlauf.append(nachricht)
            print("Nachricht gesendet:", nachricht)
            else:
                print("Fehler: Nachricht darf nicht leer sein.") # Leerzeilen vermeiden

# Zum Starten der CLI
if __name__ == "__main__":
    start_cli()