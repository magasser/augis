"""
Authors: Manuel Gasser, Julian Haldimann
Created: 10.06.2021
Last Modified: 14.06.2021
"""

import pandas as pd
import plotly.express as px
import json
import statistics as st
import math
from shapely.geometry import Point
from shapely.geometry import LineString

import data_parser as dp
import file_handler as fh
from gps import Gps


def read_file(path):
    with open(path, 'r') as myfile:
        data = myfile.read()

    # parse file
    obj = json.loads(data)
    return [(p[1], p[0]) for p in obj['features'][0]['geometry']['coordinates'][0]]

def distance_from_t_location(data, show=True):
    df_data = {
        'distance': [],
        'time': []
    }
    for d in data:
        df_data['distance'].append(Gps.get_distance(d['c_location'], d['t_location']))
        df_data['time'].append(d['time_since_start'])

    df = pd.DataFrame(df_data)

    fig = px.line(df, x='time', y='distance', labels={
        'distance': 'Distance to target location (m)',
        'time': 'Time since start (s)'
    }, title='Distance from target location')
    fig.update_layout(title_x=.5, title_y=.93)
    if show:
        fig.show()
    fig.write_image(f"images/{data[0]['name']}/{data[0]['name']}_distance.png")


def direction_to_t_location(data, show=True):
    df_data = {
        'direction': [],
        'time': []
    }

    for d in data:
        df_data['direction'].append(Gps.get_direction(d['c_location'], d['t_location']))
        df_data['time'].append(d['time_since_start'])

    df = pd.DataFrame(df_data)

    fig = px.line(df, x='time', y='direction', title='Direction to target location')
    fig.update_layout(title_x=.5, title_y=.93)
    if show:
        fig.show()
    fig.write_image(f"images/{data[0]['name']}/{data[0]['name']}_direction.png")


def engine_values(data, show=True):
    df_data = {
        'time': [],
        'Left': [],
        'Right': []
    }

    for d in data:
        if 'Stated autonomous drive' not in d and 'End autonomous drive' not in d:
            df_data['time'].append(d['time_since_start'])
            df_data['Left'].append(d['engine_left'])
            df_data['Right'].append(d['engine_right'])

    df = pd.DataFrame(df_data)

    fig = px.line(df, x='time', y=['Left', 'Right'], labels={
        'value': 'Engine values',
        'time': 'Time since start (s)',
        'variable': 'Engines'
    }, range_y=[-100, 100], title='Engine values')
    fig.update_layout(title_x=.5, title_y=.93)
    if show:
        fig.show()
    fig.write_image(f"images/{data[0]['name']}/{data[0]['name']}_engines.png")


def turn_on_spot_angle(data, show=True):
    df_data = {
        'angle': [],
        'time': [],
        'Left': [],
        'Right': []
    }

    for d in data:
        if 'turn_to_on_spot' in d['command']:
            df_data['angle'].append(float(d['command'][2]))
            df_data['time'].append(d['time_since_start'])
            df_data['Left'].append(d['engine_left'])
            df_data['Right'].append(d['engine_right'])

    df = pd.DataFrame(df_data)

    fig1 = px.line(df, x='time', y='angle', labels={
        'angle': 'Angle to target direction (°)',
        'time': 'Time since start (s)'
    }, range_y=[-180, 180], title='Turn on spot angle leveling')
    fig1.update_layout(title_x=.5, title_y=.93)
    if show:
        fig1.show()
    fig1.write_image(f"images/{data[0]['name']}/{data[0]['name']}_angle.png")
    fig2 = px.line(df, x='time', y=['Left', 'Right'], labels={
        'value': 'Engine values',
        'time': 'Time since start (s)',
        'variable': 'Engines'
    }, range_y=[-100, 100], title='Engine values angle leveling')
    fig2.update_layout(title_x=.5, title_y=.93)
    if show:
        fig2.show()
    fig2.write_image(f"images/{data[0]['name']}/{data[0]['name']}_angle_engines.png")


def pid_angles(data, show=True):
    df_data = {
        'time': [],
        'PID Correction': [],
        'Left': [],
        'Right': []
    }

    prev = 0

    for d in data:
        if 'autonomous' in d['command']:
            prev = float(d['command'][2])
            df_data['PID Correction'].append(prev)

        else:
            df_data['PID Correction'].append(prev)
        df_data['time'].append(d['time_since_start'])
        df_data['Left'].append(d['engine_left']/10)
        df_data['Right'].append(d['engine_right']/10)


    df = pd.DataFrame(df_data)

    maximum, minimum = max(df_data['PID Correction']), min(df_data['PID Correction'])
    r = max(maximum, abs(minimum)) + .5

    fig = px.line(df, x='time', y=['PID Correction', 'Left', 'Right'], labels={
        'value': 'Angle of PID correction (°), Engine values 1/10',
        'time': 'Time since start (s)'
    }, title='PID heading correction')
    fig.update_layout(title_x=.5, title_y=.93)
    if show:
        fig.show()
    fig.write_image(f"images/{data[0]['name']}/{data[0]['name']}_pid_angle.png")

def distance_phone_rtk(gps, show=True):
    df_gps = {
        'time': [d['time_since_start'] for d in gps],
        'distance': []
    }
    for d in gps:
        distance = Gps.get_distance(d['phone_loc'], d['rtk_loc'])
        df_gps['distance'].append(distance)

    mean = st.mean(df_gps['distance'])
    median = st.median(df_gps['distance'])

    df = pd.DataFrame(df_gps)

    fig = px.line(df, x='time', y='distance', labels={
        'distance': 'Distance Phone Location to RTK Location (m)',
        'time': 'Time since start (s)'
    }, title='Phone vs RTK')
    fig.add_hline(y=mean, line_dash='dot', line_color='blue',
                  annotation_text=f"Mean: {round(mean, 2)}m", annotation_position='bottom left')
    fig.update_layout(title_x=.5, title_y=.93)
    if show:
        fig.show()
    fig.write_image(f"images/{gps[0]['name']}/{gps[0]['name']}_rtk_phone.png")


def length_of_line(line):
    length = 0
    for i, p in enumerate(line):
        if i > 0:
            length += Gps.get_distance(line[i - 1], p)
    return round(length, 4)

def distance_to_nominal(gps, nominal_fn, show=True):
    rtk_line = [d['rtk_loc'] for d in gps]
    phone_line = [d['phone_loc'] for d in gps]
    nominal_line = read_file(nominal_fn)

    nominal_line = LineString(nominal_line)
    counter = 0

    df_gps = {
        'time': [d['time_since_start'] for d in gps],
        'RTK': [],
        'Phone': []
    }

    for point in rtk_line:
        p = Point(point)
        np = nominal_line.interpolate(nominal_line.project(p))
        # * 100 to get cm
        d = Gps.get_distance([np.x, np.y], point) * 100
        df_gps['RTK'].append(d)
        counter += 1

    for point in phone_line:
        p = Point(point)
        np = nominal_line.interpolate(nominal_line.project(p))
        d = Gps.get_distance([np.x, np.y], point)
        df_gps['Phone'].append(d)
        counter += 1

    df = pd.DataFrame(df_gps)

    mean_rtk = st.mean(df_gps['RTK'])
    mean_phone = st.mean(df_gps['Phone'])

    # Print Histogram
    fig = px.line(df, y='RTK', x='time', range_y=[0, 50], labels={'time': 'Time since start (s)', 'RTK': 'Distance to nominal (cm)'},
                  title='Distance to nominal line')
    fig.add_hline(y=mean_rtk, line_dash='dot', line_color='blue',
                  annotation_text=f"Mean: {round(mean_rtk, 2)}cm", annotation_position='top right')
    fig2 = px.line(df, y='Phone', x='time', range_y=[0, 5], labels={'time': 'Time since start (s)', 'Phone': 'Distance to nominal (m)'},
                  title='Distance to nominal line')
    fig2.add_hline(y=mean_phone, line_dash='dot', line_color='blue',
                  annotation_text=f"Mean: {round(mean_phone, 2)}m", annotation_position='top right')

    fig.update_layout(title_x=.5, title_y=.93)

    if show:
        fig.show()
        fig2.show()
    fig.write_image(f"images/{gps[0]['name']}/{gps[0]['name']}_nominal_distance.png")

def straightness(gps, nominal_fn, show=True):
    length_phone = length_of_line([d['phone_loc'] for d in gps])
    length_rtk = length_of_line([d['rtk_loc'] for d in gps])
    length_nominal = length_of_line(read_file(nominal_fn))

    s_phone = length_phone / length_nominal
    s_rtk = length_rtk / length_nominal
    print(length_rtk)
    print(length_phone)
    print(length_nominal)

    return s_phone, s_rtk

def deviation_heading(data, nominal_fn, show=True):
    nominal = read_file(nominal_fn)

    target_heading = Gps.get_direction(nominal[0], nominal[1])

    df_data = {
        'time': [],
        'deviation': []
    }

    for d in data:
        df_data['deviation'].append(Gps.angle_difference(target_heading, d['c_heading']))
        df_data['time'].append(d['time_since_start'])

    df = pd.DataFrame(df_data)

    fig = px.line(df, y='deviation', x='time', labels={'time': 'Time since start (s)', 'deviation': 'Deviation (°)'},
                      title='Deviation from target heading')

    fig.update_layout(title_x=.5, title_y=.93)
    if show:
        fig.show()
    fig.write_image(f"images/{data[0]['name']}/{data[0]['name']}_deviation.png")


if __name__ == '__main__':
    nominal_fn = 'geojson/gps_straight_nominal.geojson'
    nominal_short_fn = 'geojson/gps_straight_nominal_short.geojson'
    data1 = dp.autonomous_data_parser('data/data1.txt')
    data2 = dp.autonomous_data_parser('data/data2.txt')
    data3 = dp.autonomous_data_parser('data/data3.txt')
    data4 = dp.autonomous_data_parser('data/data4.txt')
    data5 = dp.autonomous_data_parser('data/data5.txt')
    data6 = dp.autonomous_data_parser('data/data6.txt')
    data7 = dp.autonomous_data_parser('data/data7.txt')
    data_straight = dp.autonomous_data_parser('data/data_straight.txt')
    gps_straight = dp.gps_data_parser('gps/gps_straight.log')

    show_fig = False
    """
    distance_from_t_location(data1, show_fig)
    turn_on_spot_angle(data1, show_fig)
    engine_values(data1, show_fig)
    """
    distance_from_t_location(data2, show_fig)
    turn_on_spot_angle(data2, show_fig)
    engine_values(data2, show_fig)
    """    
    distance_from_t_location(data3, show_fig)
    turn_on_spot_angle(data3, show_fig)
    engine_values(data3, show_fig)
    distance_from_t_location(data4, show_fig)
    turn_on_spot_angle(data4, show_fig)
    engine_values(data4, show_fig)
    distance_from_t_location(data5, show_fig)
    turn_on_spot_angle(data5, show_fig)
    engine_values(data5, show_fig)
    distance_from_t_location(data6, show_fig)
    turn_on_spot_angle(data6, show_fig)
    engine_values(data6, show_fig)
    distance_from_t_location(data7, show_fig)
    turn_on_spot_angle(data7, show_fig)
    engine_values(data7, show_fig)
    """
    distance_from_t_location(data_straight, show_fig)
    turn_on_spot_angle(data_straight, show_fig)
    engine_values(data_straight, show_fig)
    pid_angles(data_straight, show_fig)
    deviation_heading(data_straight, nominal_fn, show_fig)
    distance_phone_rtk(gps_straight, show_fig)
    distance_to_nominal(gps_straight, nominal_fn, True)
    gj_phone = fh.create_geojson([p['phone_loc'] for p in gps_straight], 'gps_straight_phone')
    gj_rtk = fh.create_geojson([p['rtk_loc'] for p in gps_straight], 'gps_straight_rtk')
    s_phone, s_rtk = straightness(gps_straight, nominal_short_fn)
    print("----------------------------- Straightness -----------------------------")
    print(f"\tPhone:\t{s_phone},\t\tRTK:\t{s_rtk}")

    with open(f"geojson/{gj_phone['name']}.geojson", 'w') as out:
        json.dump(gj_phone, out)

    with open(f"geojson/{gj_rtk['name']}.geojson", 'w') as out:
        json.dump(gj_rtk, out)
