import cv2
import socket
import pickle
import struct


cap = cv2.VideoCapture(0)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 8089))


try:
    while True:
        sock.setblocking(True)
        ret,frame=cap.read()
        # Serialize frame
        data = pickle.dumps(frame)

        # Send message length first
        message_size = struct.pack("L", len(data)) ### CHANGED

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