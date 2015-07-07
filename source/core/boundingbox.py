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
from __future__ import division

from math import sqrt, sin, cos, atan2
from copy import deepcopy

from core.point import Point

import logging
logger = logging.getLogger("core.boundingbox")

class BoundingBox:
    """ 
    Bounding Box Class. This is the standard class which provides all std. 
    Bounding Box methods.
    """
    def __init__(self, Pa=Point(0, 0), Pe=Point(0, 0), hdl=[]):
        """ 
        Standard method to initialize the class
        """

        self.Pa = Pa
        self.Pe = Pe


    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """
        s = ("\nPa : %s" % (self.Pa)) + \
           ("\nPe : %s" % (self.Pe))
        return s

    def joinBB(self, other):
        """
        Joins two Bounding Box Classes and returns the new one
        @param other: The 2nd Bounding Box
        @return: Returns the joined Bounding Box Class
        """

        if type(self.Pa) == type(None) or type(self.Pe) == type(None):
            return BoundingBox(deepcopy(other.Pa), deepcopy(other.Pe))

        xmin = min(self.Pa.x, other.Pa.x)
        xmax = max(self.Pe.x, other.Pe.x)
        ymin = min(self.Pa.y, other.Pa.y)
        ymax = max(self.Pe.y, other.Pe.y)

        return BoundingBox(Pa=Point(xmin, ymin), Pe=Point(xmax, ymax))

    def hasintersection(self, other=None, tol=eps):
        """
        Checks if the two bounding boxes have an intersection
        @param other: The 2nd Bounding Box
        @return: Returns true or false
        """
        if isinstance(other, Point):
            return self.pointisinBB(other, tol)
        elif isinstance(other, BoundingBox):
            x_inter_pos = (self.Pe.x + tol > other.Pa.x) and \
            (self.Pa.x - tol < other.Pe.x)
            y_inter_pos = (self.Pe.y + tol > other.Pa.y) and \
            (self.Pa.y - tol < other.Pe.y)

            return x_inter_pos and y_inter_pos
        else:
            logger.warning("Unsupported Instance: %s" % other.type)

    def pointisinBB(self, Point=Point(), tol=eps):
        """
        Checks if the Point is within the bounding box
        @param Point: The Point which shall be ckecke
        @return: Returns true or false
        """
        x_inter_pos = (self.Pe.x + tol > Point.x) and \
        (self.Pa.x - tol < Point.x)
        y_inter_pos = (self.Pe.y + tol > Point.y) and \
        (self.Pa.y - tol < Point.y)
        return x_inter_pos and y_inter_pos