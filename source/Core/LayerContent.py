############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
#    Jean-Paul Schouwstra
#    Robert Lichtenberger
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

import Global.Globals as g


class LayerContent(object):
    def __init__(self, nr, name, shapes):
        self.nr = nr
        self.name = name
        self.shapes = shapes

        # preset defaults
        self.axis3_retract = g.config.vars.Depth_Coordinates['axis3_retract']
        self.axis3_safe_margin = g.config.vars.Depth_Coordinates['axis3_safe_margin']

        # Use default tool 1 (always exists in config)
        self.tool_nr = 1
        self.tool_diameter = g.config.vars.Tool_Parameters['1']['diameter']
        self.speed = g.config.vars.Tool_Parameters['1']['speed']
        self.start_radius = g.config.vars.Tool_Parameters['1']['start_radius']

    def __cmp__(self, other):
        return self.LayerNr == other.LayerNr

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nLayerContent" +\
               "\nnr:     %i" % self.nr +\
               "\nname:   %s" % self.name +\
               "\nshapes: %s" % self.shapes
