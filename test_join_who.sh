#!/bin/bash
# test_join_who.sh

cd "$(dirname "$0")"
rm -f peer_info.json

echo "▶️ Starte Sara (GUI)..."
osascript -e 'tell application "Terminal"
    do script "cd \"'"$PWD"'\" && python3.11 chat_gui_client.py  --handle Sara --port 5100 5101 --whoisport 4000 --autoreply \"AFK\" --broadcast_ip 192.168.2.255"
end tell'

sleep 3

echo "▶️ Starte Ilirjon (CLI)..."
osascript -e 'tell application "Terminal"
    do script "cd \"'"$PWD"'\" && python3.11 cli.py  --handle Ilirjon --port 5200 5201 --whoisport 4000 --autoreply \"Testantwort\" --broadcast_ip 192.168.2.255"
end tell'

echo "📝 Jetzt manuell ausführen:"
echo "1. CLI: /nutzer"
echo "2. CLI: /msg Sara Hallo Sara!"
echo "3. GUI: Nachricht sichtbar?"
