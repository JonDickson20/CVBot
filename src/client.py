import cv2
import socket
import pickle
import struct
import os
from dotenv import load_dotenv

load_dotenv()

cap = cv2.VideoCapture(0)
#cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
#cap.set(cv2.CAP_PROP_FPS, 60)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((os.environ.get("HOST_ADDRESS"), int(os.environ.get("HOST_PORT"))))


try:
    while True:
        sock.setblocking(True)
        ret,frame=cap.read()
        #print(frame)
        # Serialize frame
        encoded, frame = cv2.imencode('.jpg',frame)
        data = pickle.dumps(frame)

        # Send message length first
        message_size = struct.pack("=L", len(data)) ### CHANGED

        # Then data
        sock.sendall(message_size + data)
        sock.setblocking(False)
        try:
            response = sock.recv(4096)
            print(response)
        except socket.error as e:
            pass

finally:
        print('closing socket')
        socket.close()
