#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b01_dxf_import
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

# About Dialog
# First Version of dxf2gcode_b01 Hopefully all works as it should

from Canvas import Oval, Arc, Line
from math import sqrt, sin, cos, atan2, radians, degrees, pi, floor, ceil

class PointClass:
    def __init__(self,x=0,y=0):
        self.x=x
        self.y=y
    def __str__(self):
        return ('X ->%6.3f  Y ->%6.3f' %(self.x,self.y))
        #return ('CPoints.append(PointClass(x=%6.5f, y=%6.5f))' %(self.x,self.y))
    def __cmp__(self, other) : 
      return (self.x == other.x) and (self.y == other.y)
    def __neg__(self):
        return -1.0*self
    def __add__(self, other): # add to another point
        return PointClass(self.x+other.x, self.y+other.y)
    def __sub__(self, other):
        return self + -other
    def __rmul__(self, other):
        return PointClass(other * self.x,  other * self.y)
    def __mul__(self, other):
        if type(other)==list:
            #Skalieren des Punkts
            return PointClass(x=self.x*other[0],y=self.y*other[1])
        else:
            #Skalarprodukt errechnen
            return self.x*other.x + self.y*other.y

    def unit_vector(self,Pto=None):
        diffVec=Pto-self
        l=diffVec.distance()
        return PointClass(diffVec.x/l,diffVec.y/l)
    def distance(self,other=None):
        if type(other)==type(None):
            other=PointClass(x=0.0,y=0.0)
        return sqrt(pow(self.x-other.x,2)+pow(self.y-other.y,2))
    def norm_angle(self,other=None):
        if type(other)==type(None):
            other=PointClass(x=0.0,y=0.0)
        return atan2(other.y-self.y,other.x-self.x)
    def isintol(self,other,tol):
        return (abs(self.x-other.x)<=tol) & (abs(self.y-other.y)<tol)
    def transform_to_Norm_Coord(self,other,alpha):
        xt=other.x+self.x*cos(alpha)+self.y*sin(alpha)
        yt=other.y+self.x*sin(alpha)+self.y*cos(alpha)
        return PointClass(x=xt,y=yt)
    def get_arc_point(self,ang=0,r=1):
        return PointClass(x=self.x+cos(radians(ang))*r,\
                          y=self.y+sin(radians(ang))*r)
    def triangle_height(self,other1,other2):
        #Die 3 Längen des Dreiecks ausrechnen
        a=self.distance(other1)
        b=other1.distance(other2)
        c=self.distance(other2)
        return sqrt(pow(b,2)-pow((pow(c,2)+pow(b,2)-pow(a,2))/(2*c),2))                
      
class PointsClass:
    #Initialisieren der Klasse
    def __init__(self,point_nr=0, geo_nr=0,Layer_Nr=None,be=[],en=[],be_cp=[],en_cp=[]):
        self.point_nr=point_nr
        self.geo_nr=geo_nr
        self.Layer_Nr=Layer_Nr
        self.be=be
        self.en=en
        self.be_cp=be_cp
        self.en_cp=en_cp
        
    
    #Wie die Klasse ausgegeben wird.
    def __str__(self):
        # how to print the object
        return '\npoint_nr ->'+str(self.point_nr)+'\ngeo_nr ->'+str(self.geo_nr) \
               +'\nLayer_Nr ->'+str(self.Layer_Nr)\
               +'\nbe ->'+str(self.be)+'\nen ->'+str(self.en)\
               +'\nbe_cp ->'+str(self.be_cp)+'\nen_cp ->'+str(self.en_cp)

class ContourClass:
    #Initialisieren der Klasse
    def __init__(self,cont_nr=0,closed=0,order=[],length=0):
        self.cont_nr=cont_nr
        self.closed=closed
        self.order=order
        self.length=length
        

    #Komplettes umdrehen der Kontur
    def reverse(self):
        self.order.reverse()
        for i in range(len(self.order)):
            if self.order[i][1]==0:
                self.order[i][1]=1
            else:
                self.order[i][1]=0
        return

    #Ist die klasse geschlossen wenn ja dann 1 zurück geben
    def is_contour_closed(self):

        #Immer nur die Letzte überprüfen da diese neu ist        
        for j in range(len(self.order)-1):
            if self.order[-1][0]==self.order[j][0]:
                if j==0:
                    self.closed=1
                    return self.closed
                else:
                    self.closed=2
                    return self.closed
        return self.closed


    #Ist die klasse geschlossen wenn ja dann 1 zurück geben
    def remove_other_closed_contour(self):
        for i in range(len(self.order)):
            for j in range(i+1,len(self.order)):
                #print '\ni: '+str(i)+'j: '+str(j)
                if self.order[i][0]==self.order[j][0]:
                   self.order=self.order[0:i]
                   break
        return 
    #Berechnen der Zusammengesetzen Kontur Länge
    def calc_length(self,geos=None):        
        #Falls die beste geschlossen ist und erste Geo == Letze dann entfernen
        if (self.closed==1) & (len(self.order)>1):
            if self.order[0]==self.order[-1]:
                del(self.order[-1])

        self.length=0
        for i in range(len(self.order)):
            self.length+=geos[self.order[i][0]].length
        return


    
    def analyse_and_opt(self,geos=None):
        #Errechnen der Länge
        self.calc_length(geos)
        
        #Optimierung für geschlossene Konturen
        if self.closed==1:
            summe=0
            #Berechnung der Fläch nach Gauß-Elling Positive Wert bedeutet CW
            #negativer Wert bedeutet CCW geschlossenes Polygon
            geo_point_l, dummy=geos[self.order[-1][0]].get_start_end_points(self.order[-1][1])            
            for geo_order_nr in range(len(self.order)):
                geo_point, dummy=geos[self.order[geo_order_nr][0]].get_start_end_points(self.order[geo_order_nr][1])
                summe+=(geo_point_l.x*geo_point.y-geo_point.x*geo_point_l.y)/2
                geo_point_l=geo_point
            if summe>0.0:
                self.reverse()

            #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
            min_point=geo_point_l
            min_point_nr=None
            for geo_order_nr in range(len(self.order)):
                geo_point, dummy=geos[self.order[geo_order_nr][0]].get_start_end_points(self.order[geo_order_nr][1])
                #Geringster Abstand nach unten Unten Links
                if (min_point.x+min_point.y)>=(geo_point.x+geo_point.y):
                    min_point=geo_point
                    min_point_nr=geo_order_nr
            #Kontur so anordnen das neuer Startpunkt am Anfang liegt
            self.set_new_startpoint(min_point_nr)
            
        #Optimierung für offene Konturen
        else:
            geo_spoint, dummy=geos[self.order[0][0]].get_start_end_points(self.order[0][1])
            geo_epoint, dummy=geos[self.order[0][0]].get_start_end_points(not(self.order[0][1]))
            if (geo_spoint.x+geo_spoint.y)>=(geo_epoint.x+geo_epoint.y):
                self.reverse()


    #Neuen Startpunkt an den Anfang stellen
    def set_new_startpoint(self,st_p):
        self.order=self.order[st_p:len(self.order)]+self.order[0:st_p]
        
    #Wie die Klasse ausgegeben wird.
    def __str__(self):
        # how to print the object
        return '\ncont_nr ->'+str(self.cont_nr)+'\nclosed ->'+str(self.closed) \
               +'\norder ->'+str(self.order)+'\nlength ->'+str(self.length)

class ArcGeo:
    def __init__(self,Pa=None,Pe=None,O=None,r=1,s_ang=None,e_ang=None,dir=1):
        self.type="ArcGeo"
        self.Pa=Pa
        self.Pe=Pe
        self.O=O
        self.r=abs(r)

        #Falls nicht übergeben dann Anfangs- und Endwinkel ausrechen            
        if type(s_ang)==type(None):
            s_ang=O.norm_angle(Pa)
        if type(e_ang)==type(None):
            e_ang=O.norm_angle(Pe)

        #Aus dem Vorzeichen von dir den extend ausrechnen
        self.ext=e_ang-s_ang
        if dir>0.0:
            self.ext=self.ext%(-2*pi)
            self.ext-=floor(self.ext/(2*pi))*(2*pi)
        else:
            self.ext=self.ext%(-2*pi)
            self.ext+=ceil(self.ext/(2*pi))*(2*pi)

        #Falls es ein Kreis ist Umfang 2pi einsetzen        
        if self.ext==0.0:
            self.ext=2*pi
                   
        self.s_ang=s_ang
        self.e_ang=e_ang
        self.length=self.r*abs(self.ext)

    def __str__(self):
        return ("\nArcGeo")+\
               ("\nPa : %s; s_ang: %0.5f" %(self.Pa,self.s_ang))+\
               ("\nPe : %s; e_ang: %0.5f" %(self.Pe,self.e_ang))+\
               ("\nO  : %s; r: %0.3f" %(self.O,self.r))+\
               ("\next  : %0.5f; length: %0.5f" %(self.ext,self.length))

    def reverse(self):
        Pa=self.Pa
        Pe=self.Pe
        ext=self.ext
        
        self.Pa=Pe
        self.Pe=Pa
        self.ext=ext*-1

    def plot2can(self,canvas,p0,sca,tag):

        #Das Plotten mit Tkinter hat Probleme für kleine Kreissegmente     
##        xy=p0.x+(self.O.x-abs(self.r))*sca[0],-p0.y-(self.O.y-abs(self.r))*sca[1],\
##            p0.x+(self.O.x+abs(self.r))*sca[0],-p0.y-(self.O.y+abs(self.r))*sca[1]
##
##        hdl=Arc(canvas,xy,start=degrees(self.s_ang),extent=degrees(self.ext),style="arc",\
##            tag=tag)

        x=[]; y=[]; hdl=[]
        #Alle 6 Grad ein Segment => 60 Segmente für einen Kreis !!
        segments=int((abs(degrees(self.ext))//6)+1)
        for i in range(segments+1):
            ang=self.s_ang+i*self.ext/segments
            x.append(p0.x+(self.O.x+cos(ang)*abs(self.r))*sca[0])
            y.append(p0.y+(self.O.y+sin(ang)*abs(self.r))*sca[1])

            if i>=1:
                hdl.append(Line(canvas,x[i-1],-y[i-1],x[i],-y[i],tag=tag))       
        return hdl        

    def get_start_end_points(self,direction):
        if not(direction):
            punkt=self.Pa
            angle=degrees(self.s_ang)+90*self.ext/abs(self.ext)
        elif direction:
            punkt=self.Pe
            angle=degrees(self.e_ang)-90*self.ext/abs(self.ext)
        return punkt,angle
    
    def Write_GCode(self,paras,sca,p0,dir,axis1,axis2):
        st_point, st_angle=self.get_start_end_points(dir)
        IJ=(self.O-st_point)*sca
        
        en_point, en_angle=self.get_start_end_points(not(dir))
        ende=en_point*sca+p0
        
        #Vorsicht geht nicht für Ovale
        if ((dir==0)and(self.ext>0))or((dir==1)and(self.ext<0)):
            string=("G3 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,ende.x,axis2,ende.y,IJ.x,IJ.y))
        else:
            string=("G2 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,ende.x,axis2,ende.y,IJ.x,IJ.y))
        return string      


    
class LineGeo:
    def __init__(self,Pa,Pe):
        self.type="LineGeo"
        self.Pa=Pa
        self.Pe=Pe
        self.length=self.Pa.distance(self.Pe)

    def __str__(self):
        return ("\nLineGeo")+\
               ("\nPa : %s" %self.Pa)+\
               ("\nPe : %s" %self.Pe)+\
               ("\nlength: %0.5f" %self.length)        

    def reverse(self):
        Pa=self.Pa
        Pe=self.Pe
        
        self.Pa=Pe
        self.Pe=Pa
        
    def plot2can(self,canvas,p0,sca,tag):
        anf=p0+self.Pa*sca
        ende=p0+self.Pe*sca
        hdl=Line(canvas,anf.x,-anf.y,ende.x,-ende.y,tag=tag)
        return [hdl]


    def get_start_end_points(self,direction):
        if not(direction):
            punkt=self.Pa
            angle=degrees(self.Pa.norm_angle(self.Pe))
        elif direction:
            punkt=self.Pe
            angle=degrees(self.Pe.norm_angle(self.Pa))
        return punkt, angle
    
    def Write_GCode(self,paras,sca,p0,dir,axis1,axis2):
        en_point, en_angle=self.get_start_end_points(not(dir))
        ende=en_point*sca+p0
        string=("G1 %s%0.3f %s%0.3f\n" %(axis1,ende.x,axis2,ende.y))
        return string
        
    def distance2point(self,point):
        try:
            AE=self.Pa.distance(self.Pe)
            AP=self.Pa.distance(point)
            EP=self.Pe.distance(point)
            AEPA=(AE+AP+EP)/2
            return abs(2*sqrt(abs(AEPA*(AEPA-AE)*(AEPA-AP)*(AEPA-EP)))/AE)
        except:
            return 1e10
            

    