#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
#
#dxf2gcode_b02_point
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


#from Canvas import Oval, Arc, Line
from math import sqrt, sin, cos, atan2, radians, pi, ceil

class PointClass:
    __slots__=["x","y"]  
    def __init__(self, x=0, y=0):
        
        self.x = x
        self.y = y
    def __str__(self):
        return ('X ->%6.3f  Y ->%6.3f' % (self.x, self.y))
        #return ('CPoints.append(PointClass(x=%6.5f, y=%6.5f))' %(self.x,self.y))
    def __cmp__(self, other) : 
        return (self.x == other.x) and (self.y == other.y)
    def __neg__(self):
        return - 1.0 * self
    def __add__(self, other): # add to another point
        return PointClass(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return self + -other
    def __rmul__(self, other):
        return PointClass(other * self.x, other * self.y)
    def __mul__(self, other):
        if type(other) == list:
            #Skalieren des Punkts
            return PointClass(x=self.x * other[0], y=self.y * other[1])
        else:
            #Skalarprodukt errechnen
            return self.x * other.x + self.y * other.y

    def unit_vector(self, Pto=None):
        diffVec = Pto - self
        l = diffVec.distance()
        return PointClass(diffVec.x / l, diffVec.y / l)
    def distance(self, other=None):
        if type(other) == type(None):
            other = PointClass(x=0.0, y=0.0)
        return sqrt(pow(self.x - other.x, 2) + pow(self.y - other.y, 2))
    def norm_angle(self, other=None):
        if type(other) == type(None):
            other = PointClass(x=0.0, y=0.0)
        return atan2(other.y - self.y, other.x - self.x)
    def isintol(self, other, tol):
        return (abs(self.x - other.x) <= tol) & (abs(self.y - other.y) < tol)
    def transform_to_Norm_Coord(self, other, alpha):
        xt = other.x + self.x * cos(alpha) + self.y * sin(alpha)
        yt = other.y + self.x * sin(alpha) + self.y * cos(alpha)
        return PointClass(x=xt, y=yt)
    def get_arc_point(self, ang=0, r=1):
        """ 
        Returns the point on the arc defined by r and the given angel
        @param ang: The angle of the point
        @param radius: The radius around the given point
        @return: A point on given given radius from Point self
        """ 
        
        return PointClass(x=self.x + cos(radians(ang)) * r, \
                          y=self.y + sin(radians(ang)) * r)

    def Write_GCode(self, parent=None, postpro=None):
        point = self.rot_sca_abs(parent=parent)
        return postpro.rap_pos_xy(point)
    
    def plot2can(self, canvas=None, parent=None, tag=None, col='black'):
        pass
    
    def triangle_height(self, other1, other2):
        #Die 3 Längen des Dreiecks ausrechnen
        a = self.distance(other1)
        b = other1.distance(other2)
        c = self.distance(other2)
        return sqrt(pow(b, 2) - pow((pow(c, 2) + pow(b, 2) - pow(a, 2)) / (2 * c), 2))  
      
    def rot_sca_abs(self, sca=None, p0=None, pb=None, rot=None, parent=None):
        if type(sca) == type(None) and type(parent) != type(None):
            p0 = parent.p0
            pb = parent.pb
            sca = parent.sca
            rot = parent.rot
            
            pc = self - pb
            rotx = (pc.x * cos(rot) + pc.y * -sin(rot)) * sca[0]
            roty = (pc.x * sin(rot) + pc.y * cos(rot)) * sca[1]
            p1 = PointClass(x=rotx, y=roty) + p0
            
            #Rekursive Schleife falls selbst eingefügt
            if type(parent.parent) != type(None):
                p1 = p1.rot_sca_abs(parent=parent.parent)
            
        elif type(parent) == type(None) and type(sca) == type(None):
            p0 = PointClass(0, 0)
            pb = PointClass(0, 0)
            sca = [0, 0, 0]
            rot = 0
            
            pc = self - pb
            rot = rot
            rotx = (pc.x * cos(rot) + pc.y * -sin(rot)) * sca[0]
            roty = (pc.x * sin(rot) + pc.y * cos(rot)) * sca[1]
            p1 = PointClass(x=rotx, y=roty) + p0
        else:
            pc = self - pb
            rot = rot
            rotx = (pc.x * cos(rot) + pc.y * -sin(rot)) * sca[0]
            roty = (pc.x * sin(rot) + pc.y * cos(rot)) * sca[1]
            p1 = PointClass(x=rotx, y=roty) + p0
        
        
#        print(("Self:    %s\n" %self)+\
#                ("P0:      %s\n" %p0)+\
#                ("Pb:      %s\n" %pb)+\
#                ("Pc:      %s\n" %pc)+\
#                ("rot:     %0.1f\n" %degrees(rot))+\
#                ("sca:     %s\n" %sca)+\
#                ("P1:      %s\n\n" %p1))
        
        return p1


    def get_nearest_point(self, points):
        """ 
        If there are more then 1 intersection points then use the nearest one to
        be the intersection point.
        @param points: A list of points to be checked for nearest
        @param epoint: The 2nd point which shall be nearest 
        @return: Returns the nearest point
        """ 
        if len(points) == 1:
            point = points[0]
        else:
            mindis = points[0].distance(self)
            point = points[0]
            for i in range(1, len(points)):
                curdis = points[i].distance(self)
                if curdis < mindis:
                    mindis = curdis
                    point = points[i]
                    
        return point

    def get_arc_direction(self,Pe,O):
        """ 
        Calculate the arc direction given from the 3 point. Pa (self), Pe, O
        @param Pe: End Point
        @param O: The center of the arc
        @return: Returns the direction (+ or - pi/2)
        """ 
        a1=self.norm_angle(Pe)
        a2=Pe.norm_angle(O)
        direction=a2-a1
        
        if direction>pi:
            direction=direction-2*pi
        elif direction<-pi:
            direction=direction+2*pi
            
        #print ('Die Direction ist: %s' %direction)
        
        return direction

