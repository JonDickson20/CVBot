import pickle
import socket
import struct
import cv2
import time
import datetime
import os
import numpy as np
from time import sleep
from dotenv import load_dotenv

load_dotenv()

start = time.time_ns()
frame_count = 0
total_frames = 0
fps = -1


INPUT_WIDTH = 640
INPUT_HEIGHT = 640
SCORE_THRESHOLD = 0.2
NMS_THRESHOLD = 0.05
CONFIDENCE_THRESHOLD = 0.05
AIM_DEADZONE_SIZE = 10
DISABLE_LASER_AFTER_FRAMES_MISSING = 10
X_OFFSET = -35 #USE TO GET LASER INTO CENTER OF GREEN CIRCLE
Y_OFFSET = 0 #USE TO GET LASER INTO CENTER OF GREEN CIRCLE
DEGREES_PER_PIXEL = 0
FOV = 62.2

#CREEP MODE
#AIM_MAX_DEGREES = 10
#DELAY_BETWEEN_COMMANDS = 1

#FAST MODE
AIM_MAX_DEGREES = 40 #this is most degrees aim will turn in 1 command
DELAY_BETWEEN_COMMANDS = 2000

colors = [(255, 255, 0), (0, 255, 0), (0, 255, 255), (255, 0, 0)]
connected = False
aim = ["STOP", "STOP", 0, 0, 0]
target_left_frame = 100 #target has been missing for this many frames
last_command = datetime.datetime.now() 

def build_model():
	net = cv2.dnn.readNet("../config_files/yolov5s.onnx")
	net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
	net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)
	return net

def load_classes():
	class_list = []
	with open("../config_files/classes.txt", "r") as f:
		class_list = [cname.strip() for cname in f.readlines()]
	print(class_list)
	return class_list

def detect(image, net):
	blob = cv2.dnn.blobFromImage(image, 1/255.0, (INPUT_WIDTH, INPUT_HEIGHT), swapRB=True, crop=False)
	net.setInput(blob)
	preds = net.forward()
	return preds

class_list = load_classes()

def wrap_detection(input_image, output_data):
	class_ids = []
	confidences = []
	boxes = []

	rows = output_data.shape[0]

	image_width, image_height, _ = input_image.shape

	x_factor = image_width / INPUT_WIDTH
	y_factor =  image_height / INPUT_HEIGHT

	for r in range(rows):
		row = output_data[r]
		confidence = row[4]
		if confidence >= 0.4:

			classes_scores = row[5:]
			_, _, _, max_indx = cv2.minMaxLoc(classes_scores)
			class_id = max_indx[1]
			if (classes_scores[class_id] > .25):

				confidences.append(confidence)

				class_ids.append(class_id)

				x, y, w, h = row[0].item(), row[1].item(), row[2].item(), row[3].item()
				left = int((x - 0.5 * w) * x_factor)
				top = int((y - 0.5 * h) * y_factor)
				width = int(w * x_factor)
				height = int(h * y_factor)
				box = np.array([left, top, width, height])
				boxes.append(box)
	confidences = np.array(confidences)          
	
	indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.25, 0.45)

	result_class_ids = []
	result_confidences = []
	result_boxes = []
	
	for i in indexes:
		i=i[0]
		
		result_confidences.append(confidences[i])
		result_class_ids.append(class_ids[i])
		result_boxes.append(boxes[i])

	return result_class_ids, result_confidences, result_boxes

def format_yolov5(frame):
	row, col, _ = frame.shape
	_max = max(col, row)
	result = np.zeros((_max, _max, 3), np.uint8)
	result[0:row, 0:col] = frame
	return result



net = build_model()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
print('Socket created')
s.bind((os.environ.get("HOST_ADDRESS"), int(os.environ.get("HOST_PORT"))))
print('Socket bind complete')
s.listen(10)
print('Socket now listening')

while True:
	target_in_frame = 0
	while not connected:  
		# attempt to reconnect, otherwise sleep for 2 seconds  
		try:
			print('waiting for connection')
			conn, addr = s.accept()
			print(addr)
			data = b'' ### CHANGED
			payload_size = struct.calcsize("=L") ### CHANGED  
			connected = True  
			print('client connected')
		except socket.error:  
			sleep( 2 )  
	try:
		frame_count += 1
		total_frames += 1
		i = 0 #DONT
		# Retrieve message size
		while len(data) < payload_size:
			i = i + 1 #JUDGE
			if i > 500: 
				connected = False
				break #ME
			data += conn.recv(4096)
		if i > 500:
			continue

		packed_msg_size = data[:payload_size]
		data = data[payload_size:]
		msg_size = struct.unpack("=L", packed_msg_size)[0] ### CHANGED
		# Retrieve all data based on message size
		
		while len(data) < msg_size:
			data += conn.recv(4096)

		frame_data = data[:msg_size]
		data = data[msg_size:]
		
		# Extract frame
		frame = pickle.loads(frame_data)
		frame = cv2.imdecode(frame, 1)
		#print(frame)
		# Display


		#FPS
		if frame_count >= 30:
			end = time.time_ns()
			fps = 1000000000 * frame_count / (end - start)
			frame_count = 0
			start = time.time_ns()

		if fps > 0:
			fps_label = "FPS: %.2f" % fps
			cv2.putText(frame, fps_label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

		inputImage = format_yolov5(frame)
		outs = detect(inputImage, net)

		class_ids, confidences, boxes = wrap_detection(inputImage, outs[0])

		frame_count += 1
		total_frames += 1
		
		for (classid, confidence, box) in zip(class_ids, confidences, boxes):
			color = colors[int(classid) % len(colors)]
			cv2.rectangle(frame, box, color, 2)
			cv2.rectangle(frame, (box[0], box[1] - 20), (box[0] + box[2], box[1]), color, -1)
			cv2.putText(frame, class_list[classid], (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 0))
			
			if class_list[classid]=='person' or class_list[classid] =='dog':
				target_left_frame = 0
				target_in_frame = 1
				frame_height = frame.shape[0] + Y_OFFSET
				frame_width = frame.shape[1] + X_OFFSET
				target_center = [int(box[0]+box[2]/2),int(box[1]+box[3]/2)]
				
				aim_x_degrees = abs(target_center[0] - frame_width/2)/(frame_width)*AIM_MAX_DEGREES
				if target_center[0] < frame_width/2 - AIM_DEADZONE_SIZE:
					aim_x = "LEFT"
				elif target_center[0] > frame_width/2 + AIM_DEADZONE_SIZE:
					aim_x = "RIGHT"
				else:
					aim_x = "STOP"
				
				aim_y_degrees = abs(target_center[1] - frame_height/2)/(frame_height)*AIM_MAX_DEGREES
				if target_center[1] < frame_height/2 - AIM_DEADZONE_SIZE:
					aim_y = "UP"
				elif target_center[1] > frame_height/2 + AIM_DEADZONE_SIZE:
					aim_y = "DOWN"
				else:
					aim_y = "STOP"
				
				cv2.circle(frame,target_center,3,(0,0,255),2) #center of target
				cv2.circle(frame,(int(frame_width/2), int(frame_height/2)),3,(0,255,0),2) #center of frame
				cv2.rectangle(frame, (target_center[0]-AIM_DEADZONE_SIZE, target_center[1]-AIM_DEADZONE_SIZE), (target_center[0]+AIM_DEADZONE_SIZE, target_center[1]+AIM_DEADZONE_SIZE), (255,0,0), 2)

				x_percent = aim_x_degrees/(AIM_MAX_DEGREES/2)
				y_percent = aim_y_degrees/(AIM_MAX_DEGREES/2)
				larger = max(x_percent,y_percent)
				print(larger)

				time_diff = datetime.datetime.now() - last_command
				if int(time_diff.total_seconds() * 1000) > DELAY_BETWEEN_COMMANDS*larger:			
					if aim_x != "STOP" or aim_y != "STOP" or aim[2] == 0:	
						aim = [aim_x, aim_y, 1, aim_x_degrees, aim_y_degrees]
						response = pickle.dumps(aim)
						conn.sendall(response)
						last_command = datetime.datetime.now()
						
				continue #this handles multiple targets by just dealing with the first one

				
		#no target, turn off laser
		if target_in_frame == 0:
			target_left_frame = target_left_frame + 1
			if target_left_frame > DISABLE_LASER_AFTER_FRAMES_MISSING and aim[2] == 1:
				aim[2] = 0
				aim[0] = 'STOP'
				aim[1] = 'STOP'
				aim[3] = 0
				aim[4] = 0
				conn.sendall(pickle.dumps(aim))
		

		cv2.imshow('frame', frame)
		cv2.waitKey(1)
	except Exception as e:
		connected = False
		print(e)
