import RPi.GPIO as GPIO
from time import sleep

x_pin = 14
y_pin = 21
GPIO.setmode(GPIO.BCM)
GPIO.setup(x_pin,GPIO.OUT)
GPIO.setup(y_pin,GPIO.OUT)
xp = GPIO.PWM(x_pin, 50)
yp = GPIO.PWM(y_pin, 50)
xp.start(0)
yp.start(0)

def setAngle(pin, angle):   
    duty = angle / 27 + 2
    #GPIO.output(pin,True)
    pin.ChangeDutyCycle(duty)
    sleep(1)
    #GPIO.output(pin,False)
    pin.ChangeDutyCycle(0)


setAngle(xp, 0)
setAngle(yp, 0)
setAngle(xp, 90)
setAngle(yp, 90)
setAngle(xp, 270/2)
setAngle(yp, 270/2)
setAngle(xp, 180)
setAngle(yp, 180)
setAngle(xp, 270)
setAngle(yp, 270)


xp.stop()
yp.stop()
GPIO.cleanup()
quit()