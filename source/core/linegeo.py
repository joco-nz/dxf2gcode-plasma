# -*- coding: utf-8 -*-

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

from __future__ import division

from math import sqrt, pi
from copy import deepcopy

from core.point import Point
from core.boundingbox import BoundingBox
#from core.arcgeo import ArcGeo

import logging
logger = logging.getLogger("core.linegeo")

eps= 1e-12


class LineGeo(object):
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """
    def __init__(self, Ps, Pe):
        """
        Standard Method to initialize the LineGeo.
        @param Ps: The Start Point of the line
        @param Pe: the End Point of the line
        """
        self.Ps = Ps
        self.Pe = Pe
        self.length = self.Ps.distance(self.Pe)

        self.calc_bounding_box()

        self.abs_geo = None

    def __deepcopy__(self, memo):
        return LineGeo(deepcopy(self.Ps, memo),
                       deepcopy(self.Pe, memo))

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return ("\nLineGeo(Ps=Point(x=%s ,y=%s),\n" % (self.Ps.x, self.Ps.y)) + \
               ("Pe=Point(x=%s, y=%s))" % (self.Pe.x, self.Pe.y))

    def save_v1(self):
        return "\nLineGeo" +\
               "\nPs:     %s" % self.Ps.save_v1() +\
               "\nPe:     %s" % self.Pe.save_v1() +\
               "\nlength: %0.5f" % self.length

    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        Ps = Point(x=min(self.Ps.x, self.Pe.x), y=min(self.Ps.y, self.Pe.y))
        Pe = Point(x=max(self.Ps.x, self.Pe.x), y=max(self.Ps.y, self.Pe.y))

        self.BB = BoundingBox(Ps=Ps, Pe=Pe)

    def get_start_end_points(self, start_point, angles=None):
        if start_point:
            if angles is None:
                return self.Ps
            elif angles:
                return self.Ps, self.Ps.norm_angle(self.Pe)
            else:
                return self.Ps, (self.Pe - self.Ps).unit_vector()
        else:
            if angles is None:
                return self.Pe
            elif angles:
                return self.Pe, self.Pe.norm_angle(self.Ps)
            else:
                return self.Pe, (self.Pe - self.Ps).unit_vector()

    def isHit(self, caller, xy, tol):
        return xy.distance2_to_line(self.Ps, self.Pe) <= tol**2

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent. This
        is done for rotating and scaling purposes
        """
        Ps = self.Ps.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)

        self.abs_geo = LineGeo(Ps=Ps, Pe=Pe)

    def make_path(self, caller, drawHorLine):
        drawHorLine(caller, self.Ps, self.Pe)

    def reverse(self):
        """
        Reverses the direction of the arc (switch direction).
        """
        self.Ps, self.Pe = self.Pe, self.Ps
        if self.abs_geo:
            self.abs_geo.reverse()

    def to_short_string(self):
        return "(%f, %f) -> (%f, %f)" % (self.Ps.x, self.Ps.y, self.Pe.x, self.Pe.y)

    def update_start_end_points(self, start_point, value):
        prv_ang = self.Ps.norm_angle(self.Pe)
        if start_point:
            self.Ps = value
        else:
            self.Pe = value
        new_ang = self.Ps.norm_angle(self.Pe)

        if 2 * abs(((prv_ang - new_ang) + pi) % (2 * pi) - pi) >= pi:
            # seems very unlikely that this is what you want - the direction changed (too drastically)
            self.Ps, self.Pe = self.Pe, self.Ps

        self.length = self.Ps.distance(self.Pe)

    def Write_GCode(self, PostPro):
        """
        Writes the GCODE for a Line.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        Ps = self.get_start_end_points(True)
        Pe = self.get_start_end_points(False)
        return PostPro.lin_pol_xy(Ps, Pe)










