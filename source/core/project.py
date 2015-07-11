# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2015
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

import logging
import hashlib
import re

from core.point import Point
from globals.d2gexceptions import VersionMismatchError
import globals.globals as g

from globals.six import text_type
import globals.constants as c
if c.PYQT5notPYQT4:
    from PyQt5 import QtCore
else:
    from PyQt4 import QtCore

logger = logging.getLogger("Core.Project")

class Project(object):
    header = "# +~+~+~ DXF2GCODE project file V%s ~+~+~+"
    version = 1.0

    def __init__(self, parent):
        self.parent = parent

        self.file = None
        self.point_tol = None
        self.fitting_tol = None
        self.scale = None
        self.rot = None
        self.wpzero_x = None
        self.wpzero_y = None
        self.split_lines = None
        self.aut_cut_com = None
        self.machine_type = None

        self.layers = None
        self.shapes = None

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return text_type(QtCore.QCoreApplication.translate('Project',
                                                           string_to_translate))

    def get_hash(self, shape):
        reversed = False
        if not shape.cw:
            reversed = True
            shape.reverse()
        geos = [str(geo) for geo in shape.geos.abs_iter()]
        if reversed:
            shape.reverse()
        return hashlib.sha1(''.join(sorted(geos)).encode('utf-8')).hexdigest()

    def export(self):
        # TODO Custom GCode actions still to be added, and order of shapes
        pyCode = Project.header % str(Project.version) + '''
d2g.file = "''' + self.parent.filename + '''"
d2g.point_tol = ''' + str(g.config.point_tolerance) + '''
d2g.fitting_tol = ''' + str(g.config.fitting_tolerance) + '''
d2g.scale = ''' + str(self.parent.cont_scale) + '''
d2g.rot = ''' + str(self.parent.cont_rotate) + '''
d2g.wpzero_x = ''' + str(self.parent.cont_dx) + '''
d2g.wpzero_y = ''' + str(self.parent.cont_dy) + '''
d2g.split_lines = ''' + str(g.config.vars.General['split_line_segments']) + '''
d2g.aut_cut_com = ''' + str(g.config.vars.General['automatic_cutter_compensation']) + '''
d2g.machine_type = "''' + g.config.machine_type + '''"
d2g.layers = ''' + str({layer.name: {'tool_nr': layer.tool_nr,
                                     'diameter': layer.tool_diameter,
                                     'speed': layer.speed,
                                     'start_radius': layer.start_radius,
                                     'retract': layer.axis3_retract,
                                     'safe_margin': layer.axis3_safe_margin} for layer in self.parent.layerContents})

        shapes = {}
        for shape in self.parent.shapes:
            stpoint = shape.get_start_end_points(True)
            hash_ = self.get_hash(shape)
            if hash_ in shapes:
                logger.warning(self.tr("Shape %s clashes with an appearing identical shape") % shape.nr)
                continue  # no point in overriding the shape parameters. Since we don't know with which shape
                #  it clashes, this is more informative - this shape might not get the parameters which you expected.
            shapes[hash_] = {'cut_cor': shape.cut_cor,
                             'cw': shape.cw,
                             'send_to_TSP': shape.send_to_TSP,
                             'disabled': shape.disabled,
                             'start_mill_depth': shape.axis3_start_mill_depth,
                             'slice_depth': shape.axis3_slice_depth,
                             'mill_depth': shape.axis3_mill_depth,
                             'f_g1_plane': shape.f_g1_plane,
                             'f_g1_depth': shape.f_g1_depth,
                             'start_x': stpoint.x,
                             'start_y': stpoint.y}

        pyCode += '\nd2g.shapes = ' + str(shapes)
        return pyCode

    def load(self, content):
        match = re.match(Project.header.replace('+', '\+') % r'(\d+\.\d+)', content)
        if not match:
            raise Exception('Incorrect project file')
        version = float(match.groups()[0])
        if version != Project.version:
            raise VersionMismatchError(match.group(), Project.version)

        exec(content, globals(), {'d2g': self})
        self.parent.filename = self.file
        g.config.point_tolerance = self.point_tol
        g.config.fitting_tolerance = self.fitting_tol
        self.parent.cont_scale = self.scale
        self.parent.cont_rotate = self.rot
        self.parent.cont_dx = self.wpzero_x
        self.parent.cont_dy = self.wpzero_y
        g.config.vars.General['split_line_segments'] = self.split_lines
        g.config.vars.General['automatic_cutter_compensation'] = self.aut_cut_com
        g.config.machine_type = self.machine_type

        self.parent.connectToolbarToConfig()
        self.parent.load(False)

        for layer in self.parent.layerContents:
            if layer.name in self.layers:
                parent_layer = self.layers[layer.name]
                layer.tool_nr = parent_layer['tool_nr']
                layer.tool_diameter = parent_layer['diameter']
                layer.speed = parent_layer['speed']
                layer.start_radius = parent_layer['start_radius']

                layer.axis3_retract = parent_layer['retract']
                layer.axis3_safe_margin = parent_layer['safe_margin']

        for shape in self.parent.shapes:
            hash_ = self.get_hash(shape)
            if hash_ in self.shapes:
                parent_shape = self.shapes[hash_]
                shape.cut_cor = parent_shape['cut_cor']
                shape.send_to_TSP = parent_shape['send_to_TSP']
                shape.disabled = parent_shape['disabled']
                shape.axis3_start_mill_depth = parent_shape['start_mill_depth']
                shape.axis3_slice_depth = parent_shape['slice_depth']
                shape.axis3_mill_depth = parent_shape['mill_depth']
                shape.f_g1_plane = parent_shape['f_g1_plane']
                shape.f_g1_depth = parent_shape['f_g1_depth']

                if parent_shape['cw'] != shape.cw:
                    shape.reverse()
                shape.setNearestStPoint(Point(parent_shape['start_x'], parent_shape['start_y']))

        self.parent.plot()
