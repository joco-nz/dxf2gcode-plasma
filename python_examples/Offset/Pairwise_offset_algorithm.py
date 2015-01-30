#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#Programmer: Christian Kohlöffel
#E-mail:     christian-kohloeffel@t-online.de


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
    
    def ccw(self,B,C):
        """
        This functions gives the Direction in which the three points are located.
        @param B: a second point
        @param C: a third point
        @return: If the slope of the line AB is less than the slope of the line
        AC then the three points are listed in a counterclockwise order 
        """
        #return (C.y-self.y)*(B.x-self.x) > (B.y-self.y)*(C.x-self.x)
        eps=1e-9
        
        area2 = (B.x - self.x) * (C.y - self.y) - (C.x - self.x) * (B.y - self.y)
        #logger.debug(area2)
        if (area2 < -eps): 
            return -1
        elif area2 > eps: 
            return +1
        else:
            return  0
        
    def cross_product(self, other):
        """
        Returns the cross Product of two points
        @param P1: The first Point
        @param P2: The 2nd Point
        @return: dot Product of the points.
        """ 
        return Point(self.y*other.z - self.z*other.y, self.z*other.x - self.x*other.z, self.x*other.y - self.y*other.x)
   
    def distance(self, other=None):
        """Returns distance between two given points"""
        if type(other) == type(None):
            other = Point(x=0.0, y=0.0)
        
        if isinstance(other,Point):
            return sqrt(pow(self.x - other.x, 2) + pow(self.y - other.y, 2))
        elif isinstance(other,LineGeo):
            return other.distance(self)

    def dotProd(self,P2):
        """
        Returns the dotProduct of two points
        @param self: The first Point
        @param other: The 2nd Point
        @return: dot Product of the points.
        """ 
        return (self.x*P2.x) + (self.y*P2.y)
    
    def get_arc_point(self, ang=0, r=1):
        """ 
        Returns the Point on the arc defined by r and the given angle, self is 
        Center of the arc
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
    
    def isintol(self, other, tol=1e-9):
        """Are the two points within 'tol' tolerance?"""
        return (abs(self.x - other.x) <= tol) & (abs(self.y - other.y) <= tol)

    def norm_angle(self, other=None):
        """Returns angle between two given points"""
        if type(other) == type(None):
            other = Point(x=0.0, y=0.0)
        return atan2(other.y - self.y, other.x - self.x)

    def unit_vector(self, Pto=None):
        """
        Returns vector of length 1 with similar direction as input
        @param Pto: The other point 
        @return: Returns the Unit vector
        """
        diffVec = Pto - self
        l = diffVec.distance()
        return Point(diffVec.x / l, diffVec.y / l)

    def transform_to_Norm_Coord(self, other, alpha):
        xt = other.x + self.x * cos(alpha) + self.y * sin(alpha)
        yt = other.y + self.x * sin(alpha) + self.y * cos(alpha)
        return Point(x=xt, y=yt)
 
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
    
    def unit_vector(self, Pto=None):
        """
        Returns vector of length 1 with similar direction as input
        @param Pto: The other point 
        @return: Returns the Unit vector
        """
        diffVec = Pto - self
        l = diffVec.distance()
        return Point(diffVec.x / l, diffVec.y / l)

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
    
    def hasintersection(self, other=None, tol=1e-9):
        """
        Checks if the two bounding boxes have an intersection
        @param other: The 2nd Bounding Box
        @return: Returns true or false
        """
        if isinstance(other,Point):
            return self.pointisinBB(other, tol)
        elif isinstance(other,BoundingBox): 
            x_inter_pos = (self.Pe.x + tol > other.Pa.x) and \
            (self.Pa.x - tol < other.Pe.x)
            y_inter_pos = (self.Pe.y + tol > other.Pa.y) and \
            (self.Pa.y - tol < other.Pe.y)
         
            return x_inter_pos and y_inter_pos
        else:
            logger.warning("Unsupported Instance: %s" %other.type)
    
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
        return ("type:% s" % self.type) + \
               ("\nPa : %s" % self.Pa) + \
               ("\nPe : %s" % self.Pe)  
               
    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        Pa = Point(x=min(self.Pa.x, self.Pe.x), y=min(self.Pa.y, self.Pe.y))
        Pe = Point(x=max(self.Pa.x, self.Pe.x), y=max(self.Pa.y, self.Pe.y))
        
        self.BB = BoundingBox(Pa=Pa, Pe=Pe)
        
    def colinear(self,other):
        """
        Check if two lines with same point self.Pe==other.Pa are colinear. For Point
        it check if the point is colinear with the line self.
        @param other: the possibly colinear line
        """
        if isinstance(other,LineGeo):
            return self.Pa.ccw(self.Pe,other.Pe) == 0
        elif isinstance(other,Point):
            """
            Return true iff a, b, and c all lie on the same line."
            """
            return self.Pa.ccw(self.Pe,other) == 0
        else:
            logger.debug("Unsupported instance: %s" %type(other))
    
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
            
    def distance(self, other=[]):
        """
        Find the distance between 2 geometry elements. Possible is CCLineGeo
        and CCArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        if isinstance(other,LineGeo):
            return self.distance_l_l(other)
        elif isinstance(other,Point):
            return self.distance_l_p(other)
        elif isinstance(other,ArcGeo):
            return self.distance_l_a(other)
        else:
            logger.error(self.tr("Unsupported geometry type: %s" %type(other))) 
            
    def distance_l_l(self,other):
        """
        Find the distance between 2 ccLineGeo elements. 
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        
        if self.intersect(other):
            return 0.0
        
        return min(self.distance_l_p(other.Pa),
                   self.distance_l_p(other.Pe),
                   other.distance_l_p(self.Pa),
                   other.distance_l_p(self.Pe))
        
    def distance_l_a(self,arc):
        """
        Find the distance between 2 ccLineGeo elements. 
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        
        #If it would be a circel the distance would be O to line - radius
        distance_O=self.distance_l_p(Arc.O)-Arc.r
        
        #If it within the span of the arc thtats is
        norm_angle=Arc.O.norm_angle(Arc.O)
            
    def distance_l_p(self,Point):
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
        Find the intersection between 2 Geo elements. There can be only one
        intersection between 2 lines. Returns also FIP which lay on the ray.
        @param other: the instance of the 2nd geometry element.
        @param type: Can be "TIP" for True Intersection Point or "Ray" for 
        Intersection which is in Ray (of Line)
        @return: a list of intersection points. 
        """
        if isinstance(other,LineGeo):
            inter=self.find_inter_point_l_l(other,type)
            return inter
        elif isinstance(other,ArcGeo):
            inter=self.find_inter_point_l_a(other,type)
            return inter
        else:
            logger.error("Unsupported Instance: %s" %other.type)
        
    def find_inter_point_l_l(self, other, type="TIP"):
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
        
    def find_inter_point_l_a(self, Arc,type="TIP"):
        """
        Find the intersection between 2 Geo elements. The intersection 
        between a Line and a Arc is checked here. This function is also used 
        in the Arc Class to check Arc -> Line Intersection (the other way around)
        @param Arc: the instance of the 2nd geometry element.
        @param type: Can be "TIP" for True Intersection Point or "Ray" for 
        Intersection which is in Ray (of Line)
        @return: a list of intersection points.
        @todo: FIXME: The type of the intersection is not implemented up to now 
        """
        
        Ldx = self.Pe.x - self.Pa.x
        Ldy = self.Pe.y - self.Pa.y
       
        #Mitternachtsformel zum berechnen der Nullpunkte der quadratischen 
        #Gleichung 
        a = pow(Ldx, 2) + pow(Ldy, 2)
        b = 2 * Ldx * (self.Pa.x - Arc.O.x) + 2 * Ldy * (self.Pa.y - Arc.O.y)
        c = pow(self.Pa.x - Arc.O.x, 2) + pow(self.Pa.y - Arc.O.y, 2) - pow(Arc.r, 2)
        root = pow(b, 2) - 4 * a * c
       
        #If the value under the sqrt is negative there is no intersection.
        if root < 0 or a==0.0:
            return None
        
        v1 = (-b + sqrt(root)) / (2 * a)
        v2 = (-b - sqrt(root)) / (2 * a)
        
        Pi1 = Point(x=self.Pa.x + v1 * Ldx,
                       y=self.Pa.y + v1 * Ldy)
        
        Pi2 = Point(x=self.Pa.x + v2 * Ldx,
               y=self.Pa.y + v2 * Ldy)
             
        Pi1.v = Arc.dif_ang(Arc.Pa, Pi1, Arc.ext)/Arc.ext
        Pi2.v = Arc.dif_ang(Arc.Pa, Pi2, Arc.ext)/Arc.ext

        if type=='TIP':
            if ((Pi1.v>=0.0 and Pi1.v<=1.0 and self.intersect(Pi1)) and
               (Pi1.v>=0.0 and Pi2.v<=1.0 and self.intersect(Pi2))):
                if (root==0):
                    return Pi1
                else:
                    return [Pi1, Pi2]
            elif (Pi1.v>=0.0 and Pi1.v<=1.0 and self.intersect(Pi1)):
                return Pi1
            elif  (Pi1.v>=0.0 and Pi2.v<=1.0 and self.intersect(Pi2)):
                return Pi2
            else:
                return None
        elif type=="Ray":
            #If the root is zero only one solution and the line is a tangent.
            if(root == 0):
                return Pi1 
            
            return [Pi1, Pi2]
        else:
            logger.error("We should not be here")
        
    def get_nearest_point(self,other):
        """
        Get the nearest point on a line to another line lieing on the line
        @param other: The Line to be nearest to
        @return: The point which is the nearest to other
        """
        if isinstance(other,LineGeo):
            return self.get_nearest_point_l_l(other)
        elif isinstance(other,ArcGeo):
            return self.get_nearest_point_l_a(other)
        elif isinstance(other,Point):
            return self.get_nearest_point_l_p(other)
        else:
            logger.error("Unsupported Instance: %s" %other.type)

    def get_nearest_point_l_l(self,other):
        """
        Get the nearest point on a line to another line lieing on the line
        @param other: The Line to be nearest to
        @return: The point which is the nearest to other
        """
        #logger.debug(self.intersect(other))
        if self.intersect(other):
            return self.find_inter_point_l_l(other)
        min_dis=self.distance(other)
        if min_dis==self.distance_l_p(other.Pa):
            return self.get_nearest_point_l_p(other.Pa)
        elif min_dis==self.distance_l_p(other.Pe):
            return self.get_nearest_point_l_p(other.Pe)
        elif min_dis==other.distance_l_p(self.Pa):
            return self.Pa
        elif min_dis==other.distance_l_p(self.Pe):
            return self.Pe
        else:
            logger.warning("No solution found")
            
    def get_nearest_point_l_a(self,other):
        """
        Get the nearest point to a line lieing on the line
        @param other: The Point to be nearest to
        @return: The point which is the nearest to other
        """
        if self.intersect(other):
            return self.find_inter_point_l_a(other)
        else:
            return Point(0,0)

    def get_nearest_point_l_p(self,other):
        """
        Get the nearest point to a point lieing on the line
        @param other: The Point to be nearest to
        @return: The point which is the nearest to other
        """
        if self.intersect(other):
            return other
        
        PPoint=self.perpedicular_on_line(other)
        
        if self.intersect(PPoint):
            return PPoint
        elif self.Pa.distance(other)<self.Pe.distance(other):
            return self.Pa
        else:
            return self.Pe
    
    def intersect(self,other):
        """
        Check if there is an intersection of two geometry elements
        @param, a second geometry which shall be checked for intersection
        @return: True if there is an intersection
        """
        #Do a raw check first with BoundingBox
        #logger.debug("self: %s, \nother: %s, \nintersect: %s" %(self,other,self.BB.hasintersection(other.BB)))
        #logger.debug("self.BB: %s \nother.BB: %s")
        #logger.debug(self.BB.hasintersection(other.BB))
        #We need to test Point first cause it has no BB
        if isinstance(other,Point):
            return self.intersect_l_p(other)
        elif not(self.BB.hasintersection(other.BB)):
            return False
        elif isinstance(other,LineGeo):
            return self.intersect_l_l(other)
        elif isinstance(other,ArcGeo):
            return self.intersect_l_a(other)
        else:
            logger.error("Unsupported Instance: %s" %other.type)

    def intersect_l_a(self,other):
        """
        Check if there is an intersection of the two line
        @param, a second line which shall be checked for intersection
        @return: True if there is an intersection
        """
        inter=self.find_inter_point_l_a(other)
        return not(inter is None)

    def intersect_l_l(self,other):
        """
        Check if there is an intersection of the two line
        @param, a second line which shall be checked for intersection
        @return: True if there is an intersection
        """
        A=self.Pa
        B=self.Pe
        C= other.Pa
        D= other.Pe
        return A.ccw(C,D) != B.ccw(C,D) and A.ccw(B,C) != A.ccw(B,D)
    
    def intersect_l_p(self,Point):
        """
        Check if Point is colinear and within the Line
        @param Point: A Point which will be checked
        @return: True if point Point intersects the line segment from Pa to Pe.
        Refer to http://stackoverflow.com/questions/328107/how-can-you-determine-a-point-is-between-two-other-points-on-a-line-segment
        """
        # (or the degenerate case that all 3 points are coincident)
        #logger.debug(self.colinear(Point))
        return (self.colinear(Point)
                and (self.within(self.Pa.x, Point.x, self.Pe.x) 
                     if self.Pa.x != self.Pe.x else 
                     self.within(self.Pa.y, Point.y, self.Pe.y)))

    def within(self,p, q, r):
        "Return true iff q is between p and r (inclusive)."
        return p <= q <= r or r <= q <= p
        
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
   
    def perpedicular_on_line(self,other):
        """
        This function calculates the perpendicular point on a line (or ray of line)
        with the shortest distance to the point given with other
        @param other: The point to be perpendicular to
        @return: A point which is on line and perpendicular to Point other
        @see: http://stackoverflow.com/questions/1811549/perpendicular-on-a-line-from-a-given-point
        """
        #first convert line to normalized unit vector
        unit_vector=self.Pa.unit_vector(self.Pe)
        
        #translate the point and get the dot product
        lam = ((unit_vector.x * (other.x - self.Pa.x)) 
                + (unit_vector.y * (other.y - self.Pa.y)))
        return Point(x= (unit_vector.x * lam) + self.Pa.x,
                     y= (unit_vector.y * lam) + self.Pa.y)

    def plot2plot(self, plot,format='-m'):
        plot.plot([self.Pa.x,self.Pe.x],[self.Pa.y,self.Pe.y],format)

    def reverse(self):
        """ 
        Reverses the direction of the arc (switch direction).
        """ 
        self.Pa, self.Pe = self.Pe, self.Pa
       
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
        elif self.intersect(ipoint):
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
    
class ArcGeo:
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """ 
    def __init__(self, Pa = None, Pe = None, O = None, r = 1,
                 s_ang = None, e_ang = None, direction = 1, drag = False):
        """
        Standard Method to initialize the ArcGeo. Not all of the parameters are
        required to fully define a arc. e.g. Pa and Pe may be given or s_ang and
        e_ang
        @param Pa: The Start Point of the arc
        @param Pe: the End Point of the arc
        @param O: The center of the arc
        @param r: The radius of the arc
        @param s_ang: The Start Angle of the arc
        @param e_ang: the End Angle of the arc
        @param direction: The arc direction where 1 is in positive direction
        """
        self.Pa = Pa
        self.Pe = Pe
        self.O = O
        self.r = abs(r)
        self.s_ang = s_ang
        self.e_ang = e_ang

        # Get the Circle Milllw with known Start and End Points
        if type(self.O) == type(None):
           
            if (type(Pa) != type(None)) and \
            (type(Pe) != type(None)) and \
            (type(direction) != type(None)):
               
                arc = self.Pe.norm_angle(Pa) - pi / 2
                Ve = Pe - Pa
                m = (sqrt(pow(Ve.x, 2) + pow(Ve.y, 2))) / 2
                
                if DEBUG:
                    logger.debug('lo: %s; m: %s' %(r,m))
                    
                if abs(r-m)<0.0001:
                    lo = 0.0;
                else:        
                    lo = sqrt(pow(r, 2) - pow(m, 2))
                
                if direction < 0:
                    d = -1
                else:
                    d = 1
                self.O = Pa + 0.5 * Ve
                self.O.y += lo * sin(arc) * d
                self.O.x += lo * cos(arc) * d
                
        # Falls nicht ubergeben Mittelpunkt ausrechnen  
            elif (type(self.s_ang) != type(None)) and (type(self.e_ang) != type(None)):
                self.O.x = self.Pa.x - r * cos(self.s_ang)
                self.O.y = self.Pa.y - r * sin(self.s_ang)
            else:
                logger.error(self.tr("Missing value for Arc Geometry"))

        #Falls nicht uebergeben dann Anfangs- und Endwinkel ausrechen            
        if type(self.s_ang) == type(None):
            self.s_ang = self.O.norm_angle(Pa)
            
        if type(self.e_ang) == type(None):
            self.e_ang = self.O.norm_angle(Pe)
        
        self.ext=self.dif_ang(self.Pa, self.Pe, direction)
        #self.get_arc_extend(direction)

        #Falls es ein Kreis ist Umfang 2pi einsetzen        
        if self.ext == 0.0:
            self.ext = 2 * pi
                   
        self.length = self.r * abs(self.ext)
        
        self.calc_bounding_box()

#    def __deepcopy__(self, memo):
#        return ArcGeo(copy.deepcopy(self.Pa, memo),
#                       copy.deepcopy(self.Pe, memo),
#                       copy.deepcopy(self.O, memo),
#                       copy.deepcopy(self.r, memo),
#                       copy.deepcopy(self.s_ang, memo),
#                       copy.deepcopy(self.e_ang, memo),
#                       copy.deepcopy(self.ext, memo))
#    
    
    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\nArcGeo") + \
               ("\nPa : %s; s_ang: %0.5f" % (self.Pa, self.s_ang)) + \
               ("\nPe : %s; e_ang: %0.5f" % (self.Pe, self.e_ang)) + \
               ("\nO  : %s; r: %0.3f" % (self.O, self.r)) + \
               ("\next  : %0.5f; length: %0.5f" % (self.ext, self.length))
  
    def angle_between(self, min_ang, max_ang, angle):
        """
        Returns if the angle is in the range between 2 other angles
        @param min_ang: The starting angle
        @param parent: The end angel. Always in ccw direction from min_ang
        @return: True or False
        """
        if min_ang < 0.0:
            min_ang += 2 * pi
        
        while max_ang < min_ang:
            max_ang += 2 * pi
            
        while angle < min_ang:
            angle += 2 * pi
                    
        return (min_ang < angle) and (angle <= max_ang)
                 
    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        
        Pa = Point(x=self.O.x - self.r, y=self.O.y - self.r)
        Pe = Point(x=self.O.x + self.r, y=self.O.y + self.r)
        
        #Do the calculation only for arcs have positiv extend => switch angles
        if self.ext >= 0:
            s_ang = self.s_ang
            e_ang = self.e_ang
        elif self.ext < 0:
            s_ang = self.e_ang
            e_ang = self.s_ang
                 
        #If the positive X Axis is crossed
        if not(self.wrap(s_ang, 0) >= self.wrap(e_ang, 1)):
            Pe.x = max(self.Pa.x, self.Pe.x)

        #If the positive Y Axis is crossed 
        if not(self.wrap(s_ang - pi / 2, 0) >= self.wrap(e_ang - pi / 2, 1)):
            Pe.y = max(self.Pa.y, self.Pe.y)

        #If the negative X Axis is crossed
        if not(self.wrap(s_ang - pi, 0) >= self.wrap(e_ang - pi, 1)):
            Pa.x = min(self.Pa.x, self.Pe.x)

        #If the negative Y is crossed 
        if not(self.wrap(s_ang - 1.5 * pi, 0) >= 
                self.wrap(e_ang - 1.5 * pi, 1)):
            Pa.y = min(self.Pa.y, self.Pe.y)
       
        self.BB = BoundingBox(Pa=Pa, Pe=Pe)

    def dif_ang(self, P1, P2, direction,tol=0.005):
        """
        Calculated the angle of extend based on the 3 given points. Center Point,
        P1 and P2.
        @param P1: the start Point of the arc 
        @param P2: the end Point of the arc
        @param direction: the direction of the arc
        @return: Returns the angle between -2* pi and 2 *pi for the arc extend
        """ 
        #FIXME Das koennte Probleme geben bei einem reelen Kreis
#        if P1.isintol(P2,tol):
#            return 0.0 
        sa = self.O.norm_angle(P1)
        ea = self.O.norm_angle(P2)

        if(direction > 0.0):     # GU
            dif_ang = (ea-sa)%(-2*pi)
            dif_ang -= floor(dif_ang / (2 * pi)) * (2 * pi)     
        else:
            dif_ang = (ea-sa)%(-2*pi)
            dif_ang += ceil(dif_ang / (2 * pi)) * (2 * pi)    
            
        return dif_ang
    
    def distance(self,other):
        """
        Find the distance between 2 geometry elements. Possible is LineGeo
        and CCArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        """
        Find the distance between 2 geometry elements. Possible is Point, LineGeo
        and ArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        if isinstance(other,LineGeo):
            return other.distance_l_a(self)
        elif isinstance(other,Point):
            return self.distance_a_p(other)
        elif isinstance(other,ArcGeo):
            return self.distance_arc_arc(other)
        else:
            logger.error(self.tr("Unsupported geometry type: %s" %type(other))) 
    
    def distance_a_a(self, other):
        """
        Find the distance between two arcs
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        
        return 1e99
    
    def distance_a_p(self, other):
        """
        Find the distance between a arc and a point
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        return 1e99
 
    def find_inter_point(self, other=[], type='TIP'):
        """
        Find the intersection between 2 geometry elements. Possible is CCLineGeo
        and CCArcGeo
        @param other: the instance of the 2nd geometry element.
        @param type: Can be "TIP" for True Intersection Point or "Ray" for 
        Intersection which is in Ray (of Line)        @return: a list of intersection points. 
        """
        if isinstance(other,LineGeo):
            IPoints=other.find_inter_point_l_a(self,type)
            return IPoints
        elif isinstance(other,ArcGeo):
            return self.find_inter_point_a_a(other,type)
        else:
            logger.error("Unsupported Instance: %s" %other.type)
             
    def find_inter_point_a_a(self, other, type='TIP'):
        """
        Find the intersection between 2 CCArcGeo elements. There can be only one
        intersection between 2 lines.
        @param other: the instance of the 2nd geometry element.
        @param type: Can be "TIP" for True Intersection Point or "Ray" for 
        Intersection which is in Ray (of Line)        
        @return: a list of intersection points. 
        @todo: FIXME: The type of the intersection is not implemented up to now
        """   
        O_dis = self.O.distance(other.O)
        
        #If self circle is surrounded by the other no intersection 
        if(O_dis < abs(self.r - other.r)):
            return None

        #If other circle is surrounded by the self no intersection
        if(O_dis < abs(other.r - self.r)):
            return None
        
        #If The circles are to far away from each other no intersection possible
        if (O_dis> abs(othr.r + self.r)):
            return None
        
        #If both circles have the same center and radius
        if abs(O_dis) ==0.0 and abs(self.r-other.r) ==0.0:
            Pi1=Point(x=self.Pa.x,y=self.Pa.y)
            Pi2=Point(x=self.Pe.x,y=self.Pe.y)
            
            return [Pi1, Pi2]
        #The following algorithm was found on :
        #http://www.sonoma.edu/users/w/wilsonst/Papers/Geometry/circles/default.htm
        
        root = ((pow(self.r + other.r , 2) - pow(O_dis, 2)) * 
                  (pow(O_dis, 2) - pow(other.r - self.r, 2)))
        
        #If the Line is a tangent the root is 0.0.
        if root<=0.0:
            root=0.0
        else:  
            root=sqrt(root)
        
        xbase = (other.O.x + self.O.x) / 2 + \
        (other.O.x - self.O.x) * \
        (pow(self.r, 2) - pow(other.r, 2)) / (2 * pow(O_dis, 2))
        
        ybase = (other.O.y + self.O.y) / 2 + \
        (other.O.y - self.O.y) * \
        (pow(self.r, 2) - pow(other.r, 2)) / (2 * pow(O_dis, 2))
        
        Pi1 = Point(x=xbase + (other.O.y - self.O.y) / \
                          (2 * pow(O_dis, 2)) * root,
                    y=ybase - (other.O.x - self.O.x) / \
                    (2 * pow(O_dis, 2)) * root)
        
        Pi1.v1 = self.dif_ang(self.Pa, Pi1, self.ext)/self.ext
        Pi1.v2 = other.dif_ang(other.Pa, Pi1, other.ext)/other.ext

        Pi2 = Point(x=xbase - (other.O.y - self.O.y) / \
                         (2 * pow(O_dis, 2)) * root,
                    y=ybase + (other.O.x - self.O.x) / \
                    (2 * pow(O_dis, 2)) * root)
        
        Pi2.v1 = self.dif_ang(self.Pa, Pi2, self.ext)/self.ext
        Pi2.v2 = other.dif_ang(other.Pa, Pi2, other.ext)/other.ext
        
        
        if type=='TIP':
            if ((Pi1.v1>=0.0 and Pi1.v1<=1.0 and Pi1.v2>0.0 and Pi1.v2<=1.0) and
               (Pi2.v1>=0.0 and Pi2.v1<=1.0 and Pi2.v2>0.0 and Pi2.v2<=1.0)):
                if (root==0):
                    return Pi1
                else:
                    return [Pi1, Pi2]
            elif (Pi1.v1>=0.0 and Pi1.v1<=1.0 and Pi1.v2>0.0 and Pi1.v2<=1.0):
                return Pi1
            elif  (Pi2.v1>=0.0 and Pi2.v1<=1.0 and Pi2.v2>0.0 and Pi2.v2<=1.0):
                return Pi2
            else:
                return None
        elif type=="Ray":
            #If the root is zero only one solution and the line is a tangent.
            if root==0:
                return Pi1
            else:
                return [Pi1, Pi2]
        else:
            logger.error("We should not be here")
             
    def get_arc_direction(self,newO):
        """ 
        Calculate the arc direction given from the Arc and O of the new Arc.
        @param O: The center of the arc
        @return: Returns the direction (+ or - pi/2)
        @todo: FIXME: The type of the intersection is not implemented up to now
        """ 
        
        a1= self.e_ang - pi/2 * self.ext / abs(self.ext)
        a2=self.Pe.norm_angle(newO)
        direction=a2-a1
        
        if direction>pi:
            direction=direction-2*pi
        elif direction<-pi:
            direction=direction+2*pi
            
        #print ('Die Direction ist: %s' %direction)
        
        return direction
    
    def get_nearest_point(self,other):
        """
        Get the nearest point on a line to another line lieing on the line
        @param other: The Line to be nearest to
        @return: The point which is the nearest to other
        """
        if isinstance(other,LineGeo):
            return self.get_nearest_point_a_l(other)
        elif isinstance(other,ArcGeo):
            return self.get_nearest_point_a_a(other)
        elif isinstance(other,Point):
            return self.get_nearest_point_a_p(other)
        else:
            logger.error("Unsupported Instance: %s" %other.type)

    def get_nearest_point_a_l(self,other):
        """
        Get the nearest point to a line lieing on the line
        @param other: The Point to be nearest to
        @return: The point which is the nearest to other
        """
        if self.intersect(other):
            return other.find_inter_point_l_a(self)
        else:
            return Point(0,0)

    def get_nearest_point_a_p(self,other):
        """
        Get the nearest point to a point lieing on the arc
        @param other: The Point to be nearest to
        @return: The point which is the nearest to other
        """
        if self.intersect(other):
            return other
        else:
            return Point(0,0)
        
        PPoint=self.O.get_arc_point(other.norm_angle(self.O),r=self.r)

        if self.intersect(PPoint):
            return PPoint
        elif self.Pa.distance(other)<self.Pe.distance(other):
            return self.Pa
        else:
            return self.Pe
        
    def get_nearest_point_a_a(self,other):
        return Point(0,0)
    
    def intersect(self,other):
        """
        Check if there is an intersection of two geometry elements
        @param, a second geometry which shall be checked for intersection
        @return: True if there is an intersection
        """
        #Do a raw check first with BoundingBox
        #logger.debug("self: %s, \nother: %s, \nintersect: %s" %(self,other,self.BB.hasintersection(other.BB)))
        #logger.debug("self.BB: %s \nother.BB: %s")
        
        #We need to test Point first cause it has no BB
        if isinstance(other,Point):
            return self.intersect_l_p(other)
        elif not(self.BB.hasintersection(other.BB)):
            return False
        elif isinstance(other,LineGeo):
            return other.intersect_l_a(self)
        elif isinstance(other,ArcGeo):
            return self.intersect_a_a(other)
        else:
            logger.error("Unsupported Instance: %s" %other.type)   
            
    def intersect_a_a(self,other):
        """
        Check if there is an intersection of two arcs
        @param, a second arc which shall be checked for intersection
        @return: True if there is an intersection
        """
        inter=self.find_inter_point_l_a(other)
        return not(inter is None)
        
    def plot2plot(self, plot,format='-m'):
        
        x=[]
        y=[]
        segments = int((abs(degrees(self.ext)) // 3) + 1)
        for i in range(segments + 1):
            
            ang = self.s_ang + i * self.ext / segments
            x+=[self.O.x + cos(ang) * abs(self.r)]
            y+=[self.O.y + sin(ang) * abs(self.r)]

        plot.plot(x,y,format)
 
    def split_into_2geos(self, ipoint=Point()):
        """
        Splits the given geometry into 2 not self intersection geometries. The
        geometry will be splitted between ipoint and Pe.
        @param ipoint: The Point where the intersection occures
        @return: A list of 2 CCArcGeo's will be returned.
        """ 
        #The angle between endpoint and where the intersection occures
        d_e_ang = self.e_ang - self.O.norm_angle(ipoint)
        
        #Correct by 2*pi if the direction is wrong
        if d_e_ang > self.ext:
            d_e_ang -= 2 * pi
            
        #The Point where the geo shall be splitted
        spoint = self.O.get_arc_point(ang=degrees(self.e_ang - d_e_ang / 2),
                                      r=self.r)
        
        return self.split_geo_at_point(spoint)
        
    def split_geo_at_point(self,spoint):
        """
        Splits the given geometry into 2 geometries. The
        geometry will be splitted at Point spoint.
        @param ipoint: The Point where the intersection occures
        @return: A list of 2 CCArcGeo's will be returned.
        """
        #Generate the 2 geometries and their bounding boxes.
        Arc1 = CCArcGeo(Pa=self.Pa, Pe=spoint, r=self.r,
                       O=self.O, direction=self.ext)
        
        Arc2 = CCArcGeo(Pa=spoint, Pe=self.Pe, r=self.r,
                       O=self.O, direction=self.ext)       
        return [Arc1, Arc2]
    
    def reverse(self):
        """ 
        Reverses the direction of the arc (switch direction).
        """ 
        self.Pa, self.Pe = self.Pe, self.Pa
        self.s_ang, self.e_ang = self.e_ang, self.s_ang
        self.ext = -self.ext
               
    def wrap(self, angle, isend=0):
        """
        Wrapes the given angle into a range between 0 and 2pi
        @param angle: The angle to be wraped
        @param isend: If the angle is the end angle or start angle, this makes a
        difference at 0 or 2pi.
        @return: Returns the angle between 0 and 2 *pi
        """ 
        wrap_angle = angle % (2 * pi)
        if isend and wrap_angle == 0.0:
            wrap_angle += 2 * pi
        elif wrap_angle == 2 * pi:
            wrap_angle -= 2 * pi
            
        return wrap_angle
   
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
        #self.BB = BoundingBox(Pa=None, Pe=None)
               
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
        self.convex_vertex=[]
        
        self.plotshapes=[]
        
        self.make_shape_ccw()
        self.join_colinear_lines()

        self.make_segment_types()
        
        
        for convex_vertex_nr in [1]:#range(len(self.convex_vertex)):
            convex_vertex=self.convex_vertex[convex_vertex_nr]
            logger.debug("Doing Vertex Nr: %s, %s" %(convex_vertex_nr,convex_vertex))
            forward,backward=self.PairWiseInterferenceDetection(convex_vertex,convex_vertex)
            logger.debug("forward: %s,backward: %s" %(forward,backward))
            
            #Make Raw offset curve of forward and backward segment
            fw_rawoff_seg=self.make_rawoff(forward)
            bw_rawoff_seg=self.make_rawoff(backward)
            logger.debug("\nRawoff: forward: %s,\nbackward: %s" %(fw_rawoff_seg,bw_rawoff_seg))
            
            
            #Intersect the two segements 
            iPoint=fw_rawoff_seg.find_inter_point(bw_rawoff_seg)
            self.plotshapes+=[fw_rawoff_seg,bw_rawoff_seg,iPoint]
            logger.debug("Intersection Point: %s" %iPoint)
            
            #if not(isinstance(iPoint,Point)):
                #raise ValueError("The Intersection Point has wrong size, should be 1")

            
            #Calculate the Contact points of the common tangential circle
            
            
    def make_rawoff(self,segment_nr):
        """
        This function returns the rawoffset of a segement. A line for a line and
        a circle for a reflex segement.
        @param segment_nr: The nr of the segement for which the rawoffset
        segement shall be generated
        @ return: Returns the rawoffsetsegement of the  defined segment 
        """
        
        seg=self.segments[segment_nr]
        
        if self.offtype=="out":
            offset=-self.offset
        else:
            offset=self.offset
        
        #if segement 1 is inverted change End Point
        if isinstance(seg,LineGeo):
            Pa=seg.Pa+seg.start_normal*offset
            Pe=seg.Pe+seg.end_normal*offset
            return LineGeo(Pa,Pe)
        elif isinstance(seg,Point):
            Pa=seg+seg.start_normal*offset
            Pe=seg+seg.end_normal*offset
            return ArcGeo(Pa=Pa,Pe=Pe,O=deepcopy(seg),r=self.offset)
        else:
            logger.error("Unsupportet Object type: %s" %type(seg))
            

            
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
            else:
                self.convex_vertex+=[i]          
            
            #Add the linear segment which is a line connecting 2 vertices
            self.segments+=[geo2]
        
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
            offGeo=LineGeo(Pa,Pe)
        elif isinstance(segment1,Point):
            Pa=segment1+segment1.start_normal*offset
            Pe=segment1+segment1.end_normal*offset
            O=segment1
            r=offset
            offGeo=ArcGeo(Pa=Pa,Pe=Pe,O=segment1,r=offset)
        else:
            logger.error("Unsupportet Object type: %s" %type(segment1))
            
        offGeo=LineGeo(Pa,Pe)
     
        # If the distance from the Line to the Center of the Tangential Circle 
        #is smaller then the radius we have an intersection
        logger.debug(segment2.distance(offGeo))
        return segment2.distance(offGeo)<=offset
    
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

        L1_status,L2_status="full","full"
        #Repeat until we reached the Partial-interfering-relation
        while not(L1_status=="partial" and L2_status=="partial"):
            
            segment1=self.segments[forward]
            segment2=self.segments[backward]
            
            logger.debug("\nsegment1: %s, \nsegment2: %s" %(segment1,segment2))
                
            #Check if Endpoints of segements are equal
            if isinstance(segment1,LineGeo):
                Pe_seg1=segment1.Pe
            else:
                Pe_seg1=segment1
            
            if isinstance(segment2,LineGeo):
                Pe_seg2=segment2.Pa
            else:
                Pe_seg2=segment2
                
            if Pe_seg1==Pe_seg2:
                return forward,backward
            
            [L1_status,L2_status]=self.Interfering_relation(segment1,1,segment2,-1)
            
            if L1_status=="full":
                forward+=1
            elif L1_status=="reverse":
                forward-=1  
            elif L2_status=="full":
                backward-=1
            elif L2_status=="reverse":
                backward+=1
            
            
            logger.debug("L1_status: %s,L2_status: %s" %(L1_status,L2_status))
            
        return forward,backward
                         
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
        
    def plot_segments(self,segments,sb_nr=111,text="",format=('-m','xr','og'),fcol='red'):
        self.plot1 = self.figure.add_subplot(sb_nr)
        self.plot1.set_title("Segments Plot %s" %sb_nr)
        self.plot1.grid(b=True, which='both', color='0.65',linestyle='-')
        self.plot1.hold(True)
        self.plot1.text(0.5, 0, text, ha='left', fontsize=8)
  
        for segment_nr in range(len(segments)):
            seg=segments[segment_nr]
            if isinstance(seg,LineGeo):
                seg.plot2plot(self.plot1,format[0])
                Pa=(seg.Pa+seg.Pe)*0.5
                
                seg.Pa.plot2plot(self.plot1,format=format[1])
                seg.Pe.plot2plot(self.plot1,format=format[1])
            elif isinstance(seg,ArcGeo):
                seg.plot2plot(self.plot1,format=format[0])

                Pa=(seg.Pa+seg.Pe)*0.5
                
                seg.Pa.plot2plot(self.plot1,format=format[1])
                seg.Pe.plot2plot(self.plot1,format=format[1])
                
            elif isinstance(seg,Point):
                #seg.plot2plot(self.plot1,format=format[0])
                seg.plot2plot(self.plot1,format=format[2])
                Pa=seg
            
            self.plot1.text(Pa.x+0.1,Pa.y+0.1,segment_nr,ha='left', fontsize=10, color=fcol)
            self.plot1.axis('scaled')     

            
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
        text1+=("Lies on segment L1: %s L2: %s \n" %(L1.intersect(IP1),L2.intersect(IP1)))
        text1+=("Intersection at Point: %s \n" %L1.find_inter_point(L2))
        logger.debug(text1)
        
        text2=("Check for Intersection L1; L3: %s \n" %L1.intersect(L3))
        text2+=("Lies on segment L1: %s L3: %s \n" %(L1.intersect(IP2),L3.intersect(IP2)))
        text2+=("Intersection at Point: %s \n" %L1.find_inter_point(L3))
        logger.debug(text2)
        
        text3=("Check for Intersection L1; L4: %s \n" %L1.intersect(L4))
        text3+=("Lies on segment L1: %s L4: %s \n" %(L1.intersect(IP3),L4.intersect(IP3)))
        text3+=("Intersection at Point: %s \n" %L1.find_inter_point(L4))
        logger.debug(text3)
        
        text4=("Check for Intersection L1; L5: %s \n" %L1.intersect(L5))
        text4+=("Lies on segment L1: %s L5: %s \n" %(L1.intersect(IP4),L5.intersect(IP4)))
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
        
    def Distance_Check(self):

        L1=LineGeo(Point(x=1,y=0),Point(x=2,y=2))
        L3=LineGeo(Point(x=3,y=3),Point(x=4,y=0))
        L7=LineGeo(Point(x=0,y=-2), Point(x=0,y=-1))
        Lt=LineGeo(Point(x=3,y=0),Point(x=2,y=1))
        Lc=LineGeo(Point(x=2,y=0),Point(x=3,y=2))
        Li=LineGeo(Point(x=1,y=0.5),Point(x=1.5,y=0))
        
#        PointN1=L1.get_nearest_point(L3)
#        PointN2=L3.get_nearest_point(L1)
#        NL=LineGeo(PointN1,PointN2)
#        
#        PointN3=L1.get_nearest_point(L7)
#        PointN4=L7.get_nearest_point(L1)
#        NL1=LineGeo(PointN3,PointN4)
#
#        PointN5=L1.get_nearest_point(Lt)
#        PointN6=Lt.get_nearest_point(L1)
#        logger.debug("PointN5: %s, PointN6: %s" %(PointN5,PointN6))
#        NL2=LineGeo(PointN5,PointN6)
#        
#        PointN7=L1.get_nearest_point(Lc)
#        PointN8=Lc.get_nearest_point(L1)
#        NL3=LineGeo(PointN7,PointN8)
#        
#        PointN9=L1.get_nearest_point(Li)
#        PointN10=Li.get_nearest_point(L1)
#        
#        NL4=LineGeo(PointN9,PointN10)
#        
#        segments=[L1,L3,L7,Lt,Lc,Li]
#        Pl.plot_segments(segments,121)
#        seg_con=[NL,NL1,NL2,NL3,NL4]
#        Pl.plot_segments(seg_con,121,format=('b','.b','ob'),fcol='blue')
        
        Arc0=ArcGeo(Pa=Point(x=-1,y=0),Pe=Point(x=0,y=1),O=Point(x=0,y=0),r=1)
        Lin=LineGeo(Point(-1,1),Point(0.5,-0.5))

        PointN1=L1.get_nearest_point(Arc0)
        PointN2=Arc0.get_nearest_point(L1)
        
        PointN3=Lin.get_nearest_point(Arc0)
        PointN4=Arc0.get_nearest_point(Lin)
        
        NL1=LineGeo(PointN1,PointN2)
        NL2=LineGeo(PointN3,PointN4)
        
        segments=[Arc0,L1,Lin]
        seg_con=[NL1,NL2]
        Pl.plot_segments(segments,122)
        Pl.plot_segments(seg_con,122,format=('b','.b','ob'),fcol='blue')

        
#        L0=LineGeo(Point(x=0,y=-0),Point(x=0.5,y=0))
#        L01=LineGeo(Point(x=0.5,y=0),Point(x=0.5,y=-1))
#        L02=LineGeo(Point(x=0.5,y=-1),Point(x=1,y=0))
#        L1=LineGeo(Point(x=1,y=0),Point(x=2,y=2))
#        L2=LineGeo(Point(x=2,y=2),Point(x=3,y=3))
#        L3=LineGeo(Point(x=3,y=3),Point(x=4,y=0))
#        L4=LineGeo(Point(x=4,y=0),Point(x=5,y=3))
#        L5=LineGeo(Point(x=5,y=3),Point(x=5,y=-6))
#        L6=LineGeo(Point(x=5,y=-6),Point(x=0,y=-5))
#        L7=LineGeo(Point(x=0,y=-5), Point(x=0,y=-4))
#        L8=LineGeo(Point(x=0,y=-4), Point(x=0,y=0))
#        
#        
#        
#        shape=ShapeClass(geos=[L0,L01,L02,L1,L2,L3,L4,L5,L6,L7,L8],closed=True)
#        Pl.plot_lines_plot(shape.geos,133)
#        
#        Normal=L0.Pa.get_normal_vector(L0.Pe,0.5)
#        Normal_Line1=LineGeo(L0.Pe,L0.Pe+Normal)
#        
#        Normal2=L2.Pa.get_normal_vector(L2.Pe,-0.5)
#        Normal_Line2=LineGeo(L2.Pe,L2.Pe+Normal2)
#        
#        Normal3=L3.Pa.get_normal_vector(L3.Pe,0.75)
#        Normal_Line3=LineGeo(L3.Pe,L3.Pe+Normal3)
#        
#        Pl.plot_lines_plot(shape.geos+[Normal_Line1,Normal_Line2,Normal_Line3],133)
#        
        
    def PWIDTest(self):
        master.title("PWIDTest Check")
        L0=LineGeo(Point(x=0,y=-0),Point(x=0.5,y=0))
        L01=LineGeo(Point(x=0.5,y=0),Point(x=0.5,y=-1))
        L02=LineGeo(Point(x=0.5,y=-1),Point(x=1,y=0))
        L1=LineGeo(Point(x=1,y=0),Point(x=2,y=2))
        L2=LineGeo(Point(x=2,y=2),Point(x=3,y=3))
        L3=LineGeo(Point(x=3,y=3),Point(x=4,y=0))
        L4=LineGeo(Point(x=4,y=0),Point(x=5,y=3))
        L5=LineGeo(Point(x=5,y=3),Point(x=5,y=-6))
        L6=LineGeo(Point(x=5,y=-6),Point(x=0,y=-5))
        L7=LineGeo(Point(x=0,y=-5), Point(x=0,y=-4))
        L8=LineGeo(Point(x=0,y=-4), Point(x=0,y=0))
        
        shape=ShapeClass(geos=[L0,L01,L02,L1,L2,L3,L4,L5,L6,L7,L8],closed=True)
        
        offshape=offShapeClass(shape, offset=1, offtype='in')
        Pl.plot_lines_plot(shape.geos,131)

        Pl.plot_segments(offshape.plotshapes,131,format=('b','.b','ob'),fcol='blue')
        
        
        
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
        Pl.plot_lines_plot(shape.geos,132)
           
        offshape=offShapeClass(parent=shape,offset=1,offtype='in') 
        Pl.plot_segments(offshape.segments,133,'inner offset')

        #offshape2=offShapeClass(parent=shape,offset=1,offtype='out') 
        #Pl.plot_segments(offshape2.segments,133,'outter offset')
                      
        Pl.canvas.show()        

if 1:
    logging.basicConfig(level=logging.DEBUG,format="%(funcName)-30s %(lineno)-6d: %(message)s")
    master = Tk()
    Pl=PlotClass(master)
    Ex=ExampleClass()
    
    
    #Ex.CheckColinearLines()
    #CheckForIntersections()
    #Ex.SimplePolygonCheck()
    Ex.Distance_Check() 
    #Ex.PWIDTest()
         
    master.mainloop()


     
