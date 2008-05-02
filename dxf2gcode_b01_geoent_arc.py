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

class ArcClass:
    def __init__(self,Nr=0,caller=None):
        self.Typ='Arc'
        self.Nr = Nr

        #Initialisieren der Werte        
        self.Layer_Nr = 0
        self.Points=[]
        self.Radius= 0
        self.Start_Ang=0
        self.End_Ang=0
        self.length=0

        #Lesen der Geometrie
        self.Read(caller)

    def __str__(self):
        # how to print the object
        s='\nTyp: Arc \nNr ->'+str(self.Nr) \
            +'\nLayer Nr: ->'+str(self.Layer_Nr)
        for point in self.Points:
            s=s+str(point)
        s=s+'\nRadius ->'+str(self.Radius)+'\nStart Angle ->'+str(self.Start_Ang) \
           +'\nEnd Angle ->'+str(self.End_Ang) \
           +'\nLength ->'+str(self.length)
        return s

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol):
        points.append(PointsClass(point_nr=len(points),geo_nr=i,\
                          Layer_Nr=self.Layer_Nr,\
                          be=self.Points[-2],
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
        self.Points.append(PointClass(x0,y0))
        #Radius
        s=lp.index_code(40,s+1)
        self.Radius = float(lp.line_pair[s].value)
        #Start Winkel
        s=lp.index_code(50,s+1)
        self.Start_Ang= float(lp.line_pair[s].value)
        #End Winkel
        s=lp.index_code(51,s+1)
        self.End_Ang= float(lp.line_pair[s].value)        

        #Berechnen der Start und Endwerte des Arcs
        xs=cos(radians(self.Start_Ang))*self.Radius+x0
        ys=sin(radians(self.Start_Ang))*self.Radius+y0
        self.Points.append(PointClass(xs,ys))
        xe=cos(radians(self.End_Ang))*self.Radius+x0
        ye=sin(radians(self.End_Ang))*self.Radius+y0
        self.Points.append(PointClass(xe,ye))

        #Korrektur des Endwinkels bei Werten <= 0
        if self.End_Ang<=0:
            EA_cor=self.End_Ang+360
        else:
            EA_cor=self.End_Ang
            
        self.length=self.Radius*abs(radians(EA_cor-self.Start_Ang))

        #Neuen Startwerd für die nächste Geometrie zurückgeben        
        caller.start=s

    def plot2can(self,canvas,p0,sca,tag):
        if self.End_Ang==0:
            ext=360-self.Start_Ang
        else:            
            ext=self.End_Ang-self.Start_Ang

        if ext<0:
            ext+=360

        xy=p0.x+(self.Points[0].x-self.Radius)*sca[0],-p0.y-(self.Points[0].y-self.Radius)*sca[1],\
            p0.x+(self.Points[0].x+self.Radius)*sca[0],-p0.y-(self.Points[0].y+self.Radius)*sca[1]
        hdl=Arc(canvas,xy,start=self.Start_Ang,extent=ext,style="arc",\
            tag=tag)
        return hdl

    def get_start_end_points(self,direction):
        if direction==0:
            punkt=self.Points[1]
            angle=self.Start_Ang+90
        elif direction==1:
            punkt=self.Points[2]
            angle=self.End_Ang-90
        return punkt,angle
    
    def Write_GCode(self,string,paras,sca,p0,dir,axis1,axis2):
        st_point, st_angle=self.get_start_end_points(dir)
        IJ=(self.Points[0]-st_point)*sca
        
        en_point, en_angle=self.get_start_end_points(not(dir))
        ende=en_point*sca+p0
        
        #Vorsicht geht nicht für Ovale
        if dir==0:
            string+=("G3 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,ende.x,axis2,ende.y,IJ.x,IJ.y))
        else:
            string+=("G2 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,ende.x,axis2,ende.y,IJ.x,IJ.y))

        return string
            