# Chatprogramm 
BSRN Projekt: Dies ist ein Peer-to-Peer (P2P) Chatprogramm, das im Rahmen des Moduls entwickelt wurde.

## Features 
- Benutzerdefinierte Handles (Benutzernamen)
- Lokale Discovery der anderen Nutzer über `WHO`, `JOIN`, `LEAVE`
- P2P-Kommunikation zwischen Clients
- Automatische Abwesenheitsnachrichten
- Bildübertragung 
- Konfigurierbare Ports und Einstellungen per `.toml`-Datei

## Architektur

Das Programm besteht aus drei Hauptprozessen:

- **Benutzer-Schnittstelle (UI):** Kommandozeilen-Schnittstelle (CLI) zur Interaktion; optionale grafische Oberfläche (GUI)  
- **Netzwerk-Kommunikation:** Umsetzung des Simple Local Chat Protocol (SLCP) für UDP- und TCP-Nachrichten  
- **Discovery-Dienst:** Verwaltung aktiver Teilnehmer über Broadcast-Nachrichten

Diese Prozesse kommunizieren über IPC (z. B. Sockets) und nutzen eine gemeinsame TOML-Konfigurationsdatei zur Einstellung.

## Installation und Nutzung

1. Voraussetzung: Python 3.x auf Linux-System  
2. Repository klonen und in das Projektverzeichnis wechseln  
3. Abhängigkeiten installieren (z.B. mit `pip install toml`)  
4. Die Datei `config.toml` anpassen, falls nötig (Benutzername, Ports, Speicherpfad für Bilder etc.)  
5. Programm starten über:  
   ```bash  
   python3 main.py  