#!/usr/bin/python3

import time
import pigpio


# Pin definitions - uses BCM numbering
COIL_1_PINS = (19, 16)  # These are for header marked 'Motor 3' on the board
COIL_2_PINS = (26, 20)

# Basic coil sequence configurations
MOTOR_01 = (0, 1)
MOTOR_10 = (1, 0)
MOTOR_00 = (0, 0)

# Stepper motor parameters
motor_sequence = [(MOTOR_10, MOTOR_10),
                  (MOTOR_01, MOTOR_10),
                  (MOTOR_01, MOTOR_01),
                  (MOTOR_10, MOTOR_01)]
motor_speed = 10.0  # in Hz
motor_mode = 'cw'  # alternative is 'ccw', which reverses the motor_sequence
steps_per_revolution = 20  # from datasheet, single step is 1.8 deg


def init(coil_1_pins, coil_2_pins):
    # Connect to the pigpio daemon to control GPIO pins as specified in the
    # pin definitions. These are used to drive a Darlington array, which in
    # turn energises the coils of the stepper motor.

    gpio = pigpio.pi()

    if not gpio.connected:
        raise RuntimeError('Error connecting to pigpiod.')
    else:
        gpio.set_mode(coil_1_pins[0], pigpio.OUTPUT)
        gpio.set_mode(coil_1_pins[1], pigpio.OUTPUT)
        gpio.set_mode(coil_2_pins[0], pigpio.OUTPUT)
        gpio.set_mode(coil_2_pins[1], pigpio.OUTPUT)
        print('GPIO pins successfully set as OUTPUT')

    return gpio


def cleanup(gpio, coil_1_pins, coil_2_pins):
    # Sets all GPIO pins to 0 and terminates the connection to pigpiod.

    set_rotor_position(gpio, coil_1_pins, MOTOR_00)
    set_rotor_position(gpio, coil_2_pins, MOTOR_00)
    gpio.stop()

    print('Cleanup successful')


def set_rotor_position(gpio, coil_pins, coil_state):
    # Sets the two GPIO pins that control each coil to their respective
    # states, i.e. HIGH or LOW, as specified in `coil_state`.

    gpio.write(coil_pins[0], coil_state[0])
    gpio.write(coil_pins[1], coil_state[1])


def move_one_step(gpio, coil_1_pins, coil_2_pins, motor_sequence,
                  motor_speed, mode='cw'):
    # Moves the rotor shaft one step, as specified by `motor_sequence`
    # `mode` is used to determine clockwise or counter-clockwise rotation.

    if mode == 'ccw':
        motor_sequence = motor_sequence[::-1]

    motor_sleep_time = 1.0 / motor_speed  # crude but does the job

    for step in motor_sequence:
        set_rotor_position(gpio, coil_1_pins, step[0])
        set_rotor_position(gpio, coil_2_pins, step[1])
        time.sleep(motor_sleep_time)
    print("Moved one step in {} direction".format(mode))


def move_one_revolution(gpio, coil_1_pins, coil_2_pins, motor_sequence,
                        motor_speed, steps_per_revolution, mode='cw'):
    for _ in range(steps_per_revolution):
        move_one_step(gpio, coil_1_pins, coil_2_pins, motor_sequence,
                      motor_speed, mode)


if __name__ == '__main__':
    gpio = init(COIL_1_PINS, COIL_2_PINS)
    while True:
        try:
            move_one_step(gpio, COIL_1_PINS, COIL_2_PINS,
                          motor_sequence, motor_speed,
                          motor_mode)
        except KeyboardInterrupt:
            print("Shutting down")
            cleanup(gpio, COIL_1_PINS, COIL_2_PINS)
            break
