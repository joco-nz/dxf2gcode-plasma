#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#NURBS_fittin_by_Biarc_curves
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

from __future__ import division
import matplotlib
#matplotlib see: http://matplotlib.sourceforge.net/ and  http://www.scipy.org/Cookbook/Matplotlib/
#numpy      see: http://numpy.scipy.org/ and http://sourceforge.net/projects/numpy/
matplotlib.use('TkAgg')

from numpy import arange, sin, pi

from matplotlib.axes import Subplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

from Tkconstants import TOP, BOTH, BOTTOM, LEFT, RIGHT,GROOVE
from Tkinter import Tk, Button, Frame
from math import sqrt, sin, cos, tan, atan, atan2, radians, degrees, pi, floor, ceil
import sys

from copy import deepcopy


import logging
logger = logging.getLogger() 


class Point:
    __slots__ = ["x", "y", "z"]  
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
        
    def __str__(self):
        return ('X ->%6.3f  Y ->%6.3f' % (self.x, self.y))
        #return ('CPoints.append(Point(x=%6.5f, y=%6.5f))' %(self.x,self.y))
    def __eq__(self, other):
        return (-1e-12 < self.x - other.x < 1e-12) and (-1e-12 < self.y - other.y < 1e-12)
    
    def __cmp__(self,other):
        if self.x<other.x:
            return -1
        elif self.x>other.x:
            return 1
        elif self.x==other.x and self.y<other.y:
            return -1
        elif self.x==other.x and self.y>other.y:
            return 1
        else:
            return 0
        
    def __neg__(self):
        return -1.0 * self
    def __add__(self, other): # add to another Point
        return Point(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return self + -other
    def __rmul__(self, other):
        return Point(other * self.x, other * self.y)
    def __mul__(self, other):
        """
        The function which is called if the object is multiplied with another
        object. Dependent on the object type different operations are performed
        @param other: The element which is used for the multiplication
        @return: Returns the result dependent on object type
        """
        if isinstance(other, list):
            #Scale the points
            return Point(x=self.x * other[0], y=self.y * other[1])
        elif isinstance(other, (int, float, long, complex)):
            return Point(x=self.x*other, y=self.y*other)
        elif isinstance(other,Point):
            #Calculate Scalar (dot) Product
            return self.x * other.x + self.y * other.y
        else:
            logger.warning("Unsupported type: %s" %type(other))
            
    def __truediv__(self, other):
        return Point(x=self.x / other, y=self.y / other)

    def tr(self,message):
        return message
    def cross_product(self, other):
        """
        Returns the cross Product of two points
        @param P1: The first Point
        @param P2: The 2nd Point
        @return: dot Product of the points.
        """ 
        return Point(self.y*other.z - self.z*other.y, self.z*other.x - self.x*other.z, self.x*other.y - self.y*other.x)

    def dotProd(self,P2):
        """
        Returns the dotProduct of two points
        @param self: The first Point
        @param other: The 2nd Point
        @return: dot Product of the points.
        """ 
        
        return (self.x*P2.x) + (self.y*P2.y)

    def ccw(self,B,C):
        """
        This functions gives the Direction in which the three points are located.
        @param B: a second point
        @param C: a third point
        @return: If the slope of the line AB is less than the slope of the line
        AC then the three points are listed in a counterclockwise order 
        """
        #return (C.y-self.y)*(B.x-self.x) > (B.y-self.y)*(C.x-self.x)
        area2 = (B.x - self.x) * (C.y - self.y) - (C.x - self.x) * (B.y - self.y)
        if (area2 < 0): 
            return -1
        elif area2 > 0: 
            return +1;
        else:
            return  0;
    
    
    def between(self,B,C):
        """
        is c between a and b?     // Reference: O' Rourke p. 32
        @param B: a second point
        @param C: a third point
        @return: If C is between those points
        """
        if (self.ccw(B, C) != 0):
            return False
        if (self.x == B.x) and (self.y == B.y):
            return (self.x == C.x) and (self.y == C.y)
        
        elif (self.x != B.x):
            # ab not vertical
            return ((self.x <= C.x) and (C.x <= B.x)) or ((self.x >= C.x) and (C.x >= B.x))
        
        else:
            # ab not horizontal
            return ((self.y <= C.y) and (C.y <= B.y)) or ((self.y >= C.y) and (C.y >= B.y))
        
    def unit_vector(self, Pto=None):
        """
        Returns vector of length 1 with similar direction as input
        @param Pto: The other point 
        @return: Returns the Unit vector
        """
        diffVec = Pto - self
        l = diffVec.distance()
        return Point(diffVec.x / l, diffVec.y / l)

    def distance(self, other=None):
        """Returns distance between two given points"""
        if type(other) == type(None):
            other = Point(x=0.0, y=0.0)
        
        if isinstance(other,Point):
            return sqrt(pow(self.x - other.x, 2) + pow(self.y - other.y, 2))
        elif isinstance(other,LineGeo):
            return other.distance(self)

    def norm_angle(self, other=None):
        """Returns angle between two given points"""
        if type(other) == type(None):
            other = Point(x=0.0, y=0.0)
        return atan2(other.y - self.y, other.x - self.x)

    def isintol(self, other, tol):
        """Are the two points within 'tol' tolerance?"""
        return (abs(self.x - other.x) <= tol) & (abs(self.y - other.y) < tol)

    def transform_to_Norm_Coord(self, other, alpha):
        xt = other.x + self.x * cos(alpha) + self.y * sin(alpha)
        yt = other.y + self.x * sin(alpha) + self.y * cos(alpha)
        return Point(x=xt, y=yt)

    def get_arc_point(self, ang=0, r=1):
        """ 
        Returns the Point on the arc defined by r and the given angle
        @param ang: The angle of the Point
        @param radius: The radius from the given Point
        @return: A Point at given radius and angle from Point self
        """ 
        return Point(x=self.x + cos(ang) * r, \
                     y=self.y + sin(ang) * r)
        
    def get_normal_vector(self,other,r=1):
        """
        This function return the Normal to a vector defined by self and other
        @param: The second point
        @param r: The length of the normal (-length for other direction)
        @return: Returns the Normal Vector
        """
        unit_vector=self.unit_vector(other)
        return Point(x=unit_vector.y*r,y=-unit_vector.x*r)
        
    def triangle_height(self, other1, other2):
        """
        Calculate height of triangle given lengths of the sides
        @param other1: Point 1 for triangle
        @param other2: Point 2 for triangel
        """
        #The 3 lengths of the triangle to calculate
        a = self.distance(other1)
        b = other1.distance(other2)
        c = self.distance(other2)
        return sqrt(pow(b, 2) - pow((pow(c, 2) + pow(b, 2) - pow(a, 2)) / (2 * c), 2))
      
    def get_nearest_point(self, points):
        """ 
        If there are more then 1 intersection points then use the nearest one to
        be the intersection Point.
        @param points: A list of points to be checked for nearest
        @return: Returns the nearest Point
        """ 
        if len(points) == 1:
            Point = points[0]
        else:
            mindis = points[0].distance(self)
            Point = points[0]
            for i in range(1, len(points)):
                curdis = points[i].distance(self)
                if curdis < mindis:
                    mindis = curdis
                    Point = points[i]
                    
        return Point

    def get_arc_direction(self, Pe, O):
        """ 
        Calculate the arc direction given from the 3 Point. Pa (self), Pe, O
        @param Pe: End Point
        @param O: The center of the arc
        @return: Returns the direction (+ or - pi/2)
        """ 
        a1 = self.norm_angle(Pe)
        a2 = Pe.norm_angle(O)
        direction = a2 - a1
        
        if direction > pi:
            direction = direction - 2 * pi
        elif direction < -pi:
            direction = direction + 2 * pi
            
        #print ('The Direction is: %s' %direction)
        
        return direction

    def plot2plot(self, plot,format='xr'):
        plot.plot([self.x],[self.y],format)
        
class BoundingBox:
    """ 
    Bounding Box Class. This is the standard class which provides all std. 
    Bounding Box methods.
    """ 
    def __init__(self, Pa=Point(0, 0), Pe=Point(0, 0), hdl=[]):
        """ 
        Standard method to initialize the class
        """ 
        self.Pa = Pa
        self.Pe = Pe
        
    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        s = ("\nPa : %s" % (self.Pa)) + \
           ("\nPe : %s" % (self.Pe))
        return s
    
    def joinBB(self, other):
        """
        Joins two Bounding Box Classes and returns the new one
        @param other: The 2nd Bounding Box
        @return: Returns the joined Bounding Box Class
        """
        
        if type(self.Pa) == type(None) or type(self.Pe) == type(None):
            return BoundingBox(copy(other.Pa), copy(other.Pe))
        
        xmin = min(self.Pa.x, other.Pa.x)
        xmax = max(self.Pe.x, other.Pe.x)
        ymin = min(self.Pa.y, other.Pa.y)
        ymax = max(self.Pe.y, other.Pe.y)
        
        return BoundingBox(Pa=Point(xmin, ymin), Pe=Point(xmax, ymax))
    
    def hasintersection(self, other=None, tol=0.0):
        """
        Checks if the two bounding boxes have an intersection
        @param other: The 2nd Bounding Box
        @return: Returns true or false
        """        
        x_inter_pos = (self.Pe.x + tol > other.Pa.x) and \
        (self.Pa.x - tol < other.Pe.x)
        y_inter_pos = (self.Pe.y + tol > other.Pa.y) and \
        (self.Pa.y - tol < other.Pe.y)
     
        return x_inter_pos and y_inter_pos
    
    def pointisinBB(self, Point=Point(), tol=0.01):
        """
        Checks if the Point is within the bounding box
        @param Point: The Point which shall be ckecke
        @return: Returns true or false
        """
        x_inter_pos = (self.Pe.x + tol > Point.x) and \
        (self.Pa.x - tol < Point.x)
        y_inter_pos = (self.Pe.y + tol > Point.y) and \
        (self.Pa.y - tol < Point.y)
        return x_inter_pos and y_inter_pos
     
class LineGeo:
    def __init__(self,Pa,Pe):
        self.type="LineGeo"
        self.Pa=Pa
        self.Pe=Pe
        self.length=self.Pa.distance(self.Pe)
        self.inters=[]
        self.calc_bounding_box()

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\type:%s" % self.type) + \
               ("\nPa : %s" % self.Pa) + \
               ("\nPe : %s" % self.Pe) + \
               ("\nBB : %s" % self.BB) + \
               ("\ninters : %s" % self.inters) + \
               ("\nlength: %0.5f" % self.length)  
               

    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        Pa = Point(x=min(self.Pa.x, self.Pe.x), y=min(self.Pa.y, self.Pe.y))
        Pe = Point(x=max(self.Pa.x, self.Pe.x), y=max(self.Pa.y, self.Pe.y))
        
        self.BB = BoundingBox(Pa=Pa, Pe=Pe)
        
    def colinear(self,other):
        """
        Check if two lines with same point self.Pe==other.Pa are colinear
        @param other: the possibly colinear line
        """

        A=self.Pa
        B=self.Pe
        #C= other.Pa
        D= other.Pe
        return A.ccw(B, D) == 0
    
  
    def cmp_asscending(self,P1,P2):
        """
        Compare Function for the sorting
        """  
        d1= P1.distance(self.Pa)
        d2= P2.distance(self.Pa)
              
        if d1>d2:
            return 1
        elif d1==d2:
            return 0
        else:
            return -1

    def colinearoverlapping(self,other):
        """
        Check if the lines are colinear overlapping
        Ensure A<B, C<D, and A<=C (which you can do by simple swapping). Then:
        •if B<C, the segments are disjoint
        •if B=C, then the intersection is the single point B=C
        •if B>C, then the intersection is the segment [C, min(B, D)]
        @param other: The other line
        @return: True if they are overlapping
        """
        if not(self.colinear(other)):
            return False
        else:
            if self.Pa<self.Pe:
                A=self.Pa
                B=self.Pe
            else:
                A=self.Pe
                B=self.Pa
            if other.Pa<self.Pe:
                C=other.Pa
                D=other.Pe
            else:
                C=other.Pe
                D=other.Pa
            
            #Swap lines if required
            if not(A<=C):
                A,B,C,D=C,D,A,B
                
        if B<C:
            return False
        elif B==C:
            return False
        else:
            return True
                      
    def colinearconnected(self,other):
        """
        Check if Lines are connected and colinear
        @param other: Another Line which will be checked
        """
        
        
        if not(self.colinear(other)):
            return False
        elif self.Pa==other.Pa:
            return True
        elif self.Pe==other.Pa:
            return True
        elif self.Pa==other.Pe:
            return True
        elif self.Pe==other.Pe:
            return True
        else:
            return False
        
#    def distance2point(self,point):
#        AE=self.Pa.distance(self.Pe)
#        AP=self.Pa.distance(point)
#        EP=self.Pe.distance(point)
#        AEPA=(AE+AP+EP)/2
#        return abs(2*sqrt(abs(AEPA*(AEPA-AE)*(AEPA-AP)*(AEPA-EP)))/AE)
#    
    
    def distance(self, other=[]):
        """
        Find the distance between 2 geometry elements. Possible is CCLineGeo
        and CCArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        if isinstance(other,LineGeo):
            return self.distance_line_line(other)
        elif isinstance(other,Point):
            return self.distance_point_line(other)
        else:
            logger.error(self.tr("Unsupported geometry type: %s" %type(other))) 
            
    def distance_line_line(self,other):
        """
        Find the distance between 2 ccLineGeo elements. 
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        
        return min(self.distance_point_line(other.Pa),
                   self.distance_point_line(other.Pe),
                   other.distance_point_line(self.Pa),
                   other.distance_point_line(self.Pe))
            
        
    def distance_point_line(self,Point):
        """
        Find the shortest distance between CCLineGeo and Point elements.  
        Algorithm acc. to 
        http://notejot.com/2008/09/distance-from-Point-to-line-segment-in-2d/
        http://softsurfer.com/Archive/algorithm_0106/algorithm_0106.htm
        @param Point: the Point
        @return: The shortest distance between the Point and Line
        """
        
        d=self.Pe-self.Pa
        v=Point-self.Pa
    
        t=d.dotProd(v)
        
        if t<=0:
            #our Point is lying "behind" the segment
            #so end Point 1 is closest to Point and distance is length of
            #vector from end Point 1 to Point.
            return self.Pa.distance(Point)
        elif t>=d.dotProd(d):
            #our Point is lying "ahead" of the segment
            #so end Point 2 is closest to Point and distance is length of
            #vector from end Point 2 to Point.
            return self.Pe.distance(Point)
        else:
            #our Point is lying "inside" the segment
            #i.e.:a perpendicular from it to the line that contains the line
            #segment has an end Point inside the segment
            return sqrt(v.dotProd(v) - (t*t)/d.dotProd(d));
                
    
    def find_inter_point(self, other, type='TIP'):
        """
        Find the intersection between 2 LineGeo elements. There can be only one
        intersection between 2 lines. Returns also FIP which lay on the ray.
        @param other: the instance of the 2nd geometry element.
        @param type: Can be "TIP" for True Intersection Point or "Ray" for 
        Intersection which is in Ray (of Line)
        @return: a list of intersection points. 
        """
        
        if self.colinear(other):
            return []
        
        elif type=='TIP' and not(self.intersect(other)):
            return []
        

        dx1 = self.Pe.x - self.Pa.x
        dy1 = self.Pe.y - self.Pa.y
        
        dx2 = other.Pe.x - other.Pa.x
        dy2 = other.Pe.y - other.Pa.y

        dax = self.Pa.x - other.Pa.x
        day = self.Pa.y - other.Pa.y

        #Return nothing if one of the lines has zero length
        if (dx1 == 0 and dy1 == 0) or (dx2 == 0 and dy2 == 0):
            return []
        

        #If to avoid division by zero.
        try:
            if(abs(dx2) >= abs(dy2)):
                v1 = (day - dax * dy2 / dx2) / (dx1 * dy2 / dx2 - dy1)
                v2 = (dax + v1 * dx1) / dx2    
            else:
                v1 = (dax - day * dx2 / dy2) / (dy1 * dx2 / dy2 - dx1)
                v2 = (day + v1 * dy1) / dy2
        except:
            return []
            
        return Point(x=self.Pa.x + v1 * dx1,
                          y=self.Pa.y + v1 * dy1)
#        return IPoint(x=self.Pa.x + v1 * dx1,
#                          y=self.Pa.y + v1 * dy1,
#                          v1=v1,
#                          v2=v2,
#                          geo1=self,
#                          geo2=other)
#    

    def get_start_end_points(self,direction):
        if direction==0:
            punkt=self.Pa
            angle=self.Pe.norm_angle(self.Pa)
        elif direction==1:
            punkt=self.Pe
            angle=self.Pa.norm_angle(self.Pe)
        return punkt, angle
    
    def plot2plot(self, plot,format='-m'):
        plot.plot([self.Pa.x,self.Pe.x],[self.Pa.y,self.Pe.y],format)
        """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """ 

    
    def intersect(self,other):
        """
        Check if there is an intersection of the two line
        @param, a second line which shall be checked for intersection
        """
        A=self.Pa
        B=self.Pe
        C= other.Pa
        D= other.Pe
        return A.ccw(C,D) != B.ccw(C,D) and A.ccw(B,C) != A.ccw(B,D)
    
    def join_colinear_line(self,other):
        """
        Check if the two lines are colinear connected or inside of each other, in 
        this case these lines will be joined to one common line, otherwise return
        both lines
        @param other: a second line
        @return: Return one or two lines 
        """
        if self.colinearconnected(other)or self.colinearoverlapping(other):
            if self.Pa < self.Pe:
                newPa=min(self.Pa,other.Pa,other.Pe)
                newPe=max(self.Pe,other.Pa,other.Pe)
                
            else:
                newPa=max(self.Pa,other.Pa,other.Pe)
                newPe=min(self.Pe,other.Pa,other.Pe)
            return [LineGeo(newPa,newPe)]
        else:
            return [self,other]
                
        
    
    

    def liesonsegment(self,c):
        """
        Check if Point is colinear and within the Line
        @param c: A Point which will be checked
        Check if slope of a to c is the same as a to b ;
        # that is, when moving from a.x to c.x, c.y must be proportionally
        # increased than it takes to get from a.x to b.x .

        # Then, c.x must be between a.x and b.x, and c.y must be between a.y and b.y.
        # => c is after a and before b, or the opposite
        # that is, the absolute value of cmp(a, b) + cmp(b, c) is either 0 ( 1 + -1 )
        #    or 1 ( c == a or c == b)
        
        """
        if not(c):
            return False
        
        a, b = self.Pa, self.Pe             

#        return ((b.x - a.x) * (c.y - a.y) == (c.x - a.x) * (b.y - a.y) and 
#                abs(cmp(a.x, c.x) + cmp(b.x, c.x)) <= 1 and
#                abs(cmp(a.y, c.y) + cmp(b.y, c.y)) <= 1)
        
        dotProduct = (c.x - a.x) * (c.x - b.x) + (c.y - a.y) * (c.y - b.y);
        return dotProduct < 0 

    
    def rawoffset(self, radius=10.0, direction=41):
        """
        Returns the Offset Curve defined by radius and offset direction of the 
        geometry self.
        @param radius: The offset of the curve
        @param direction: The direction of offset 41==Left 42==Right
        @return: A list of 2 CCLineGeo's will be returned.
        """   
        Pa, s_angle = self.get_start_end_points(0)
        Pe, e_angle = self.get_start_end_points(1)
        if direction == 41:
            offPa = Pa.get_arc_point(s_angle + pi/2, radius)
            offPe = Pe.get_arc_point(e_angle - pi/2, radius)
        elif direction == 42:
            offPa = Pa.get_arc_point(s_angle - pi/2, radius)
            offPe = Pe.get_arc_point(e_angle + pi/2, radius)
            
        offLine = CCLineGeo(Pa=offPa, Pe=offPe)
        offLine.calc_bounding_box()
        
        return [offLine]
    
    def reverse(self):
        """ 
        Reverses the direction of the arc (switch direction).
        """ 
        self.Pa, self.Pe = self.Pe, self.Pa
    
    def sort_inters_asscending(self):
        """
        Sorts the intersection points in self.inters in asscending order
        """       
        self.inters.sort(self.cmp_asscending)
          

    
       
    def split_into_2geos(self, ipoint=Point()):
        """
        Splits the given geometry into 2 not self intersection geometries. The
        geometry will be splitted between ipoint and Pe.
        @param ipoint: The Point where the intersection occures
        @return: A list of 2 CCLineGeo's will be returned if intersection is inbetween
        """
        #The Point where the geo shall be splitted
        if not(ipoint):
            return [self]
        elif self.liesonsegment(ipoint):
            return self.split_geo_at_point(ipoint)
        else:
            return [self]
        
    def split_geo_at_point(self,spoint):
        """
        Splits the given geometry into 2 geometries. The
        geometry will be splitted at Point spoint.
        @param ipoint: The Point where the intersection occures
        @return: A list of 2 CCArcGeo's will be returned.
        """
        Li1 = LineGeo(Pa=self.Pa, Pe=spoint)
        Li2 = LineGeo(Pa=spoint, Pe=self.Pe)
        
        return [Li1, Li2]
      
class ShapeClass():
    """
    The Shape Class may contain a Polyline or a Polygon. These are based on geos
    which are stored in this class.  
    """
    def __init__(self,geos=[], closed=False, length=0.0):
        """ 
        Standard method to initialize the class
        @param closed: Gives information about the shape, when it is closed this
        value becomes 1. Closed means it is a Polygon, otherwise it is a Polyline
        @param length: The total length of the shape including all geometries
        @param geos: The list with all geometries included in the shape. May 
        also contain arcs. These will be reflected by multiple lines in order 
        to easy calclations.
        """       
        self.geos = geos
        self.closed = closed
        self.length = length
        self.BB = BoundingBox(Pa=None, Pe=None)

                
    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ('\ntype:        %s' % self.type) + \
               ('\nclosed:      %i' % self.closed) + \
               ('\nlen(geos):   %i' % len(self.geos)) + \
               ('\ngeos:        %s' % self.geos) 
               
    def contains_point(self, p=Point(x=0, y=0)):
        """
        This method may be called in order to check if point is inside a closed
        shape
        @param p: The point which shall be checked
        """
        
        if not(self.closed):
            return False
        
    def FindNearestStPoint(self, StPoint=Point(x=0.0, y=0.0)):
        """
        Find Nearest Point to given StartPoint. This is used to change the
        start of closed contours
        @param StPoint: This i sthe point for which the nearest point shall
        be searched.
        """
                
        if self.closed:
            logger.debug(self.tr("Clicked Point: %s") %StPoint)
            start, dummy = self.geos[0].get_start_end_points(0, self.parent)
            min_distance = start.distance(StPoint)
            
            logger.debug(self.tr("Old Start Point: %s") %start)
            
            min_geo_nr = 0
            for geo_nr in range(1, len(self.geos)):
                start, dummy = self.geos[geo_nr].get_start_end_points(0, self.parent)
                
                if (start.distance(StPoint) < min_distance):
                    min_distance = start.distance(StPoint)
                    min_geo_nr = geo_nr
    
            #Overwrite the geometries in changed order.
            self.geos = self.geos[min_geo_nr:len(self.geos)] + self.geos[0:min_geo_nr]
            
            start, dummy = self.geos[0].get_start_end_points(0, self.parent)
            logger.debug(self.tr("New Start Point: %s") % start)
                     

    def get_st_en_points(self, dir=None):
        """
        Returns the start/end Point and its direction
        @param dir: direction - 0 to return start Point or 1 to return end Point
        @return: a list of Point and angle 
        """
        start, start_ang = self.geos[0].get_start_end_points(0, self.parent)
        ende, end_ang = self.geos[-1].get_start_end_points(1, self.parent)
        
        if dir == None:
            return start, ende
        elif dir == 0:
            return start, start_ang
        elif dir == 1:
            return ende, end_ang
        
    def join_colinear_lines(self):
        """
        This function is called to search for colinear connected lines an joins 
        them if there are any
        """
        # Do only if more then 2 geometies
        if len(self.geos)<2:
            return
                
        new_geos=[self.geos[0]]
        for i in range(1,len(self.geos)):
            geo1=new_geos[-1]
            geo2=self.geos[i]
            
            #Remove first geometry and add result of joined geometries. Required
            #Cause the join will give back the last 2 geometries.
            new_geos.pop()
            new_geos+=geo1.join_colinear_line(geo2)
            
            
        #For closed polylines check if the first and last items are colinear
        if self.closed:
            geo1=new_geos[-1]
            geo2=new_geos[0]
            joined_geos=geo1.join_colinear_line(geo2)
            
            #If they are joind replace firste item by joined and remove last one
            if len(joined_geos)==1:
                new_geos[0]=joined_geos[0]
                new_geos.pop()    
        
        self.geos=new_geos
            

            

    def make_shape_ccw(self):
        """ 
        This method is called after the shape has been generated before it gets
        plotted to change all shape direction to a CW shape.
        """ 

        if not(self.closed):
            return
        
        # Optimization for closed shapes
        # Start value for the first sum
        
        summe = 0.0
        for geo in self.geos:
            if geo.type == 'LineGeo':
                start = geo.Pa
                ende  = geo.Pe
                summe += (start.x + ende.x) * (ende.y - start.y) / 2
                start = ende
            elif geo.type == 'ArcGeo':
                segments = int((abs(degrees(geo.ext)) // 90) + 1)
                for i in range(segments): 
                    ang = geo.s_ang + (i + 1) * geo.ext / segments
                    ende = Point(x=(geo.O.x + cos(ang) * abs(geo.r)),
                                 y=(geo.O.y + sin(ang) * abs(geo.r)))
                    summe += (start.x + ende.x) * (ende.y - start.y) / 2
                    start = ende

        #Positiv sum means the shape is oriented CCW
        if summe > 0.0:
            self.reverse()
            logger.debug(self.tr("Had to reverse the shape to be ccw"))
            
    def reverse(self):
        """ 
        Reverses the direction of the whole shape (switch direction).
        """ 
        self.geos.reverse()
        for geo in self.geos: 
            geo.reverse()
                  
    def tr(self, string_to_translate):
        """
        Dummy Function required to reuse existing log messages.
        @param: string_to_translate: a unicode string    
        @return: the translated unicode string if it was possible to translate
        """
        return string_to_translate

class offShapeClass(ShapeClass):
    """
    This Class is used to generate The fofset aof a shape according to:
    "A pair-wise offset Algorithm for 2D point sequence curve"
    http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.101.8855
    """
    def __init__(self,parent=ShapeClass(), offset=1, offtype='in'):
        """ 
        Standard method to initialize the class
        @param closed: Gives information about the shape, when it is closed this
        value becomes 1. Closed means it is a Polygon, otherwise it is a Polyline
        @param length: The total length of the shape including all geometries
        @param geos: The list with all geometries included in the shape. May 
        also contain arcs. These will be reflected by multiple lines in order 
        to easy calclations.
        """

        
        ShapeClass.__init__(self, closed=parent.closed, 
                            length=parent.length,
                            geos=deepcopy(parent.geos))
        self.offset=offset
        self.offtype= offtype
        self.segments=[]
        
        self.make_shape_ccw()
        self.join_colinear_lines()

        self.make_segment_types()
        self.start_vertex=self.get_start_vertex()     
        
        self.PairWiseInterferenceDetection(self.start_vertex,self.start_vertex-1)
        
        
    def make_segment_types(self):
        """
        This function is called in order to generate the segements according to 
        Definiton 2.
        An edge (line) is a linear segment and a reflex vertex is is reflex 
        segment. Colinear lines are assumed to be removed prior to the segment 
        type definition.        
        """
         # Do only if more then 2 geometies
        if len(self.geos)<2:
            return
            
        #Start with first Vertex if the line is closed                
        if self.closed:
            start=0
        else:
            start=1
            
        for i in range(start,len(self.geos)):
            geo1=self.geos[i-1]
            geo1.end_normal=geo1.Pa.get_normal_vector(geo1.Pe)
            geo2=self.geos[i]
            geo2.start_normal=geo2.Pa.get_normal_vector(geo2.Pe)
            geo2.end_normal=geo2.Pa.get_normal_vector(geo2.Pe)
          
            #If it is a reflex vertex add a reflex segemnt (single point)
            if (((geo1.Pa.ccw(geo1.Pe,geo2.Pe)==1) and  self.offtype=="in") or
                (geo1.Pa.ccw(geo1.Pe,geo2.Pe)==-1 and self.offtype=="out")):
                geo1.Pe.start_normal=geo1.end_normal
                geo1.Pe.end_normal=geo2.end_normal
                self.segments+=[geo1.Pe]           
            
            #Add the linear segment which is a line connecting 2 vertices
            self.segments+=[geo2]
        
    def get_start_vertex(self):
        """
        Find first convex vertex to start PWID Testing. Any of the convex vertexes
        can be used as a starting point 
        """
        if self.closed:
            start=0
        else:
            start=1
        
        for i in range(start,len(self.geos)):
            seg1=self.segments[i-1]
            seg2=self.segments[i]
            if isinstance(seg1,LineGeo) and isinstance(seg2,LineGeo):
                return i
            
        #If no start_vertex exisst return None
        return None
    
    def interfering_full(self,segment1,dir,segment2):
        """
        Check if the Endpoint (dependent on dir) of segment 1 is interfering with 
        segment 2 Definition according to Definition 6
        @param segment 1: The first segment 
        @param dir: The direction of the line 1, as given -1 reversed direction
        @param segment 2: The second segment to be checked
        @ return: Returns True or False
        """
        
        #if segement 1 is inverted change End Point
        if isinstance(segment1,LineGeo) and dir==1:
            Pe=segment1.Pe
        elif isinstance(segment1,LineGeo) and dir==-1:
            Pe=segment1.Pa
        elif isinstance(segment1,Point):
            Pe=segment1
        else:
            logger.error("Unsupportet Object type: %s" %type(segment1))
            
        # if we cut outside reverse the offset
        if self.offtype=="out":
            offset=-self.offset
        else:
            offset=self.offset
            
        distance=segment2.distance(Pe+segment1.end_normal*offset)
        

        # If the distance from the Segment to the Center of the Tangential Circle 
        #is smaller then the radius we have an intersection
        logger.debug(distance)
        return distance<=offset
    
    def interfering_partly(self,segment1,dir,segment2):
        """
        Check if any tangential circle of segment 1 is interfering with 
        segment 2. Definition according to Definition 5
        @param segment 1: The first Line 
        @param dir: The direction of the segment 1, as given -1 reversed direction
        @param segment 2: The second line to be checked
        @ return: Returns True or False
        """
        # if we cut outside reverse the offset
        # if we cut outside reverse the offset
        if self.offtype=="out":
            offset=-self.offset
        else:
            offset=self.offset
        
        #if segement 1 is inverted change End Point
        if isinstance(segment1,LineGeo):
            Pa=segment1.Pa+segment1.start_normal*offset
            Pe=segment1.Pe+segment1.end_normal*offset
        elif isinstance(segment1,Point):
            Pa=segment1+segment1.start_normal*offset
            Pe=segment1+segment1.end_normal*offset
        else:
            logger.error("Unsupportet Object type: %s" %type(segment1))
            
        offLine=LineGeo(Pa,Pe)
     
        # If the distance from the Line to the Center of the Tangential Circle 
        #is smaller then the radius we have an intersection
        logger.debug(segment2.distance(offLine))
        return segment2.distance(offLine)<=offset
    
    def Interfering_relation(self, segment1, dir1, segment2, dir2):
        """
        Check the interfering relation between two segements (segment1 and segment2).
        Definition acccording to Definition 6 
        @param segment1: The first segment
        @param dir1: The direction of segment 1 (-1 for reversed)
        @param segment2: The second segment
        @param dir2: The direction of segment 2 (-1 for reversed)
        @return: Returns one of [full, partial, reverse] interfering relations 
        for both segments
        """
        
        if self.interfering_full(segment1, dir1,segment2):
            L1_status="full"
        elif self.interfering_partly(segment1,dir1,segment2):
            L1_status="partial"
        else:
            L1_status="reverse"
            
        if self.interfering_full(segment2, dir2, segment1):
            L2_status="full"
        elif self.interfering_partly(segment2,dir2,segment1):
            L2_status="partial"
        else:
            L2_status="reverse"
        
        return [L1_status,L2_status]
    
    def PairWiseInterferenceDetection(self, forward, backward):
        """
        Returns the first forward and backward segment nr. for which both
        interfering conditions are partly.
        @param foward: The nr of the first forward segment
        @param backward: the nr. of the first backward segment
        @return: forward, backward
        """

        segment1=self.segments[forward]
        segment2=self.segments[backward]
        [L1_status,L2_status]=self.Interfering_relation(segment1,1,segment2,-1)
        
        logger.debug("L1_status: %s,L2_status: %s" %(L1_status,L2_status))
              
        
                
class PlotClass:
    """
    Class which calls matplotlib to plot the results.
    """
    def __init__(self,master=[]):
        
        self.master=master
 
        #Erstellen des Fensters mit Rahmen und Canvas
        self.figure = Figure(figsize=(7,7), dpi=100)
        self.frame_c=Frame(relief = GROOVE,bd = 2)
        self.frame_c.pack(fill=BOTH, expand=1,)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame_c)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=1)

        #Erstellen der Toolbar unten
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.frame_c)
        self.toolbar.update()
        self.canvas._tkcanvas.pack( fill=BOTH, expand=1)

    def plot_lines_plot(self,lines,sb_nr=111,text=""):
        self.plot1 = self.figure.add_subplot(sb_nr)
        self.plot1.set_title("Lines Plot %s" %sb_nr)
        self.plot1.grid(b=True, which='both', color='0.65',linestyle='-')
        self.plot1.hold(True)
        self.plot1.text(0.5, 0, text, ha='left', fontsize=8)
  
        for line_nr in range(len(lines)):
            
            line=lines[line_nr]
            
            line.plot2plot(self.plot1)
            line.Pa.plot2plot(self.plot1,format='xr')
            line.Pe.plot2plot(self.plot1,format='og')
            self.plot1.text(line.Pa.x,line.Pa.y,line_nr,ha='left', fontsize=10, color='red')
            
        self.plot1.axis('scaled')     
        self.plot1.margins(y=.1, x=.1)
        self.plot1.autoscale(True,'both',False)
        self.canvas.show()
        
    def plot_segments(self,segments,sb_nr=111,text=""):
        self.plot1 = self.figure.add_subplot(sb_nr)
        self.plot1.set_title("Segments Plot %s" %sb_nr)
        self.plot1.grid(b=True, which='both', color='0.65',linestyle='-')
        self.plot1.hold(True)
        self.plot1.text(0.5, 0, text, ha='left', fontsize=8)
  
        for segment_nr in range(len(segments)):
            
            seg=segments[segment_nr]
            seg.plot2plot(self.plot1)
            if isinstance(seg,LineGeo):
                Pa=(seg.Pa+seg.Pe)/2
                
                seg.Pa.plot2plot(self.plot1,format='xr')
                seg.Pe.plot2plot(self.plot1,format='xr')
            else:
                seg.plot2plot(self.plot1,format='og')
                Pa=seg
            self.plot1.text(Pa.x+0.1,Pa.y+0.1,segment_nr,ha='left', fontsize=10, color='red')
            
        self.plot1.margins(y=.1, x=.1)
        self.plot1.autoscale(True,'both',False)
        self.canvas.show()
    
class ExampleClass:
    def __init__(self):
        pass
    def CheckColinearLines(self):
        master.title("Check for Colinear Lines and Join")
        
        L1=LineGeo(Point(x=0,y=0),Point(x=2,y=2))
        L2=LineGeo(Point(x=2,y=2),Point(x=4,y=4))
        L3=LineGeo(Point(x=1.5,y=1.5),Point(x=4,y=4))
        L4=LineGeo(Point(x=2.5,y=2.5),Point(x=4,y=4))
        L5=LineGeo(Point(x=1.5,y=1.5), Point(x=3,y=0))
        
        lines1=L1.join_colinear_line(L2)
        lines2=L1.join_colinear_line(L3)
        lines3=L1.join_colinear_line(L4)
        lines4=L1.join_colinear_line(L5)

        text1=("\nCheck for Intersection L1; L2: %s \n" %L1.intersect(L2))
        text1+=("Check for Colinear L1; L2: %s \n" %L1.colinear(L2))
        text1+=("Check for colinearoverlapping L1; L2: %s \n" %L1.colinearoverlapping(L2))
        text1+=("Check for colinearconnected L1; L2: %s \n" %L1.colinearconnected(L2))
        logger.debug(text1)
        
        text2=("\nCheck for Intersection L1; L3: %s \n" %L1.intersect(L3))
        text2+=("Check for Colinear L1; L3: %s \n" %L1.colinear(L3))
        text2+=("Check for colinearoverlapping L1; L3: %s \n" %L1.colinearoverlapping(L3))
        text2+=("Check for colinearconnected L1; L3: %s \n" %L1.colinearconnected(L3))
        logger.debug(text2)
        
        
        text3=("\nCheck for Intersection L1; L4: %s \n" %L1.intersect(L4))
        text3+=("Check for Colinear L1; L4: %s \n" %L1.colinear(L4))
        text3+=("Check for colinearoverlapping L1; L4: %s \n" %L1.colinearoverlapping(L4))
        text3+=("Check for colinearconnected L1; L4: %s \n" %L1.colinearconnected(L4))
        logger.debug(text3)
        
        text4=("\nCheck for Intersection L1; L5: %s \n" %L1.intersect(L5))
        text4+=("Check for Colinear L1; L5: %s \n" %L1.colinear(L5))
        text4+=("Check for colinearoverlapping L1; L5: %s \n" %L1.colinearoverlapping(L5))
        text4+=("Check for colinearconnected L1; L5: %s \n" %L1.colinearconnected(L5))
        logger.debug(text4)
        
        
        Pl.plot_lines_plot(lines1,221,text1)
        Pl.plot_lines_plot(lines2,222,text2)
        Pl.plot_lines_plot(lines3,223,text3)
        Pl.plot_lines_plot(lines4,224,text4)
        
    def CheckForIntersections(self):
        master.title("Check for Intersections and split Lines")
        
        L1=LineGeo(Point(x=0,y=0),Point(x=2,y=2))
        L2=LineGeo(Point(x=0,y=2),Point(x=2,y=0))
        L3=LineGeo(Point(x=1,y=3),Point(x=3,y=1))
        L4=LineGeo(Point(x=2,y=5),Point(x=4,y=2))
        L5=LineGeo(Point(x=2,y=2), Point(x=3,y=0))
        
        IP1=L1.find_inter_point(L2)
        IP2=L1.find_inter_point(L3)
        IP3=L1.find_inter_point(L4)
        IP4=L1.find_inter_point(L5)
        
        lines1=[]+L1.split_into_2geos(IP1)+L2.split_into_2geos(IP1)
        lines2=[]+L1.split_into_2geos(IP2)+L3.split_into_2geos(IP2)
        lines3=[]+L1.split_into_2geos(IP3)+L4.split_into_2geos(IP3)
        lines4=[]+L1.split_into_2geos(IP4)+L5.split_into_2geos(IP4)

        text1=("\nCheck for Intersection L1; L2: %s \n" %L1.intersect(L2))
        text1+=("Lies on segment L1: %s L2: %s \n" %(L1.liesonsegment(IP1),L2.liesonsegment(IP1)))
        text1+=("Intersection at Point: %s \n" %L1.find_inter_point(L2))
        logger.debug(text1)
        
        text2=("Check for Intersection L1; L3: %s \n" %L1.intersect(L3))
        text2+=("Lies on segment L1: %s L3: %s \n" %(L1.liesonsegment(IP2),L3.liesonsegment(IP2)))
        text2+=("Intersection at Point: %s \n" %L1.find_inter_point(L3))
        logger.debug(text2)
        
        text3=("Check for Intersection L1; L4: %s \n" %L1.intersect(L4))
        text3+=("Lies on segment L1: %s L4: %s \n" %(L1.liesonsegment(IP3),L4.liesonsegment(IP3)))
        text3+=("Intersection at Point: %s \n" %L1.find_inter_point(L4))
        logger.debug(text3)
        
        text4=("Check for Intersection L1; L5: %s \n" %L1.intersect(L5))
        text4+=("Lies on segment L1: %s L5: %s \n" %(L1.liesonsegment(IP4),L5.liesonsegment(IP4)))
        text4+=("Intersection at Point: %s \n" %L1.find_inter_point(L5))
        logger.debug(text4)
                
        Pl.plot_lines_plot(lines1,221,text1)
        Pl.plot_lines_plot(lines2,222,text2)
        Pl.plot_lines_plot(lines3,223,text3)
        Pl.plot_lines_plot(lines4,224,text4)
        
    def SimplePolygonCheck(self):
        master.title("Simple Polygon Check")
        
        L0=LineGeo(Point(x=0,y=-1),Point(x=0,y=0))
        L1=LineGeo(Point(x=0,y=0),Point(x=2,y=2))
        L2=LineGeo(Point(x=2,y=2),Point(x=3,y=3))
        L3=LineGeo(Point(x=3,y=3),Point(x=3,y=-6))
        L4=LineGeo(Point(x=3,y=-6),Point(x=0,y=-5))
        L5=LineGeo(Point(x=0,y=-5), Point(x=0,y=-4))
        L6=LineGeo(Point(x=0,y=-4), Point(x=0,y=-1))
        shape=ShapeClass(geos=[L0,L1,L2,L3,L4,L5,L6],closed=True)
        
        L0=LineGeo(Point(x=0,y=-1),Point(x=0,y=0))
        L1=LineGeo(Point(x=0,y=0),Point(x=2,y=2))
        L2=LineGeo(Point(x=2,y=2),Point(x=3,y=3))
        L3=LineGeo(Point(x=3,y=3),Point(x=3,y=-6))
        L4=LineGeo(Point(x=3,y=-6),Point(x=0,y=-5))
        L5=LineGeo(Point(x=0,y=-5), Point(x=0,y=-4))
        shape2=ShapeClass(geos=[L0,L1,L2,L3,L4,L5],closed=False)
        
        Pl.plot_lines_plot(shape.geos,221)
        
        shape.make_shape_ccw()
        Pl.plot_lines_plot(shape.geos,222)
        
        shape.join_colinear_lines()
        Pl.plot_lines_plot(shape.geos,223)
        
        shape2.join_colinear_lines()
        Pl.plot_lines_plot(shape2.geos,224)
        
    def PsCurveParametrizationCheck(self):
        master.title("PS Curve Parameterization Check")
        
        L0=LineGeo(Point(x=0,y=-1),Point(x=0,y=0))
        L1=LineGeo(Point(x=0,y=0),Point(x=2,y=2))
        L2=LineGeo(Point(x=2,y=2),Point(x=3,y=3))
        L3=LineGeo(Point(x=3,y=3),Point(x=4,y=0))
        L4=LineGeo(Point(x=4,y=0),Point(x=5,y=3))
        L5=LineGeo(Point(x=5,y=3),Point(x=5,y=-6))
        L6=LineGeo(Point(x=5,y=-6),Point(x=0,y=-5))
        L7=LineGeo(Point(x=0,y=-5), Point(x=0,y=-4))
        L8=LineGeo(Point(x=0,y=-4), Point(x=0,y=-1))
        
        shape=ShapeClass(geos=[L0,L1,L2,L3,L4,L5,L6,L7,L8],closed=True)
        Pl.plot_lines_plot(shape.geos,221)
           
        offshape=offShapeClass(parent=shape,offset=1,offtype='in') 
        Pl.plot_segments(offshape.segments,222,'inner offset')
        if not(offshape.start_vertex is None):
            offshape.segments[offshape.start_vertex].Pa.plot2plot(Pl.plot1,format='or')
        
        offshape2=offShapeClass(parent=shape,offset=1,offtype='out') 
        Pl.plot_segments(offshape2.segments,223,'outter offset')
        
        if not(offshape2.start_vertex is None):
            offshape2.segments[offshape2.start_vertex].Pa.plot2plot(Pl.plot1,format='or')        
        
        L0=LineGeo(Point(x=0,y=-1),Point(x=0,y=0))
        L1=LineGeo(Point(x=0,y=0),Point(x=2,y=2))
        L2=LineGeo(Point(x=2,y=2),Point(x=3,y=3))
        L3=LineGeo(Point(x=3,y=3),Point(x=3,y=-6))
        L4=LineGeo(Point(x=3,y=-6),Point(x=0,y=-5))
        L5=LineGeo(Point(x=0,y=-5), Point(x=0,y=-4))
        L6=LineGeo(Point(x=0,y=-4), Point(x=0,y=-1))
        shape3=ShapeClass(geos=[L0,L1,L2,L3,L4,L5,L6],closed=True)
                  
        offshape3=offShapeClass(parent=shape3,offset=1,offtype='out') 
        Pl.plot_segments(offshape3.segments,224,'outer offset')
        if not(offshape3.start_vertex is None):
            offshape3.segments[offshape3.start_vertex].Pa.plot2plot(Pl.plot1,format='oc')
        
        Pl.canvas.show()
        
    def PWIDTest(self):
        master.title("PS Curve Parameterization Check")
        
        L0=LineGeo(Point(x=0,y=-1),Point(x=1,y=0))
        L1=LineGeo(Point(x=1,y=0),Point(x=2,y=2))
        L2=LineGeo(Point(x=2,y=2),Point(x=3,y=3))
        L3=LineGeo(Point(x=3,y=3),Point(x=4,y=0))
        L4=LineGeo(Point(x=4,y=0),Point(x=5,y=3))
        L5=LineGeo(Point(x=5,y=3),Point(x=5,y=-6))
        L6=LineGeo(Point(x=5,y=-6),Point(x=0,y=-5))
        L7=LineGeo(Point(x=0,y=-5), Point(x=0,y=-4))
        L8=LineGeo(Point(x=0,y=-4), Point(x=0,y=-1))
        
        shape=ShapeClass(geos=[L0,L1,L2,L3,L4,L5,L6,L7,L8],closed=True)
        Pl.plot_lines_plot(shape.geos,221)
        
        Normal=L0.Pa.get_normal_vector(L0.Pe,0.5)
        Normal_Line1=LineGeo(L0.Pe,L0.Pe+Normal)
        
        Normal2=L2.Pa.get_normal_vector(L2.Pe,-0.5)
        Normal_Line2=LineGeo(L2.Pe,L2.Pe+Normal2)
        
        Normal3=L3.Pa.get_normal_vector(L3.Pe,0.75)
        Normal_Line3=LineGeo(L3.Pe,L3.Pe+Normal3)
        
        Pl.plot_lines_plot(shape.geos+[Normal_Line1,Normal_Line2,Normal_Line3],221)
        
        offshape=offShapeClass(shape, offset=1, offtype='in')
        Pl.plot_segments(offshape.segments,222,offshape.start_vertex)
        #if not(offshape.start_vertex is None):
        offshape.segments[offshape.start_vertex].Pa.plot2plot(Pl.plot1,format='oc')
        Pl.canvas.show()
      

if 1:
    logging.basicConfig(level=logging.DEBUG,format="%(funcName)-30s %(lineno)-6d: %(message)s")
    master = Tk()
    Pl=PlotClass(master)
    Ex=ExampleClass()
    
    
    #Ex.CheckColinearLines()
    #CheckForIntersections()
    #Ex.SimplePolygonCheck()
    #Ex.PsCurveParametrizationCheck() 
    Ex.PWIDTest()
         
    master.mainloop()


     
