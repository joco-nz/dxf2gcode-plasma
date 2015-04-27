############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
#    Jean-Paul Schouwstra
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from math import sqrt
from math import cos, sin, degrees
from copy import deepcopy
import logging

from PyQt5 import QtCore

import Global.Globals as g
from Core.Point import Point
from Core.LineGeo import LineGeo
from Core.ArcGeo import ArcGeo


logger = logging.getLogger("Core.Shape")


class Shape(object):
    """
    The Shape Class includes all plotting, GUI functionality and export functions
    related to the Shapes.
    """
    def __init__(self, nr, closed,
                 cut_cor, length,
                 parentEntity,
                 geos):
        """
        Standard method to initialize the class
        @param nr: The number of the shape. Starting from 0 for the first one
        @param closed: Gives information about the shape, when it is closed this
        value becomes 1
        @param cut_cor: Gives the selected Curring Correction of the shape
        (40=None, 41=Left, 42= Right)
        @param length: The total length of the shape including all geometries
        @param parent: The parent EntitieContent Class of the shape
        @param geow: The list with all geometries included in the shape
        @param axis3_mill_depth: Optional parameter for the export of the shape.
        If this parameter is None the mill_depth of the parent layer will be used.
        """
        self.type = "Shape"
        self.nr = nr
        self.closed = closed
        self.cut_cor = 40
        self.lenght = length
        self.parentEntity = parentEntity
        self.parentLayer = None
        self.geos = geos

        self.send_to_TSP = g.config.vars.Route_Optimisation['default_TSP']

        self.disabled = False
        self.allowedToChange = True

        # preset defaults
        self.axis3_start_mill_depth = g.config.vars.Depth_Coordinates['axis3_start_mill_depth']
        self.axis3_slice_depth = g.config.vars.Depth_Coordinates['axis3_slice_depth']
        self.axis3_mill_depth = g.config.vars.Depth_Coordinates['axis3_mill_depth']
        self.f_g1_plane = g.config.vars.Feed_Rates['f_g1_plane']
        self.f_g1_depth = g.config.vars.Feed_Rates['f_g1_depth']

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\ntype:        %s" % self.type +\
               "\nnr:          %i" % self.nr +\
               "\nclosed:      %i" % self.closed +\
               "\ncut_cor:     %s" % self.cut_cor +\
               "\nlen(geos):   %i" % len(self.geos) +\
               "\ngeos:        %s" % self.geos

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return QtCore.QCoreApplication.translate("ShapeClass", string_to_translate, None)

    def contains_point(self, x, y):
        min_distance = float(0x7fffffff)
        p = (x, y)
        t = 0.0
        while t < 1.0:
            point = self.path.pointAtPercent(t)
            spline_point = (point.x(), point.y())
            distance = self.distance(p, spline_point)
            if distance < min_distance:
                min_distance = distance
            t += 0.01
        return min_distance

    def distance(self, p0, p1):
        a = p1[0] - p0[0]
        b = p1[1] - p0[1]
        return sqrt(a * a + b * b)

    def setDisable(self, flag=False):
        self.disabled = flag

    def isDisabled(self):
        return self.disabled

    def setToolPathOptimized(self, flag=False):
        self.send_to_TSP = flag

    def isToolPathOptimized(self):
        return self.send_to_TSP

    def AnalyseAndOptimize(self):
        logger.debug(self.tr("Analysing the shape for CW direction Nr: %s" % self.nr))
        # Optimization for closed shapes
        if self.closed:
            # Start value for the first sum
            start, dummy = self.geos[0].get_start_end_points(0)
            summe = 0.0
            for geo in self.geos:
                if isinstance(geo, LineGeo):
                    end, dummy = geo.get_start_end_points(1)
                    summe += (start.x + end.x) * (end.y - start.y) / 2
                    start = deepcopy(end)
                elif isinstance(geo, ArcGeo):
                    segments = int((abs(degrees(geo.ext)) // 90) + 1)
                    for i in range(segments):
                        ang = geo.s_ang + (i + 1) * geo.ext / segments
                        end = Point(geo.O.x + cos(ang) * abs(geo.r),
                                    geo.O.y + sin(ang) * abs(geo.r))
                        summe += (start.x + end.x) * (end.y - start.y) / 2
                        start = deepcopy(end)

            if summe > 0.0:
                self.reverse()
                logger.debug(self.tr("Had to reverse the shape to be cw"))

    def setNearestStPoint(self, stPoint):
        if self.closed:
            logger.debug(self.tr("Clicked Point: %s" % stPoint))
            start, dummy = self.geos[0].get_start_end_points(0, self.parentEntity)
            min_distance = start.distance(stPoint)

            logger.debug(self.tr("Old Start Point: %s" % start))

            min_geo_nr = 0
            for geo_nr in range(1, len(self.geos)):
                start, dummy = self.geos[geo_nr].get_start_end_points(0, self.parentEntity)

                if start.distance(stPoint) < min_distance:
                    min_distance = start.distance(stPoint)
                    min_geo_nr = geo_nr

            # Overwrite the geometries in changed order.
            self.geos = self.geos[min_geo_nr:len(self.geos)] + self.geos[0:min_geo_nr]

            start, dummy = self.geos[0].get_start_end_points(0, self.parentEntity)
            logger.debug(self.tr("New Start Point: %s" % start))

    def reverse(self):
        self.geos.reverse()
        for geo in self.geos:
            geo.reverse()

    def get_st_en_points(self, direction=None):
        start, start_ang = self.geos[0].get_start_end_points(0, self.parentEntity)
        end, end_ang = self.geos[-1].get_start_end_points(1, self.parentEntity)

        if direction is None:
            return start, end
        elif direction == 0:
            return start, start_ang
        elif direction == 1:
            return end, end_ang
