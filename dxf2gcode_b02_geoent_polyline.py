#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_geoent_polyline
#Programmers:   Christian Kohlöffel
#               Vinzenz Schulzel
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
from dxf2gcode_b02_point import PointClass, LineGeo, ArcGeo, PointsClass, ContourClass

class PolylineClass:
    def __init__(self,Nr=0,caller=None):
        self.Typ='Polyline'
        self.Nr = Nr
        self.Layer_Nr = 0
        self.geo=[]
        self.length= 0

        #Lesen der Geometrie
        self.Read(caller)
        
    def __str__(self):
        # how to print the object
        string=("\nTyp: Polyline")+\
               ("\nNr: %i" %self.Nr)+\
               ("\nLayer Nr: %i" %self.Layer_Nr)+\
               ("\nNr. of Lines: %i" %len(self.geo))+\
               ("\nlength: %0.3f" %self.length)

        return string

    def reverse(self):
        self.geo.reverse()
        for geo in self.geo:
            geo.reverse()

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol,warning):
        if abs(self.length)<tol:
            pass
            
        #Hinzufügen falls es keine geschlossene Polyline ist
        elif self.geo[0].Pa.isintol(self.geo[-1].Pe,tol):
            self.analyse_and_opt()
            cont.append(ContourClass(len(cont),1,[[i,0]],self.length))
        else:            
            points.append(PointsClass(point_nr=len(points),geo_nr=i,\
                                      Layer_Nr=self.Layer_Nr,\
                                      be=self.geo[0].Pa,
                                      en=self.geo[-1].Pe,be_cp=[],en_cp=[])) 
                                    
        return warning

##            if abs(self.length)>tol:
##                points.append(PointsClass(point_nr=len(points),geo_nr=i,\
##                                          Layer_Nr=self.Layer_Nr,\
##                                          be=self.geo[0].Pa,
##                                          en=self.geo[-1].Pe,be_cp=[],en_cp=[])) 
##            else:
##                showwarning("Short Polyline Elemente", ("Length of Line geometrie too short!"\
##                                                   "\nLenght must be greater then tolerance."\
##                                                   "\nSkipping Line Geometrie"))
            
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
        e=lp.index_both(0,"SEQEND",caller.start+1)+1
        #Layer zuweisen        
        s=lp.index_code(8,caller.start+1)
        self.Layer_Nr=caller.Get_Layer_Nr(lp.line_pair[s].value)

        #Pa=None für den ersten Punkt
        Pa=None
          
        #Polyline flag 
        s_temp=lp.index_code(70,s+1,e)
        if s_temp==None:
            PolyLineFlag=0
        else:
            PolyLineFlag=int(lp.line_pair[s_temp].value)
            s=s_temp
            
        #print("PolylineFlag: %i" %PolyLineFlag)
             
        while 1: #and not(s==None):
            s=lp.index_both(0,"VERTEX",s+1,e)
            if s==None:
                break
            
            #XWert
            s=lp.index_code(10,s+1,e)
            x=float(lp.line_pair[s].value)
            #YWert
            s=lp.index_code(20,s+1,e)
            y=float(lp.line_pair[s].value)
            Pe=PointClass(x=x,y=y)

            #Bulge
            bulge=0
            
            e_vertex=lp.index_both(0,"VERTEX",s+1,e)
            if e_vertex==None:
                e_vertex=e
                
            s_temp=lp.index_code(42,s+1,e_vertex)
            #print('stemp: %s, e: %s, next 10: %s' %(s_temp,e,lp.index_both(0,"VERTEX",s+1,e)))
            if s_temp!=None:
                bulge=float(lp.line_pair[s_temp].value)
                s=s_temp
                
            #Vertex flag (bit-coded); default is 0; 1 = Closed; 128 = Plinegen
            s_temp=lp.index_code(70,s+1,e_vertex)
            if s_temp==None:
                VertexFlag=0
            else:
                VertexFlag=int(lp.line_pair[s_temp].value)
                s=s_temp
                
            #print("Vertex Flag: %i" %PolyLineFlag)
            
            #Zuweisen der Geometrien für die Polyline
            if (VertexFlag!=16):
                if type(Pa)!=type(None):
                    if next_bulge==0:
                        self.geo.append(LineGeo(Pa=Pa,Pe=Pe))
                    else:
                        #self.geo.append(LineGeo(Pa=Pa,Pe=Pe))
                        #print bulge
                        self.geo.append(self.bulge2arc(Pa,Pe,next_bulge))
                    
                    #Länge drauf rechnen wenns eine Geometrie ist
                    self.length+=self.geo[-1].length
                        
                #Der Bulge wird immer für den und den nächsten Punkt angegeben
                next_bulge=bulge
                Pa=Pe
                    
        #Es ist eine geschlossene Polyline
        if PolyLineFlag==1:
            #print("sollten Übereinstimmen: %s, %s" %(Pa,Pe))
            if next_bulge==0:
                self.geo.append(LineGeo(Pa=Pa,Pe=self.geo[0].Pa))
            else:
                self.geo.append(self.bulge2arc(Pa,self.geo[0].Pa,next_bulge))
            #Länge drauf rechnen wenns eine Geometrie ist   
            self.length+=self.geo[-1].length
      
        #Neuen Startwert für die nächste Geometrie zurückgeben        
        caller.start=e
    
    def get_start_end_points(self,direction=0):
        if not(direction):
            punkt, angle=self.geo[0].get_start_end_points(direction)
        elif direction:
            punkt, angle=self.geo[-1].get_start_end_points(direction)
        return punkt,angle
    
    def bulge2arc(self,Pa,Pe,bulge):
        c=(1/bulge-bulge)/2
        
        #Berechnung des Mittelpunkts (Formel von Mickes!
        O=PointClass(x=(Pa.x+Pe.x-(Pe.y-Pa.y)*c)/2,\
                     y=(Pa.y+Pe.y+(Pe.x-Pa.x)*c)/2)
                    
        #Abstand zwischen dem Mittelpunkt und PA ist der Radius
        r=O.distance(Pa)
        #Kontrolle ob beide gleich sind (passt ...)
        #r=O.distance(Pe)

        #Unterscheidung für den Öffnungswinkel.
        if bulge>0:
            return ArcGeo(Pa=Pa,Pe=Pe,O=O,r=r)  
        else:
            arc=ArcGeo(Pa=Pe,Pe=Pa,O=O,r=r)
            arc.reverse()
            return arc