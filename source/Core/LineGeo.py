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

from __future__ import absolute_import
from math import sqrt
import copy


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

    def __deepcopy__(self, memo):
        return LineGeo(copy.deepcopy(self.Ps, memo),
                       copy.deepcopy(self.Pe, memo))

    def __str__(self):
        return "\nLineGeo" +\
               "\nPs:     %s" % self.Ps +\
               "\nPe:     %s" % self.Pe +\
               "\nlength: %0.5f" % self.length

    def to_short_string(self):
        return "(%f, %f) -> (%f, %f)" % (self.Ps.x, self.Ps.y, self.Pe.x, self.Pe.y)

    def reverse(self):
        self.Ps, self.Pe = self.Pe, self.Ps

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent.
        @param parent: The parent of the geometry (EntityContentClass)
        @return: A new LineGeoClass will be returned.
        """
        Ps = self.Ps.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)

        return LineGeo(Ps=Ps, Pe=Pe)

    def distance2point(self, point):
        """
        Returns the distance between a line and a given Point
        @param point: The Point which shall be checked
        @return: returns the distance to the Line
        """
        if self.Ps == self.Pe:
            return 1e10
        else:
            AE = self.Ps.distance(self.Pe)
            AP = self.Ps.distance(point)
            EP = self.Pe.distance(point)
            AEPA = (AE + AP + EP) / 2
            return abs(2 * sqrt(abs(AEPA * (AEPA - AE) *
                                    (AEPA - AP) * (AEPA - EP))) / AE)

    def get_start_end_points(self, direction, parent=None):
        if not direction:
            punkt = self.Ps.rot_sca_abs(parent=parent)
            punkt_e = self.Pe.rot_sca_abs(parent=parent)
            angle = punkt.norm_angle(punkt_e)
        else:
            punkt_a = self.Ps.rot_sca_abs(parent=parent)
            punkt = self.Pe.rot_sca_abs(parent=parent)
            angle = punkt.norm_angle(punkt_a)

        return punkt, angle
