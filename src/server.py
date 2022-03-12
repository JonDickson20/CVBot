import pickle
import socket
import struct
import cv2
import time
import os
from dotenv import load_dotenv

load_dotenv()

start = time.time_ns()
frame_count = 0
total_frames = 0
fps = -1

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created')
s.bind((os.environ.get("HOST_ADDRESS"), os.environ.get("HOST_PORT")))
print('Socket bind complete')
s.listen(10)
print('Socket now listening')

conn, addr = s.accept()

data = b'' ### CHANGED
payload_size = struct.calcsize("L") ### CHANGED

while True:
    frame_count += 1
    total_frames += 1
    # Retrieve message size
    while len(data) < payload_size:
        data += conn.recv(4096)

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0] ### CHANGED

    # Retrieve all data based on message size
    while len(data) < msg_size:
        data += conn.recv(4096)


    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Extract frame
    frame = pickle.loads(frame_data)

    # Display

    response = "response"
    conn.sendall(response.encode())

    #FPS
    if frame_count >= 30:
        end = time.time_ns()
        fps = 1000000000 * frame_count / (end - start)
        frame_count = 0
        start = time.time_ns()

    if fps > 0:
        fps_label = "FPS: %.2f" % fps
        cv2.putText(frame, fps_label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)


    cv2.imshow('frame', frame)
    cv2.waitKey(1)