# aipod

Auto-update and run:
```
cd /home/pi/aipod && echo `{ git pull && echo "up to date" > git_status.txt ; } || echo "could not update" > git_status.txt` && python3 mp3player.py
```