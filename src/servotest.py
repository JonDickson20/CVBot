import cv2
import RPi.GPIO as GPIO
from piservo import Servo
from time import sleep
from sshkeyboard import listen_keyboard

x_pin = 19
y_pin = 18

x = Servo(x_pin)
y = Servo(y_pin)

x.write(270/2)
y.write(270/2)
sleep(1)

GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)
GPIO.output(12,GPIO.LOW)
#while True:
#	GPIO.output(12,GPIO.LOW)
#	sleep(.1)
#	GPIO.output(12,GPIO.HIGH)
#	sleep(.1)
#quit()


adjustby = 10
x_angle = 270/2
y_angle = 270/2

def press(key):	
	global x
	global y
	global x_angle
	global y_angle
	global adjustby
	print(key)
	if key == "esc":
		GPIO.output(12,GPIO.LOW)
		GPIO.cleanup()
		quit()
	if key == "up":	
		y_angle = y_angle + adjustby
		y.write(y_angle)
	if key == "down":
		y_angle = y_angle - adjustby
		y.write(y_angle)
	if key == "right":
		x_angle = x_angle + adjustby
		x.write(x_angle)
	if key == "left":
		x_angle = x_angle - adjustby
		x.write(x_angle)

def release(key):
	print("released "+key)

listen_keyboard(on_press=press, on_release=release)
