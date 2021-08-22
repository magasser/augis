"""
Authors: Manuel Gasser, Julian Haldimann
Created: 02.03.2021
Last Modified: 08.05.2021
"""

import logging as log

import paho.mqtt.client as mqtt

import thread_handler as th
from config import Config


class Mqtt(mqtt.Client):
    """
    Publish a payload to a specific topic.

    :param topic:   The topic is the place where the message should be published
    :param payload: The payload is the data that should be published
    """

    def pub(self, topic, payload, qos=1, retain=False):
        with th.locks["pub_lock"]:
            self.publish(topic, payload, qos=1, retain=retain)

    """
    Subscribe to a specific topic to receive messages
    
    :param topic: The topic is the route where the message appears
    """

    def sub(self, topic, qos=1):
        self.subscribe(topic, qos=qos)

    """
    Connect to the mqtt client with username and password
    """

    def connect_to_client(self, domain=Config.DOMAIN, port=Config.PORT, keepalive=60):
        self.username_pw_set(Config.USER, Config.PASSWORD)

        try:
            self.connect(domain, port, keepalive=keepalive)
        except (ConnectionError, OSError, ValueError) as err:
            log.error(f"Could not connect to MQTT on: {domain}:{port}, Stacktrace {err}")
