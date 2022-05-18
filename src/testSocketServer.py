import socket
import os
import cv2
import numpy as np
import base64
import websockets
from _thread import *

ServerSocket = socket.socket()
host = '192.168.68.125'
port = 8089
ThreadCount = 0
try:
    ServerSocket.bind((host, port))
except socket.error as e:
    print(str(e))

print('Waitiing for a Connection..')
ServerSocket.listen(5)

def get_frame(conn, last_packet):
    buffer_size = 10000
    data = last_packet
    while True:
        packet = conn.recv(buffer_size)
        #print(packet)
        print(packet.decode('ascii'))
        #print(base64.decodebytes(packet))
        quit()
        data += packet
        print(data)
        if packet[0] == 255 and packet[1] == 216 and packet[2] == 255 and data != b'':
            last_packet = packet
            break
    image_array = np.array(bytearray(data), dtype=np.uint8)
    frame = cv2.imdecode(image_array, -1)
    # todo some frames are bad. found here. fix?
    if isinstance(frame, type(None)):
        frame = get_frame(conn, last_packet)

    return frame, last_packet


def threaded_client(connection):
    last_packet = b''
    #connection.send(str.encode('Welcome to the Server'))
    while True:
        frame, last_packet = get_frame(connection, last_packet)
        cv2.imshow('frame', frame)
        cv2.waitKey(100)
        #reply = 'Server Says: Test'
        #connection.sendall(str.encode(reply))
    connection.close()


while True:
    Client, address = ServerSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(threaded_client, (Client,))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))
ServerSocket.close()
