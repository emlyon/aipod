# aipod

Auto-update and run:

```
crontab -e
@reboot sleep 10 && cd /home/pi/aipod && echo `{ git pull && echo '{"result":"up to date"}' > git_status.json ; } || echo '{"result":"could not update"}' > git_status.json` && python3 mp3player.py
```