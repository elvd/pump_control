#!/usr/bin/python
# Import required libraries
import sys, time, threading
import RPi.GPIO as GPIO
 
# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)
 
# Define GPIO signals to use

StepPins = [[17,18,27,22],
            [4,25,24,23],
            [13,12,6,5],
            [20,26,16,19]]
 
# Set all pins as output
for pin in StepPins:
  print "Setup pins"
  GPIO.setup(pin,GPIO.OUT)
  GPIO.output(pin, False)
 
# Define advanced sequence
# as shown in manufacturers datasheet
Seq = [[1,0,0,1],
       [1,0,0,0],
       [1,1,0,0],
       [0,1,0,0],
       [0,1,1,0],
       [0,0,1,0],
       [0,0,1,1],
       [0,0,0,1]]
        
StepCount = len(Seq)
StepDir = 1 # Set to 1 or 2 for clockwise
            # Set to -1 or -2 for anti-clockwise
 
# Initialise variables
StepCounter = 0
WaitTime = 0.001

#======================================================================
# Reading single character by forcing stdin to raw mode
import sys
import tty
import termios

def readchar():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    if ch == '0x03':
        raise KeyboardInterrupt
    return ch

def readkey(getchar_fn=None):
    getchar = getchar_fn or readchar
    c1 = getchar()
    if ord(c1) != 0x1b:
        return c1
    c2 = getchar()
    if ord(c2) != 0x5b:
        return c1
    c3 = getchar()
    return chr(0x10 + ord(c3) - 65)  # 16=Up, 17=Down, 18=Right, 19=Left arrows

# End of single character reading
#======================================================================
# Create  main loop which runs in separate thread
def step():
  global stepMotor, running, StepCounter
  while running:
    if (stepMotor >= 0):
      for pin in range(0,4):
        xpin=StepPins[stepMotor][pin]# Get GPIO
        if Seq[StepCounter][pin]!=0:
          GPIO.output(xpin, True)
        else:
          GPIO.output(xpin, False)
   
    StepCounter += StepDir
    if (StepCounter>=StepCount):
      StepCounter = 0
    if (StepCounter<0):
      StepCounter = StepCount+StepDir
    time.sleep(WaitTime)

# Startup the stepping thread
threadC = threading.Thread(target = step)
stepMotor = -1
running = True
threadC.start()

try:
  while True:
    keyp = readkey()
    if keyp == '1':
      stepMotor = 0
      print 'Motor 1'
    elif keyp == '2':
      stepMotor = 1
      print 'Motor 2'
    elif keyp == '3':
      stepMotor = 2
      print 'Motor 3'
    elif keyp == '4':
      stepMotor = 3
      print 'Motor 4'
    elif ord(keyp) == 3:
      break
    else:
      stepMotor = -1
      print 'Stop'

except KeyboardInterrupt:
    print

finally:
  running = False
  time.sleep(1)
  GPIO.cleanup()
    
# Start main loop which runs in separate thread
def step():
  global stepMotor, running
  while running:
    if (stepMotor >= 0):
      for pin in range(0,4):
        xpin=StepPins[stepMotor][pin]# Get GPIO
        if Seq[StepCounter][pin]!=0:
          GPIO.output(xpin, True)
        else:
          GPIO.output(xpin, False)
   
    StepCounter += StepDir
    if (StepCounter>=StepCount):
      StepCounter = 0
    if (StepCounter<0):
      StepCounter = StepCount+StepDir
    time.sleep(WaitTime)
