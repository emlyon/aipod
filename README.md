# aipod

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
@reboot sleep 10 && cd /home/pi/aipod && echo `{ git pull && echo '{"result":"up to date"}' > git_status.json ; } || echo '{"result":"could not update"}' > git_status.json` && python3 aipod.py
```