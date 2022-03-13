import cv2
import socket
import pickle
import struct
import os
import time
from dotenv import load_dotenv

#only for Pi
from picamera.array import PiRGBArray
from picamera import PiCamera
camera = PiCamera()
camera.resolution = (640,640)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640,640))
time.sleep(0.1)

load_dotenv()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
cap.set(cv2.CAP_PROP_FPS, 60)

print(os.environ.get("HOST_PORT"))

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((os.environ.get("HOST_ADDRESS"), int(os.environ.get("HOST_PORT"))))


try:
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        img = frame.array      
        sock.setblocking(True)
        #ret,frame=cap.read()
        # Serialize frame
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
            print(response)
        except socket.error as e:
            pass

finally:
        print('closing socket')
        socket.close()