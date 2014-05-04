# -*- coding: utf-8 -*-

############################################################################
#   
#   Copyright (C) 2008-2014
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

from PyQt4 import QtCore, QtGui

#Length of the cross.
dl = 0.2
DEBUG = 1

class WpZero(QtGui.QGraphicsItem):
    """
    class WpZero
    """
    def __init__(self, center, color=QtCore.Qt.gray):
        self.sc = 1
        super(WpZero, self).__init__()

        self.center = center
        self.allwaysshow = False
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
        self.color = color
        self.pen = QtGui.QPen(self.color, 1, QtCore.Qt.SolidLine,
                  QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.pen.setCosmetic(True)
        
        self.diameter = 20.0

    def contains_point(self, x, y):
        """
        TODO - check arguments as this returns a constant value
        """
        min_distance = float(0x7fffffff)
        return min_distance
 
    def setSelected(self, flag=True):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        pass
        
    def setallwaysshow(self, flag=False):
        """
        If the directions shall be allwaysshown the paramerter will
        be set and all paths will be shown.
        @param flag: The flag to enable or disable Selection
        """
        self.allwaysshow = flag
        if flag is True:
            self.show()
        else:
            self.hide()
        self.update(self.boundingRect())
               
    def paint(self, painter, option, widget=None):
        """
        paint()
        """
        demat = painter.deviceTransform()
        self.sc = demat.m11()
        
        diameter1 = self.diameter / self.sc
        diameter2 = (self.diameter-4) / self.sc
       
        rectangle1 = QtCore.QRectF(-diameter1/2, -diameter1/2, diameter1, diameter1)
        rectangle2 = QtCore.QRectF(-diameter2/2, -diameter2/2, diameter2, diameter2)
        startAngle1 = 90 * 16
        spanAngle = 90 * 16
        startAngle2 = 270 * 16
    
        painter.drawEllipse(rectangle1)
        painter.drawEllipse(rectangle2)
        painter.drawPie(rectangle2, startAngle1, spanAngle)

        painter.setBrush(self.color)
        painter.drawPie(rectangle2, startAngle2, spanAngle)
        
    def boundingRect(self):
        """
        Override inherited function to enlarge selection of Arrow to include all
        @param flag: The flag to enable or disable Selection
        """
        diameter = self.diameter / self.sc
        return QtCore.QRectF(-20, -20.0, 40.0, 40.0)
        
