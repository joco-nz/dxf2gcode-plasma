#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_v01_geoent_ellipse
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
from math import sqrt, sin, cos, tan, atan, atan2, radians, degrees, pi
from dxf2gcode_v01_point import PointClass, LineGeo, ArcGeo, PointsClass, ContourClass, BiarcClass


class EllipseClass:
    def __init__(self,Nr=0,caller=None):
        self.Typ='Ellipse'
        self.Nr = Nr
        #Initialisieren der Werte        
        self.Layer_Nr = 0
        self.center = PointClass(0,0) #Mittelpunkt der Geometrie
        self.vector = PointClass(1,0) #Vektor A = große Halbachse a, = Drehung der Ellipse
                                      # http://de.wikipedia.org/wiki/Gro%C3%9Fe_Halbachse
        self.ratio = 1                #Verhältnis der kleinen zur großen Halbachse (b/a)
        self.AngS = 0                 #Startwinkel beim zeichnen eines Ellipsensegments
        self.AngE = radians(360)      #Endwinkel (Winkel im DXF als Radians!)
        #Die folgenden Grundwerte werden später ein mal berechnet

        self.length = 0
        self.Points=[]
        self.Points.append(self.center)
        #Lesen der Geometrie
        self.Read(caller)

        #Zuweisen der Toleranz fürs Fitting
        tol=caller.config.fitting_tolerance.get()

        #Errechnen der Ellipse
        self.Ellipse_Grundwerte()
        self.Ellipse_2_Arcs(tol)

    def __str__(self):
        # how to print the object #Geht auch so ellegant wie sprintf in C oder Matlab usw. siehe erste zeile  !!!!!!!!!!!!!!!!!!!!!!
        s=('Typ: Ellipse\n')+ \
        ('Nr:     %i \n' %(self.Nr))+\
        'Layer:  '+str(self.Layer_Nr) +'\n' + \
        'center: '+str(self.center) +'\n' + \
        'vector: '+str(self.vector) +'\n' + \
        'ratio:  '+str(self.ratio) +'\n' + \
        'angles: '+str(degrees(self.AngS))+' -> '+str(degrees(self.AngE))+'\n' + \
        'a:      '+str(self.a) +'\n' + \
        'b:      '+str(self.b) +'\n' + \
        'length: '+str(self.length) +\
        ("\nNr. of arcs: %i" %len(self.geo))
        return s

    def reverse(self):
        self.geo.reverse()
        for geo in self.geo:
            geo.reverse()    

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol):
        #Hinzufügen falls es keine geschlossene Polyline ist
        if self.geo[0].Pa.isintol(self.geo[-1].Pe,tol):
            self.analyse_and_opt()
            cont.append(ContourClass(len(cont),1,[[i,0]],self.length))
        else:
            points.append(PointsClass(point_nr=len(points),geo_nr=i,\
                          Layer_Nr=self.Layer_Nr,\
                          be=self.geo[0].Pa,
                          en=self.geo[-1].Pe,be_cp=[],en_cp=[]))      

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
        self.center=PointClass(x0,y0)
        #XWert, YWert. Vektor, relativ zum Zentrum, Große Halbachse
        s=lp.index_code(11,s+1)
        x1=float(lp.line_pair[s].value)
        s=lp.index_code(21,s+1)
        y1=float(lp.line_pair[s].value)
        self.vector=PointClass(x1,y1)
        #Ratio minor to major axis
        s=lp.index_code(40,s+1)
        self.ratio = float(lp.line_pair[s].value)
        #Start Winkel - Achtung, ist als rad (0-2pi) im dxf
        s=lp.index_code(41,s+1)
        self.Start_Ang=float(lp.line_pair[s].value)
        #End Winkel - Achtung, ist als rad (0-2pi) im dxf
        s=lp.index_code(42,s+1)
        self.End_Ang=float(lp.line_pair[s].value)
        #Neuen Startwert für die nächste Geometrie zurückgeben
        caller.start=e

    def analyse_and_opt(self):
        #Richtung in welcher der Anfang liegen soll (unten links)        
        Popt=PointClass(x=-1e3,y=-1e6)
        
        #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
        min_distance=self.geo[0].Pa.distance(Popt)
        min_geo_nr=0
        for geo_nr in range(1,len(self.geo)):
            if (self.geo[geo_nr].Pa.distance(Popt)<min_distance):
                min_distance=self.geo[geo_nr].Pa.distance(Popt)
                min_geo_nr=geo_nr

        #Kontur so anordnen das neuer Startpunkt am Anfang liegt
        self.geo=self.geo[min_geo_nr:len(self.geo)]+self.geo[0:min_geo_nr]
        
    def get_start_end_points(self,direction=0):
        if not(direction):
            punkt, angle=self.geo[0].get_start_end_points(direction)
        elif direction:
            punkt, angle=self.geo[-1].get_start_end_points(direction)
        return punkt,angle
    
    def Ellipse_2_Arcs(self, tol):

        #Anfangswert für Anzahl Elemente
        num_elements=2
        intol=False   

        while not(intol):
            intol=True
            
            #Anfangswete Ausrechnen
            angle = self.AngS
            Pa = self.Ellipse_Point(angle)
            tana= self.Ellipse_Tangent(angle)

            self.geo=[]
            self.PtsVec=[]
            self.PtsVec.append([Pa,tana])
            
            for sec in range(num_elements*2):
                #Neuer Winkel errechnen
                angle+=-(2*pi)/num_elements/2

                #Endwerte errechnen            
                Pb = self.Ellipse_Point(angle)
                tanb= self.Ellipse_Tangent(angle)

                #Biarc erstellen und an geo anhängen        
                biarcs=BiarcClass(Pa,tana,Pb,tanb,tol/100)
                self.geo+=biarcs.geos[:]             

                #Letzer Wert = Startwert
                Pa=Pb
                tana=tanb
                
                self.PtsVec.append([Pa,tana])

                if not(self.check_ellipse_fitting_tolerance(biarcs,tol,angle,angle+(2*pi)/num_elements/2)):
                    intol=False
                    num_elements+=1
                    break
                      
    def check_ellipse_fitting_tolerance(self,biarc,tol,ang0,ang1):
        check_step=(ang1-ang0)/4
        check_ang=[]
        check_Pts=[]
        fit_error=[]
        
        for i in range(1,4):
            check_ang.append(ang0+check_step*i)
            check_Pts.append(self.Ellipse_Point(check_ang[-1]))
            fit_error.append(biarc.get_biarc_fitting_error(check_Pts[-1]))

        if max(fit_error)>=tol:
            return 0
        else:
            return 1            

    def Ellipse_Grundwerte(self):
        #Weitere Grundwerte der Ellipse, die nur einmal ausgerechnet werden müssen
        self.rotation = atan2(self.vector.y, self.vector.x)
        self.a = sqrt(self.vector.x**2 + self.vector.y**2)
        self.b = self.a * self.ratio

    def Ellipse_Point(self, alpha=0):#PointClass(0,0)
        #große Halbachse, kleine Halbachse, rotation der Ellipse (rad), Winkel des Punkts in der Ellipse (rad)
        Ex = self.a*cos(alpha) * cos(self.rotation) - self.b*sin(alpha) * sin(self.rotation);
        Ey = self.a*cos(alpha) * sin(self.rotation) + self.b*sin(alpha) * cos(self.rotation);
        return PointClass(self.center.x+Ex, self.center.y+Ey)
    
    def Ellipse_Tangent(self, alpha=0):#PointClass(0,0)
        #große Halbachse, kleine Halbachse, rotation der Ellipse (rad), Winkel des Punkts in der Ellipse (rad)
        phi=atan2(self.a*sin(alpha),self.b*cos(alpha))+self.rotation-pi/2
        return phi