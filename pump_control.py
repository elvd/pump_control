#!/usr/bin/python3

import curses
import pump


# Pin definitions - uses BCM numbering
COIL_1_PINS = (19, 16)  # These are for header marked 'Motor 3' on the board
COIL_2_PINS = (26, 20)

# Basic coil sequence configurations
MOTOR_01 = (0, 1)
MOTOR_10 = (1, 0)
MOTOR_00 = (0, 0)

# Stepper motor sequence, from data sheet
FULL_STEP_SEQUENCE = [(MOTOR_10, MOTOR_10),
                      (MOTOR_01, MOTOR_10),
                      (MOTOR_01, MOTOR_01),
                      (MOTOR_10, MOTOR_01)]
SPEED = 10.0  # in Hz
STEPS = 20  # from datasheet, single step is 1.8 deg

num_steps_cw = 0
num_steps_ccw = 0

if __name__ == '__main__':
    # Initialise motor control
    try:
        test_pump = pump.Pump(COIL_1_PINS, COIL_2_PINS, FULL_STEP_SEQUENCE,
                              SPEED, STEPS)
    except RuntimeError:
        print('pigpiod not initialised. Please run "sudo pigpiod &" first')
        exit()

    # Initialise curses
    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()
    screen.keypad(True)
    screen.scrollok(True)

    screen.addstr('Press UP for clockwise and DOWN for counter-clockwise\n')
    screen.addstr('Press "X" to exit\n')

    while True:
        input_key = screen.getch()

        if input_key == curses.KEY_UP:
            test_pump.move_one_revolution(mode='cw')
            num_steps_cw += 1
            screen.addstr('Moved 1 revolution clockwise\n')
            screen.refresh()
        elif input_key == curses.KEY_DOWN:
            test_pump.move_one_revolution(mode='ccw')
            num_steps_ccw += 1
            screen.addstr('Moved 1 revolution counter-clockwise\n')
            screen.refresh()
        elif input_key == ord('x'):
            break

    # Clean up curses and return screen to normal
    curses.nocbreak()
    screen.keypad(False)
    curses.echo()
    curses.endwin()

    # Clean up and release motor control
    test_pump.cleanup()

    print('Number of steps in CW: {}'.format(num_steps_cw))
    print('Number of steps in CCW: {}'.format(num_steps_ccw))
