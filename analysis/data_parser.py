"""
Authors: Manuel Gasser, Julian Haldimann
Created: 10.06.2021
Last Modified: 10.06.2021
"""

import os
from datetime import datetime as dt


def autonomous_data_parser(file):
    with open(file, 'r') as data_file:
        all_data = []
        parse_data = False
        first = True
        for l in data_file:
            if parse_data:
                if 'End autonomous drive' in l:
                    break
                line = l.split(' ')
                if len(line) <= 1:
                    continue
                if first:
                    start = dt.strptime(f"{line[0]} {line[1]}", '%Y-%m-%d %H:%M:%S.%f')
                diff = dt.strptime(f"{line[0]} {line[1]}", '%Y-%m-%d %H:%M:%S.%f') - start
                data = {
                    'name': file.split('/')[-1][:-4],
                    'time': f"{line[0]} {line[1]}",
                    'time_since_start': diff.total_seconds(),
                    'c_location': [float(line[2][1:-1]), float(line[3][:-1])],
                    'c_heading': float(line[4]),
                    'speed': float(line[5]),
                    't_location': [float(line[6][1:-1]), float(line[7][:-1])],
                    'engine_left': float(line[8]),
                    'engine_right': float(line[9]),
                    'command': line[10:]
                }
                all_data.append(data)
                first = False

            if 'Started autonomous drive' in l:
                parse_data = True
    if not os.path.exists(f"images/{all_data[0]['name']}"):
        os.mkdir(f"images/{all_data[0]['name']}")

    return all_data


def gps_data_parser(file):
    with open(file, 'r') as gps_file:
        all_gps = []
        first = True
        start = None
        for l in gps_file:
            line = l.split(';')
            if len(line) <= 1:
                continue
            if first:
                start = dt.strptime(line[0], '%Y-%m-%d %H:%M:%S.%f')
            diff = dt.strptime(line[0], '%Y-%m-%d %H:%M:%S.%f') - start
            gps = {
                'name': file.split('/')[-1][:-4],
                'time': line[0],
                'time_since_start': diff.total_seconds(),
                'c_heading': float(line[1]),
                'rtk_time': float(line[2].split(',')[0][1:]),
                'rtk_loc': [float(line[2].split(',')[1][2:]), float(line[2].split(',')[2][1:-2])],
                'phone_time': float(line[3].split(',')[0][1:]),
                'phone_loc': [float(line[3].split(',')[1][2:]), float(line[3].split(',')[2][1:-2])],
            }
            all_gps.append(gps)
            first = False

    if not os.path.exists(f"images/{all_gps[0]['name']}"):
        os.mkdir(f"images/{all_gps[0]['name']}")

    return all_gps
