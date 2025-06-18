#!/bin/bash

cd "$(dirname "$0")"

echo "Bereinige vorherige Peer-Daten..."
rm -f peer_info.json

echo "Starte Chat-GUI (Sara, WHOIS-Port 4000)..."
osascript -e 'tell application "Terminal"
    do script "cd \"'"$PWD"'\" && python3.11 chat_gui_client.py --handle Sara --port 5100 5101 --whoisport 4000 --autoreply \"AFK für 5 Min\""
end tell'

sleep 2

echo "Starte Chat-CLI (Ilirjon, WHOIS-Port 4000)..."
osascript -e 'tell application "Terminal"
    do script "cd \"'"$PWD"'\" && python3.11 chat_gui_client.py --handle Ilirjon --port 5200 5201 --whoisport 4000 --autoreply \"Bin gleich zurück\""
end tell'
