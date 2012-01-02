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


from math import sin, cos, acos, radians, pi
from Core.Point import Point

from PyQt4 import QtCore, QtGui

#Length of the cross.
dl = 0.2
DEBUG = 1
                                                
class Arrow(QtGui.QGraphicsLineItem):
    def __init__(self, startp, length, angle, 
                 color=QtCore.Qt.red,pencolor=QtCore.Qt.green,
                 dir=0):
        """
        Initialisation of the class.
        """
        self.sc=1
        super(Arrow, self).__init__()

        self.startp = QtCore.QPointF(startp.x,-startp.y)
        self.endp=QtCore.QPointF(startp.x,-startp.y)
        self.length=length
        self.angle=angle
        self.dir=dir
        self.allwaysshow=False
        
        
        self.arrowHead = QtGui.QPolygonF()
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
        self.myColor=color
        self.pen=QtGui.QPen(pencolor, 1, QtCore.Qt.SolidLine,
                QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.arrowSize = 8.0
        
        self.pen.setCosmetic(True)
        
    def setSelected(self,flag=True):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        if self.allwaysshow:
            pass
        elif flag is True:
            self.show()
        else:
            self.hide()
        
        self.update(self.boundingRect())
        
    def reverseshape(self,startp,angle):
        """
        Method is called when the shape direction is changed and therefor the
        arrow gets new Point and direction
        @param startp: The new startpoint
        @param angle: The new angle of the arrow
        """
        self.startp=QtCore.QPointF(startp.x,-startp.y)
        self.angle=angle
        self.update(self.boundingRect())
        
    def setallwaysshow(self,flag=False):
        """
        If the directions shall be allwaysshown the paramerter will be set and 
        all paths will be shown.
        @param flag: The flag to enable or disable Selection
        """
        self.allwaysshow=flag
        if flag is True:
            self.show()
        elif flag is True and self.isSelected():
            self.show()
        else:
            self.hide()
        self.update(self.boundingRect())
            
               
    def paint(self, painter, option, widget=None):
        """
        Method for painting the arrow.
        """

        demat=painter.deviceTransform()
        self.sc=demat.m11()
        
        dx = cos(radians(self.angle)) * self.length/self.sc
        dy = sin(radians(self.angle)) * self.length/self.sc
        
        self.endp=QtCore.QPointF(self.startp.x()+dx,self.startp.y()-dy)
        
        
        arrowSize=self.arrowSize/self.sc
        #print(demat.m11())
       
    
        painter.setPen(self.pen)
        painter.setBrush(self.myColor)

        centerLine = QtCore.QLineF(self.startp, self.endp)
        

        
        self.setLine(QtCore.QLineF(self.endp,self.startp))
        line = self.line()

        angle = acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = (pi * 2.0) - angle

        if self.dir==0:
            arrowP1 = line.p1() + QtCore.QPointF(sin(angle + pi / 3.0) * arrowSize,
                                            cos(angle + pi / 3) * arrowSize)
            arrowP2 = line.p1() + QtCore.QPointF(sin(angle + pi - pi / 3.0) * arrowSize,
                                            cos(angle + pi - pi / 3.0) * arrowSize)
            self.arrowHead.clear()
            for Point in [line.p1(), arrowP1, arrowP2]:
                self.arrowHead.append(Point)
                
        else:
            arrowP1 = line.p2() - QtCore.QPointF(sin(angle + pi / 3.0) * arrowSize,
                                            cos(angle + pi / 3) * arrowSize)
            arrowP2 = line.p2() - QtCore.QPointF(sin(angle + pi - pi / 3.0) * arrowSize,
                                            cos(angle + pi - pi / 3.0) * arrowSize)
            self.arrowHead.clear()
            for Point in [line.p2(), arrowP1, arrowP2]:
                self.arrowHead.append(Point)

        

        painter.drawLine(line)
        painter.drawPolygon(self.arrowHead)


    def boundingRect(self):
        """
        Override inherited function to enlarge selection of Arrow to include all
        @param flag: The flag to enable or disable Selection
        """
        
        #print("super: %s" %super(Arrow, self).boundingRect())
        arrowSize=self.arrowSize/self.sc
        extra = (self.pen.width() + arrowSize) / 2.0
      
        return QtCore.QRectF(self.startp,
                              QtCore.QSizeF(self.endp.x()-self.startp.x(),
                                             self.endp.y()-self.startp.y())).normalized().adjusted(-extra, -extra, extra, extra)


