#!/usr/bin/python3

import time
import smbus
import pigpio


# Picon Zero (PZ) definitions
PZ_ADDR = 0x22  # I2C address
PZ_I2C_RETRIES = 10   # Maximum number of retries for I2C calls
PZ_RESET = 20  # Reset the board
PZ_MOTOR_A = 1  # H-bridge motor A
PZ_MOTOR_B = 0  # H-bridge motor B
PZ_MOTOR_10 = 127
PZ_MOTOR_01 = -127
PZ_MOTOR_00 = 0

# Picon Zero (PZ) variables
pz_motor_sequence = [(PZ_MOTOR_10, PZ_MOTOR_10),
                     (PZ_MOTOR_01, PZ_MOTOR_10),
                     (PZ_MOTOR_01, PZ_MOTOR_01),
                     (PZ_MOTOR_10, PZ_MOTOR_01)]
pz_motor_speed = 25.0  # in Hz
pz_motor_mode = 'cw'

# Pistep2Q (PQ) definitions
PQ_COIL_1_PINS = (19, 16)  # These are for header marked 'Motor 3' on the board
PQ_COIL_2_PINS = (26, 20)  # Pigpio uses BCM numbering of pins
PQ_MOTOR_01 = (0, 1)
PQ_MOTOR_10 = (1, 0)
PQ_MOTOR_00 = (0, 0)

# Pistep2Q (PQ) variables
pq_motor_sequence = [(PQ_MOTOR_10, PQ_MOTOR_10),
                     (PQ_MOTOR_01, PQ_MOTOR_10),
                     (PQ_MOTOR_01, PQ_MOTOR_01),
                     (PQ_MOTOR_10, PQ_MOTOR_01)]
pq_motor_speed = 10.0  # in Hz
pq_motor_mode = 'cw'

# Global flag for board selection in demo mode
BOARD = 'PQ'  # Alternative option is 'PZ'


def pq_init(coil_1_pins, coil_2_pins):
    # Connect to the pigpio daemon to control GPIO pins as specified in the
    # PQ definitions. These are used to drive a Darlington array, which in
    # turn energises the coils of the stepper motor

    pq_gpio = pigpio.pi()

    if not pq_gpio.connected:
        print('Error initialising GPIO access, program terminating')
        exit()
    else:
        pq_gpio.set_mode(coil_1_pins[0], pigpio.OUTPUT)
        pq_gpio.set_mode(coil_1_pins[1], pigpio.OUTPUT)
        pq_gpio.set_mode(coil_2_pins[0], pigpio.OUTPUT)
        pq_gpio.set_mode(coil_2_pins[1], pigpio.OUTPUT)
        print('GPIO pins successfully set as OUTPUT')

    return pq_gpio


def pq_cleanup(gpio_conn, coil_1_pins, coil_2_pins):
    # Sets all GPIO pins to 0 and terminates the connection to pigpiod

    pq_set_rotor_position(gpio_conn, coil_1_pins, PQ_MOTOR_00)
    pq_set_rotor_position(gpio_conn, coil_2_pins, PQ_MOTOR_00)
    gpio_conn.stop()

    print('Cleanup successful')


def pq_set_rotor_position(gpio_conn, coil_pins, coil_state):
    # Sets the two GPIO pins that control each coil to their respective
    # states, i.e. HIGH or LOW, as specified in the coil_state variable.

    gpio_conn.write(coil_pins[0], coil_state[0])
    gpio_conn.write(coil_pins[1], coil_state[1])


def pq_move_one_step(gpio_conn, coil_1_pins, coil_2_pins, motor_sequence,
                     motor_speed, mode='cw'):
    # Equivalent to pz_move_one_step, however uses GPIO pins rather than
    # I2C control

    if mode == 'ccw':
        motor_sequence = motor_sequence[::-1]

    motor_sleep_time = 1.0 / motor_speed

    for step in motor_sequence:
        pq_set_rotor_position(gpio_conn, coil_1_pins, step[0])
        pq_set_rotor_position(gpio_conn, coil_2_pins, step[1])
        time.sleep(motor_sleep_time)
    print("Moved one step in {} direction".format(mode))


def pz_init():
    # Establish connection to Picon Zero and reset the board
    # For revision 1 Raspberry Pi, change to bus = smbus.SMBus(0)
    # DO NOT USE I2C 0 on Raspberry Pi 3 or Raspberry Pi 0

    i2c_bus = smbus.SMBus(1)

    for attempt in range(PZ_I2C_RETRIES):
        try:
            i2c_bus.write_byte_data(PZ_ADDR, PZ_RESET, 0)
            print("Picon Zero initialised successfully")
            break
        except:
            print("Error initialising Picon Zero, retrying")
    else:
        print("Picon Zero not initialised, program terminating")
        exit()

    time.sleep(0.01)  # 10 ms delay to allow time to complete

    return i2c_bus


def pz_cleanup(i2c_bus):
    # Cleanup the Board (same as init)

    for attempt in range(PZ_I2C_RETRIES):
        try:
            i2c_bus.write_byte_data(PZ_ADDR, PZ_RESET, 0)
            print("Picon Zero reset successfully")
            break
        except:
            print("Error resetting Picon Zero, retrying")
    else:
        print("Error during Picon Zero clean-up phase")

    time.sleep(0.01)   # 10 ms delay to allow time to complete


def pz_set_rotor_position(i2c_bus, motor, value):
    # Set polarity on Motor A and Motor B outputs. These are normally meant for
    # DC motors with variable speed, but can be used for stepper motors as well
    # by setting 'value' to either minimum (-127) or maximum (127)

    if ((motor == 0 or motor == 1) and (value == -127 or value == 127)):
        for attempt in range(PZ_I2C_RETRIES):
            try:
                i2c_bus.write_byte_data(PZ_ADDR, motor, value)
                print("Set motor {} to {}".format(motor, value))
                break
            except:
                print("Error in set_motor(), retrying")
        else:
            print("Error setting motor, program terminating")
            exit()


def pz_move_one_step(i2c_bus, motor_sequence, motor_speed, mode='cw'):
    # Run through a sequence as defined by motor_sequence, with a sleep time
    # of 1 / motor_speed in between individual steps. One whole sequence is
    # is one full rotation of the shaft. Default is clockwise (cw) rotation,
    # although counter-clockwise (ccw) can be specified via the mode parameter.
    # This function assumes that pz_init() has already been called.

    if mode == 'ccw':
        motor_sequence = motor_sequence[::-1]

    motor_sleep_time = 1.0 / motor_speed

    try:
        for step in motor_sequence:
            pz_set_rotor_position(i2c_bus, PZ_MOTOR_A, step[0])
            pz_set_rotor_position(i2c_bus, PZ_MOTOR_B, step[1])
            time.sleep(motor_sleep_time)
        print("Moved one step in {} direction".format(mode))
    except:
        print("Error moving the motor shaft, shutting down")
        pz_cleanup(i2c_bus)


if __name__ == '__main__':

    if BOARD == 'PZ':
        pz_i2c_bus = pz_init()
        while True:
            try:
                pz_move_one_step(pz_i2c_bus, pz_motor_sequence,
                                 pz_motor_speed, pz_motor_mode)
            except KeyboardInterrupt:
                print("Shutting down")
                pz_set_rotor_position(pz_i2c_bus, PZ_MOTOR_A, PZ_MOTOR_00)
                pz_set_rotor_position(pz_i2c_bus, PZ_MOTOR_B, PZ_MOTOR_00)
                pz_cleanup(pz_i2c_bus)
                break
    elif BOARD == 'PQ':
        pq_gpio = pq_init(PQ_COIL_1_PINS, PQ_COIL_2_PINS)
        while True:
            try:
                pq_move_one_step(pq_gpio, PQ_COIL_1_PINS, PQ_COIL_2_PINS,
                                 pq_motor_sequence, pq_motor_speed,
                                 pq_motor_mode)
            except KeyboardInterrupt:
                print("Shutting down")
                pq_cleanup(pq_gpio, PQ_COIL_1_PINS, PQ_COIL_2_PINS)
                break
    else:
        print('Board not supported')
