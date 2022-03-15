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
#NORMAL WEBCAM
else:
    cap = cv2.VideoCapture(0)
    #cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    #cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    #cap.set(cv2.CAP_PROP_FPS, 60)

try:
    while True:
        sock.setblocking(True)
        ret,img=cap.read()
        encoded, img = cv2.imencode('.jpg',img)
        data = pickle.dumps(img)
        message_size = struct.pack("=L", len(data)) ### CHANGED
        sock.sendall(message_size + data)
        sock.setblocking(False)
        try:
            response = sock.recv(4096)
            response = pickle.loads(response)
            print(response)
        except socket.error as e:
            pass
finally:
        print('closing socket')
        socket.close()
