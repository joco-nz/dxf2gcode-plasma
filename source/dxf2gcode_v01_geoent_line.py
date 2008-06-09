#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_v01_geoent_line
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

from Canvas import Oval, Arc, Line
from math import sqrt, sin, cos, atan2, radians, degrees
from dxf2gcode_v01_point import PointClass, LineGeo, PointsClass, ContourClass

class LineClass:
    def __init__(self,Nr=0,caller=None):
        self.Typ='Line'
        self.Nr = Nr
        self.Layer_Nr = 0
        self.geo = []
        self.length= 0

        #Lesen der Geometrie
        self.Read(caller)

    def __str__(self):
        # how to print the object
        return("\nTyp: Line")+\
              ("\nNr: %i" %self.Nr)+\
              ("\nLayer Nr: %i" %self.Layer_Nr)+\
              str(self.geo[-1])

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol):
        points.append(PointsClass(point_nr=len(points),geo_nr=i,\
                                  Layer_Nr=self.Layer_Nr,\
                                  be=self.geo[-1].Pa,
                                  en=self.geo[-1].Pe,be_cp=[],en_cp=[]))      
        
    def Read(self, caller):
        #Kürzere Namen zuweisen
        lp=caller.line_pairs

        #Layer zuweisen        
        s=lp.index_code(8,caller.start+1)
        self.Layer_Nr=caller.Get_Layer_Nr(lp.line_pair[s].value)
        #XWert
        s=lp.index_code(10,s+1)
        x0=float(lp.line_pair[s].value)
        #YWert
        s=lp.index_code(20,s+1)
        y0=float(lp.line_pair[s].value)
        #XWert2
        s=lp.index_code(11,s+1)
        x1 = float(lp.line_pair[s].value)
        #YWert2
        s=lp.index_code(21,s+1)
        y1 = float(lp.line_pair[s].value)

        Pa=PointClass(x0,y0)
        Pe=PointClass(x1,y1)               

        #Anhängen der LineGeo Klasse für die Geometrie
        self.geo.append(LineGeo(Pa=Pa,Pe=Pe))

        #Länge entspricht der Länge des Kreises
        self.length=self.geo[-1].length
        
        #Neuen Startwert für die nächste Geometrie zurückgeben        
        caller.start=s

    def get_start_end_points(self,direction):
        punkt,angle=self.geo[-1].get_start_end_points(direction)
        return punkt,angle
            

