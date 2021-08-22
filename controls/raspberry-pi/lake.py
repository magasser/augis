"""
Authors: Manuel Gasser, Julian Haldimann
Created: 20.03.2021
Last Modified: 21.03.2021
"""

from shapely.geometry.linestring import LineString
from shapely.geometry.point import Point

import file_handler as fh


class Lake:

    def __init__(self, lake_geojson):
        self.exterior, self.interior, self.obstacles = fh.parse_lake_geojson(lake_geojson)

    """
    Function checks if a given geometry is inside the exterior polygon
    of the lake.
    
    :param geometry: to check if it is inside
    :returns: true if it is inside, false otherwise
    """

    def contains(self, geometry):
        return self.exterior.contains(geometry)

    """
    Function checks if a straight line between the current point
    and next point will intersect with the exterior polygon of
    the lake.
    
    :param cp: current point
    :param np: next point
    :returns: true if there is no intersection, false otherwise
    """

    def no_intersection(self, cp, np):
        line = LineString((cp, np))
        return not self.exterior.intersects(line)

    """
    Function calculates new route from current point to next point which
    does not intersect with the exterior polygon.
    
    This algorithm is inspired by the Weiler Atherton algorithm 
    for polygon clipping.
    
    :param cp: current point
    :param np: next point
    :return: calculated route or None if route cannot be calculated
    """

    def calc_new_route(self, cp, np):
        # Return none if either point is not inside the exterior polygon
        if not self.contains(cp) or not self.contains(np):
            return None
        # Create line from points
        line = LineString((cp, np))
        # Get intersection points between line and exterior polygon
        ints = line.intersection(self.exterior)
        # Get intersection points closest to cp and np
        int_points = [Point(ints[0].coords[1]), Point(ints[len(ints) - 1].coords[0])]
        # Points of the exterior and interior polygons
        exterior_points = self.exterior.exterior.coords
        interior_points = self.interior.exterior.coords
        # Init loop values
        c = 0
        index_i = -1
        index_o = -1
        # Loop through all points to find between which points the intersection points are
        for i, j in zip(exterior_points, exterior_points[1:]):
            # Check if line between points is close to intersection points
            if LineString((i, j)).distance(int_points[0]) < 1e-8:
                index_i = c
            if LineString((i, j)).distance(int_points[1]) < 1e-8:
                index_o = c
            c += 1
        # Get minimum distance between intersection point indices
        d = int(Lake.__min_dist_indices(index_i, index_o, len(exterior_points)))
        # Create new route with the indices along the interior polygon of the lake
        if d > 0:
            route = [interior_points[(index_i + i) % len(interior_points)] for i in range(1, d + 1)]
        else:
            route = [interior_points[(index_i - i) % len(interior_points)] for i in range(0, -d)]
        # Add nex point to created route
        route.append(np)

        return route

    """
    Function calculates minimum distance between indices of an array.
    
    :param i1: first index
    :param i2: second index
    :param l: length of the array
    :returns: minimum distance between indices, positive or negative
    """

    @staticmethod
    def __min_dist_indices(i1, i2, l):
        return ((i2 - i1 + 1.5 * l) % l) - l / 2
