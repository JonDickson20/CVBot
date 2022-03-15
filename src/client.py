import cv2
import socket
import pickle
import struct
import os
import platform
import time
from dotenv import load_dotenv

load_dotenv()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((os.environ.get("HOST_ADDRESS"), int(os.environ.get("HOST_PORT"))))

uname = platform.uname()

def send_capture(sock,img):
    sock.setblocking(True)      
    encoded, img = cv2.imencode('.jpg', img)
    data = pickle.dumps(img)
    message_size = struct.pack("L", len(data))    
    sock.sendall(message_size + data)    
    sock.setblocking(False)
    try:
        response = sock.recv(4096)
        print(response)
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
            send_capture(sock,frame.array)           
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
