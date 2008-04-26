#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b01_ent_ellipse
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


class EllipseClass:
    def __init__(self,Nr=0,caller=None):
        self.Typ='Ellipse'
        self.Nr = Nr
        #Initialisieren der Werte        
        self.Layer_Nr = 0
        self.Center = PointClass(0,0) #Mittelpunkt der Geometrie
        self.Vektor = PointClass(1,0) #Vektor A = große Halbachse a, = Drehung der Ellipse
                                      # http://de.wikipedia.org/wiki/Gro%C3%9Fe_Halbachse
        self.Ratio = 1                #Verhältnis der kleinen zur großen Halbachse (b/a)
        self.AngS = 0                 #Startwinkel beim zeichnen eines Ellipsensegments
        self.AngE = radians(360)      #Endwinkel (Winkel im DXF als Radians!)
        #Die folgenden Grundwerte werden später ein mal berechnet
        self.Rotation = 0
        self.a = 1
        self.b = 1
        self.length = 0
        self.Points=[]
        self.Points.append(self.Center)
        #Lesen der Geometrie
        self.Read(caller)


    def __str__(self):
        # how to print the object
        s=  'Typ: Ellipse\n' + \
        'Nr:     '+str(self.Nr) +'\n' + \
        'Layer:  '+str(self.Layer_Nr) +'\n' + \
        'Center: '+str(self.Center) +'\n' + \
        'Vektor: '+str(self.Vektor) +'\n' + \
        'Ratio:  '+str(self.Ratio) +'\n' + \
        'Winkel: '+str(degrees(self.AngS))+' -> '+str(degrees(self.AngE))+'\n' + \
        'a:      '+str(self.a) +'\n' + \
        'b:      '+str(self.b) +'\n' + \
        'Length: '+str(self.length)
        return s


    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol):
        #Ich nehm das mal wörtlich und berechne die Punkte erst hier,
        # ... weil ich hier auch die tol habe
        self.Ellipse_2_Polyline(tol)
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
        #Kürzere Namen zuweisen
        lp=caller.line_pairs
        e=lp.index_code(0,caller.start+1)
        #Layer zuweisen
        s=lp.index_code(8,caller.start+1)
        self.Layer_Nr=caller.Get_Layer_Nr(lp.line_pair[s].value)
        #XWert, YWert Center
        s=lp.index_code(10,s+1)
        x0=float(lp.line_pair[s].value)
        s=lp.index_code(20,s+1)
        y0=float(lp.line_pair[s].value)
        self.Center=PointClass(x0,y0)
        #XWert, YWert. Vektor, relativ zum Zentrum, Große Halbachse
        s=lp.index_code(11,s+1)
        x1=float(lp.line_pair[s].value)
        s=lp.index_code(21,s+1)
        y1=float(lp.line_pair[s].value)
        self.Vektor=PointClass(x1,y1)
        #Ratio minor to major axis
        s=lp.index_code(40,s+1)
        self.Ratio = float(lp.line_pair[s].value)
        #Start Winkel - Achtung, ist als rad (0-2pi) im dxf
        s=lp.index_code(41,s+1)
        self.Start_Ang=float(lp.line_pair[s].value)
        #End Winkel - Achtung, ist als rad (0-2pi) im dxf
        s=lp.index_code(42,s+1)
        self.End_Ang=float(lp.line_pair[s].value)
        #Neuen Startwert für die nächste Geometrie zurückgeben
        caller.start=e
        #Ellipse-spezifische Funktionen
        self.Ellipse_Grundwerte()


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
            hdl.append(Line(canvas,p0[0]+self.Points[i-1].x*sca[0],-p0[1]-self.Points[i-1].y*sca[1],\
                            p0[0]+self.Points[i].x*sca[0],-p0[1]-self.Points[i].y*sca[1],\
                            tag=tag))     
        return hdl


    def get_start_end_points(self,direction=0,nr=0):
        if direction==0:
            punkt=self.Points[nr]
            #punkt=self.Ellipse_Point(self.Center, self.a, self.b, self.Rotation, self.AngS)
            dx=self.Points[1].x-self.Points[0].x
            dy=self.Points[1].y-self.Points[0].y
            angle=degrees(atan2(dy, dx))
        elif direction==1:
            punkt=self.Points[len(self.Points)-nr-1]
            #punkt=self.Ellipse_Point(self.Center, self.a, self.b, self.Rotation, self.AngE)
            dx=self.Points[-2].x-self.Points[-1].x
            dy=self.Points[-2].y-self.Points[-1].y
            angle=degrees(atan2(dy, dx))
        return punkt,angle


    def Write_GCode(self,string,paras,sca,p0,dir,axis1,axis2):
        for p_nr in range(len(self.Points)-1):
            en_point, en_angle=self.get_start_end_points(not(dir),p_nr+1)
            x_en=(en_point.x*sca[0])+p0[0]
            y_en=(en_point.y*sca[1])+p0[1]
            string+=("G1 %s%0.3f %s%0.3f\n" %(axis1,x_en,axis2,y_en))
        return string


    def Ellipse_2_Polyline(self, tol):
        self.Points=[]
        angle = self.AngS
        while(angle < self.AngE): # kein <= weil wir den Endpunkt auf jeden Fall anhängen müssen
            newPoint = self.Ellipse_Point(self.Center, self.a, self.b, self.Rotation, angle)
            #nur Punkte anhängen, die sich lohnen, Startpunkt auf jeden Fall:
            if (angle==self.AngS) or (not newPoint.isintol(self.Points[-1],tol)) : 
                self.Points.append(newPoint)
            angle += radians(1)
        # letzter Winkel muss genau der Endwinkel sein und keine Tol-Betrachtung
        self.Points.append(self.Ellipse_Point(self.Center, self.a, self.b, self.Rotation, self.AngE))


    def Ellipse_Grundwerte(self):
        #Weitere Grundwerte der Ellipse, die nur einmal ausgerechnet werden müssen
        self.Rotation = atan2(self.Vektor.y, self.Vektor.x)
        self.a = sqrt(self.Vektor.x**2 + self.Vektor.y**2)
        self.b = self.a * self.Ratio


    def Ellipse_Point(self, Pcenter=None, a=1, b=1, rot=0, alfa=0):#PointClass(0,0)
        #große Halbachse, kleine Halbachse, Rotation der Ellipse (rad), Winkel des Punkts in der Ellipse (rad)
        Ex = a*cos(alfa) * cos(rot) - b*sin(alfa) * sin(rot);
        Ey = a*cos(alfa) * sin(rot) + b*sin(alfa) * cos(rot);
        return PointClass(Pcenter.x+Ex, Pcenter.y+Ey)