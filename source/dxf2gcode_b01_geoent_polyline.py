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


class PolylineClass:
    def __init__(self,Nr=0,caller=None):
        self.Typ='Polyline'
        self.Nr = Nr

        #Initialisieren der Werte        
        self.Layer_Nr = 0
        self.Points=[]
        self.length= 0

        #Lesen der Geometrie
        self.Read(caller)
        
    def __str__(self):
        # how to print the object
        s= '\nTyp: Polyline \nNr ->'+str(self.Nr) +'\nLayer Nr: ->'+str(self.Layer_Nr)
        for point in self.Points:
            s=s+str(point)
        s=s+'\nLength ->'+str(self.length)
        return s

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol):
        #Hinzufügen falls es keine geschlossene Polyline ist
        if self.Points[0].isintol(self.Points[-1],tol):
            self.analyse_and_opt()
            cont.append(ContourClass(len(cont),1,[[i,0]],self.length))
        else:            
            points.append(PointsClass(point_nr=len(points),geo_nr=i,\
                          Layer_Nr=self.Layer_Nr,\
                          be=self.Points[0],
                          en=self.Points[-1],be_cp=[],en_cp=[]))      
            
    def Read(self, caller):
        Old_Point=PointClass(0,0)

        #Kürzere Namen zuweisen        
        lp=caller.line_pairs
        e=lp.index_both(0,"SEQEND",caller.start+1)+1

        #Layer zuweisen        
        s=lp.index_code(8,caller.start+1)
        self.Layer_Nr=caller.Get_Layer_Nr(lp.line_pair[s].value)        
        
        while 1:
            s=lp.index_both(0,"VERTEX",s+1,e)
            if s==None:
                break
            
            #XWert
            s=lp.index_code(10,s+1,e)
            x=float(lp.line_pair[s].value)
            #YWert
            s=lp.index_code(20,s+1,e)
            y=float(lp.line_pair[s].value)

            self.Points.append(PointClass(x,y))             

            if (Old_Point==self.Points[-1]):
               # add to boundary if not zero-length segment
               Old_Point=self.Points[-1]
               if len(self.Points)>1:
                   self.length+=self.Points[-2].distance(self.Points[-1])
                   
        #Neuen Startwert für die nächste Geometrie zurückgeben        
        caller.start=e

    def analyse_and_opt(self):
        summe=0
        #Berechnung der Fläch nach Gauß-Elling Positive Wert bedeutet CW
        #negativer Wert bedeutet CCW geschlossenes Polygon            
        for p_nr in range(1,len(self.Points)):
            summe+=(self.Points[p_nr-1].x*self.Points[p_nr].y-self.Points[p_nr].x*self.Points[p_nr-1].y)/2
        if summe>0.0:
            self.Points.reverse()

        #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
        min_point=self.Points[0]
        min_p_nr=0
        del(self.Points[-1])
        for p_nr in range(1,len(self.Points)):
            #Geringster Abstand nach unten Unten Links
            if (min_point.x+min_point.y)>=(self.Points[p_nr].x+self.Points[p_nr].y):
                min_point=self.Points[p_nr]
                min_p_nr=p_nr
        #Kontur so anordnen das neuer Startpunkt am Anfang liegt
        self.Points=self.Points[min_p_nr:len(self.Points)]+self.Points[0:min_p_nr]+[self.Points[min_p_nr]]
 
    def plot2can(self,canvas,p0,sca,tag):
        hdl=[]
        for i in range(1,len(self.Points)):
            hdl.append(Line(canvas,p0.x+self.Points[i-1].x*sca[0],-p0.y-self.Points[i-1].y*sca[1],\
                            p0.x+self.Points[i].x*sca[0],-p0.y-self.Points[i].y*sca[1],\
                            tag=tag))
        return hdl
    
    def get_start_end_points(self,direction=0,nr=0):
        if direction==0:
            punkt=self.Points[nr]
            dx=self.Points[1].x-self.Points[0].x
            dy=self.Points[1].y-self.Points[0].y
            angle=degrees(atan2(dy, dx))
        elif direction==1:
            punkt=self.Points[len(self.Points)-nr-1]
            dx=self.Points[-2].x-self.Points[-1].x
            dy=self.Points[-2].y-self.Points[-1].y
            angle=degrees(atan2(dy, dx))

        return punkt,angle
    
    def Write_GCode(self,string,paras,sca,p0,dir,axis1,axis2):
        
        for p_nr in range(len(self.Points)-1):
            en_point, en_angle=self.get_start_end_points(not(dir),p_nr+1)
            ende=en_point*sca+p0
            string+=("G1 %s%0.3f %s%0.3f\n" %(axis1,ende.x,axis2,ende.y))
        return string
        


