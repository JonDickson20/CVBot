# CVBot
 A Computer Vision Bot


To autorun. Edit to point to server.py:
crontab -e
@reboot sleep 20 && /usr/bin/python3 /home/pi/Desktop/OpenCV/bot/server.py > /tmp/boterror


On pi:
sudo apt-get install libatlas-base-dev;
pip install -U numpy
