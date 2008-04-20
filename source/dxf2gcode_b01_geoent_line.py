#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b01_ent_polyline
#Programmer: Christian Kohlöffel
#E-mail:     n/A
#
#Copyright 2008 Christian Kohlöffel
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

from dxf2gcode_b01_dxf_import import PointClass
from dxf2gcode_b01_dxf_import import PointsClass
from dxf2gcode_b01_dxf_import import ContourClass

class LineClass:
    def __init__(self,Nr=0,caller=None):
        self.Typ='Line'
        self.Nr = Nr
        
        #Initialisieren der Werte        
        self.Layer_Nr = 0
        self.Points = []
        self.length= 0

        #Lesen der Geometrie
        self.Read(caller)
        
    def __str__(self):
        # how to print the object
        s= '\nTyp: Line \nNr ->'+str(self.Nr) +'\nLayer Nr: ->'+str(self.Layer_Nr)
        for point in self.Points:
            s=s+str(point)
        s=s+'\nLength ->'+str(self.length)
        return s

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol):
        points.append(PointsClass(point_nr=len(points),geo_nr=i,\
                                  Layer_Nr=self.Layer_Nr,\
                                  be=self.Points[0],
                                  en=self.Points[-1],be_cp=[],en_cp=[]))      
        
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

        self.Points.append(PointClass(x0,y0))
        self.Points.append(PointClass(x1,y1))                
        #Berechnen der Vektorlänge
        self.length=self.Points[0].distance(self.Points[1])

        #Neuen Startwert für die nächste Geometrie zurückgeben        
        caller.start=s

    def plot2can(self,canvas,p0,sca,tag):
        hdl=Line(canvas,p0[0]+self.Points[0].x*sca[0],-p0[1]-self.Points[0].y*sca[1],\
             p0[0]+self.Points[1].x*sca[0],-p0[1]-self.Points[1].y*sca[1],\
             tag=tag)
        return hdl
    
    def get_start_end_points(self,direction):
        if direction==0:
            punkt=self.Points[0]
            dx=self.Points[1].x-self.Points[0].x
            dy=self.Points[1].y-self.Points[0].y
            angle=degrees(atan2(dy, dx))
        elif direction==1:
            punkt=self.Points[-1]
            dx=self.Points[-2].x-self.Points[-1].x
            dy=self.Points[-2].y-self.Points[-1].y
            angle=degrees(atan2(dy, dx))

        return punkt, angle
    
    def Write_GCode(self,string,paras,sca,p0,dir,axis1,axis2):
        en_point, en_angle=self.get_start_end_points(not(dir))
        x_en=(en_point.x*sca[0])+p0[0]
        y_en=(en_point.y*sca[1])+p0[1]
        string+=("G1 %s%0.3f %s%0.3f\n" %(axis1,x_en,axis2,y_en))
        return string
        

