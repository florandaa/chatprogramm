#!/bin/bash

cd "$(dirname "$0")"

echo "Starte Chat-Client 1 (Sara, WHOIS-Port 4000)..."
osascript -e 'tell application "Terminal"
    do script "cd \"'"$PWD"'\" && python3.11 chat_gui_client.py --handle Sara --whoisport 4000"
end tell'

rm -f peer_info.json

sleep 2

echo "Starte Chat-Client 2 (Ilirjon, WHOIS-Port 0)..."
osascript -e 'tell application "Terminal"
    do script "cd \"'"$PWD"'\" && python3.11 chat_gui_client.py --handle Ilirjon --whoisport 0"
end tell'


