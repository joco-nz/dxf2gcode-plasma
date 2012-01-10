#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
#
#dxf2gcode_b02_point
#Programmers:   Christian Kohlöffel
#               Vinzenz Schulz
#
#Distributed under the terms of the GPL (GNU Public License)
#
#dxf2gcode is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


from Core.Point import Point

from PyQt4 import QtCore, QtGui

import logging
logger=logging.getLogger("Gui.RouteText") 

class RouteText(QtGui.QGraphicsItem):
    def __init__(self, text='S', startp=Point(x=0.0,y=0.0),):
        """
        Initialisation of the class.
        """
        QtGui.QGraphicsItem.__init__(self) 
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
        
        self.sc=1.0
        self.startp = QtCore.QPointF(startp.x,-startp.y)
        
        pencolor=QtGui.QColor(0, 200, 255)
        self.brush=QtGui.QColor(0, 100, 255)
        
        self.pen=QtGui.QPen(pencolor, 1, QtCore.Qt.SolidLine,
                QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.pen.setCosmetic(True)

        #self.setFont(QtGui.QFont("Arial",10/self.sc))
        #self.setTextWidth(150)
        #self.setPos(QtCore.QPointF(startp.x,-startp.y))
        #self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        
        #ItemIgnoresTransformations ( using
        
        #self.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations, True)
        
        self.path=QtGui.QPainterPath()
        self.path.addText(QtCore.QPointF(0, 0),
                          QtGui.QFont("Arial",8/self.sc),
                          text)

   
    def updatepos(self,startp):
        """
        Method to update the position after optimisation of the shape.
        """
        self.startp = QtCore.QPointF(startp.x,-startp.y)
        self.update
        
               
    def paint(self, painter, option, widget=None):
        """
        Method for painting the arrow.
        """
        demat=painter.deviceTransform()
        self.sc=demat.m11()
        #self.setScale(1/self.sc)
        
        #self.resetTransform()
        
        
        #logger.debug('Scale: %s' %self.scale())
        
        painter.setClipRect(self.boundingRect())
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.scale(1/self.sc,1/self.sc)
        painter.translate(self.startp.x()*(self.sc),
                          self.startp.y()*(self.sc))
        
        painter.drawPath(self.path)

        
    def boundingRect(self):
        """ 
        Required method for painting. Inherited by Painterpath
        @return: Gives the Bounding Box
        """ 
        rect=self.path.boundingRect().getRect()
 
        logger.debug(rect)
        logger.debug(self.startp)
       
        newrect= QtCore.QRectF(self.startp.x()+rect[0]/self.sc,
                             self.startp.y()+rect[1]/self.sc,
                             rect[2]/self.sc,
                             rect[3]/self.sc)
        
        logger.debug(newrect)
        
        return newrect
        
#        extra=15/self.sc
#        return QtCore.QRectF(self.startp,
#                              QtCore.QSizeF(0,0)).normalized().adjusted(-extra, -extra, extra, extra)
    