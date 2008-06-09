#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_v01_geoent_spline
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

from math import sqrt, sin, cos, atan2, radians, degrees
from dxf2gcode_v01_nurbs_calc import Spline2Arcs
from dxf2gcode_v01_point import PointClass, PointsClass, ContourClass

class SplineClass:
    def __init__(self,Nr=0,caller=None):
        self.Typ='Spline'
        self.Nr = Nr

        #Initialisieren der Werte        
        self.Layer_Nr = 0
        self.Spline_flag=[]
        self.degree=1
        self.Knots=[]
        self.Weights=[]
        self.CPoints=[]
        self.geo=[]
        self.length= 0.0

        #Lesen der Geometrie
        self.Read(caller)

        #Zuweisen der Toleranz fürs Fitting
        tol=caller.config.fitting_tolerance.get()

        #Umwandeln zu einem ArcSpline
        Spline2ArcsClass=Spline2Arcs(degree=self.degree,Knots=self.Knots,\
                                Weights=self.Weights,CPoints=self.CPoints,tol=0.01)

        self.geo=Spline2ArcsClass.Curve

        for geo in self.geo:
            self.length+=geo.length

    def __str__(self):
        # how to print the object
        s= ('\nTyp: Spline')+\
           ('\nNr: %i' %self.Nr)+\
           ('\nLayer Nr: %i' %self.Layer_Nr)+\
           ('\nSpline flag: %i' %self.Spline_flag)+\
           ('\ndegree: %i' %self.degree)+\
           ('\nlength: %0.3f' %self.length)+\
           ('\nGeo elements: %i' %len(self.geo))+\
           ('\nKnots: %s' %self.Knots)+\
           ('\nWeights: %s' %self.Weights)+\
           ('\nCPoints: ')
           
        for point in self.CPoints:
            s=s+"\n"+str(point)
        s+=('\ngeo: ')

        return s

    def reverse(self):
        self.geo.reverse()
        for geo in self.geo:
            geo.reverse()    
          
    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol):
        #Hinzufügen falls es keine geschlossener Spline ist
        if self.CPoints[0].isintol(self.CPoints[-1],tol):
            self.analyse_and_opt()
            cont.append(ContourClass(len(cont),1,[[i,0]],self.length)) 
        else:
            points.append(PointsClass(point_nr=len(points),geo_nr=i,\
                                      Layer_Nr=self.Layer_Nr,\
                                      be=self.geo[0].Pa,\
                                      en=self.geo[-1].Pe,\
                                      be_cp=[],en_cp=[]))
            
    def analyse_and_opt(self):
        summe=0

        #Richtung in welcher der Anfang liegen soll (unten links)        
        Popt=PointClass(x=-1e3,y=-1e6)
        
        #Berechnung der Fläch nach Gauß-Elling Positive Wert bedeutet CW
        #negativer Wert bedeutet CCW geschlossenes Polygon            
        for Line in self.geo:
            summe+=(Line.Pa.x*Line.Pe.y-Line.Pe.x*Line.Pa.y)/2
        
        if summe>0.0:
            self.reverse()
        
        #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
        min_distance=self.geo[0].Pa.distance(Popt)
        min_geo_nr=0
        for geo_nr in range(1,len(self.geo)):
            if (self.geo[geo_nr].Pa.distance(Popt)<min_distance):
                min_distance=self.geo[geo_nr].Pa.distance(Popt)
                min_geo_nr=geo_nr

        #Kontur so anordnen das neuer Startpunkt am Anfang liegt
        self.geo=self.geo[min_geo_nr:len(self.geo)]+self.geo[0:min_geo_nr]

    def Read(self, caller):

        #Kürzere Namen zuweisen        
        lp=caller.line_pairs
        e=lp.index_code(0,caller.start+1)

        #Layer zuweisen        
        s=lp.index_code(8,caller.start+1)
        self.Layer_Nr=caller.Get_Layer_Nr(lp.line_pair[s].value)

        #Spline Flap zuweisen
        s=lp.index_code(70,s+1)
        self.Spline_flag=int(lp.line_pair[s].value) 

        #Spline Ordnung zuweisen
        s=lp.index_code(71,s+1)
        self.degree=int(lp.line_pair[s].value)

        #Number of CPts
        s=lp.index_code(73,s+1)
        nCPts=int(lp.line_pair[s].value)          


        #Lesen der Knoten
        while 1:
            #Knoten Wert
            sk=lp.index_code(40,s+1,e)
            if sk==None:
                break
            self.Knots.append(float(lp.line_pair[sk].value))
            s=sk

        #Lesen der Gewichtungen
        while 1:
            #Knoten Gewichtungen
            sg=lp.index_code(41,s+1,e)
            if sg==None:
                break
            self.Weights.append(float(lp.line_pair[sg].value))
            s=sg
            
        if len(self.Weights)==0:
            for nr in range(nCPts):
                self.Weights.append(1)
                
        #Lesen der Kontrollpunkte
        while 1:  
            #XWert
            s=lp.index_code(10,s+1,e)
            #Wenn kein neuer Punkt mehr gefunden wurde abbrechen ...
            if s==None:
                break
            
            x=float(lp.line_pair[s].value)
            #YWert
            s=lp.index_code(20,s+1,e)
            y=float(lp.line_pair[s].value)

            self.CPoints.append(PointClass(x,y))                

        caller.start=e
        
    def get_start_end_points(self,direction=0):
        if not(direction):
            punkt, angle=self.geo[0].get_start_end_points(direction)
        elif direction:
            punkt, angle=self.geo[-1].get_start_end_points(direction)

        return punkt,angle
    