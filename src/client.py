import cv2
import socket
import pickle
import struct
import os
import platform
import time
import RPi.GPIO as GPIO
from time import sleep
from piservo import Servo
from dotenv import load_dotenv

load_dotenv()

x_pin = 19
y_pin = 18
laser = 12
center = 270/2
x = Servo(x_pin)
y = Servo(y_pin)
x.write(center)
y.write(center)
sleep(1)
GPIO.setmode(GPIO.BCM)
GPIO.setup(laser, GPIO.OUT)
GPIO.output(laser,GPIO.LOW)
x_angle = center
y_angle = center
adjustby = 1

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((os.environ.get("HOST_ADDRESS"), int(os.environ.get("HOST_PORT"))))

uname = platform.uname()

def send_capture(sock,img, x, y, adjustby):
    global x_angle
    global y_angle

    sock.setblocking(True)      
    encoded, img = cv2.imencode('.jpg', img)
    data = pickle.dumps(img)
    message_size = struct.pack("=L", len(data))    
    sock.sendall(message_size + data)    
    sock.setblocking(False)
    try:
        response = sock.recv(4096)
        response = pickle.loads(response)
        print(response[0])
        if response[1] == "UP":
                y_angle = y_angle + adjustby
                y.write(y_angle)
        if response[1] == "DOWN":
                y_angle = y_angle - adjustby
                y.write(y_angle)
        if response[0] == "LEFT":
                x_angle = x_angle + adjustby
                x.write(x_angle)
        if response[0] == "RIGHT":
                x_angle = x_angle - adjustby
                x.write(x_angle)

    except socket.error as e:
        pass

try:
    #PI CAMERA
    if uname.machine.startswith('arm'):
        from picamera.array import PiRGBArray
        from picamera import PiCamera
        H = 640
        W = 640
        camera = PiCamera()
        camera.resolution = (H,W)
        camera.framerate = 32
        rawCapture = PiRGBArray(camera, size=(H,W))
        time.sleep(0.1)        
        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            send_capture(sock,frame.array, x, y, adjustby)           
            rawCapture.truncate(0)            

    #NORMAL WEBCAM
    else:
        cap = cv2.VideoCapture(0)
        #cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        #cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        #cap.set(cv2.CAP_PROP_FPS, 60)        
        while True:
            ret,img=cap.read()
            send_capture(sock,img)            
finally:
        print('closing socket')
        socket.close()
