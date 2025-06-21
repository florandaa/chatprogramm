# Chatprogramm 
BSRN Projekt: Dies ist ein Peer-to-Peer (P2P) Chatprogramm, das im Rahmen des Moduls entwickelt wurde.

## Installation und Nutzung

1. Voraussetzung: Python 3.10 oder höher auf Linux-System  
2. Repository klonen und in das Projektverzeichnis wechseln  
3. Abhängigkeiten installieren (z.B. mit `pip install toml`)  
4. Die Datei `config.toml` anpassen, falls nötig (Benutzername, Ports Speicherpfad für Bilder etc.)  
5. Programm starten über:  
   python3 main.py

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

Diese Prozesse kommunizieren über IPC und nutzen eine gemeinsame TOML-Konfigurationsdatei zur Einstellung.

### Protokoll

Es wird das Simple Local Chat Protocol (SLCP) genutzt, das Textnachrichten und Bildübertragungen über UDP/TCP erlaubt. Wichtige Befehle sind JOIN, LEAVE, WHO, MSG und IMG.

## 3. Designentscheidungen und Ansätze

- Verwendung von Python für schnelle Entwicklung und gute Bibliotheksunterstützung  
- Trennung in drei Prozesse zur modularen Struktur und parallelen Verarbeitung  
- IPC via Sockets für effiziente und flexible Kommunikation zwischen Prozessen  
- Konfiguration über TOML-Datei für einfache Anpassbarkeit und Übersichtlichkeit  
- Unterstützung von CLI und GUI für unterschiedliche Nutzerbedürfnisse

## 4. Kommunikationsabläufe

- **JOIN:** Nutzer tritt dem Chat bei, sendet Broadcast mit Handle und Port  
- **LEAVE:** Nutzer verlässt den Chat, informiert Discovery-Dienst und andere Clients  
- **WHO:** Broadcast-Anfrage zur Ermittlung aktiver Teilnehmer  
- **KNOWUSERS:** Discovery-Dienst antwortet mit Liste bekannter Nutzer  
- **MSG:** Versand von Textnachrichten direkt an einen Nutzer (Unicast)  
- **IMG:** Versand von Bildnachrichten mit anschließenden Binärdaten

## 5. Besondere Herausforderungen & Lösungen

- **Mehrfachstart des Discovery-Dienstes:** Es wird sichergestellt, dass nur ein Discovery-Dienst läuft  
- **Bildübertragung:** Synchronisation und genaue Größenangabe bei Binärdaten  
- **Netzwerkfehler und Verbindungsabbrüche:** Fehlerbehandlung und automatische Wiederverbindung implementiert  
- **Konfigurationsänderungen zur Laufzeit:** Modifikation der TOML-Datei über die CLI ermöglicht dynamische Anpassungen

## 6. Bedienung und Konfiguration

- Start des Programms via `python3 main.py` auf Linux-Systemen  
- Konfigurationsdatei `config.toml` im Projektordner, mit Parametern wie `handle`, `port`, `whoisport`, `autoreply`, `imagepath`  
- CLI-Befehle zur Kommunikation und Konfigurationsanpassung  
- Optional: GUI für benutzerfreundliche Bedienung  

## 7. Erweiterungsmöglichkeiten

- Erweiterung der GUI für bessere Nutzererfahrung  
- Verschlüsselung der Nachrichten für mehr Sicherheit  
- Unterstützung für Gruppen-Chats  
- Erweiterung des Protokolls für weitere Medientypen  
- Unterstützung weiterer Plattformen (Windows, macOS)

## 8. Anhang

### Diagramme

- Architekturdiagramm der Prozess-Kommunikation  
- Ablaufdiagramme für JOIN, WHO, MSG etc.

### Screenshots

- Beispielhafte Darstellung der CLI und GUI  
- Beispielhafte Anzeige empfangener Nachrichten und Bilder

---

## Dokumentation

Die ausführliche Quellcodedokumentation ist mit Doxygen generiert und im `/docs` Verzeichnis enthalten.
