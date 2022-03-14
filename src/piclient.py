import cv2
import socket
import pickle
import struct
import os
import time
from dotenv import load_dotenv
from picamera.array import PiRGBArray
from picamera import PiCamera

load_dotenv()

H = 640
W = 480
camera = PiCamera()
camera.resolution = (H,W)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(H,W))
time.sleep(0.1)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((os.environ.get("HOST_ADDRESS"), int(os.environ.get("HOST_PORT"))))

try:
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        img = frame.array      
        sock.setblocking(True)       
        encoded, img = cv2.imencode('.jpg', img)
        data = pickle.dumps(img)
    
        # Send message length first
        message_size = struct.pack("L", len(data)) ### CHANGED        

        # Then data
        sock.sendall(message_size + data)
        
        #key = cv2.waitKey(1) & 0xFF
        rawCapture.truncate(0)
        
        sock.setblocking(False)
        try:
            response = sock.recv(4096)
            #print(response)
        except socket.error as e:
            pass

finally:
        print('closing socket')
        socket.close()