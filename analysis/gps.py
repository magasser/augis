from numpy import arctan2, sin, cos, degrees, sqrt
import re
import math
from serial.serialutil import SerialException
import logging as log


class Gps:
    RTK = 'rtk'
    PHONE = 'phone'
    DRG = 'drg'

    LAT = 0
    LNG = 1

    WAIT = 3

    """
    Convert the degree coordinates to the decimal format

    :param coordinates: The degree coordinates as string
    :returns: The decimals formatted coordinates
    """
    @staticmethod
    def convert_coordinates_to_decimal(coordinates):
        coord_array = re.split('[°\'"]+', coordinates)
        return float(coord_array[0]) + float(coord_array[1]) / 60 + float(coord_array[2]) / 3600

    """
    Convert gps data from GPGGA to JSON format.
    
    :param data: GPGGA data
    """
    @staticmethod
    def convert_gpgga_to_json(data):
        fields = data.split(',')
        qi = ['No GPS data', 'Uncorrected', 'Differentially corrected', 'RTK Fix', 'RTK Float']

        lat = str(float(fields[2][0:2]) + float(fields[2][2:])/60)
        lng = str(float(fields[4][0:3]) + float(fields[4][3:])/60)

        return {
            'name': fields[0][1:],
            'timestamp': fields[1],
            'latitude': lat,
            'longitude': lng,
            'quality_indicator': qi[int(fields[6])],
            'nr_of_satellites': fields[7],
            'altitude': fields[9]
        }

    """
    Calculate the direction from two given points.
    
    :param pos:     The start point
    :param dest:    The destination point 
    :returns:       The direction in degrees (0-360)
    """
    @staticmethod
    def get_direction(pos, dest):
        d_lon = Gps.degrees_to_radians(dest[Gps.LNG] - pos[Gps.LNG])
        lat_dest = Gps.degrees_to_radians(dest[Gps.LAT])
        lat_pos = Gps.degrees_to_radians(pos[Gps.LAT])

        x = cos(lat_dest) * sin(d_lon)
        y = cos(lat_pos) * sin(lat_dest) - sin(lat_pos) * cos(lat_dest) * cos(d_lon)

        bearing = arctan2(x, y)

        return (degrees(bearing) + 360) % 360

    """
    Calculate the distance between two gps points.
    
    :param p1: first point
    :param p2: second point
    :returns: distance between points in meters
    """
    @staticmethod
    def get_distance(p1, p2):
        radius = 6371
        d_lat = Gps.degrees_to_radians(p1[Gps.LAT] - p2[Gps.LAT])
        d_lon = Gps.degrees_to_radians(p1[Gps.LNG] - p2[Gps.LNG])

        lat_p1 = Gps.degrees_to_radians(p1[Gps.LAT])
        las_p2 = Gps.degrees_to_radians(p2[Gps.LAT])

        a = sin(d_lat / 2) * sin(d_lat / 2) + sin(d_lon / 2) * sin(d_lon / 2) * cos(lat_p1) * cos(las_p2)

        c = 2 * arctan2(sqrt(a), sqrt(1 - a))
        return radius * c * 1000

    """
    Calculate the absolute difference between two angles in a circle.
    
    :param a1: first angle
    :param a2: second angle
    :returns: absolute difference between the two angles
    """
    @staticmethod
    def angle_difference(a1, a2):
        return ((a2 - a1 + 540) % 360) - 180

    """
    Convert degrees to radians.
    
    :param deg: A number of degrees
    :returns:       The radians from passed degrees
    """
    @staticmethod
    def degrees_to_radians(deg):
        return deg * math.pi / 180

    """
    Calculate the actual speed
    
    :param distance:    The actual driven distance
    :param time:        The actual driven time
    :returns:           The actual speed of the AUGIS
    """
    @staticmethod
    def calculate_speed(distance, time):
        return distance / time

