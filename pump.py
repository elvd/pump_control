import time
import pigpio


class Pump:
    # Control of stepper motor as part of a syringe pump
    # `coil_1_pins`, `coil_2_pins` - RPi pins connected to motor's coils
    # `motor_sequence` - from datasheet, coil sequence to turn 1 step
    # `motor_speed` - in Hz, how fast to rotate shaft
    # `steps_per_revolutions` - from datasheet, steps for a 360 deg turn
    def __init__(self, coil_1_pins, coil_2_pins, motor_sequence, motor_speed,
                 steps_per_revolution):
        self.coil_1_pins = coil_1_pins
        self.coil_2_pins = coil_2_pins
        self.motor_sequence = motor_sequence
        self.motor_speed = motor_speed
        self.motor_sleep_time = 1.0 / motor_speed
        self.steps_per_revolution = steps_per_revolution

        self.gpio = pigpio.pi()  # connect to pigpiod

        if not self.gpio.connected:
            raise RuntimeError('Error connecting to pigpiod.')
        else:
            self.gpio.set_mode(self.coil_1_pins[0], pigpio.OUTPUT)
            self.gpio.set_mode(self.coil_1_pins[1], pigpio.OUTPUT)
            self.gpio.set_mode(self.coil_2_pins[0], pigpio.OUTPUT)
            self.gpio.set_mode(self.coil_2_pins[1], pigpio.OUTPUT)

    def set_rotor(self, pins, state):
        # Sets rotor position
        self.gpio.write(pins[0], state[0])
        self.gpio.write(pins[1], state[1])

    def cleanup(self):
        # Turns off RPi GPIO pins and releases pigpiod
        self.set_rotor(self.coil_1_pins, (0, 0))
        self.set_rotor(self.coil_2_pins, (0, 0))
        self.gpio.stop()

    def move_one_step(self, mode='cw'):
        # Goes through `motor_sequence` once, advancing 1 step
        if mode == 'ccw':
            motor_sequence = self.motor_sequence[::-1]
        else:
            motor_sequence = self.motor_sequence

        for step in motor_sequence:
            self.set_rotor(self.coil_1_pins, step[0])
            self.set_rotor(self.coil_2_pins, step[1])
            time.sleep(self.motor_sleep_time)  # crude but it works

    def move_one_revolution(self, mode='cw'):
        # Full rotation of motor shaft in 'cw' or 'ccw' direction
        for _ in range(self.steps_per_revolution):
            self.move_one_step(mode)
