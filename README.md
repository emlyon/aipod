# aipod

## Wiring
![](aipod.svg)
Display is a 16x2 chars LCD connected as follow:
- RS is connected to GPIO16
- EN is connected to GPIO12
- D4 is connected to GPIO25
- D5 is connected to GPIO24
- D6 is connected to GPIO23
- D7 is connected to GPIO18

Buttons are connected to GPIO4, configured as input pullup.


## Install & run

**Clone repo**
```bash
cd /home/pi
git clone https://github.com/emlyon/aipod
```

**Install Dependencies**
```bash
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install python3-pip
sudo pip3 install pygame adafruit-blinka adafruit-circuitpython-charlcd
```
From [Update Your Pi to the Latest Raspbian](https://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi?view=all#update-your-pi-to-the-latest-raspbian-3-1)

**Run**
```bash
cd /home/pi/aipod
python3 aipod.py
```
___

## Auto-update and run on boot

**Configure WIFI**
```bash
sudo raspi-config

# Set Wifi settings:
-> 2. Network Options
-> N2 Wi-fi
SSID: makerslab
passphrase: makerslab
```

**Run task on boot**
```bash
crontab -e

# and add:
@reboot sleep 10 && cd /home/pi/aipod && echo `{ git pull && echo '{"result":"up to date"}' > /home/pi/git_status.json ; } || echo '{"result":"could not update"}' > /home/pi/git_status.json` && python3 aipod.py
```

## Resources
- [Adafruit-Blinka](https://pypi.org/project/Adafruit-Blinka/)
- [Adafruit CIRCUITPYTHON_CHARLCD Library](https://circuitpython.readthedocs.io/projects/charlcd/en/latest/)
- [pygame.mixer.music](https://www.pygame.org/docs/ref/music.html)
- [Drive a 16x2 LCD with the Raspberry Pi Output Character](https://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi?view=all)
