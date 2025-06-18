#!/bin/bash

echo "🔍 Projektüberprüfung startet..."
echo "===================================="

# 1. Check: Python-Version
echo "🧪 Python-Version:"
python3.11 --version || { echo "❌ Python 3.11 nicht gefunden."; exit 1; }

# 2. Check: Wichtige Dateien vorhanden?
dateien=("main.py" "cli.py" "network.py" "chat_gui_client.py" "config.toml")

for file in "${dateien[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file gefunden"
    else
        echo "❌ $file fehlt!"
    fi
done

# 3. Check: Python-Module vorhanden?
echo "🧪 Python-Module:"
fehlermodul=0
for modul in toml tkinter; do
    python3.11 -c "import $modul" 2>/dev/null \
        && echo "✅ $modul vorhanden" \
        || { echo "❌ $modul fehlt"; fehlermodul=1; }
done
[[ $fehlermodul -eq 1 ]] && echo "👉 Bitte mit 'pip install toml' nachinstallieren."

# 4. Check: config.toml lesbar?
echo "🧪 config.toml testen:"
python3.11 -c "import toml; toml.load('config.toml')" && echo "✅ config.toml ok" || echo "❌ Fehler beim Einlesen von config.toml"

# 5. Check: Ports auslesen
UDPPORT=$(python3.11 -c "import toml; c=toml.load('config.toml'); print(c['port'][1])")
TCPPORT=$(python3.11 -c "import toml; c=toml.load('config.toml'); print(c['port'][0])")

echo "🧪 UDP-Port: $UDPPORT / TCP-Port: $TCPPORT"

# 6. Check: Ports frei?
echo "🧪 Prüfe ob Ports blockiert sind:"
if lsof -i UDP:$UDPPORT >/dev/null; then echo "⚠️ UDP $UDPPORT belegt"; else echo "✅ UDP-Port frei"; fi
if lsof -i TCP:$TCPPORT >/dev/null; then echo "⚠️ TCP $TCPPORT belegt"; else echo "✅ TCP-Port frei"; fi

# 7. Testweise Discovery starten?
read -p "🚀 Discovery-Dienst jetzt testweise starten? (y/n) " antwort
if [[ "$antwort" == "y" ]]; then
    echo "📡 Starte Discovery (Strg+C zum Beenden)..."
    python3.11 discovery.py
else
    echo "⏩ Überspringe Discovery-Test"
fi

echo "===================================="
echo "✅ Projektprüfung abgeschlossen."

