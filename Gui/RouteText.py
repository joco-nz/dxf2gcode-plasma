# -*- coding: utf-8 -*-

############################################################################
#   
#   Copyright (C) 2008-2014
#    Christian Kohlöffel
#    Vinzenz Schulz
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


from Core.Point import Point

from PyQt4 import QtCore, QtGui

import logging
logger = logging.getLogger("Gui.RouteText") 

class RouteText(QtGui.QGraphicsItem):
    def __init__(self, text='S', startp=Point(x=0.0, y=0.0),):
        """
        Initialisation of the class.
        """
        QtGui.QGraphicsItem.__init__(self) 
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
        
        self.text = text
        self.sc = 1.0
        self.startp = QtCore.QPointF(startp.x, -startp.y)
        
        pencolor = QtGui.QColor(0, 200, 255)
        self.brush = QtGui.QColor(0, 100, 255)
        
        self.pen = QtGui.QPen(pencolor, 1, QtCore.Qt.SolidLine,
                     QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.pen.setCosmetic(True)

        self.path = QtGui.QPainterPath()
        self.path.addText(QtCore.QPointF(0, 0),
                          QtGui.QFont("Arial", 10/self.sc),
                          self.text)

   
    def updatepos(self, startp):
        """
        Method to update the position after optimisation of the shape.
        """
        self.prepareGeometryChange()
        self.startp = QtCore.QPointF(startp.x, -startp.y)
      
    def paint(self, painter, option, widget=None):
        """
        Method for painting the arrow.
        """
        demat = painter.deviceTransform()
        self.sc = demat.m11()

        
        #painter.setClipRect(self.boundingRect())
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.scale(1/self.sc, 1/self.sc)
        painter.translate(self.startp.x()*(self.sc),
                          self.startp.y()*(self.sc))
        
        painter.drawPath(self.path)
        
    def shape(self):
        """ 
        Reimplemented function to select outline only.
        @return: Returns the Outline only
        """ 
        logger.debug("Hier sollte ich nicht sein")
        return super(RouteText, self).shape()
    
    def boundingRect(self):
        """ 
        Required method for painting. Inherited by Painterpath
        @return: Gives the Bounding Box
        """ 
        rect = self.path.boundingRect().getRect()
 
        newrect = QtCore.QRectF(self.startp.x()+rect[0]/self.sc,
                             self.startp.y()+rect[1]/self.sc,
                             rect[2]/self.sc,
                             rect[3]/self.sc)
        return newrect
