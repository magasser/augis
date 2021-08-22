"""
Authors: Manuel Gasser, Julian Haldimann
Created: 15.05.2021
Last Modified: 17.05.2021
"""

import json

from art import *

from config import Config
from mqtt import Mqtt
from thread_handler import start_thread
from topics import Topics

cmd_done = True

"""
MQTT Message Hook
"""


def on_message(c, userdata, msg):
    global cmd_done

    payload = msg.payload

    if type(payload) is bytes:
        payload = payload.decode('utf-8')

    if msg.topic == Topics.MOCK_DONE:
        cmd_done = True


"""
MQTT Connect Hook
"""


def on_connect(c, userdata, flags, rc):
    client.sub(Topics.MOCK_DONE)


"""
MQTT Disconnect Hook
"""


def on_disconnect(c, userdata, rc):
    print("Disconnected")
    pass


"""
Loop until the user close the program
"""


def command_loop():
    resp = input("Do you want to read in a file or type commands? (f/c):\n")

    if resp == 'f':
        fn = input("Enter file name located in 'mock' folder:\n")
        handle_file(fn)
    elif resp == 'c':
        print("Enter 'exit' to cancel or 'help' to show commands.")
        while True:
            cmd = input("Enter command:\n")
            if cmd == 'exit':
                break
            if cmd == 'help' or cmd == 'h':
                print('Commands:')
                print('\tds\t-> drive straight.\tFormat: ds {time in seconds}')
                print('\ttt\t-> turn to.\tFormat: tt {heading}')
                print('\ttb\t-> turn by.\tFormat: tb {angle}')
                print('\tstop\t-> stop.\t\tFormat: stop')
            else:
                handle_command(cmd)
        command_loop()
    else:
        print("No matching command found try again")
        command_loop()


"""
Handle a specific incoming command

:param cmd: What type of action should be done
"""


def handle_command(cmd):
    global cmd_done
    print("Execute the following command: " + cmd)
    cmd = cmd.split(' ')
    if cmd[0] == 'ds':
        client.publish(Topics.MOCK_DS, cmd[1])
    elif cmd[0] == 'tt':
        client.publish(Topics.MOCK_TT, cmd[1])
    elif cmd[0] == 'tb':
        client.publish(Topics.MOCK_TB, cmd[1])
    elif cmd[0] == 'stop':
        client.publish(Topics.MOCK_STOP, 'true')


"""
Read file and execute every command 

:param fn: Filename
"""


def handle_file(fn):
    global cmd_done

    with open('../mock/' + fn) as file:
        data = json.load(file)
        for cmd in data['commands']:
            if cmd_done:
                cmd_done = False
                handle_command(cmd)
    command_loop()


if __name__ == '__main__':
    # Display cool ascii-art text
    print(text2art('AUGIS', font='small'))
    client = Mqtt()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect_to_client(Config.DOMAIN, 1883, keepalive=30)

    start_thread(command_loop, ())

    client.loop_forever()
