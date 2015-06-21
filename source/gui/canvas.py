# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2011-2015
#    Christian Kohlöffel
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


"""
This Canvas function can be called as any class.
Since it will pretend to be, depending on the settings,
to be the canvas3d or canvas2d class
"""
def Canvas(parent=None):
    from gui.canvas2d import MyGraphicsView
    return MyGraphicsView(parent)

def CanvasObject():
    from PyQt4.QtGui import QGraphicsView
    return QGraphicsView

class CanvasBase(CanvasObject()):
    def __init__(self, parent=None):
        super(CanvasBase, self).__init__(parent)

        self.isMultiSelect = False
