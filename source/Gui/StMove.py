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


import Core.Globals as g
from Core.LineGeo import LineGeo
from Core.ArcGeo import ArcGeo

from PyQt4 import QtCore, QtGui

#Length of the cross.
dl = 0.2
DEBUG = 1

class StMove(QtGui.QGraphicsLineItem):
    def __init__(self, startp, angle, 
                 pencolor=QtCore.Qt.green,
                 cutcor=40,parent=None):
        """
        Initialisation of the class.
        """
        self.sc=1
        super(StMove, self).__init__()

        self.startp = startp
        self.endp=startp
        self.angle=angle
        self.cutcor=cutcor
        self.parent=parent
        self.allwaysshow=False
        self.geos=[]
        self.path=QtGui.QPainterPath()
        
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
        
        self.pen=QtGui.QPen(pencolor, 1, QtCore.Qt.SolidLine,
                QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.pen.setCosmetic(True)
        
        self.make_start_moves()
        self.make_papath()
        
        
    def make_start_moves(self):
        del(self.geos[:])

        #Einlaufradius und Versatz 
        start_rad = g.config.vars.Tool_Parameters['start_radius']
        start_ver = start_rad

        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad = g.config.vars.Tool_Parameters['diameter'] / 2
        
        #Errechnen des Startpunkts mit und ohne Werkzeug Kompensation        
        start=self.startp
        angle=self.angle
        
#        print start_rad
#        print tool_rad
#        print start
      
        if self.cutcor == 40:              
            self.geos.append(start)

        #Frï¿½sradiuskorrektur Links        
        elif self.cutcor == 41:
            #Mittelpunkts fï¿½r Einlaufradius
            Oein = start.get_arc_point(angle + 90, start_rad + tool_rad)
            #Startpunkts fï¿½r Einlaufradius
            Pa_ein = Oein.get_arc_point(angle + 180, start_rad + tool_rad)
            #Startwerts fï¿½r Einlaufgerade
            Pg_ein = Pa_ein.get_arc_point(angle + 90, start_ver)
            
            #Eintauchpunkt errechnete Korrektur
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.geos.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line = LineGeo(Pg_ein, Pa_ein)
            self.geos.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad = ArcGeo(Pa=Pa_ein, Pe=start, O=Oein, 
                               r=start_rad + tool_rad, direction=1)
            self.geos.append(start_rad)
            
        #Frï¿½sradiuskorrektur Rechts        
        elif self.cutcor == 42:

            #Mittelpunkt fï¿½r Einlaufradius
            Oein = start.get_arc_point(angle - 90, start_rad + tool_rad)
            #Startpunkt fï¿½r Einlaufradius
            Pa_ein = Oein.get_arc_point(angle + 180, start_rad + tool_rad)
            #IJ=Oein-Pa_ein
            #Startwerts fï¿½r Einlaufgerade
            Pg_ein = Pa_ein.get_arc_point(angle - 90, start_ver)
            
            #Eintauchpunkts errechnete Korrektur
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.geos.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line = LineGeo(Pg_ein, Pa_ein)
            self.geos.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad = ArcGeo(Pa=Pa_ein, Pe=start, O=Oein, 
                               r=start_rad + tool_rad, direction=0)
            self.geos.append(start_rad)
            
            
    def updateCutCor(self, cutcor):
        """
        This function is called to update the Cutter Correction and therefore 
        the  startmoves if smth. has changed or it shall be generated for 
        first time.
        """
        
        self.cutcor=cutcor
        self.make_start_moves()
        self.make_papath()
        self.update()
        
        g.logger.logger.debug("Updating CutterCorrection of Selected shape")
            
    def make_papath(self):
        """
        To be called if a Shape shall be printed to the canvas
        @param canvas: The canvas to be printed in
        @param pospro: The color of the shape 
        """
        self.hide()
        del(self.path)
        self.path=QtGui.QPainterPath()
        
        for geo in self.geos:
            geo.add2path(papath=self.path,parent=self.parent)
        self.show()

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
        self.startp=startp
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
        painter.setPen(self.pen)
        painter.drawPath(self.path) 

    def boundingRect(self):
        """ 
        Required method for painting. Inherited by Painterpath
        @return: Gives the Bounding Box
        """ 
        return self.path.boundingRect()
    

