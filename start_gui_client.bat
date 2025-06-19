@echo off
setlocal EnableDelayedExpansion

REM 🧹 Lokale Peer-Datei löschen
if exist peer_info.json del peer_info.json

REM 👤 Eingaben abfragen
set /p HANDLE=Dein Benutzername (z. B. Sara): 
set /p UDPPORT=UDP-Port (z. B. 5100): 
set /p UDPPORT2=Zusätzlicher Port (z. B. 5101): 
set /p WHOISPORT=WHOIS-Port (z. B. 4000): 
set /p AUTOREPLY=Autoreply-Text: 

REM 🚀 Starte Chat-GUI in neuem Fenster
start cmd /k python chat_gui_client.py --handle %HANDLE% --port %UDPPORT% %UDPPORT2% --whoisport %WHOISPORT% --autoreply "%AUTOREPLY%"
