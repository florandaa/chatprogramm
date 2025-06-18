#!/bin/bash

cd "$(dirname "$0")"

# 🧹 Lokale Peer-Datei optional löschen
rm -f peer_info.json

# �� Benutzereingabe
read -p "Dein Benutzername (z. B. Sara): " HANDLE
read -p "UDP Port (z. B. 5100): " UDPPORT
read -p "Zusätzlicher Port (z. B. 5101): " UDPPORT2
read -p "WHOIS-Port (z. B. 4000): " WHOISPORT
read -p "Autoreply-Text: " AUTOREPLY

echo "Starte Chat-GUI für $HANDLE..."

osascript -e 'tell application "Terminal"
    do script "cd \"'"$PWD"'\" && python3.11 chat_gui_client.py \
    --handle '"$HANDLE"' \
    --port '"$UDPPORT"' '"$UDPPORT2"' \
    --whoisport '"$WHOISPORT"' \
    --autoreply \"'"$AUTOREPLY"'\""
end tell'

