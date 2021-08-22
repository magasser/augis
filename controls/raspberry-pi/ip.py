"""
Authors: Manuel Gasser, Julian Haldimann
Created: 12.04.2021
Last Modified: 12.04.2021
"""

import fcntl
import logging as log
import socket
import struct


def get_ip_address(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(
            fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', bytes(ifname[:15], 'utf-8')))[20:24])
    except OSError as err:
        log.error(f"Could not get IP address for interface {ifname}. Stacktrace {err}")
        return None
