#!/usr/bin/python
#
#geoent_point
#     Michael Haberlerr
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

#from math import sqrt, sin, cos, atan2, radians, degrees
from dxf2gcode_b02_point import PointClass, LineGeo, PointGeo, PointsClass, ContourClass
#import wx

class PointGeoClass:
    def __init__(self,Nr=0,caller=None):
        self.Typ='Point'
        self.Nr = Nr
        self.Layer_Nr = 0
        self.geo = []
        self.length= 0

        #Lesen der Geometrie
        self.Read(caller)

    def __str__(self):
        # how to print the object
        return("\nTyp: Point")+\
              ("\nNr: %i" %self.Nr)+\
              ("\nLayer Nr: %i" %self.Layer_Nr)+\
              str(self.geo[0])

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol,warning):
        cont.append(ContourClass(len(cont),1,[[i,0]],self.length))
        return warning

        
    def Read(self, caller):
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

        # Farbe (optional)
        cs=lp.index_code(62,caller.start+1,stopcode=0)
        if cs:
            color = lp.line_pair[cs].value
            #print "Point color ='%s'" % color
        else:
            # print "no point color present"
            color = None
            
        Pa=PointClass(x0,y0)
        
        self.geo.append(PointGeo(Pa=Pa,color=color))  
        self.length= 0
        caller.start=s

    def get_start_end_points(self,direction):
        punkt,angle=self.geo[-1].get_start_end_points(direction)
        return punkt,angle
            

