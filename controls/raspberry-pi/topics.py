"""
Authors: Manuel Gasser, Julian Haldimann
Created: 02.03.2021
Last Modified: 02.06.2021
"""


class Topics:
    ITEM_ROUTE_ID = 'augis/item/route'
    ITEM_CURRENT_ROUTE = 'augis/item/current-route'
    RTK_ROVER_ONLINE = 'Rover/9C8BE24C22/online'
    RTK_ROVER_EVENT = 'Rover/9C8BE24C22/event'
    RTK_ROVER_INTENT = 'Rover/9C8BE24C22/intent'
    SENSOR_GPS_ALL = 'augis/sensor/gps/#'
    SENSOR_GPS_PHONE = 'augis/sensor/gps/phone'
    SENSOR_GPS_DRG = 'augis/sensor/gps/drg'
    SENSOR_HEADING = 'augis/sensor/heading'
    COMMAND_DRIVE = 'augis/command/drive'
    COMMAND_MODE = 'augis/command/mode'
    COMMAND_ENGINE = 'augis/command/engine'
    INFO_STATUS = 'augis/info/status'
    INFO_MODE = 'augis/info/mode'
    INFO_SPEED = 'augis/info/speed'
    INFO_CONN = 'augis/info/conn'
    ERROR_CONN = 'augis/error/conn'
    ERROR_DRIVE = 'augis/error/drive'
    ERROR_SENSOR = 'augis/error/sensor'
    LWT = 'augis/lwt'
    HELLO_REQ = 'augis/hello/req'
    HELLO_RESP = 'augis/hello/resp'
    RASP_IP = 'augis/raspberry/ip'
    RECORD = 'augis/record'

    MOCK_ALL = 'augis/mock/#'
    MOCK_TT = 'augis/mock/tt'
    MOCK_TB = 'augis/mock/tb'
    MOCK_DS = 'augis/mock/ds'
    MOCK_STOP = 'augis/mock/stop'
    MOCK_DONE = 'augis/mock/done'
