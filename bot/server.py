#!/usr/bin/env python3

import asyncio
import websockets
import RPi.GPIO as GPIO
import sys
import socket
import json
from piservo import Servo
from time import sleep

#host on current LAN address
#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#s.connect(("8.8.8.8", 80))
#local_address = s.getsockname()[0]
HOST = '192.168.68.193'
PORT = 8000
#PORT = int(sys.argv[1])

GPIO.setmode(GPIO.BCM)  
GPIO.setwarnings(False)

riser_1 = 3
riser_2 = 4
riser_enable = 2

GPIO.setmode(GPIO.BCM)  
GPIO.setwarnings(False)

R_FPWM = 13;
R_BPWM = 6;
R_F_EN = 26; 
R_B_EN = 19; 
L_FPWM = 21;
L_BPWM = 20;
L_F_EN = 12;
L_B_EN = 16;

Riser_Up_PWM = 3;
Riser_Down_PWM = 2;
Riser_Up_EN = 4;
Riser_Down_EN = 17;

GPIO.setup(L_FPWM, GPIO.OUT)
GPIO.setup(L_BPWM, GPIO.OUT)
GPIO.setup(L_F_EN, GPIO.OUT)
GPIO.setup(L_B_EN, GPIO.OUT)
GPIO.setup(R_FPWM, GPIO.OUT)
GPIO.setup(R_BPWM, GPIO.OUT)
GPIO.setup(R_F_EN, GPIO.OUT)
GPIO.setup(R_B_EN, GPIO.OUT)

GPIO.setup(Riser_Up_PWM, GPIO.OUT)
GPIO.setup(Riser_Down_PWM, GPIO.OUT)
GPIO.setup(Riser_Up_EN, GPIO.OUT)
GPIO.setup(Riser_Down_EN, GPIO.OUT)

# Enable "Left" and "Right" movement on the HBRidge
GPIO.output(L_F_EN, True)
GPIO.output(L_B_EN, True)
GPIO.output(R_F_EN, True)
GPIO.output(R_B_EN, True)
GPIO.output(Riser_Up_EN, True)
GPIO.output(Riser_Down_EN, True)

lfpwm= GPIO.PWM(L_FPWM, 5000)
lbpwm= GPIO.PWM(L_BPWM, 5000)
rfpwm= GPIO.PWM(R_FPWM, 5000)
rbpwm= GPIO.PWM(R_BPWM, 5000)
riserupwm= GPIO.PWM(Riser_Up_PWM, 1000)
riserdpwm= GPIO.PWM(Riser_Down_PWM, 1000)

rfpwm.start(0)
rbpwm.start(0)
lfpwm.start(0)
lbpwm.start(0)
riserupwm.start(0)
riserdpwm.start(0)

grabber = Servo(18)
grabber_open_degrees = 180;
grabber_closed_degrees = 110;



async def serve(websocket, path):

    while True:
        try:   
            data = await websocket.recv()
            #print(f"< {data}")
            command = json.loads(data)
            print(command)
            
            if(command['left'] is None or command['left'] == 0):
                command['left'] = 0
                lfpwm.stop()
                lbpwm.stop()            
            if(command['right'] is None or command['right'] == 0):
                command['right'] = 0
                rfpwm.stop()
                rbpwm.stop()
                
            if(command['riser'] is None or command['riser'] == 0):
                command['riser'] = 0
                riserupwm.stop()
                riserdpwm.stop()
                
            if(command['left'] > 0):
                lbpwm.stop()
                sleep(0.01)
                lfpwm.start(abs(command['left']))
            if(command['left'] < 0):
                lfpwm.stop()
                sleep(0.01)
                lbpwm.start(abs(command['left']))
                
            if(command['right'] > 0):
                rbpwm.stop()
                rfpwm.start(abs(command['right']))
            if(command['right'] < 0):
                rfpwm.stop()
                rbpwm.start(abs(command['right']))
                
            if(command['riser'] > 0):
                riserupwm.stop()
                riserupwm.start(abs(command['riser']))
            if(command['riser'] < 0):
                riserdpwm.stop()
                riserdpwm.start(abs(command['riser']))                        
        
            if(command['grabber'] is None or command['grabber'] == 0):
                grabber_position = grabber_open_degrees
                grabber.write(grabber_position)
            if(command['grabber'] != 0):
                grabber_position = grabber_open_degrees - ((grabber_open_degrees - grabber_closed_degrees)*(command['grabber']/100))
                grabber.write(grabber_position)
        except Exception as e:
            print(str(e))
            with open("/home/pi/Desktop/bot/log.txt", "a") as log:
                log.write(str(e)+"\n")
            lfpwm.stop()
            lbpwm.stop()            
            rfpwm.stop()
            rbpwm.stop()
            riserupwm.stop()
            riserdpwm.stop()
            grabber_position = grabber_open_degrees
            grabber.write(grabber_position)
            break
try:    
    start_server = websockets.serve(serve, HOST, PORT)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
except Exception as e:
    with open("/home/pi/Desktop/bot/log.txt", "a") as log:
        log.write(str(e)+"\n")        
    lfpwm.stop()
    lbpwm.stop()            
    rfpwm.stop()
    rbpwm.stop()
    riserupwm.stop()
    riserdpwm.stop()
    grabber_position = grabber_open_degrees
    grabber.write(grabber_position)    
