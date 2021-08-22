"""
Authors: Manuel Gasser, Julian Haldimann
Created: 02.03.2021
Last Modified: 17.06.2021
"""

import json
import logging as log
import time
from datetime import datetime as dt

import serial
from picamera import PiCamera
from picamera.exc import PiCameraMMALError, PiCameraError
from serial.serialutil import SerialException

import file_handler as fh
import ip
import request_handler as rh
import thread_handler as th
from command import Command as Cmd
from config import Config
from engine import Engine
from gps import Gps
from lake import Lake
from mqtt import Mqtt
from pid import Pid
from thread_handler import s_print, start_thread
from topics import Topics

# Variables for drive thread
drive_thread = None
stop_drive = False

# Time to wait for command in milliseconds
COMMAND_WAIT = 5000
RECONNECT_WAIT = 3000
time_last_command = time.time()
conn_err = False

created_route_AUGIS = []
driven_route_AUGIS = []
# Polygon of the lake the AUGIS is driving in
lake = None

heading = 0
heading_time = time.time()

gps_pos = {
    Gps.RTK: None,
    Gps.PHONE: None,
    Gps.DRG: None
}

start_pos = None

gps_times = {
    Gps.RTK: time.time(),
    Gps.PHONE: time.time(),
    Gps.DRG: time.time()
}

DISTANCE_EPSILON = 1
FAIL_C_DISTANCE_EPSILON = 5
FAIL_C_WAIT = 30

"""
Drive through a route of points.

:param points:   List filled with GPS points
:param stop:     To stop the thread
"""


def autonomous_drive(points, stop):
    global stop_drive
    engine.log_data('Started autonomous drive')
    client.pub(Topics.INFO_STATUS, "Started autonomous drive")

    # engine.halt()
    # Get current GPS position
    pos = get_best_gps_pos()

    # Drive through points on route
    for i, point in enumerate(points):
        # Check if straight route to next point is possible
        if lake.no_intersection(pos, point):
            # Calculate and drive new route
            new_route = lake.calc_new_route(pos, point)
            # Check if route could be created
            if new_route is None:
                log.error(f"Can not drive straight to next point and new route could not be calculated: Current Point: "
                          f"{pos}, Next Point: {point}")
                client.pub(Topics.ERROR_DRIVE, f"Can not drive straight to next point and new route could not be "
                                               f"calculated: Current Point: {pos}, Next Point: {point}")
                engine.stop()
                stop_drive = True
            else:
                autonomous_drive(new_route, lambda: stop_drive, )
        else:
            engine.set_target(point)
            # Get direction to next point
            direction = Gps.get_direction(pos, point)
            # Turn towards point
            engine.turn_to_on_spot(direction)
            # Put engine on full throttle
            engine.throttle(Engine.MAX_THROTTLE * .7)
            # Drive towards point until AUGIS is close
            while Gps.get_distance(pos, point) > DISTANCE_EPSILON and not stop_drive:
                # Get current GPS position
                pos = get_best_gps_pos()
                # Get direction to next point
                direction = Gps.get_direction(pos, point)
                # Calculate correction angle
                c_angle = pid.control(direction, heading, 1)
                # Turn by correction angle
                engine.turn_by(c_angle)
                engine.log_data('autonomous', direction, c_angle)
                time.sleep(Engine.TIME_BETWEEN_UPDATES)

        # Stop the AUGIS when it has reached the point
        engine.halt()
    engine.log_data('End autonomous drive')


"""
Function that will send a message to the arduino.

:param prefix:  The name of the message
:param value:   The payload of the message
"""


def send_command(prefix, value):
    start_thread(send_command_thread, (prefix, value,))


def send_command_thread(prefix, value):
    with th.locks["serial_lock"]:
        try:
            if serial_ard is not None:
                serial_ard.write(f"{prefix}: {value}\n".encode("utf-8"))
        except SerialException as ex:
            log.error(f"Raspberry Pi could not write on Serial USB connection, Stacktrace {ex}")


"""
Read commands and convert them into a Command object.

:returns: command that was read
"""


def read_command():
    with th.locks["serial_read_lock"]:
        try:
            if serial_ard is not None:
                line_splits = serial_ard.readline().decode('utf-8').split(':')
                if len(line_splits) == 2:
                    return Cmd(line_splits[0].strip(), line_splits[1].strip())
        except SerialException as ex:
            log.error(f"Raspberry Pi could not read from Serial USB connection, Stacktrace {ex}")
            client.pub(Topics.ERROR_CONN, "Raspberry Pi could not read from Serial USB connection.")
            return None


def on_message_callback(client, userdata, msg):
    start_thread(on_message, (client, userdata, msg,))


"""
Callback method if the subscription receive a message.

:param client:   Client instance
:param userdata: Information about the user
:param msg:      The message itself with topic and payload inside
"""


def on_message(client, userdata, msg):
    global stop_drive
    global drive_thread
    global conn_err
    global created_route_AUGIS
    global driven_route_AUGIS
    global heading
    global heading_time
    global lake
    global start_pos
    global connected_to_base

    payload = msg.payload

    if type(payload) is bytes:
        payload = payload.decode('utf-8')

    if msg.topic == Topics.ITEM_ROUTE_ID:
        start_thread(load_route, (payload,))
    elif msg.topic == Topics.ITEM_CURRENT_ROUTE:
        if payload == 'get':
            if len(driven_route_AUGIS) > 0:
                gj = json.dumps(fh.create_geojson(driven_route_AUGIS))
                client.pub(Topics.ITEM_CURRENT_ROUTE, gj)
            else:
                client.pub(Topics.ITEM_CURRENT_ROUTE, 'none')
    elif msg.topic == Topics.COMMAND_ENGINE:
        send_command('engine', payload)
    elif msg.topic == Topics.COMMAND_MODE:
        mode = payload.lower()

        if mode == 'auto':
            send_command('mode', mode)
        elif mode == 'radio-remote':
            # Stop the thread running the drive
            stop_drive = True
            send_command('mode', mode)
    elif msg.topic == Topics.COMMAND_DRIVE:
        if payload == 'start':
            stop_drive = False
            start_pos = get_best_gps_pos()
            if start_pos is not None:
                engine.reset()
                drive_thread = start_thread(autonomous_drive, (created_route_AUGIS, lambda: stop_drive,))
            else:
                client.pub(Topics.ERROR_DRIVE, "No GPS data available")
                log.error("No GPS data available")
        elif payload == 'stop':
            stop_drive = True
            engine.stop()
            start_thread(engine.halt, ())
            client.pub(Topics.INFO_STATUS, "Stopped autonomous drive")
        elif payload == 'return':
            stop_drive = True
            engine.stop()
            time.sleep(5)
            engine.reset()
            stop_drive = False
            drive_thread = start_thread(autonomous_drive, ([start_pos], lambda: stop_drive,))
    elif msg.topic == Topics.RTK_ROVER_ONLINE:
        client.pub(Topics.RTK_ROVER_INTENT, '224CC28A9F')
    elif msg.topic == Topics.RTK_ROVER_EVENT:
        try:
            data = payload.split(',')
            gps_pos[Gps.RTK] = [float(data[0]), float(data[1])]
            gps_times[Gps.RTK] = time.time()
            pos = get_best_gps_pos()
            # Only update gps position if location is different
            if len(driven_route_AUGIS) == 0 or driven_route_AUGIS[-1] != pos:
                driven_route_AUGIS.append(pos)
            engine.update_gps_pos(pos)
        except:
            print(dt.now(), "Could not read RTK data.")
    elif msg.topic.startswith(Topics.SENSOR_GPS_ALL[:-1]):
        t = msg.topic.split('/')[-1]
        coords = payload.split(',')

        gps_pos[t] = [float(coords[Gps.LAT]), float(coords[Gps.LNG])]
        gps_times[t] = time.time()
        pos = get_best_gps_pos()
        # Only update gps position if location is different
        if len(driven_route_AUGIS) == 0 or driven_route_AUGIS[-1] != pos:
            driven_route_AUGIS.append(pos)
        engine.update_gps_pos(pos)
    elif msg.topic == Topics.SENSOR_HEADING:
        heading = float(payload)
        heading_time = time.time()
        engine.update_heading(heading)
    elif msg.topic == Topics.LWT:
        if payload == 'base-station':
            connected_to_base = False
            # Failsafe C
            log.warning('Raspberry Pi lost connection to Base-Station.')
            log.info('Executing Failsafe C.')
            stop_drive = True
            engine.stop()
            if not th.locks["engine_halt_lock"].locked():
                start_thread(engine.halt, ())
            send_command('mode', 'radio.remote')
            start_thread(check_movement, (FAIL_C_WAIT,))
    elif msg.topic == Topics.HELLO_REQ:
        connected_to_base = True
        client.pub(Topics.HELLO_RESP, 'raspberry')
    elif msg.topic.startswith(Topics.MOCK_ALL[:-1]):
        cmd = msg.topic.split('/')[-1]
        if cmd == 'done':
            return
        start_thread(handle_command, (cmd, msg.payload,))
    elif msg.topic == Topics.RECORD:
        if camera is None:
            return
        if payload == 'start':
            camera.start_preview()
            camera.start_recording(f"/home/pi/Desktop/recordings/water_{int(time.time())}.h264")
            client.pub(Topics.INFO_STATUS, "Started recording")
        elif payload == 'stop':
            camera.stop_recording()
            camera.stop_preview()
            client.pub(Topics.INFO_STATUS, "Stopped recording")


"""
Function to handle mock commands

:param cmd: command to be executed
:param value: value of the command
"""


def handle_command(cmd, value):
    if cmd == 'tt':
        value = int(value)
        engine.turn_to_on_spot(value)
    elif cmd == 'tb':
        value = int(value)
        engine.turn_by(value, True)
    elif cmd == 'ds':
        value = int(value)
        engine.throttle(Engine.MAX_THROTTLE)
        time.sleep(value)
        engine.halt()
    elif cmd == 'stop':
        engine.stop()
        time.sleep(.3)
        engine.reset()
        engine.halt()

    client.pub(Topics.MOCK_DONE, 'true')


"""
Load route from aws api.
"""


def load_route(id):
    global created_route_AUGIS
    global lake

    route_json = rh.get_route_by_id(id)
    created_route_AUGIS = fh.parse_route_geojson(route_json['json'])
    lake_json = rh.get_lake_by_id(route_json['lake'])
    lake = Lake(lake_json['json'])
    client.pub(Topics.INFO_STATUS, f"Got lake from DB with id: {id}")


"""
Function for Failsafe C to check if AUGIS has moved after given time.

:param t: time to wait for AUGIS to move in seconds
"""


def check_movement(t):
    time.sleep(5)
    s_pos = get_best_gps_pos()
    if s_pos is not None and not connected_to_base:
        time.sleep(t - 5)
        e_pos = get_best_gps_pos()
        if Gps.get_distance(s_pos, e_pos) < FAIL_C_DISTANCE_EPSILON:
            autonomous_drive([start_pos], lambda: stop_drive)


"""
Get the best current GPS location from the different devices (RTK, Phone, Dragino).
"""


# noinspection PyUnresolvedReferences
def get_best_gps_pos():
    global gps_pos

    if gps_pos[Gps.RTK] is not None:
        return gps_pos[Gps.RTK]
    elif gps_pos[Gps.PHONE] is not None:
        return gps_pos[Gps.PHONE]
    elif gps_pos[Gps.DRG] is not None:
        return gps_pos[Gps.DRG]

    return None


def on_connect_callback(c, userdata, flags, rc):
    start_thread(on_connect, (c, userdata, flags, rc,))


"""
Callback function if the client could connect successfully to the broker.

:param client:      Client instance
:param userdata:    Information about the user
:param flags:       Optional flags
"""


def on_connect(c, userdata, flags, rc):
    global client

    client.connected = True
    log.info(f"Successfully connected to MQTT Broker on {ip_addr}:{Config.PORT}")
    client.sub(Topics.ITEM_ROUTE_ID)
    client.sub(Topics.ITEM_CURRENT_ROUTE)
    client.sub(Topics.RTK_ROVER_EVENT)
    client.sub(Topics.SENSOR_GPS_ALL)
    client.sub(Topics.SENSOR_HEADING)
    client.sub(Topics.COMMAND_DRIVE)
    client.sub(Topics.COMMAND_ENGINE)
    client.sub(Topics.COMMAND_MODE)
    client.sub(Topics.LWT)
    client.sub(Topics.HELLO_REQ)
    client.sub(Topics.HELLO_RESP)
    client.sub(Topics.RECORD)
    client.sub(Topics.MOCK_ALL)

    client.pub(Topics.HELLO_RESP, 'raspberry')
    client.pub(Topics.RASP_IP, ip_addr, retain=True)
    client.pub(Topics.RTK_ROVER_INTENT, '224CC28A9F')


"""
Callback function if the client gets disconnected.

:param client:      Client instance
:param userdata:    Information about the user
:param flags:       Optional flags
"""


def on_disconnect(c, userdata, rc):
    global client

    client.connected = False

    log.warning(f"Disconnected from MQTT Broker on {Config.DOMAIN}:{Config.PORT}")


"""
Send ping pong signal to arduino to confirm connection is still up.
"""


def conn_arduino():
    global time_last_command
    global conn_err
    global ip_addr
    global serial_ard

    fs = False
    time_last_command = time_ms()
    time_last_reconnect = time_ms()

    while True:
        send_command('conn', 'raspberry-pi')

        cmd = read_command()

        if cmd is not None:
            if cmd.get_prefix() == 'conn' and cmd.get_data() == 'arduino':
                time_last_command = time_ms()
        elif time_ms() - time_last_reconnect > RECONNECT_WAIT:
            serial_ard = connect_serial(Config.SERIAL_PORT_ARD, Config.BAUDRATE)

        conn_err = time_ms() - time_last_command > COMMAND_WAIT

        if conn_err and not fs:
            log.error('Raspberry Pi lost connection to Arduino.')
            client.pub(Topics.ERROR_CONN, 'rasp-ard')
            fs = True
        elif not conn_err and fs:
            fs = False
            log.error(f"Reestablished connection to Arduino.")
            client.pub(Topics.INFO_CONN, 'rasp-ard')

        time.sleep(1)


"""
Returns time in milliseconds since epoch.

:returns: Time in milliseconds since epoch
"""


def time_ms():
    return time.time() * 1000


"""
Connect to serial USB port to connect with devices.

:param serial_port: name of the serial port
:param baud_rate: to be used for the connection
:param timeout: time to wait when reading from serial port
"""


def connect_serial(serial_port, baudrate):
    try:
        s = serial.Serial(serial_port, baudrate=Config.BAUDRATE, writeTimeout=.3, rtscts=False, dsrdtr=False)
        s.flush()
        log.info(f"Successfully Connected to Serial Port: {serial_port}")
        return s
    except SerialException as ex:
        log.error(f"Raspberry Pi could not connect on Serial Port: {serial_port}, Stacktrace {ex}")
        client.pub(Topics.ERROR_CONN, f"Raspberry Pi could not connect on Serial Port: {serial_port}")
        return None


"""
Check if sensor data is current information and set it to None if not.
"""


def check_sensor_data():
    global gps_times
    global gps_pos
    global heading_time
    global heading

    prev_pos = None
    prev_heading = None

    while True:
        current_time = time.time()

        if current_time - gps_times[Gps.RTK] > Gps.WAIT:
            gps_pos[Gps.RTK] = None
        if current_time - gps_times[Gps.PHONE] > Gps.WAIT:
            gps_pos[Gps.PHONE] = None
        if current_time - gps_times[Gps.DRG] > Gps.WAIT:
            gps_pos[Gps.DRG] = None

        if current_time - heading_time > Gps.WAIT:
            heading = None

        pos = get_best_gps_pos()

        # Failsafe D
        if pos is None:
            log.error('No GPS Position data available.')
            log.info('Executing Failsafe D.')
            client.pub(Topics.ERROR_SENSOR, 'No GPS Position data available.')
            engine.stop()
            if not th.locks["engine_halt_lock"].locked():
                start_thread(engine.halt, ())
        elif heading is None:
            if prev_pos is not None:
                if prev_pos[Gps.LAT] != pos[Gps.LAT] and prev_pos[Gps.LNG] != pos[Gps.LNG]:
                    heading = Gps.get_direction(prev_pos, pos)
                else:
                    heading = prev_heading

        prev_pos = pos
        prev_heading = heading
        time.sleep(.5)


def lock_thread():
    while True:
        for lock in th.locks:
            s_print(th.locks[lock].locked(), lock)
        time.sleep(1)


if __name__ == '__main__':
    # Setup for log file
    log.basicConfig(filename='augis.log', format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S',
                    level=log.INFO)

    # Connection flag for base station
    connected_to_base = False

    # Get IP Address
    ip_addr = ip.get_ip_address('wlan0')
    if ip_addr is None:
        ip_addr = ip.get_ip_address('eth0')

    # Setup MQTT client
    client = Mqtt()
    client.connected = False
    client.on_connect = on_connect_callback
    client.on_disconnect = on_disconnect
    client.on_message = on_message_callback
    client.will_set(Topics.LWT, payload='raspberry')

    client.connect_to_client(Config.DOMAIN, Config.PORT, keepalive=3)

    # Connect to Dragino and Arduino over Serial Ports
    serial_ard = connect_serial(Config.SERIAL_PORT_ARD, Config.BAUDRATE)
    serial_drg = connect_serial(Config.SERIAL_PORT_DRG, Config.BAUDRATE)

    # Initialize engine and Pid controller
    engine = Engine()
    if serial_ard is not None:
        engine.set_serial(serial_ard)
    engine.set_mqtt_client(client)
    pid = Pid()

    # Start getting GPS information from Dragino
    if serial_drg is not None:
        start_thread(Gps.gps_reader, (serial_drg, client,))

    # Thread to keep sensor data current
    start_thread(check_sensor_data, ())
    # Start thread for connection check
    start_thread(conn_arduino, ())

    # Thread to check status of locks
    # start_thread(lock_thread, ())

    try:
        camera = PiCamera()
        camera.resolution = (1280, 720)
        camera.framerate = 24
    except (PiCameraMMALError, PiCameraError) as err:
        s_print(err)

    # Create file to log data
    data_fn = f"/home/pi/Desktop/data/data_{int(time.time())}.txt"
    engine.set_data_filename(data_fn)
    f = open(data_fn, 'x')
    f.close()

    # MQTT loop
    client.loop_forever()

    while True:
        pass
