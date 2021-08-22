"""
Authors: Manuel Gasser, Julian Haldimann
Created: 18.03.2021
Last Modified: 13.06.2021
"""

import logging as log
import time
from datetime import datetime as dt

from serial.serialutil import SerialException

import thread_handler as th
from gps import Gps
from topics import Topics


class Engine:
    MAX_THROTTLE = 100

    TURN_ON_SPOT_ANGLE_EPSILON = 5
    TURN_TO_ANGLE_EPSILON = 2
    TURN_TIME_EPSILON = 2
    TIME_BETWEEN_UPDATES = .1
    HALT_SPEED_EPSILON = .2
    HALT_TIME_EPSILON = 2

    BWD_PW_ADJ = 3
    ANGLE_PW_ADJ = 8

    def __init__(self):
        self.serial = None
        self.mqttClient = None
        self.gps_pos = [47, 7.3]
        self.heading = 0
        self.eng_l = 0
        self.eng_r = 0
        self.speed = 0
        self.__stop = False
        self.__time = time.time()
        self.__data_fn = ''
        self.__target = None

    def set_serial(self, s):
        self.serial = s

    def set_data_filename(self, fn):
        self.__data_fn = fn

    def set_target(self, target):
        self.__target = target

    def set_mqtt_client(self, c):
        self.mqttClient = c

    """
    Update GPS position and calculate speed with current and previous GPS position.
    
    :param pos: new GPS position
    """

    def update_gps_pos(self, pos):
        with th.locks["engine_update_lock"]:
            temp = time.time()
            # Calculate speed of the AUGIS
            t = temp - self.__time
            s = Gps.get_distance(self.gps_pos, pos)
            self.speed = s / t
            # Update time to current time
            self.__time = temp
            # Negate speed if the AUGIS is driving backwards
            if Gps.angle_difference(Gps.get_direction(self.gps_pos, pos), self.heading) > 180:
                self.speed *= -1
            self.gps_pos = pos

            if self.mqttClient is not None:
                self.mqttClient.pub(Topics.INFO_SPEED, self.speed)

    def update_heading(self, heading):
        with th.locks["engine_update_lock"]:
            self.heading = heading

    def stop(self):
        # with th.locks["engine_cmd_lock"]:
        with th.locks["engine_stop_lock"]:
            self.__stop = True

    def reset(self):
        with th.locks["engine_reset_lock"]:
            self.eng_l = 0
            self.eng_r = 0
            self.__stop = False
            self.__time = time.time()

    """
    Update engine throttle values and send command over serial to Arduino.
    
    :param eng_l: the left engine throttle
    :param eng_r: the right engine throttle
    """

    def __update_engines(self, eng_l, eng_r):
        eng_l = 100 if eng_l > 100 else eng_l
        eng_l = -100 if eng_l < -100 else eng_l
        eng_r = 100 if eng_r > 100 else eng_r
        eng_r = -100 if eng_r < -100 else eng_r

        self.eng_l = round(eng_l)
        self.eng_r = round(eng_r)
        self.send_command('engine', f"{self.eng_l},{self.eng_r}")

    """
    This function updates the engine throttle to turn the AUGIS
    to the given heading when standing still.
    
    :param heading: to turn to
    """

    def turn_to_on_spot(self, heading):
        # Get the turn angle for the new heading
        angle = self.__turn_angle(heading)
        # If the turn angle is already in the acceptable range just return
        if abs(angle) <= Engine.TURN_ON_SPOT_ANGLE_EPSILON:
            return

        time_epsilon = 0
        # Turn towards new heading until it is stable
        while time_epsilon < Engine.TURN_TIME_EPSILON and not self.__stop:
            # Calculate the power percentage for each engine
            temp = round(angle / 1.8) + Engine.ANGLE_PW_ADJ
            # Update engines to new values
            if temp >= 0:
                left = temp / Engine.BWD_PW_ADJ
                right = -temp
            else:
                left = temp
                right = -temp / Engine.BWD_PW_ADJ
            self.__update_engines(left, right)
            # Log data into file
            self.log_data('turn_to_on_spot', heading, angle, Engine.TURN_TIME_EPSILON - time_epsilon)
            # Delay to not repeat the steps to often
            time.sleep(Engine.TIME_BETWEEN_UPDATES)
            # Recalculate the turn angle
            angle = self.__turn_angle(heading)
            # Count the time the new heading is in the acceptable limits
            if abs(angle) <= Engine.TURN_ON_SPOT_ANGLE_EPSILON:
                time_epsilon += Engine.TIME_BETWEEN_UPDATES
            else:
                time_epsilon = 0

        # Stop engines
        self.throttle(0)

    """
    This function updates the engine throttle to turn the AUGIS
    to the given heading when moving.
    
    :param heading: to turn to
    """

    def turn_to(self, heading):
        # Get the turn angle for the new heading
        angle = self.__turn_angle(heading)
        # If the turn angle is already in the acceptable range just return
        if abs(angle) <= Engine.TURN_TO_ANGLE_EPSILON:
            return
        # Save engine values before turn
        engine_values = [self.eng_l, self.eng_r]
        # Turn towards new heading until heading is reached
        while abs(angle) > Engine.TURN_TO_ANGLE_EPSILON and not self.__stop:
            # Calculate the percentage which the turn engine should slow down
            temp = abs(round(angle / 180 * max(self.eng_l, self.eng_r))) + Engine.ANGLE_PW_ADJ
            # If angle is positive turn clockwise else turn counterclockwise
            if angle >= 0:
                self.__update_engines(self.eng_l, self.eng_r - temp)
            else:
                self.__update_engines(self.eng_l - temp, self.eng_r)
            # Log data into file
            self.log_data('turn_to', heading, angle)
            # Delay to not repeat the steps to often
            time.sleep(Engine.TIME_BETWEEN_UPDATES)
            # Recalculate the turn angle
            angle = self.__turn_angle(heading)
            self.eng_l = engine_values[0]
            self.eng_r = engine_values[1]

        # Reset engines to values before the turn
        self.__update_engines(engine_values[0], engine_values[1])

    """
    This function calculates the new heading to turn to and calls
    the turn to function according to if it is on spot or not.
    
    :param degrees: to turn
    :param on_spot: if the AUGIS is on spot or not
    """

    def turn_by(self, degrees, on_spot=False):
        heading = self.heading + degrees
        if heading >= 360:
            heading -= 360
        elif heading < 0:
            heading += 360

        if on_spot:
            self.turn_to_on_spot(heading)
        else:
            self.turn_to(heading)

    """
    Determine the direction which is shortest to turn to the new heading and the
    corresponding angle difference.
    Positive angle means turn clockwise and negative angle means turn
    counterclockwise.
    
    :returns: turn angle
    """

    def __turn_angle(self, heading):
        return ((heading - self.heading + 540) % 360) - 180

    """
    Update both engines according to throttle value. Throttle value is between -100 to 100.
    
    :param throttle: to be applied to both engines
    """

    def throttle(self, throttle):
        self.__update_engines(throttle, throttle)

        # Log data into file
        self.log_data('throttle')

    """
    Halt the AUGIS as fast as possible.
    """

    def halt(self):
        if th.locks["engine_halt_lock"].locked():
            return
        with th.locks["engine_halt_lock"]:
            if self.speed <= Engine.HALT_SPEED_EPSILON:
                return
            # Reverse engine throttle values for half a second to slow movement as best as possible
            self.__update_engines(-self.eng_l, -self.eng_r)
            time.sleep(.5)

            time_epsilon = 0
            # Slow down until speed is stable below speed epsilon
            while time_epsilon < Engine.HALT_TIME_EPSILON and not self.__stop:
                # Calculate engine throttle proportional to speed (0.02 is equivalent to max speed of 2m/s)
                temp = self.speed / .02
                temp = min(temp, Engine.MAX_THROTTLE)
                # Update engines to new values
                self.__update_engines(temp, temp)
                # Log data into file
                self.log_data('halt', Engine.HALT_TIME_EPSILON - time_epsilon)
                # Delay to not repeat the steps to often
                time.sleep(Engine.TIME_BETWEEN_UPDATES)
                # Count the time the speed is in the acceptable limits
                if self.speed <= Engine.HALT_SPEED_EPSILON:
                    time_epsilon += Engine.TIME_BETWEEN_UPDATES
                else:
                    time_epsilon = 0

            # Stop engines
            self.throttle(0)

    """
    Function that will send a message to the arduino.
    
    :param prefix:  The name of the message
    :param value:   The payload of the message
    """

    def send_command(self, prefix, value):
        if th.locks["serial_lock"].locked():
            return
        with th.locks["serial_lock"]:
            try:
                if self.serial is not None:
                    self.serial.write(f"{prefix}: {value}\n".encode("utf-8"))
            except SerialException as ex:
                log.error(f"Raspberry Pi could not read from Serial USB connection, Stacktrace {ex}")
                # client.pub(Topics.ERROR_CONN, "Raspberry Pi could not write on Serial USB connection.")

    def log_data(self, *data):
        with open(self.__data_fn, 'a') as file:
            temp = f"{dt.now()} {self.gps_pos} {self.heading} {self.speed} {self.__target} {self.eng_l} {self.eng_r} "
            for arg in data:
                temp += f"{arg} "
            temp += '\n'
            file.write(temp)
