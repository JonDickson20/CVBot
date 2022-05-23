#!/usr/bin/env python
import asyncio
import websockets
import cv2
import numpy as np
import time
import datetime
import json
from simple_pid import PID

x_pid = PID(1, 0.1, 0.05, setpoint=0)
y_pid = PID(1, 0.1, 0.05, setpoint=0)

#FPS Stuff
start = time.time_ns()
frame_count = 0
total_frames = 0
fps = -1
clients = []

#YOLO Stuff
INPUT_WIDTH = 640
INPUT_HEIGHT = 640
SCORE_THRESHOLD = 0.2
NMS_THRESHOLD = 0.05
CONFIDENCE_THRESHOLD = 0.05
AIM_DEADZONE_SIZE = 20
DISABLE_LASER_AFTER_FRAMES_MISSING = 10
X_OFFSET = 25 #USE TO GET LASER INTO CENTER OF GREEN CIRCLE
Y_OFFSET = -75 #USE TO GET LASER INTO CENTER OF GREEN CIRCLE
X_OFFSET = 0 #USE TO GET LASER INTO CENTER OF GREEN CIRCLE
Y_OFFSET = 0 #USE TO GET LASER INTO CENTER OF GREEN CIRCLE
DEGREES_PER_PIXEL = 0
FOV = 62.2
#CREEP MODE
#AIM_MAX_DEGREES = 10
#DELAY_BETWEEN_COMMANDS = 1
#FAST MODE
AIM_MAX_DEGREES = 15 #this is most degrees aim will turn in 1 command
DELAY_BETWEEN_COMMANDS = 100
colors = [(255, 255, 0), (0, 255, 0), (0, 255, 255), (255, 0, 0)]
aim = dict()

target_left_frame = 100 #target has been missing for this many frames
last_command_time = datetime.datetime.now()


x_angle = 90
y_angle = 90
aim['laser'] = 0
aim['aim_x_degrees'] = x_angle
aim['aim_y_degrees'] = y_angle
command = json.dumps(aim)

last_command_sent = command

show_video = True


def build_model():
    net = cv2.dnn.readNet("../config_files/yolov5s.onnx")
    #net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    #net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)
    return net


net = build_model()


def load_classes():
    class_list = []
    with open("../config_files/classes.txt", "r") as f:
        class_list = [cname.strip() for cname in f.readlines()]
    print(class_list)
    return class_list


class_list = load_classes()


def detect(image, net):
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (INPUT_WIDTH, INPUT_HEIGHT), swapRB=True, crop=False)
    net.setInput(blob)
    preds = net.forward()
    return preds


def wrap_detection(input_image, output_data):
    class_ids = []
    confidences = []
    boxes = []

    rows = output_data.shape[0]

    image_width, image_height, _ = input_image.shape

    x_factor = image_width / INPUT_WIDTH
    y_factor = image_height / INPUT_HEIGHT

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
        #i = i[0]

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


def show_fps(frame):
    global frame_count, total_frames, fps, start
    frame_count += 1
    total_frames += 1
    if frame_count >= 30:
        end = time.time_ns()
        fps = 1000000000 * frame_count / (end - start)
        frame_count = 0
        start = time.time_ns()

    if fps > 0:
        fps_label = "FPS: %.2f" % fps
        cv2.putText(frame, fps_label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return frame


def format_yolov5(frame):
    row, col, _ = frame.shape
    _max = max(col, row)
    result = np.zeros((_max, _max, 3), np.uint8)
    result[0:row, 0:col] = frame
    return result


def aim_at_objects(frame):
    global target_left_frame, aim, last_command_time, class_list, command, x_angle, y_angle

    input_image = format_yolov5(frame)
    outs = detect(input_image, net)
    class_ids, confidences, boxes = wrap_detection(input_image, outs[0])
    target_in_frame = 0

    for (class_id, confidence, box) in zip(class_ids, confidences, boxes):
        color = colors[int(class_id) % len(colors)]
        cv2.rectangle(frame, box, color, 2)
        cv2.rectangle(frame, (box[0], box[1] - 20), (box[0] + box[2], box[1]), color, -1)
        cv2.putText(frame, class_list[class_id], (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 0))

        if class_list[class_id] == 'person' or class_list[class_id] == 'dog':
            target_left_frame = 0
            target_in_frame = 1
            frame_height = frame.shape[0] + Y_OFFSET
            frame_width = frame.shape[1] + X_OFFSET
            target_center = [int(box[0] + box[2] / 2), int(box[1] + box[3] / 2)]

            aim_x_degrees = abs(target_center[0] - frame_width / 2) / (frame_width) * AIM_MAX_DEGREES
            if target_center[0] < frame_width / 2 - AIM_DEADZONE_SIZE:
                aim_x = "LEFT"
            elif target_center[0] > frame_width / 2 + AIM_DEADZONE_SIZE:
                aim_x = "RIGHT"
            else:
                aim_x = "STOP"

            aim_y_degrees = abs(target_center[1] - frame_height / 2) / (frame_height) * AIM_MAX_DEGREES
            if target_center[1] < frame_height / 2 - AIM_DEADZONE_SIZE:
                aim_y = "UP"
            elif target_center[1] > frame_height / 2 + AIM_DEADZONE_SIZE:
                aim_y = "DOWN"
            else:
                aim_y = "STOP"

            cv2.circle(frame, target_center, 3, (0, 0, 255), 2)  # center of target
            cv2.circle(frame, (int(frame_width / 2), int(frame_height / 2)), 3, (0, 255, 0),
                       2)  # center of frame
            cv2.rectangle(frame, (target_center[0] - AIM_DEADZONE_SIZE, target_center[1] - AIM_DEADZONE_SIZE),
                          (target_center[0] + AIM_DEADZONE_SIZE, target_center[1] + AIM_DEADZONE_SIZE),
                          (255, 0, 0), 2)

            x_percent = aim_x_degrees / (AIM_MAX_DEGREES / 2)
            y_percent = aim_y_degrees / (AIM_MAX_DEGREES / 2)
            larger = max(x_percent, y_percent)
            # print(larger)

            time_diff = datetime.datetime.now() - last_command_time
            if int(time_diff.total_seconds() * 1000) > DELAY_BETWEEN_COMMANDS:
                if aim_x != "STOP" or aim_y != "STOP" or aim['laser'] == 0:
                    aim['laser'] = 1
                    if aim_x == "RIGHT":
                        aim_x_degrees = -aim_x_degrees
                    if aim_y == "DOWN":
                        aim_y_degrees = -aim_y_degrees
                    x_control = -x_pid(aim_x_degrees)
                    y_control = -y_pid(aim_y_degrees)
                    x_angle = max(min(x_angle + x_control, 180), 0)
                    y_angle = max(min(y_angle + y_control, 180), 0)
                    aim['aim_x_degrees'] = x_angle
                    aim['aim_y_degrees'] = y_angle
                    # SEND COMMAND HERE
                    command = json.dumps(aim)
                    #print(command)
                    last_command_time = datetime.datetime.now()

            continue  # this handles multiple targets by just dealing with the first one

    # no target, turn off laser
    if target_in_frame == 0:
        target_left_frame = target_left_frame + 1
        if target_left_frame > DISABLE_LASER_AFTER_FRAMES_MISSING and aim['laser'] == 1:
            aim['laser'] = 0
            aim['aim_x_degrees'] = x_angle
            aim['aim_y_degrees'] = y_angle
            # SEND COMMAND HERE
            command = json.dumps(aim)
            #print(command)

    return frame, command


async def handler(websocket):
    clients.append(websocket)
    print(clients)
    async for message in websocket:
        # print(message)
        image_array = np.array(bytearray(message), dtype=np.uint8)
        frame = cv2.imdecode(image_array, -1)
        frame = show_fps(frame)
        # detect objects and aim
        frame, command = aim_at_objects(frame)
        if show_video:
            cv2.imshow('frame', frame)
            cv2.waitKey(1)
        for client in clients:
            if client != websocket:
                # this message will send to all but the original sender
                await client.send(message)
            else:
                # this message will send back to only the original sender
                print(command)

                await websocket.send(command)


async def main():
    async with websockets.serve(handler, "192.168.68.125", 8089):
        await asyncio.Future()  # run forever

asyncio.run(main())
