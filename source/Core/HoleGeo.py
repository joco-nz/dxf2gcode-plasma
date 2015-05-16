############################################################################
#
#   Copyright (C) 2014-2015
#    Robert Lichtenberger
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

import logging
from copy import deepcopy
from math import pi


logger = logging.getLogger("Core.HoleGeo")


class HoleGeo(object):
    """
    HoleGeo represents drilling holes.
    """
    def __init__(self, Ps):
        """
        Standard Method to initialise the HoleGeo
        """
        self.Ps = Ps

        self.topLeft = None
        self.bottomRight = None

    def __deepcopy__(self, memo):
        return HoleGeo(deepcopy(self.Ps, memo))

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nHoleGeo at (%s) " % self.Ps

    def reverse(self):
        """
        Reverses the direction.
        """
        pass

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent.
        @param parent: The parent of the geometry (EntityContentClass)
        @return: A new HoleGeoClass will be returned.
        """
        Ps = self.Ps.rot_sca_abs(parent=parent)

        return HoleGeo(Ps)

    def get_start_end_points(self, direction, parent=None):
        """
        Returns the start/end Point and its direction
        @param direction: 0 to return start Point and 1 to return end Point
        @return: a list of Point and angle
        """
        return self.Ps.rot_sca_abs(parent=parent), 0

    def make_path(self, caller, drawHorLine):
        abs_geo = self.make_abs_geo(caller.parentEntity)

        radius = caller.parentLayer.tool_diameter / 2
        segments = 30
        Ps = abs_geo.Ps.get_arc_point(0, radius)
        self.topLeft = deepcopy(Ps)
        self.bottomRight = deepcopy(Ps)
        for i in range(1, segments + 1):
            ang = i * 2 * pi / segments
            Pe = abs_geo.Ps.get_arc_point(ang, radius)
            drawHorLine(Ps, Pe, caller.axis3_start_mill_depth)
            drawHorLine(Ps, Pe, caller.axis3_mill_depth)
            self.topLeft.detTopLeft(Pe)
            self.bottomRight.detBottomRight(Pe)
            Ps = Pe

    def Write_GCode(self, parent=None, PostPro=None):
        """
        Writes the GCODE for a Hole.
        @param parent: This is the parent LayerContentClass
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        return PostPro.make_print_str("(Drilled hole)%nl")
