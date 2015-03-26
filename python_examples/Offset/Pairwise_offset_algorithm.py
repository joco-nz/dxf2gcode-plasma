#!/usr/bin/python
# -*- coding: cp1252 -*-
#
# Programmer: Christian Kohlöffel
# E-mail:     christian-kohloeffel@t-online.de


from __future__ import division
import matplotlib
# matplotlib see: http://matplotlib.sourceforge.net/ and  http://www.scipy.org/Cookbook/Matplotlib/
# numpy      see: http://numpy.scipy.org/ and http://sourceforge.net/projects/numpy/
matplotlib.use('TkAgg')

import cProfile

from numpy import arange, sin, pi

from matplotlib.axes import Subplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

from Tkconstants import TOP, BOTH, BOTTOM, LEFT, RIGHT, GROOVE
from Tkinter import Tk, Button, Frame
from math import sqrt, sin, cos, tan, atan, atan2, radians, degrees, pi, floor, ceil
import sys

from copy import deepcopy


import logging
logger = logging.getLogger()

eps = 1e-9

class Point:
    __slots__ = ["x", "y", "z"]
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return ('X ->%6.3f  Y ->%6.3f' % (self.x, self.y))
        # return ('CPoints.append(Point(x=%6.5f, y=%6.5f))' %(self.x,self.y))

    def __eq__(self, other):
        """
        Implementaion of is equal of two point, for all other instances it will
        return False
        @param other: The other point for the compare
        @return: True for the same points within tolerance
        """
        if isinstance(other, Point):
            return (-eps < self.x - other.x < eps) and (-eps < self.y - other.y < eps)
        else:
            return False

    def __cmp__(self, other):
        """
        Implementaion of comparing of two point
        @param other: The other point for the compare
        @return: 1 if self is bigger, -1 if smaller, 0 if the same
        """
        if self.x < other.x:
            return -1
        elif self.x > other.x:
            return 1
        elif self.x == other.x and self.y < other.y:
            return -1
        elif self.x == other.x and self.y > other.y:
            return 1
        else:
            return 0

    def __neg__(self):
        """
        Implemnetaion of Point negation
        @return: Returns a new Point which is negated 
        """
        return -1.0 * self

    def __add__(self, other):  # add to another Point
        """
        Implemnetaion of Point addition
        @param other: The other Point which shall be added
        @return: Returns a new Point 
        """
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        """
        Implemnetaion of Point subtraction
        @param other: The other Point which shall be subtracted
        @return: Returns a new Point 
        """
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
            # Scale the points
            return Point(x=self.x * other[0], y=self.y * other[1])
        elif isinstance(other, (int, float, long, complex)):
            return Point(x=self.x * other, y=self.y * other)
        elif isinstance(other, Point):
            # Calculate Scalar (dot) Product
            return self.x * other.x + self.y * other.y
        else:
            logger.warning("Unsupported type: %s" % type(other))

    def __truediv__(self, other):
        return Point(x=self.x / other, y=self.y / other)

    def tr(self, message):
        return message

    def between(self, B, C):
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

    def ccw(self, B, C):
        """
        This functions gives the Direction in which the three points are located.
        @param B: a second point
        @param C: a third point
        @return: If the slope of the line AB is less than the slope of the line
        AC then the three points are listed in a counterclockwise order 
        """
        # return (C.y-self.y)*(B.x-self.x) > (B.y-self.y)*(C.x-self.x)


        area2 = (B.x - self.x) * (C.y - self.y) - (C.x - self.x) * (B.y - self.y)
        # logger.debug(area2)
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
        return Point(self.y * other.z - self.z * other.y, self.z * other.x - self.x * other.z, self.x * other.y - self.y * other.x)

    def distance(self, other=None):
        """Returns distance between two given points"""
        if type(other) == type(None):
            other = Point(x=0.0, y=0.0)
        if isinstance(other, Point):
            return sqrt(pow(self.x - other.x, 2) + pow(self.y - other.y, 2))
        elif isinstance(other, LineGeo):
            return other.distance(self)
        elif isinstance(other, ArcGeo):
            return other.distance(self)
        else:
            logger.error("unsupported instance: %s" % type(other))

    def dotProd(self, P2):
        """
        Returns the dotProduct of two points
        @param self: The first Point
        @param other: The 2nd Point
        @return: dot Product of the points.
        """
        return (self.x * P2.x) + (self.y * P2.y)

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

    def get_normal_vector(self, other, r=1):
        """
        This function return the Normal to a vector defined by self and other
        @param: The second point
        @param r: The length of the normal (-length for other direction)
        @return: Returns the Normal Vector
        """
        unit_vector = self.unit_vector(other)
        return Point(x=unit_vector.y * r, y=-unit_vector.x * r)

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

        # print ('The Direction is: %s' %direction)

        return direction

    def isintol(self, other, tol=eps):
        """Are the two points within 'tol' tolerance?"""
        return (abs(self.x - other.x) <= tol) & (abs(self.y - other.y) <= tol)

    def norm_angle(self, other=None):
        """Returns angle between two given points"""
        if type(other) == type(None):
            other = Point(x=0.0, y=0.0)
        return atan2(other.y - self.y, other.x - self.x)

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
        # The 3 lengths of the triangle to calculate
        a = self.distance(other1)
        b = other1.distance(other2)
        c = self.distance(other2)
        return sqrt(pow(b, 2) - pow((pow(c, 2) + pow(b, 2) - pow(a, 2)) / (2 * c), 2))

    def trim(self, Point, dir=1, rev_norm=False):
        """
        This instance is used to trim the geometry at the given point. The point 
        can be a point on the offset geometry a perpendicular point on line will
        be used for trimming.
        @param Point: The point / perpendicular point for new Geometry
        @param dir: The direction in which the geometry will be kept (1  means the
        being will be trimmed)
        """
        if not(hasattr(self, "end_normal")):
            return self
        new_normal = self.unit_vector(Point)
        if rev_norm:
            new_normal = -new_normal
        if dir == 1:
            self.start_normal = new_normal
            return self
        else:
            self.end_normal = new_normal
            return self

    def unit_vector(self, Pto=None, r=1):
        """
        Returns vector of length 1 with similar direction as input
        @param Pto: The other point 
        @return: Returns the Unit vector
        """
        diffVec = Pto - self
        l = diffVec.distance()
        return Point(diffVec.x / l * r, diffVec.y / l * r)

    def plot2plot(self, plot, format='xr'):
        plot.plot([self.x], [self.y], format)

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
            return BoundingBox(deepcopy(other.Pa), deepcopy(other.Pe))

        xmin = min(self.Pa.x, other.Pa.x)
        xmax = max(self.Pe.x, other.Pe.x)
        ymin = min(self.Pa.y, other.Pa.y)
        ymax = max(self.Pe.y, other.Pe.y)

        return BoundingBox(Pa=Point(xmin, ymin), Pe=Point(xmax, ymax))

    def hasintersection(self, other=None, tol=eps):
        """
        Checks if the two bounding boxes have an intersection
        @param other: The 2nd Bounding Box
        @return: Returns true or false
        """
        if isinstance(other, Point):
            return self.pointisinBB(other, tol)
        elif isinstance(other, BoundingBox):
            x_inter_pos = (self.Pe.x + tol > other.Pa.x) and \
            (self.Pa.x - tol < other.Pe.x)
            y_inter_pos = (self.Pe.y + tol > other.Pa.y) and \
            (self.Pa.y - tol < other.Pe.y)

            return x_inter_pos and y_inter_pos
        else:
            logger.warning("Unsupported Instance: %s" % other.type)

    def pointisinBB(self, Point=Point(), tol=eps):
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
    def __init__(self, Pa, Pe):
        self.type = "LineGeo"
        self.Pa = Pa
        self.Pe = Pe
        self.length = self.Pa.distance(self.Pe)
        self.inters = []
        self.calc_bounding_box()

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """
        return ("\nLineGeo(Pa=Point(x=%s ,y=%s),\n" % (self.Pa.x, self.Pa.y)) + \
               ("Pe=Point(x=%s, y=%s))" % (self.Pe.x, self.Pe.y))

    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        Pa = Point(x=min(self.Pa.x, self.Pe.x), y=min(self.Pa.y, self.Pe.y))
        Pe = Point(x=max(self.Pa.x, self.Pe.x), y=max(self.Pa.y, self.Pe.y))

        self.BB = BoundingBox(Pa=Pa, Pe=Pe)

    def colinear(self, other):
        """
        Check if two lines with same point self.Pe==other.Pa are colinear. For Point
        it check if the point is colinear with the line self.
        @param other: the possibly colinear line
        """
        if isinstance(other, LineGeo):
            return ((self.Pa.ccw(self.Pe, other.Pe) == 0) and
                    (self.Pa.ccw(self.Pe, other.Pa) == 0))
        elif isinstance(other, Point):
            """
            Return true iff a, b, and c all lie on the same line."
            """
            return self.Pa.ccw(self.Pe, other) == 0
        else:
            logger.debug("Unsupported instance: %s" % type(other))

    def colinearoverlapping(self, other):
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
            if self.Pa < self.Pe:
                A = self.Pa
                B = self.Pe
            else:
                A = self.Pe
                B = self.Pa
            if other.Pa < self.Pe:
                C = other.Pa
                D = other.Pe
            else:
                C = other.Pe
                D = other.Pa

            # Swap lines if required
            if not(A <= C):
                A, B, C, D = C, D, A, B

        if B < C:
            return False
        elif B == C:
            return False
        else:
            return True

    def colinearconnected(self, other):
        """
        Check if Lines are connected and colinear
        @param other: Another Line which will be checked
        """

        if not(self.colinear(other)):
            return False
        elif self.Pa == other.Pa:
            return True
        elif self.Pe == other.Pa:
            return True
        elif self.Pa == other.Pe:
            return True
        elif self.Pe == other.Pe:
            return True
        else:
            return False

    def distance(self, other=[]):
        """
        Find the distance between 2 geometry elements. Possible is CCLineGeo
        and ArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        if isinstance(other, LineGeo):
            return self.distance_l_l(other)
        elif isinstance(other, Point):
            return self.distance_l_p(other)
        elif isinstance(other, ArcGeo):
            return self.distance_l_a(other)
        else:
            logger.error(self.tr("Unsupported geometry type: %s" % type(other)))

    def distance_l_l(self, other):
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

    def distance_l_a(self, other):
        """
        Find the distance between 2 ccLineGeo elements. 
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """

        if self.intersect(other):
            return 0.0

        # Get the nearest Point to the Center of the Arc
        POnearest = self.get_nearest_point_l_p(other.O)

        # The Line is outside of the Arc
        if other.O.distance(POnearest) > other.r:
            # If the Nearest Point is on Arc Segement it is the neares one.
            # logger.debug("Nearest Point is outside of arc")
            if other.PointAng_withinArc(POnearest):
                return POnearest.distance(other.O.get_arc_point(other.O.norm_angle(POnearest), r=other.r))
            elif self.distance(other.Pa) < self.distance(other.Pe):
                    return self.get_nearest_point(other.Pa).distance(other.Pa)
            else:
                    return self.get_nearest_point(other.Pe).distance(other.Pe)

        # logger.debug("Nearest Point is Inside of arc")
        # logger.debug("self.distance(other.Pa): %s, self.distance(other.Pe): %s" %(self.distance(other.Pa),self.distance(other.Pe)))
        # The Line may be inside of the ARc or cross it
        if self.distance(other.Pa) < self.distance(other.Pe):
            dis_min = self.distance(other.Pa)
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
        else:
            dis_min = self.distance(other.Pe)
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))

        if ((other.PointAng_withinArc(self.Pa)) and
            abs(other.r - other.O.distance(self.Pa)) < dis_min):
            dis_min = abs(other.r - other.O.distance(self.Pa))
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))

        if ((other.PointAng_withinArc(self.Pe)) and
            abs((other.r - other.O.distance(self.Pe))) < dis_min):
            dis_min = abs(other.r - other.O.distance(self.Pe))
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))

        return dis_min

    def distance_l_p(self, Point):
        """
        Find the shortest distance between CCLineGeo and Point elements.  
        Algorithm acc. to 
        http://notejot.com/2008/09/distance-from-Point-to-line-segment-in-2d/
        http://softsurfer.com/Archive/algorithm_0106/algorithm_0106.htm
        @param Point: the Point
        @return: The shortest distance between the Point and Line
        """
        d = self.Pe - self.Pa
        v = Point - self.Pa

        t = d.dotProd(v)

        if t <= 0:
            # our Point is lying "behind" the segment
            # so end Point 1 is closest to Point and distance is length of
            # vector from end Point 1 to Point.
            return self.Pa.distance(Point)
        elif t >= d.dotProd(d):
            # our Point is lying "ahead" of the segment
            # so end Point 2 is closest to Point and distance is length of
            # vector from end Point 2 to Point.
            return self.Pe.distance(Point)
        else:
            # our Point is lying "inside" the segment
            # i.e.:a perpendicular from it to the line that contains the line
            # segment has an end Point inside the segment
            # logger.debug(v.dotProd(v))
            # logger.debug(d.dotProd(d))
            # logger.debug(v.dotProd(v) - (t*t)/d.dotProd(d))
            if abs(v.dotProd(v) - (t * t) / d.dotProd(d)) < eps:
                return 0.0

            return sqrt(v.dotProd(v) - (t * t) / d.dotProd(d));

    def find_inter_point(self, other, type='TIP'):
        """
        Find the intersection between 2 Geo elements. There can be only one
        intersection between 2 lines. Returns also FIP which lay on the ray.
        @param other: the instance of the 2nd geometry element.
        @param type: Can be "TIP" for True Intersection Point or "Ray" for 
        Intersection which is in Ray (of Line)
        @return: a list of intersection points. 
        """
        if isinstance(other, LineGeo):
            inter = self.find_inter_point_l_l(other, type)
            return inter
        elif isinstance(other, ArcGeo):
            inter = self.find_inter_point_l_a(other, type)
            return inter
        else:
            logger.error("Unsupported Instance: %s" % other.type)

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
            return None

        elif type == 'TIP' and not(self.intersect(other)):

            return None


        dx1 = self.Pe.x - self.Pa.x
        dy1 = self.Pe.y - self.Pa.y

        dx2 = other.Pe.x - other.Pa.x
        dy2 = other.Pe.y - other.Pa.y

        dax = self.Pa.x - other.Pa.x
        day = self.Pa.y - other.Pa.y

        # Return nothing if one of the lines has zero length
        if (dx1 == 0 and dy1 == 0) or (dx2 == 0 and dy2 == 0):
            return None

        # If to avoid division by zero.
        try:
            if(abs(dx2) >= abs(dy2)):
                v1 = (day - dax * dy2 / dx2) / (dx1 * dy2 / dx2 - dy1)
                v2 = (dax + v1 * dx1) / dx2
            else:
                v1 = (dax - day * dx2 / dy2) / (dy1 * dx2 / dy2 - dx1)
                v2 = (day + v1 * dy1) / dy2
        except:
            return None

        return Point(x=self.Pa.x + v1 * dx1,
                          y=self.Pa.y + v1 * dy1)

    def find_inter_point_l_a(self, Arc, type="TIP"):
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

        # Mitternachtsformel zum berechnen der Nullpunkte der quadratischen
        # Gleichung
        a = pow(Ldx, 2) + pow(Ldy, 2)
        b = 2 * Ldx * (self.Pa.x - Arc.O.x) + 2 * Ldy * (self.Pa.y - Arc.O.y)
        c = pow(self.Pa.x - Arc.O.x, 2) + pow(self.Pa.y - Arc.O.y, 2) - pow(Arc.r, 2)
        root = pow(b, 2) - 4 * a * c

        # If the value under the sqrt is negative there is no intersection.
        if root < 0 or a == 0.0:
            return None

        v1 = (-b + sqrt(root)) / (2 * a)
        v2 = (-b - sqrt(root)) / (2 * a)

        Pi1 = Point(x=self.Pa.x + v1 * Ldx,
                       y=self.Pa.y + v1 * Ldy)

        Pi2 = Point(x=self.Pa.x + v2 * Ldx,
               y=self.Pa.y + v2 * Ldy)

        Pi1.v = Arc.dif_ang(Arc.Pa, Pi1, Arc.ext) / Arc.ext
        Pi2.v = Arc.dif_ang(Arc.Pa, Pi2, Arc.ext) / Arc.ext

        if type == 'TIP':
            if ((Pi1.v >= 0.0 and Pi1.v <= 1.0 and self.intersect(Pi1)) and
               (Pi1.v >= 0.0 and Pi2.v <= 1.0 and self.intersect(Pi2))):
                if (root == 0):
                    return Pi1
                else:
                    return [Pi1, Pi2]
            elif (Pi1.v >= 0.0 and Pi1.v <= 1.0 and self.intersect(Pi1)):
                return Pi1
            elif  (Pi1.v >= 0.0 and Pi2.v <= 1.0 and self.intersect(Pi2)):
                return Pi2
            else:
                return None
        elif type == "Ray":
            # If the root is zero only one solution and the line is a tangent.
            if(root == 0):
                return Pi1

            return [Pi1, Pi2]
        else:
            logger.error("We should not be here")

    def get_nearest_point(self, other):
        """
        Get the nearest point on a line to another line lieing on the line
        @param other: The Line to be nearest to
        @return: The point which is the nearest to other
        """
        if isinstance(other, LineGeo):
            return self.get_nearest_point_l_l(other)
        elif isinstance(other, ArcGeo):
            return self.get_nearest_point_l_a(other)
        elif isinstance(other, Point):
            return self.get_nearest_point_l_p(other)
        else:
            logger.error("Unsupported Instance: %s" % other.type)

    def get_nearest_point_l_l(self, other):
        """
        Get the nearest point on a line to another line lieing on the line
        @param other: The Line to be nearest to
        @return: The point which is the nearest to other
        """
        # logger.debug(self.intersect(other))
        if self.intersect(other):
            return self.find_inter_point_l_l(other)
        min_dis = self.distance(other)
        if min_dis == self.distance_l_p(other.Pa):
            return self.get_nearest_point_l_p(other.Pa)
        elif min_dis == self.distance_l_p(other.Pe):
            return self.get_nearest_point_l_p(other.Pe)
        elif min_dis == other.distance_l_p(self.Pa):
            return self.Pa
        elif min_dis == other.distance_l_p(self.Pe):
            return self.Pe
        else:
            logger.warning("No solution found")

    def get_nearest_point_l_a(self, other, ret="line"):
        """
        Get the nearest point to a line lieing on the line
        @param other: The Point to be nearest to
        @return: The point which is the nearest to other
        """
        if self.intersect(other):
            return self.find_inter_point_l_a(other)

        # Get the nearest Point to the Center of the Arc
        POnearest = self.get_nearest_point_l_p(other.O)

        # The Line is outside of the Arc
        if other.O.distance(POnearest) > other.r:
            # If the Nearest Point is on Arc Segement it is the neares one.
            # logger.debug("Nearest Point is outside of arc")
            if other.PointAng_withinArc(POnearest):
                if ret == "line":
                    return POnearest
                elif ret == "arc":
                    return other.O.get_arc_point(other.O.norm_angle(POnearest), r=other.r)
            elif self.distance(other.Pa) < self.distance(other.Pe):
                if ret == "line":
                    return self.get_nearest_point(other.Pa)
                elif ret == "arc":
                    return other.Pa
            else:
                if ret == "line":
                    return self.get_nearest_point(other.Pe)
                elif ret == "art":
                    return other.Pe

        # logger.debug("Nearest Point is Inside of arc")
        # logger.debug("self.distance(other.Pa): %s, self.distance(other.Pe): %s" %(self.distance(other.Pa),self.distance(other.Pe)))
        # The Line may be inside of the ARc or cross it
        if self.distance(other.Pa) < self.distance(other.Pe):
            Pnearest = self.get_nearest_point(other.Pa)
            Pnother = other.Pa
            dis_min = self.distance(other.Pa)
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
        else:
            Pnearest = self.get_nearest_point(other.Pe)
            Pnother = other.Pe
            dis_min = self.distance(other.Pe)
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))

        if ((other.PointAng_withinArc(self.Pa)) and
            abs(other.r - other.O.distance(self.Pa)) < dis_min):

            Pnearest = self.Pa
            Pnother = other.O.get_arc_point(other.O.norm_angle(Pnearest), r=other.r)
            dis_min = abs(other.r - other.O.distance(self.Pa))
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))

        if ((other.PointAng_withinArc(self.Pe)) and
            abs((other.r - other.O.distance(self.Pe))) < dis_min):
            Pnearest = self.Pe
            Pnother = other.O.get_arc_point(other.O.norm_angle(Pnearest), r=other.r)

            dis_min = abs(other.r - other.O.distance(self.Pe))
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
        if ret == "line":
            return Pnearest
        elif ret == "arc":
            return Pnother

    def get_nearest_point_l_p(self, other):
        """
        Get the nearest point to a point lieing on the line
        @param other: The Point to be nearest to
        @return: The point which is the nearest to other
        """
        if self.intersect(other):
            return other

        PPoint = self.perpedicular_on_line(other)

        if self.intersect(PPoint):
            return PPoint

        if self.Pa.distance(other) < self.Pe.distance(other):
            return self.Pa
        else:
            return self.Pe

    def intersect(self, other):
        """
        Check if there is an intersection of two geometry elements
        @param, a second geometry which shall be checked for intersection
        @return: True if there is an intersection
        """
        # Do a raw check first with BoundingBox
        # logger.debug("self: %s, \nother: %s, \nintersect: %s" %(self,other,self.BB.hasintersection(other.BB)))
        # logger.debug("self.BB: %s \nother.BB: %s")
        # logger.debug(self.BB.hasintersection(other.BB))
        # We need to test Point first cause it has no BB
        if isinstance(other, Point):
            return self.intersect_l_p(other)
        elif not(self.BB.hasintersection(other.BB)):
            return False
        elif isinstance(other, LineGeo):
            return self.intersect_l_l(other)
        elif isinstance(other, ArcGeo):
            return self.intersect_l_a(other)
        else:
            logger.error("Unsupported Instance: %s" % other.type)

    def intersect_l_a(self, other):
        """
        Check if there is an intersection of the two line
        @param, a second line which shall be checked for intersection
        @return: True if there is an intersection
        """
        inter = self.find_inter_point_l_a(other)
        return not(inter is None)

    def intersect_l_l(self, other):
        """
        Check if there is an intersection of the two line
        @param, a second line which shall be checked for intersection
        @return: True if there is an intersection
        """
        A = self.Pa
        B = self.Pe
        C = other.Pa
        D = other.Pe
        return A.ccw(C, D) != B.ccw(C, D) and A.ccw(B, C) != A.ccw(B, D)

    def intersect_l_p(self, Point):
        """
        Check if Point is colinear and within the Line
        @param Point: A Point which will be checked
        @return: True if point Point intersects the line segment from Pa to Pe.
        Refer to http://stackoverflow.com/questions/328107/how-can-you-determine-a-point-is-between-two-other-points-on-a-line-segment
        """
        # (or the degenerate case that all 3 points are coincident)
        # logger.debug(self.colinear(Point))
        return (self.colinear(Point)
                and (self.within(self.Pa.x, Point.x, self.Pe.x)
                     if self.Pa.x != self.Pe.x else
                     self.within(self.Pa.y, Point.y, self.Pe.y)))

    def within(self, p, q, r):
        "Return true iff q is between p and r (inclusive)."
        return p <= q <= r or r <= q <= p

    def join_colinear_line(self, other):
        """
        Check if the two lines are colinear connected or inside of each other, in 
        this case these lines will be joined to one common line, otherwise return
        both lines
        @param other: a second line
        @return: Return one or two lines 
        """
        if self.colinearconnected(other)or self.colinearoverlapping(other):
            if self.Pa < self.Pe:
                newPa = min(self.Pa, other.Pa, other.Pe)
                newPe = max(self.Pe, other.Pa, other.Pe)
            else:
                newPa = max(self.Pa, other.Pa, other.Pe)
                newPe = min(self.Pe, other.Pa, other.Pe)
            return [LineGeo(newPa, newPe)]
        else:
            return [self, other]

    def perpedicular_on_line(self, other):
        """
        This function calculates the perpendicular point on a line (or ray of line)
        with the shortest distance to the point given with other
        @param other: The point to be perpendicular to
        @return: A point which is on line and perpendicular to Point other
        @see: http://stackoverflow.com/questions/1811549/perpendicular-on-a-line-from-a-given-point
        """
        # first convert line to normalized unit vector
        unit_vector = self.Pa.unit_vector(self.Pe)

        # translate the point and get the dot product
        lam = ((unit_vector.x * (other.x - self.Pa.x))
                + (unit_vector.y * (other.y - self.Pa.y)))
        return Point(x=(unit_vector.x * lam) + self.Pa.x,
                     y=(unit_vector.y * lam) + self.Pa.y)

    def plot2plot(self, plot, format='-m'):
        plot.plot([self.Pa.x, self.Pe.x], [self.Pa.y, self.Pe.y], format)

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
        # The Point where the geo shall be splitted
        if not(ipoint):
            return [self]
        elif self.intersect(ipoint):
            Li1 = LineGeo(Pa=self.Pa, Pe=ipoint)
            Li2 = LineGeo(Pa=ipoint, Pe=self.Pe)
            return [Li1, Li2]        
        else:
            return [self]

    def trim(self, Point, dir=1, rev_norm=False):
        """
        This instance is used to trim the geometry at the given point. The point 
        can be a point on the offset geometry a perpendicular point on line will
        be used for trimming.
        @param Point: The point / perpendicular point for new Geometry
        @param dir: The direction in which the geometry will be kept (1  means the
        being will be trimmed)
        """
        newPoint = self.perpedicular_on_line(Point)
        if dir == 1:
            new_line = LineGeo(newPoint, self.Pe)
            new_line.end_normal = self.end_normal
            new_line.start_normal = self.start_normal
            return new_line
        else:
            new_line = LineGeo(self.Pa, newPoint)
            new_line.end_normal = self.end_normal
            new_line.start_normal = self.start_normal
            return new_line

class ArcGeo:
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """
    def __init__(self, Pa=None, Pe=None, O=None, r=1,
                 s_ang=None, e_ang=None, direction=1, drag=False):
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

                if abs(r - m) < 0.0001:
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

        # Falls nicht uebergeben dann Anfangs- und Endwinkel ausrechen
        if type(self.s_ang) == type(None):
            self.s_ang = self.O.norm_angle(Pa)

        if type(self.e_ang) == type(None):
            self.e_ang = self.O.norm_angle(Pe)

        self.ext = self.dif_ang(self.Pa, self.Pe, direction)
        # self.get_arc_extend(direction)

        # Falls es ein Kreis ist Umfang 2pi einsetzen
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
        return ("\nArcGeo(Pa=Point(x=%s ,y=%s), \n" % (self.Pa.x, self.Pa.y)) + \
               ("Pe=Point(x=%s, y=%s),\n" % (self.Pe.x, self.Pe.y)) + \
               ("O=Point(x=%s, y=%s),\n" % (self.O.x, self.O.y)) + \
               ("s_ang=%s,e_ang=%s,\n" % (self.s_ang, self.e_ang)) + \
               ("r=%s, \n" % self.r) + \
               ("ext=%s)" % self.ext)

#        return ("\nArcGeo") + \
#               ("\nPa : %s; s_ang: %0.5f" % (self.Pa, self.s_ang)) + \
#               ("\nPe : %s; e_ang: %0.5f" % (self.Pe, self.e_ang)) + \
#               ("\nO  : %s; r: %0.3f" % (self.O, self.r)) + \
#               ("\next  : %0.5f; length: %0.5f" % (self.ext, self.length))

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

        # Do the calculation only for arcs have positiv extend => switch angles
        if self.ext >= 0:
            s_ang = self.s_ang
            e_ang = self.e_ang
        elif self.ext < 0:
            s_ang = self.e_ang
            e_ang = self.s_ang

        # If the positive X Axis is crossed
        if not(self.wrap(s_ang, 0) >= self.wrap(e_ang, 1)):
            Pe.x = max(self.Pa.x, self.Pe.x)

        # If the positive Y Axis is crossed
        if not(self.wrap(s_ang - pi / 2, 0) >= self.wrap(e_ang - pi / 2, 1)):
            Pe.y = max(self.Pa.y, self.Pe.y)

        # If the negative X Axis is crossed
        if not(self.wrap(s_ang - pi, 0) >= self.wrap(e_ang - pi, 1)):
            Pa.x = min(self.Pa.x, self.Pe.x)

        # If the negative Y is crossed
        if not(self.wrap(s_ang - 1.5 * pi, 0) >= 
                self.wrap(e_ang - 1.5 * pi, 1)):
            Pa.y = min(self.Pa.y, self.Pe.y)

        self.BB = BoundingBox(Pa=Pa, Pe=Pe)

    def dif_ang(self, P1, P2, direction, tol=eps):
        """
        Calculated the angle of extend based on the 3 given points. Center Point,
        P1 and P2.
        @param P1: the start Point of the arc 
        @param P2: the end Point of the arc
        @param direction: the direction of the arc
        @return: Returns the angle between -2* pi and 2 *pi for the arc extend
        """
        # FIXME Das koennte Probleme geben bei einem reelen Kreis
#        if P1.isintol(P2,tol):
#            return 0.0
        sa = self.O.norm_angle(P1)
        ea = self.O.norm_angle(P2)

        if(direction > 0.0):  # GU
            dif_ang = (ea - sa) % (-2 * pi)
            dif_ang -= floor(dif_ang / (2 * pi)) * (2 * pi)
        else:
            dif_ang = (ea - sa) % (-2 * pi)
            dif_ang += ceil(dif_ang / (2 * pi)) * (2 * pi)

        return dif_ang

    def distance(self, other):
        """
        Find the distance between 2 geometry elements. Possible is LineGeo
        and ArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        """
        Find the distance between 2 geometry elements. Possible is Point, LineGeo
        and ArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        if isinstance(other, LineGeo):
            return other.distance_l_a(self)
        elif isinstance(other, Point):
            return self.distance_a_p(other)
        elif isinstance(other, ArcGeo):
            return self.distance_a_a(other)
        else:
            logger.error(self.tr("Unsupported geometry type: %s" % type(other)))

    def distance_a_a(self, other):
        """
        Find the distance between two arcs
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        # logger.error('Unsupported function')
        Pself = self.get_nearest_point(other)
        Pother = other.get_nearest_point(self)
        return Pself.distance(Pother)

    def distance_a_p(self, other):
        """
        Find the distance between a arc and a point
        @param other: the instance of the 2nd geometry element.
        @return: The distance between the two geometries 
        """
        # The Pont is outside of the Arc
        if self.O.distance(other) > self.r:
            # If the Nearest Point is on Arc Segement it is the neares one.
            # logger.debug("Nearest Point is outside of arc")
            if self.PointAng_withinArc(other):
                return other.distance(self.O.get_arc_point(self.O.norm_angle(other), r=self.r))
            elif other.distance(self.Pa) < other.distance(self.Pe):
                    return other.distance(self.Pa)
            else:
                    return other.distance(self.Pe)

        # logger.debug("Nearest Point is Inside of arc")
        # logger.debug("self.distance(other.Pa): %s, self.distance(other.Pe): %s" %(self.distance(other.Pa),self.distance(other.Pe)))
        # The Line may be inside of the ARc or cross it
        if other.distance(self.Pa) < other.distance(self.Pe):
            dis_min = other.distance(self.Pa)
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
        else:
            dis_min = other.distance(self.Pe)
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))

        if ((self.PointAng_withinArc(other)) and
            abs(self.r - self.O.distance(other)) < dis_min):
            dis_min = abs(self.r - self.O.distance(other))
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))

        return dis_min

    def find_inter_point(self, other=[], type='TIP'):
        """
        Find the intersection between 2 geometry elements. Possible is CCLineGeo
        and ArcGeo
        @param other: the instance of the 2nd geometry element.
        @param type: Can be "TIP" for True Intersection Point or "Ray" for 
        Intersection which is in Ray (of Line)        @return: a list of intersection points. 
        """
        if isinstance(other, LineGeo):
            IPoints = other.find_inter_point_l_a(self, type)
            return IPoints
        elif isinstance(other, ArcGeo):
            return self.find_inter_point_a_a(other, type)
        else:
            logger.error("Unsupported Instance: %s" % other.type)

    def find_inter_point_a_a(self, other, type='TIP'):
        """
        Find the intersection between 2 ArcGeo elements. There can be only one
        intersection between 2 lines.
        @param other: the instance of the 2nd geometry element.
        @param type: Can be "TIP" for True Intersection Point or "Ray" for 
        Intersection which is in Ray (of Line)        
        @return: a list of intersection points. 
        @todo: FIXME: The type of the intersection is not implemented up to now
        """
        O_dis = self.O.distance(other.O)

        # If self circle is surrounded by the other no intersection
        if(O_dis < abs(self.r - other.r)):
            return None

        # If other circle is surrounded by the self no intersection
        if(O_dis < abs(other.r - self.r)):
            return None

        # If The circles are to far away from each other no intersection possible
        if (O_dis > abs(other.r + self.r)):
            return None

        # If both circles have the same center and radius
        if abs(O_dis) == 0.0 and abs(self.r - other.r) == 0.0:
            Pi1 = Point(x=self.Pa.x, y=self.Pa.y)
            Pi2 = Point(x=self.Pe.x, y=self.Pe.y)

            return [Pi1, Pi2]
        # The following algorithm was found on :
        # http://www.sonoma.edu/users/w/wilsonst/Papers/Geometry/circles/default.htm

        root = ((pow(self.r + other.r , 2) - pow(O_dis, 2)) * 
                  (pow(O_dis, 2) - pow(other.r - self.r, 2)))

        # If the Line is a tangent the root is 0.0.
        if root <= 0.0:
            root = 0.0
        else:
            root = sqrt(root)

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

        Pi1.v1 = self.dif_ang(self.Pa, Pi1, self.ext) / self.ext
        Pi1.v2 = other.dif_ang(other.Pa, Pi1, other.ext) / other.ext

        Pi2 = Point(x=xbase - (other.O.y - self.O.y) / \
                         (2 * pow(O_dis, 2)) * root,
                    y=ybase + (other.O.x - self.O.x) / \
                    (2 * pow(O_dis, 2)) * root)

        Pi2.v1 = self.dif_ang(self.Pa, Pi2, self.ext) / self.ext
        Pi2.v2 = other.dif_ang(other.Pa, Pi2, other.ext) / other.ext


        if type == 'TIP':
            if ((Pi1.v1 >= 0.0 and Pi1.v1 <= 1.0 and Pi1.v2 > 0.0 and Pi1.v2 <= 1.0) and
               (Pi2.v1 >= 0.0 and Pi2.v1 <= 1.0 and Pi2.v2 > 0.0 and Pi2.v2 <= 1.0)):
                if (root == 0):
                    return Pi1
                else:
                    return [Pi1, Pi2]
            elif (Pi1.v1 >= 0.0 and Pi1.v1 <= 1.0 and Pi1.v2 > 0.0 and Pi1.v2 <= 1.0):
                return Pi1
            elif  (Pi2.v1 >= 0.0 and Pi2.v1 <= 1.0 and Pi2.v2 > 0.0 and Pi2.v2 <= 1.0):
                return Pi2
            else:
                return None
        elif type == "Ray":
            # If the root is zero only one solution and the line is a tangent.
            if root == 0:
                return Pi1
            else:
                return [Pi1, Pi2]
        else:
            logger.error("We should not be here")

    def get_arc_direction(self, newO):
        """ 
        Calculate the arc direction given from the Arc and O of the new Arc.
        @param O: The center of the arc
        @return: Returns the direction (+ or - pi/2)
        @todo: FIXME: The type of the intersection is not implemented up to now
        """

        a1 = self.e_ang - pi / 2 * self.ext / abs(self.ext)
        a2 = self.Pe.norm_angle(newO)
        direction = a2 - a1

        if direction > pi:
            direction = direction - 2 * pi
        elif direction < -pi:
            direction = direction + 2 * pi

        # print ('Die Direction ist: %s' %direction)

        return direction

    def get_nearest_point(self, other):
        """
        Get the nearest point on the arc to another geometry.
        @param other: The Line to be nearest to
        @return: The point which is the nearest to other
        """
        if isinstance(other, LineGeo):
            return other.get_nearest_point_l_a(self, ret="arc")
        elif isinstance(other, ArcGeo):
            return self.get_nearest_point_a_a(other)
        elif isinstance(other, Point):
            return self.get_nearest_point_a_p(other)
        else:
            logger.error("Unsupported Instance: %s" % other.type)

    def get_nearest_point_a_p(self, other):
        """
        Get the nearest point to a point lieing on the arc
        @param other: The Point to be nearest to
        @return: The point which is the nearest to other
        """
        if self.intersect(other):
            return other

        PPoint = self.O.get_arc_point(self.O.norm_angle(other), r=self.r)
        if self.intersect(PPoint):
            return PPoint
        elif self.Pa.distance(other) < self.Pe.distance(other):
            return self.Pa
        else:
            return self.Pe

    def get_nearest_point_a_a(self, other, ret="self"):
        """
        Get the nearest point to a line lieing on the line
        @param other: The Point to be nearest to
        @return: The point which is the nearest to other
        """
        if self.intersect(other):
            return self.find_inter_point_a_a(other)



        # The Arc is outside of the Arc
        # if other.O.distance(self.O)>(other.r+other.r):

        # If Nearest point is on both Arc Segments.
        if other.PointAng_withinArc(self.O) and self.PointAng_withinArc(other.O):
            if ret == "self":
                return self.O.get_arc_point(self.O.norm_angle(other.O), r=self.r)
            elif ret == "other":
                return other.O.get_arc_point(other.O.norm_angle(self.O), r=other.r)
        # If Nearest point is on self Arc Segment but not other
        elif self.PointAng_withinArc(other.O):
            if self.distance(other.Pa) < self.distance(other.Pe):
                if ret == "self":
                    return self.O.get_arc_point(self.O.norm_angle(other.Pa), r=self.r)
                elif ret == "other":
                    return other.Pa
            else:
                if ret == "self":
                    return self.O.get_arc_point(self.O.norm_angle(other.Pe), r=self.r)
                elif ret == "other":
                    return other.Pe
        # If Nearest point is on other Arc Segment but not self
        elif other.PointAng_withinArc(self.O):
            if other.distance(self.Pa) < other.distance(self.Pe):
                if ret == "self":
                    return self.Pa
                elif ret == "other":
                    return other.O.get_arc_point(other.O.norm_angle(self.Pa), r=other.r)
            else:
                if ret == "self":
                    return self.Pe
                elif ret == "other":
                    return other.O.get_arc_point(other.O.norm_angle(self.Pe), r=other.r)
        # If the min distance is not on any arc segemtn but other.Pa is nearer then other.Pe
        elif self.distance(other.Pa) < self.distance(other.Pe):
            if self.Pa.distance(other.Pa) < self.Pe.distance(other.Pa):
                if ret == "self":
                    return self.Pa
                elif ret == "other":
                    return other.Pa
            else:
                if ret == "self":
                    return self.Pe
                elif ret == "other":
                    return other.Pa
        else:
            if self.Pa.distance(other.Pe) < self.Pe.distance(other.Pe):
                if ret == "self":
                    return self.Pa
                elif ret == "other":
                    return other.Pe
            else:
                if ret == "self":
                    return self.Pe
                elif ret == "other":
                    return other.Pe



#         #logger.debug("Nearest Point is Inside of arc")
#         #logger.debug("self.distance(other.Pa): %s, self.distance(other.Pe): %s" %(self.distance(other.Pa),self.distance(other.Pe)))
#         # The Line may be inside of the ARc or cross it
#         if self.distance(other.Pa)<self.distance(other.Pe):
#             Pnearest=self.get_nearest_point(other.Pa)
#             Pnother=other.Pa
#             dis_min=self.distance(other.Pa)
#             #logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
#         else:
#             Pnearest=self.get_nearest_point(other.Pe)
#             Pnother=other.Pe
#             dis_min=self.distance(other.Pe)
#             #logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
#
#         if ((other.PointAng_withinArc(self.Pa)) and
#             abs(other.r-other.O.distance(self.Pa)) < dis_min):
#
#             Pnearest=self.Pa
#             Pnother=other.O.get_arc_point(other.O.norm_angle(Pnearest),r=other.r)
#             dis_min=abs(other.r-other.O.distance(self.Pa))
#             #logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
#
#         if ((other.PointAng_withinArc(self.Pe)) and
#             abs((other.r-other.O.distance(self.Pe))) < dis_min):
#             Pnearest=self.Pe
#             Pnother=other.O.get_arc_point(other.O.norm_angle(Pnearest),r=other.r)
#
#             dis_min=abs(other.r-other.O.distance(self.Pe))
#             #logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
#         if ret=="line":
#             return Pnearest
#         elif ret=="arc":
#             return Pnother

    def intersect(self, other):
        """
        Check if there is an intersection of two geometry elements
        @param, a second geometry which shall be checked for intersection
        @return: True if there is an intersection
        """
        # Do a raw check first with BoundingBox
        # logger.debug("self: %s, \nother: %s, \nintersect: %s" %(self,other,self.BB.hasintersection(other.BB)))
        # logger.debug("self.BB: %s \nother.BB: %s")

        # We need to test Point first cause it has no BB
        if isinstance(other, Point):
            return self.intersect_a_p(other)
        elif not(self.BB.hasintersection(other.BB)):
            return False
        elif isinstance(other, LineGeo):
            return other.intersect_l_a(self)
        elif isinstance(other, ArcGeo):
            return self.intersect_a_a(other)
        else:
            logger.error("Unsupported Instance: %s" % other.type)

    def intersect_a_a(self, other):
        """
        Check if there is an intersection of two arcs
        @param, a second arc which shall be checked for intersection
        @return: True if there is an intersection
        """
        inter = self.find_inter_point_a_a(other)
        return not(inter is None)

    def intersect_a_p(self, other):
        """
        Check if there is an intersection of an point and a arc
        @param, a second arc which shall be checked for intersection
        @return: True if there is an intersection
        """
        # No intersection possible if point is not within radius
        if not(abs(self.O.distance(other) - self.r) < abs):
            return False
        elif self.PointAng_withinArc(other):
            return True
        else:
            return False

    def plot2plot(self, plot, format='-m'):

        x = []
        y = []
        segments = int((abs(degrees(self.ext)) // 3) + 1)
        for i in range(segments + 1):

            ang = self.s_ang + i * self.ext / segments
            x += [self.O.x + cos(ang) * abs(self.r)]
            y += [self.O.y + sin(ang) * abs(self.r)]

        plot.plot(x, y, format)

    def PointAng_withinArc(self, Point):
        """
        Check if the angle defined by Point is within the span of the arc.
        @param Point: The Point which angle to be checked 
        @return: True or False
        """
        v = self.dif_ang(self.Pa, Point, self.ext) / self.ext
        return v >= 0.0 and v <= 1.0

    def reverse(self):
        """ 
        Reverses the direction of the arc (switch direction).
        """
        self.Pa, self.Pe = self.Pe, self.Pa
        self.s_ang, self.e_ang = self.e_ang, self.s_ang
        self.ext = -self.ext

    def split_into_2geos(self, ipoint=Point()):
        """
        Splits the given geometry into 2 not self intersection geometries. The
        geometry will be splitted between ipoint and Pe.
        @param ipoint: The Point where the intersection occures
        @return: A list of 2 ArcGeo's will be returned.
        """
        # The angle between endpoint and where the intersection occures
        d_e_ang = self.e_ang - self.O.norm_angle(ipoint)

        # Correct by 2*pi if the direction is wrong
        if d_e_ang > self.ext:
            d_e_ang -= 2 * pi

        # The Point where the geo shall be splitted
        spoint = self.O.get_arc_point(ang=degrees(self.e_ang - d_e_ang / 2),
                                      r=self.r)

        # Generate the 2 geometries and their bounding boxes.
        Arc1 = ArcGeo(Pa=self.Pa, Pe=spoint, r=self.r,
                       O=self.O, direction=self.ext)

        Arc2 = ArcGeo(Pa=spoint, Pe=self.Pe, r=self.r,
                       O=self.O, direction=self.ext)
        return [Arc1, Arc2]

    def trim(self, Point, dir=1, rev_norm=False):
        """
        This instance is used to trim the geometry at the given point. The point 
        can be a point on the offset geometry a perpendicular point on line will
        be used for trimming.
        @param Point: The point / perpendicular point for new Geometry
        @param dir: The direction in which the geometry will be kept (1  means the
        beginn will be trimmed)
        @param rev_norm: If the direction of the point is on the reversed side.
        """

        logger.debug("I'm getting trimmed: %s, %s, %s, %s" % (self, Point, dir, rev_norm))
        new_normal = self.O.get_arc_point(self.O.norm_angle(Point), r=1)
        if rev_norm:
           new_normal = -new_normal


        newPoint = self.O + new_normal * self.r
        [Arc1, Arc2] = self.split_into_2geos(newPoint)
         
        if dir == 1:
            new_arc = Arc1
            if hasattr(self, "end_normal"):
                new_arc.end_normal = self.end_normal
                new_arc.start_normal = new_normal
            return new_arc
        else:
            new_arc = Arc2
            if hasattr(self, "end_normal"):
                new_arc.end_normal = new_normal
                new_arc.start_normal = self.start_normal
            return new_arc
#         return self

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
    def __init__(self, geos=[], closed=False, length=0.0):
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
        # self.BB = BoundingBox(Pa=None, Pe=None)

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
        if len(self.geos) < 2:
            return

        new_geos = [self.geos[0]]
        for i in range(1, len(self.geos)):
            geo1 = new_geos[-1]
            geo2 = self.geos[i]

            # Remove first geometry and add result of joined geometries. Required
            # Cause the join will give back the last 2 geometries.
            new_geos.pop()
            if isinstance(geo1, LineGeo) and isinstance(geo2, LineGeo):
                new_geos += geo1.join_colinear_line(geo2)

            # If start end End Point are the same remove geometry
            if new_geos[-1].Pa == new_geos[-1].Pe:
                new_geos.pop()


        # For closed polylines check if the first and last items are colinear
        if self.closed:
            geo1 = new_geos[-1]
            geo2 = new_geos[0]
            joined_geos = geo1.join_colinear_line(geo2)

            # If they are joind replace firste item by joined and remove last one
            if len(joined_geos) == 1:
                new_geos[0] = joined_geos[0]
                new_geos.pop()

        self.geos = new_geos

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
            if isinstance(geo, LineGeo):
                start = geo.Pa
                ende = geo.Pe
                summe += (start.x + ende.x) * (ende.y - start.y) / 2
                start = ende
            elif isinstance(geo, ArcGeo):
                segments = int((abs(degrees(geo.ext)) // 90) + 1)
                for i in range(segments):
                    ang = geo.s_ang + (i + 1) * geo.ext / segments
                    ende = Point(x=(geo.O.x + cos(ang) * abs(geo.r)),
                                 y=(geo.O.y + sin(ang) * abs(geo.r)))
                    summe += (start.x + ende.x) * (ende.y - start.y) / 2
                    start = ende

        # Positiv sum means the shape is oriented CCW
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

class ConvexPoint(Point):
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

        Point.__init__(self, x=x, y=y, z=z)
    def plot2plot(self, plot, format='dk'):
        plot.plot([self.x], [self.y], 'dk')

class offShapeClass(ShapeClass):
    """
    This Class is used to generate The fofset aof a shape according to:
    "A pair-wise offset Algorithm for 2D point sequence curve"
    http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.101.8855
    """
    def __init__(self, parent=ShapeClass(), offset=1, offtype='in'):
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
        self.offset = offset
        self.offtype = offtype
        self.segments = []
        self.rawoff = []

        self.plotshapes = []

        self.make_shape_ccw()
        # self.join_colinear_lines()

        self.make_segment_types()
        nextConvexPoint = [e for e in self.segments if isinstance(e, ConvexPoint)]
        # nextConvexPoint=[nextConvexPoint[31]]
        self.counter = 0


        while len(nextConvexPoint):  # [self.convex_vertex[-1]]:
            convex_vertex_nr = self.segments.index(nextConvexPoint[0])

            forward, backward = self.PairWiseInterferenceDetection(convex_vertex_nr + 1, convex_vertex_nr - 1)

            if forward is None:
                return
                break


            if backward == 0 and forward == (len(self.segments) - 1):
                self.segments = []
                break

            # Make Raw offset curve of forward and backward segment
            fw_rawoff_seg = self.make_rawoff_seg(self.segments[forward])
            bw_rawoff_seg = self.make_rawoff_seg(self.segments[backward])

            # Intersect the two segements
            iPoint = fw_rawoff_seg.find_inter_point(bw_rawoff_seg)

            # logger.debug("fw_rawoff_seg: %s, bw_rawoff_seg: %s" %(fw_rawoff_seg,bw_rawoff_seg))
            # logger.debug("forward: %s, backward: %s, iPoint: %s =====================================" %(forward,backward,iPoint))

            self.plotshapes = [fw_rawoff_seg, bw_rawoff_seg, iPoint]


            if iPoint is None:
                logger.error("No intersection found?!")
                # logger.debug(fw_rawoff_seg)
                # logger.debug(bw_rawoff_seg)
                break

            # Reomve the LIR from the PS Curce
            self.remove_LIR(forward, backward, iPoint)
            nextConvexPoint = [e for e in self.segments if isinstance(e, ConvexPoint)]
            # logger.debug(nextConvexPoint)
            # nextConvexPoint=[]
            # logger.debug(nextConvexPoint)


        for seg in self.segments:
            self.rawoff += [self.make_rawoff_seg(seg)]

    def make_rawoff_seg(self, seg):
        """
        This function returns the rawoffset of a segement. A line for a line and
        a circle for a reflex segement.
        @param segment_nr: The nr of the segement for which the rawoffset
        segement shall be generated
        @ return: Returns the rawoffsetsegement of the  defined segment 
        """

        # seg=self.segments[segment_nr]

        if self.offtype == "out":
            offset = -abs(self.offset)
        else:
            offset = abs(self.offset)

        # if segement 1 is inverted change End Point
        if isinstance(seg, LineGeo):
            Pa = seg.Pa + seg.start_normal * offset
            Pe = seg.Pe + seg.end_normal * offset
            return LineGeo(Pa, Pe)

        elif isinstance(seg, Point):
            Pa = seg + seg.start_normal * offset
            Pe = seg + seg.end_normal * offset

            return ArcGeo(Pa=Pa, Pe=Pe, O=deepcopy(seg), r=self.offset, direction=offset)
        elif isinstance(seg, ArcGeo):
            Pa = seg.Pa + seg.start_normal * offset
            Pe = seg.Pe + seg.end_normal * offset

            if seg.ext > 0:
                return ArcGeo(Pa=Pa, Pe=Pe, O=seg.O, r=seg.r + offset, direction=seg.ext)
            else:
                return ArcGeo(Pa=Pa, Pe=Pe, O=seg.O, r=seg.r - offset, direction=seg.ext)

        elif isinstance(seg, ConvexPoint):
            Pa = seg + seg.start_normal * offset
            Pe = seg + seg.end_normal * offset
            return ArcGeo(Pa=Pa, Pe=Pe, O=deepcopy(seg), r=self.offset, direction=offset)
        else:
            logger.error("Unsupportet Object type: %s" % type(seg))

    def make_segment_types(self):
        """
        This function is called in order to generate the segements according to 
        Definiton 2.
        An edge (line) is a linear segment and a reflex vertex is is reflex 
        segment. Colinear lines are assumed to be removed prior to the segment 
        type definition.        
        """
         # Do only if more then 2 geometies
        if len(self.geos) < 2:
            return

        # Start with first Vertex if the line is closed
        if self.closed:
            start = 0
        else:
            start = 1

        for i in range(start, len(self.geos)):
            geo1 = self.geos[i - 1]
            geo2 = self.geos[i]

            if i == start:
                if isinstance(geo1, LineGeo):
                    geo1.start_normal = geo1.Pa.get_normal_vector(geo1.Pe)
                    geo1.end_normal = geo1.Pa.get_normal_vector(geo1.Pe)
                else:
                    geo1.start_normal = geo1.Pa.unit_vector(geo1.O, r=1)
                    geo1.end_normal = geo1.Pe.unit_vector(geo1.O, r=1)
                
            if isinstance(geo2, LineGeo):
                geo2.start_normal = geo2.Pa.get_normal_vector(geo2.Pe)
                geo2.end_normal = geo2.Pa.get_normal_vector(geo2.Pe)
            elif isinstance(geo2, ArcGeo):
                geo2.start_normal = geo2.Pa.unit_vector(geo2.O, r=1)
                geo2.end_normal = geo2.Pe.unit_vector(geo2.O, r=1)
                
            # logger.debug("geo1: %s, geo2: %s" % (geo1, geo2))
            # logger.debug("geo1.end_normal: %s, geo2.start_normal: %s" % (geo1.end_normal, geo2.start_normal))

            # If it is a reflex vertex add a reflex segemnt (single point)

            if (((geo1.Pe.ccw(geo1.Pe + geo1.end_normal,
                              geo1.Pe + geo1.end_normal + 
                              geo2.start_normal) == 1) and  
                 self.offtype == "in") or
                (geo1.Pe.ccw(geo1.Pe + geo1.end_normal,
                             geo1.Pe + geo1.end_normal + 
                             geo2.start_normal) == -1 and 
                 self.offtype == "out")):
                
                # logger.debug("reflex")

                geo1.Pe.start_normal = geo1.end_normal
                geo1.Pe.end_normal = geo2.start_normal
                self.segments += [geo1.Pe, geo2]

            # Add the linear segment which is a line connecting 2 vertices
            else:
                # logger.debug("convex")
                self.segments += [ConvexPoint(geo1.Pe.x, geo1.Pe.y), geo2]

    def interfering_full(self, segment1, dir, segment2):
        """
        Check if the Endpoint (dependent on dir) of segment 1 is interfering with 
        segment 2 Definition according to Definition 6
        @param segment 1: The first segment 
        @param dir: The direction of the line 1, as given -1 reversed direction
        @param segment 2: The second segment to be checked
        @ return: Returns True or False
        """

        # if segement 1 is inverted change End Point
        if isinstance(segment1, LineGeo) and dir == 1:
            Pe = segment1.Pe
        elif isinstance(segment1, LineGeo) and dir == -1:
            Pe = segment1.Pa
        elif isinstance(segment1, ConvexPoint):
            return False
        elif isinstance(segment1, Point):
            Pe = segment1
        elif isinstance(segment1, ArcGeo) and dir == 1:
            Pe = segment1.Pe
        elif isinstance(segment1, ArcGeo) and dir == -1:
            Pe = segment1.Pa
        else:
            logger.error("Unsupportet Object type: %s" % type(segment1))

        # if we cut outside reverse the offset
        if self.offtype == "out":
            offset = -abs(self.offset)
        else:
            offset = abs(self.offset)


        if dir == 1:
            distance = segment2.distance(Pe + segment1.end_normal * offset)
            self.interferingshapes += [LineGeo(Pe, Pe + segment1.end_normal * offset),
                                     segment2,
                                     ArcGeo(O=Pe + segment1.end_normal * offset,
                                            Pa=Pe, Pe=Pe ,
                                            s_ang=0, e_ang=2 * pi, r=self.offset)]
        else:
            logger.debug(Pe)
            logger.debug(segment1)
            logger.debug(segment1.start_normal)
            distance = segment2.distance(Pe + segment1.start_normal * offset)
            self.interferingshapes += [LineGeo(Pe, Pe + segment1.start_normal * offset),
                                     segment2,
                                     ArcGeo(O=Pe + segment1.start_normal * offset,
                                            Pa=Pe, Pe=Pe,
                                            s_ang=0, e_ang=2 * pi, r=self.offset)]

        # logger.debug("Full distance: %s" %distance)


        # If the distance from the Segment to the Center of the Tangential Circle
        # is smaller then the radius we have an intersection
        # logger.debug(distance)
        return distance <= abs(offset)

    def interfering_partly(self, segment1, dir, segment2):
        """
        Check if any tangential circle of segment 1 is interfering with 
        segment 2. Definition according to Definition 5
        @param segment 1: The first Line 
        @param dir: The direction of the segment 1, as given -1 reversed direction
        @param segment 2: The second line to be checked
        @ return: Returns True or False
        """
        if isinstance(segment1, ConvexPoint):
            logger.debug("Should not be here")
            return False
        else:
            offGeo = self.make_rawoff_seg(segment1)
            self.interferingshapes += [offGeo]
        
        # if we cut outside reverse the offset
        if self.offtype == "out":
            offset = -abs(self.offset)
        else:
            offset = abs(self.offset)
# 
#         # if segement 1 is inverted change End Point
#         if isinstance(segment1, LineGeo):
#             Pa = segment1.Pa + segment1.start_normal * offset
#             Pe = segment1.Pe + segment1.end_normal * offset
#             offGeo = LineGeo(Pa, Pe)
#             self.interferingshapes += [offGeo]
#         elif isinstance(segment1, ArcGeo):
#             # if the direction is cw and resulting radius is still bigger 0
#             if segment1.r + offset > 0:
#                 Pa = segment1.Pa + segment1.start_normal * offset
#                 Pe = segment1.Pe + segment1.end_normal * offset
#                 r = segment1.r + offset
#                 offGeo = ArcGeo(Pa=Pa, Pe=Pe, O=segment1.O, r=r, direction=segment1.ext)
#                 self.interferingshapes += [offGeo]
#             # if the direction is cw and resulting radius is still bigger 0
# 
# 
#             # Resulting radius is smaller then 0
#             else:
#                 logger.error("Should not be here")
# 
# 
# 
#         elif isinstance(segment1, ConvexPoint):
#             # logger.debug("Should not be here")
#             return False
#         elif isinstance(segment1, Point):
#             Pa = segment1 + segment1.start_normal * offset
#             Pe = segment1 + segment1.end_normal * offset
#             O = segment1
#             r = offset
#             offGeo = ArcGeo(Pa=Pa, Pe=Pe, O=segment1, r=offset, direction=offset)
#             self.interferingshapes += [offGeo]
#         else:
#             logger.error("Unsupportet Object type: %s" % type(segment1))

        # offGeo=LineGeo(Pa,Pe)
        # logger.debug(segment2)
        # logger.debug(offGeo)
        # logger.debug("Partly distance: %s" %segment2.distance(offGeo))
        # If the distance from the Line to the Center of the Tangential Circle
        # is smaller then the radius we have an intersection
        return segment2.distance(offGeo) <= abs(offset)

    def Interfering_relation(self, segment1, segment2):
        """
        Check the interfering relation between two segements (segment1 and segment2).
        Definition acccording to Definition 6 
        @param segment1: The first segment (forward)
        @param segment2: The second segment (backward)
        @return: Returns one of [full, partial, reverse, None] interfering relations 
        for both segments
        """

        # logger.debug("\nChecking: segment1: %s, \nsegment2: %s" %(segment1,segment2))

        # Check if segments are equal
        if segment1 == segment2:
            return None, None

        if self.interfering_full(segment1, 1, segment2):
            self.interfering_partly(segment1, 1, segment2)
            L1_status = "full"
        elif self.interfering_partly(segment1, 1, segment2):
            L1_status = "partial"
        else:
            L1_status = "reverse"

        if self.interfering_full(segment2, -1, segment1):
            self.interfering_partly(segment2, -1, segment1)
            L2_status = "full"
        elif self.interfering_partly(segment2, -1, segment1):
            L2_status = "partial"
        else:
            L2_status = "reverse"

        return [L1_status, L2_status]

    def PairWiseInterferenceDetection(self, forward, backward,):
        """
        Returns the first forward and backward segment nr. for which both
        interfering conditions are partly.
        @param foward: The nr of the first forward segment
        @param backward: the nr. of the first backward segment
        @return: forward, backward
        """
        val = 1000
        self.counter = 0
        # self.counter=0
        L1_status, L2_status = "full", "full"
        # Repeat until we reached the Partial-interfering-relation
        while not(L1_status == "partial" and L2_status == "partial"):
            self.interferingshapes = []
            self.counter += 1

            segment1 = self.segments[forward]
            segment2 = self.segments[backward]

            if isinstance(segment1, ConvexPoint):
                forward += 1
                segment1 = self.segments[forward]
                # logger.debug("Forward ConvexPoint")
            if isinstance(segment2, ConvexPoint):
                backward -= 1
                segment2 = self.segments[backward]
                # logger.debug("Backward ConvexPoint")

            # logger.debug("Checking: forward: %s, backward: %s" %(forward, backward))
            [L1_status, L2_status] = self.Interfering_relation(segment1, segment2)
            # logger.debug("Start Status: L1_status: %s,L2_status: %s" %(L1_status,L2_status))

            """
            The reverse interfering segment is replaced  by the first 
            non-reverse-interfering segment along it's tracking direction
            """
            if L1_status == "reverse":
                while L1_status == "reverse":
                    self.counter += 1
                    # logger.debug(self.counter)
                    if self.counter > val:
                        break
                    if self.counter >= val:
                        self.interferingshapes = []
                    forward += 1
                    if forward >= len(self.segments):
                        forward = 0
                    segment1 = self.segments[forward]

                    if isinstance(segment1, ConvexPoint):
                        forward += 1
                        segment1 = self.segments[forward]
                        # logger.debug("Forward ConvexPoint")

                    # logger.debug("Reverse Replace Checking: forward: %s, backward: %s" %(forward, backward))

                    [L1_status, L2_status] = self.Interfering_relation(segment1, segment2)
                    # logger.debug("Checking: forward: %s, backward: %s" %(forward, backward))
                    # logger.debug("Replace Reverse: L1_status: %s,L2_status: %s" %(L1_status,L2_status))

            elif L2_status == "reverse":
                while L2_status == "reverse":
                    self.counter += 1
                    # logger.debug(self.counter)
                    if self.counter > val:
                        break
                    if self.counter >= val:
                        self.interferingshapes = []
                    backward -= 1
                    # logger.debug("Reveerse Replace Checking: forward: %s, backward: %s" %(forward, backward))
                    segment2 = self.segments[backward]

                    if isinstance(segment2, ConvexPoint):
                        backward -= 1
                        segment2 = self.segments[backward]
                        # logger.debug("Backward ConvexPoint")


                    [L1_status, L2_status] = self.Interfering_relation(segment1, segment2)
                    # logger.debug("Checking: forward: %s, backward: %s" %(forward, backward))
                    # logger.debug("Replace Reverse: L1_status: %s,L2_status: %s" %(L1_status,L2_status))


            """
            Full interfering segment is replaced by the nexst segemnt along the
            tracking direction.
            """
            if L1_status == "full" and (L2_status == "partial" or L2_status == "full"):
                forward += 1
            elif L2_status == "full" and (L1_status == "partial" or L1_status == "partial"):
                backward -= 1

            # If The begin end point is the end end point we are done.
            if L1_status is None and L2_status is None:
                # logger.debug("Begin = End; Remove all")
                return len(self.segments) - 1, 0

            # logger.debug(self.counter)
            # logger.debug("L1_status: %s,L2_status: %s" %(L1_status,L2_status))
            if self.counter == val:
                self.interferingshapes = []

            if self.counter > val:  # 26:
                logger.error("No partial - partial status found")
                return None, None

        # logger.debug("Result: forward: %s, backward: %s" %(forward, backward))
        return forward, backward

    def remove_LIR(self, forward, backward, iPoint):
        """
        The instance is used to remove the LIR from the PS curve.
        @param forward: The forward segment of the LIR
        @param backward: The backward segement of the LIR
        @param iPoint: The Intersection point of the LIR
        """

        pop_range = self.segments[backward + 1:forward]
        if self.offtype == "out":
            rev = True
        else:
            rev = False
        # Modify the first segment and the last segment of the LIR
        self.segments[forward] = self.segments[forward].trim(Point=iPoint, dir=1, rev_norm=rev)
        self.segments[backward] = self.segments[backward].trim(Point=iPoint, dir=-1, rev_norm=rev)

        # Remove the segments which are inbetween the LIR
        self.segments = [x for x in self.segments if x not in pop_range]

class SweepLine:
    def __init__(self, geos=[], closed=True):
        """
        This the init function of the SweepLine Class. It is calling a sweep line
        algorithm in order to find all intersection of the given geometries
        @param geos: A list if with geometries in their ordered structure.
        @param closed: If the geometries are closed or not (Polyline or Polygon)
        """

        self.geos = []
        self.closed = closed

        self.sweep_array = []
        self.intersections = []

        self.add_to_sweep_array(geos, self.closed)

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """
        sweep_array_order = []
        for element in self.sweep_array:
            add_array = []
            rem_array = []
            swoop_array = []

            for add_ele in element.add:
                add_array.append(add_ele.nr)
            for rem_ele in element.remove:
                rem_array.append(rem_ele.nr)
            for swoop_ele in element.swoop:
                swoop_array.append(swoop_ele)



            sweep_array_order += [[element.Point.x, element.Point.y], add_array, rem_array, swoop_array]

        return ('\nlen(geos):   %i' % len(self.geos)) + \
               ('\nclosed:      %i' % self.closed) + \
               ('\ngeos:        %s' % self.geos) + \
               ('\nsweep_array_order:  %s' % sweep_array_order)

    def add_to_sweep_array(self, geos=[], closed=True):
        """
        This instance adds the given geometries to the sweep array. If there 
        are already some defined it will just continue to add them. This may be 
        used to get the intersection of two shapes
        @param: the geometries to be added
        @param: if these geometries are closed shape or not
        """

        sweep_array = []
        self.geos += geos

        for geo_nr in range(len(geos)):
            geo = geos[geo_nr]
            y_val = (geo.BB.Pa.y + geo.BB.Pe.y) / 2

            geo.neighbors = []
            geo.nr = geo_nr
            geo.Point = Point(x=geo.BB.Pa.x, y=y_val)

            # Add the neighbors before the geometrie
            if geo_nr == 0 and closed:
                geo.neighbors.append(geos[geo_nr - 1])
            else:
                geo.neighbors.append(geos[geo_nr - 1])

            # Add the neighbors after the geometrie
            if geo_nr == len(geos) - 1 and closed:
                geo.neighbors.append(geos[0])
            else:
                geo.neighbors.append(geos[geo_nr + 1])

            y_val = (geo.BB.Pa.y + geo.BB.Pe.y) / 2
            sweep_array.append(SweepElement(Point=geo.Point, add=[geo], remove=[]))
            sweep_array.append(SweepElement(Point=Point(x=geo.BB.Pe.x, y=y_val), add=[], remove=[geo]))


        # logger.debug(sweep_array)
        sweep_array.sort(self.cmp_SweepElement)

        # Remove all Points which are there twice
        self.sweep_array = [sweep_array[0]]
        for ele_nr in range(1, len(sweep_array)):
            if abs(self.sweep_array[-1].Point.x - sweep_array[ele_nr].Point.x) < eps:
                self.sweep_array[-1].add += sweep_array[ele_nr].add
                self.sweep_array[-1].remove += sweep_array[ele_nr].remove
            else:
                self.sweep_array.append(sweep_array[ele_nr])

    def cmp_SweepElement(self, ele1, ele2):
        """
        Compare Function for the sorting of the sweep array.
        @param Point1: First SweepElement point for compare
        @param Point2: The second SweepElement point for the compare
        @return: True or false whichever is bigger.
        """
        if ele1.Point.x < ele2.Point.x:
            return -1
        elif ele1.Point.x > ele2.Point.x:
            return 1
        else:
            return 0

    def cmp_SweepElementy(self, ele1, ele2):
        """
        Compare Function for the sorting of the sweep array just in y direction.
        @param ele1: First SweepElement point for compare
        @param ele2: The second SweepElement point for the compare
        @return: True or false whichever is bigger.
        """
        # logger.debug(ele1)
        # logger.debug(ele2)

        if ele1.Point.y < ele2.Point.y:
            return -1
        elif ele1.Point.y > ele2.Point.y:
            return 1
        else:
            return 0

    def search_intersections(self):
        """
        This instance is called to search all intersection points between the 
        Elements defined in geos
        """
        search_array = []
        self.found = []
        ele_nr = 0

        while ele_nr < len(self.sweep_array):
            ele = self.sweep_array[ele_nr]
            # logger.debug(ele)
            ele_nr += 1

            for geo in ele.add:
                search_array.append(geo)
                search_array.sort(self.cmp_SweepElementy)
                index = search_array.index(geo)
                # logger.debug("add_index: %s" %index)
                # logger.debug(index)
                # logger.debug(geo)
                if len(search_array) >= 2:
                    if index > 0:
                        self.search_geo_intersection(geo, search_array[index - 1])


                    if index < (len(search_array) - 1):
                        self.search_geo_intersection(geo, search_array[index + 1])

            for geo in ele.swoop:
                # The y values of the elements are exchanged and the upper and
                # lower neighbors are checked for intersections
                # logger.debug(geo[0].Point)
                # logger.debug(geo[1].Point)
                # logger.debug(search_array)


                y0 = geo[0].Point.y
                y1 = geo[1].Point.y

                geo[1].Point.y = y0
                geo[0].Point.y = y1

                # logger.debug(geo[0].Point)
                # logger.debug(geo[1].Point)
                # logger.debug(search_array)

                index0 = search_array.index(geo[0])
                index1 = search_array.index(geo[1])
                # logger.debug("Pre sort index: %s, %s" %(index0,index1))

                search_array.sort(self.cmp_SweepElementy)

                index0 = search_array.index(geo[0])
                index1 = search_array.index(geo[1])
                # logger.debug("Post sort index: %s, %s" %(index0,index1))

                min_ind = min(index0, index1)
                max_ind = max(index0, index1)
                if min_ind > 0:
                    self.search_geo_intersection(search_array[min_ind], search_array[min_ind - 1])


                if max_ind < (len(search_array) - 1):
                    self.search_geo_intersection(search_array[max_ind], search_array[max_ind + 1])


            for geo in ele.remove:
                index = search_array.index(geo)
                # logger.debug("remove_index: %s" %index)

                search_array.pop(index)
                if len(search_array) >= 2:
                    if index > 0 and index <= (len(search_array) - 1):
                        self.search_geo_intersection(search_array[index - 1], search_array[index])


        logger.debug(self.found)

    def search_geo_intersection(self, geo1, geo2):
        """
        This function is called so search the intersections and to add the 
        intersection point to the sweep array. This is called during each search
        
        """
        # logger.debug(search_array[index+1])
        # logger.debug("geo1: %s\ngeo2: %s" %(geo1,geo2))
        iPoint = (geo1.find_inter_point(geo2))
        if (not(iPoint is None) and
            not(geo2 in geo1.neighbors)):
            # if there is only one instersection
            if isinstance(iPoint, Point):
                self.found.append(iPoint)
                self.sweep_array.append(SweepElement(Point=iPoint, add=[], remove=[], swoop=[[geo1, geo2]]))
            else:
                self.found += iPoint
                self.sweep_array.append(SweepElement(Point=iPoint[0], add=[], remove=[], swoop=[[geo1, geo2]]))
                self.sweep_array.append(SweepElement(Point=iPoint[1], add=[], remove=[], swoop=[[geo1, geo2]]))

            self.sweep_array.sort(self.cmp_SweepElement)
            # logger.debug(self)
class SweepElement:
    def __init__(self, Point=Point(0, 0), add=[], remove=[], swoop=[]):
        """
        This is the class for each SweepElement given in the sweep_array
        @param Point: the Point of the SweepElement (e.g. 2 Points per LineGeo)
        @param add: The geometrie to be added
        @param remove: The geometrie to be removed

        """
        self.Point = Point
        self.add = add
        self.remove = remove
        self.swoop = swoop

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """
        return ('\nPoint:     %s ' % (self.Point)) + \
               ('\nadd:       %s ' % self.add) + \
               ('\nremove:    %s ' % self.remove)

class PlotClass:
    """
    Class which calls matplotlib to plot the results.
    """
    def __init__(self, master=[]):

        self.master = master

        # Erstellen des Fensters mit Rahmen und Canvas
        self.figure = Figure(figsize=(7, 7), dpi=100)
        self.frame_c = Frame(relief=GROOVE, bd=2)
        self.frame_c.pack(fill=BOTH, expand=1,)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame_c)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=1)

        # Erstellen der Toolbar unten
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.frame_c)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(fill=BOTH, expand=1)

    def plot_lines_plot(self, lines, sb_nr=111, text="", wtp=[True, True, True]):
        self.plot1 = self.figure.add_subplot(sb_nr)
        self.plot1.set_title("Lines Plot %s" % sb_nr)
        self.plot1.grid(b=True, which='both', color='0.65', linestyle='-')
        self.plot1.hold(True)
        self.plot1.text(0.5, 0, text, ha='left', fontsize=8)

        for line_nr in range(len(lines)):

            line = lines[line_nr]
            if wtp[0]:
                line.plot2plot(self.plot1)
            if wtp[1]:
                line.Pa.plot2plot(self.plot1, format='xr')
                line.Pe.plot2plot(self.plot1, format='og')
            Pa = (line.Pa + line.Pe) * 0.5
            if wtp[2]:
                self.plot1.text(Pa.x, Pa.y, line_nr, ha='left', fontsize=10, color='red')

        self.plot1.axis('scaled')
        self.plot1.margins(y=.1, x=.1)
        self.plot1.autoscale(True, 'both', False)
        self.canvas.show()

    def plot_segments(self, segments, sb_nr=111, text="", format=('-m', 'xr', 'og'), fcol='red', wtp=[True, True, True]):
        self.plot1 = self.figure.add_subplot(sb_nr)
        self.plot1.set_title("Segments Plot %s" % sb_nr)
        self.plot1.grid(b=True, which='both', color='0.65', linestyle='-')
        self.plot1.hold(True)
        self.plot1.text(0.5, 0, text, ha='left', fontsize=8)

        for segment_nr in range(len(segments)):
            seg = segments[segment_nr]
            if isinstance(seg, LineGeo):
                if wtp[0]:
                    seg.plot2plot(self.plot1, format[0])

                Pa = (seg.Pa + seg.Pe) * 0.5
                if wtp[1]:
                    seg.Pa.plot2plot(self.plot1, format=format[1])
                    seg.Pe.plot2plot(self.plot1, format=format[1])
            elif isinstance(seg, ArcGeo):
                if wtp[0]:
                    seg.plot2plot(self.plot1, format=format[0])

                Pa = (seg.Pa + seg.Pe) * 0.5

                if wtp[1]:
                    seg.Pa.plot2plot(self.plot1, format=format[1])
                    seg.Pe.plot2plot(self.plot1, format=format[1])

            elif isinstance(seg, Point):
                # seg.plot2plot(self.plot1,format=format[0])
                if wtp[0]:
                    seg.plot2plot(self.plot1, format=format[2])
                Pa = seg

            if wtp[2]:
                self.plot1.text(Pa.x + 0.1, Pa.y + 0.1, segment_nr, ha='left', fontsize=10, color=fcol)
            self.plot1.axis('scaled')


        self.plot1.margins(y=.1, x=.1)
        self.plot1.autoscale(True, 'both', False)
        self.canvas.show()

class ExampleClass:
    def __init__(self):
        pass
    def CheckColinearLines(self):
        master.title("Check for Colinear Lines and Join")

        L1 = LineGeo(Point(x=0, y=0), Point(x=2, y=2))
        L2 = LineGeo(Point(x=2, y=2), Point(x=4, y=4))
        L3 = LineGeo(Point(x=1.5, y=1.5), Point(x=4, y=4))
        L4 = LineGeo(Point(x=2.5, y=2.5), Point(x=4, y=4))
        L5 = LineGeo(Point(x=1.5, y=1.5), Point(x=3, y=0))

        lines1 = L1.join_colinear_line(L2)
        lines2 = L1.join_colinear_line(L3)
        lines3 = L1.join_colinear_line(L4)
        lines4 = L1.join_colinear_line(L5)

        text1 = ("\nCheck for Intersection L1; L2: %s \n" % L1.intersect(L2))
        text1 += ("Check for Colinear L1; L2: %s \n" % L1.colinear(L2))
        text1 += ("Check for colinearoverlapping L1; L2: %s \n" % L1.colinearoverlapping(L2))
        text1 += ("Check for colinearconnected L1; L2: %s \n" % L1.colinearconnected(L2))
        logger.debug(text1)

        text2 = ("\nCheck for Intersection L1; L3: %s \n" % L1.intersect(L3))
        text2 += ("Check for Colinear L1; L3: %s \n" % L1.colinear(L3))
        text2 += ("Check for colinearoverlapping L1; L3: %s \n" % L1.colinearoverlapping(L3))
        text2 += ("Check for colinearconnected L1; L3: %s \n" % L1.colinearconnected(L3))
        logger.debug(text2)


        text3 = ("\nCheck for Intersection L1; L4: %s \n" % L1.intersect(L4))
        text3 += ("Check for Colinear L1; L4: %s \n" % L1.colinear(L4))
        text3 += ("Check for colinearoverlapping L1; L4: %s \n" % L1.colinearoverlapping(L4))
        text3 += ("Check for colinearconnected L1; L4: %s \n" % L1.colinearconnected(L4))
        logger.debug(text3)

        text4 = ("\nCheck for Intersection L1; L5: %s \n" % L1.intersect(L5))
        text4 += ("Check for Colinear L1; L5: %s \n" % L1.colinear(L5))
        text4 += ("Check for colinearoverlapping L1; L5: %s \n" % L1.colinearoverlapping(L5))
        text4 += ("Check for colinearconnected L1; L5: %s \n" % L1.colinearconnected(L5))
        logger.debug(text4)


        Pl.plot_lines_plot(lines1, 221, text1)
        Pl.plot_lines_plot(lines2, 222, text2)
        Pl.plot_lines_plot(lines3, 223, text3)
        Pl.plot_lines_plot(lines4, 224, text4)

    def CheckForIntersections(self):
        master.title("Check for Intersections and split Lines")

        L1 = LineGeo(Point(x=0, y=0), Point(x=2, y=2))
        L2 = LineGeo(Point(x=0, y=2), Point(x=2, y=0))
        L3 = LineGeo(Point(x=1, y=3), Point(x=3, y=1))
        L4 = LineGeo(Point(x=2, y=5), Point(x=4, y=2))
        L5 = LineGeo(Point(x=2, y=2), Point(x=3, y=0))

        IP1 = L1.find_inter_point(L2)
        IP2 = L1.find_inter_point(L3)
        IP3 = L1.find_inter_point(L4)
        IP4 = L1.find_inter_point(L5)
        
        Arc1 = ArcGeo(Pa=Point(x=-10 , y=29),
               Pe=Point(x=10, y=29),
               O=Point(x=0, y=29),
               s_ang=3.14159265359, e_ang=0.0,
               r=10,
               direction=-3.14159265359)
        
        IP5 = Point(-14.142, 34.000)
        
        # [Arc1, Arc2] = Arc1.split_into_2geos(IP5)
        Arc3 = Arc1.trim(IP5, 1, True)
         
        lines4 = [] + [Arc3]  # , 1, True
    

        lines1 = [] + L1.split_into_2geos(IP1) + L2.split_into_2geos(IP1)
        lines2 = [] + L1.split_into_2geos(IP2) + L3.split_into_2geos(IP2)
        lines3 = [] + L1.split_into_2geos(IP3) + L4.split_into_2geos(IP3)
        # lines4 = [] + L1.split_into_2geos(IP4) + L5.split_into_2geos(IP4)

        text1 = ("\nCheck for Intersection L1; L2: %s \n" % L1.intersect(L2))
        text1 += ("Lies on segment L1: %s L2: %s \n" % (L1.intersect(IP1), L2.intersect(IP1)))
        text1 += ("Intersection at Point: %s \n" % L1.find_inter_point(L2))
        logger.debug(text1)

        text2 = ("Check for Intersection L1; L3: %s \n" % L1.intersect(L3))
        text2 += ("Lies on segment L1: %s L3: %s \n" % (L1.intersect(IP2), L3.intersect(IP2)))
        text2 += ("Intersection at Point: %s \n" % L1.find_inter_point(L3))
        logger.debug(text2)

        text3 = ("Check for Intersection L1; L4: %s \n" % L1.intersect(L4))
        
        logger.debug(L1)
        logger.debug(L4)
        logger.debug(IP3)
        # text3 += ("Lies on segment L1: %s L4: %s \n" % (L1.intersect(IP3), L4.intersect(IP3)))
        # text3 += ("Intersection at Point: %s \n" % L1.find_inter_point(L4))
        # logger.debug(text3)

#         text4 = ("Check for Intersection L1; L5: %s \n" % L1.intersect(L5))
#         text4 += ("Lies on segment L1: %s L5: %s \n" % (L1.intersect(IP4), L5.intersect(IP4)))
#         text4 += ("Intersection at Point: %s \n" % L1.find_inter_point(L5))
#         logger.debug(text4)

        Pl.plot_lines_plot(lines1, 221, text1)
        Pl.plot_lines_plot(lines2, 222, text2)
        Pl.plot_lines_plot(lines3, 223, text3)
        Pl.plot_lines_plot(lines4, 224)

    def SimplePolygonCheck(self):
        master.title("Simple Polygon Check")

        L0 = LineGeo(Point(x=0, y=-1), Point(x=0, y=0))
        L1 = LineGeo(Point(x=0, y=0), Point(x=2, y=2))
        L2 = LineGeo(Point(x=2, y=2), Point(x=3, y=3))
        L3 = LineGeo(Point(x=3, y=3), Point(x=3, y=-6))
        L4 = LineGeo(Point(x=3, y=-6), Point(x=0, y=-5))
        L5 = LineGeo(Point(x=0, y=-5), Point(x=0, y=-4))
        L6 = LineGeo(Point(x=0, y=-4), Point(x=0, y=-1))
        shape = ShapeClass(geos=[L0, L1, L2, L3, L4, L5, L6], closed=True)

        L0 = LineGeo(Point(x=0, y=-1), Point(x=0, y=0))
        L1 = LineGeo(Point(x=0, y=0), Point(x=2, y=2))
        L2 = LineGeo(Point(x=2, y=2), Point(x=3, y=3))
        L3 = LineGeo(Point(x=3, y=3), Point(x=3, y=-6))
        L4 = LineGeo(Point(x=3, y=-6), Point(x=0, y=-5))
        L5 = LineGeo(Point(x=0, y=-5), Point(x=0, y=-4))
        shape2 = ShapeClass(geos=[L0, L1, L2, L3, L4, L5], closed=False)

        Pl.plot_lines_plot(shape.geos, 221)

        shape.make_shape_ccw()
        Pl.plot_lines_plot(shape.geos, 222)

        shape.join_colinear_lines()
        Pl.plot_lines_plot(shape.geos, 223)

        shape2.join_colinear_lines()
        Pl.plot_lines_plot(shape2.geos, 224)

    def Distance_Check(self):

        L1 = LineGeo(Point(x=1, y=0), Point(x=2, y=2))
        L3 = LineGeo(Point(x=3, y=3), Point(x=4, y=0))
        L7 = LineGeo(Point(x=0, y=-2), Point(x=0, y=-1))
        Lt = LineGeo(Point(x=3, y=0), Point(x=2, y=1))
        Lc = LineGeo(Point(x=2, y=0), Point(x=3, y=2))
        Li = LineGeo(Point(x=1, y=0.5), Point(x=1.5, y=0))

        Arct = ArcGeo(Pa=Point(-11.680, 14.364), s_ang=1.11502, Pe=Point(-12.120, 14.466), e_ang=1.57080, O=Point(-12.120, 13.466), r=1.000)
        Linet = LineGeo(Point(-11.409, 14.364), Point(-11.497, 14.364))
        Arct.find_inter_point(Linet)




        PointN1 = L1.get_nearest_point(L3)
        PointN2 = L3.get_nearest_point(L1)
        NL = LineGeo(PointN1, PointN2)

        PointN3 = L1.get_nearest_point(L7)
        PointN4 = L7.get_nearest_point(L1)
        NL1 = LineGeo(PointN3, PointN4)

        PointN5 = L1.get_nearest_point(Lt)
        PointN6 = Lt.get_nearest_point(L1)
        NL2 = LineGeo(PointN5, PointN6)

        PointN7 = L1.get_nearest_point(Lc)
        PointN8 = Lc.get_nearest_point(L1)
        NL3 = LineGeo(PointN7, PointN8)

        PointN9 = L1.get_nearest_point(Li)
        PointN10 = Li.get_nearest_point(L1)

        NL4 = LineGeo(PointN9, PointN10)

        SD1 = L1.distance(L3)
        SD2 = L1.distance(L7)
        SD3 = L1.distance(Lt)
        SD4 = L1.distance(Lc)
        SD5 = L1.distance(Li)


        segments = [L1, L3, L7, Lt, Lc, Li]
        Pl.plot_segments(segments, 131, text=("SD1: %0.2f, SD2: %0.2f, SD3: %0.2f, SD4: %0.2f, SD5: %0.2f") % (SD1, SD2, SD3, SD4, SD5))
        seg_con = [NL, NL1, NL2, NL3, NL4]
        Pl.plot_segments(seg_con, 131, format=('b', '.b', 'ob'), fcol='blue')

        Arc0 = ArcGeo(Pa=Point(x=1, y=0), Pe=Point(x=0, y=1), O=Point(x=0, y=0), r=1)
        Lin = LineGeo(Point(-1, 1), Point(0.7, 0.7))
        Lin2 = LineGeo(Point(x=-1, y=0.3), Point(x=-2, y=2))
        Lout = LineGeo(Point(3, 2), Point(2, -2))

        PointN1 = L1.get_nearest_point(Arc0)
        PointN2 = Arc0.get_nearest_point(L1)

        PointN3 = Lin.get_nearest_point(Arc0)
        PointN4 = Arc0.get_nearest_point(Lin)

        PointN5 = Lout.get_nearest_point(Arc0)
        PointN6 = Arc0.get_nearest_point(Lout)

        PointN7 = Lin2.get_nearest_point(Arc0)
        PointN8 = Arc0.get_nearest_point(Lin2)

        PointN9 = Linet.get_nearest_point(Arct)
        PointN10 = Arct.get_nearest_point(Linet)

        NL1 = LineGeo(PointN1, PointN2)
        NL2 = LineGeo(PointN3, PointN4)
        NL3 = LineGeo(PointN5, PointN6)
        NL4 = LineGeo(PointN7, PointN8)
        NL5 = LineGeo(PointN9, PointN10)

        SD1 = L1.distance(Arc0)
        SD2 = Lin.distance(Arc0)
        SD3 = Lout.distance(Arc0)
        SD4 = Lin2.distance(Arc0)
        SD5 = Linet.distance(Arct)

        segments = [Arc0, L1, Lin, Lout, Lin2, Linet, Arct]
        seg_con = [NL1, NL2, NL3, NL4]

        Pl.plot_segments(segments, 132, text=("SD1: %0.2f, SD2: %0.2f, SD3: %0.2f, SD4: %0.2f, SD5: %s") % (SD1, SD2, SD3, SD4, SD5))

        Pl.plot_segments(seg_con, 132, format=('b', '.b', 'ob'), fcol='blue')

        Ltest = LineGeo(Pa=Point(x=-12.222 , y=13.466), Pe=Point(x=-12.222, y=15.144))
        Atest = ArcGeo(Pa=Point(x=-10.509 , y=13.364),
                        Pe=Point(x=-11.409, y=14.264),
                        O=Point(x=-11.409, y=13.364),
                        s_ang=0.0, e_ang=1.57079632679,
                        r=0.9,
                        direction=1.57079632679)


        Pt1 = Arct.get_nearest_point(Atest)
        Pt2 = Atest.get_nearest_point(Arct)

        NLt = LineGeo(Pt1, Pt2)

        SDt = Arct.distance(Atest)
        logger.debug(SDt)


        segments = [Atest, Arct]
        seg_con = [NLt]

        Pl.plot_segments(segments, 133, text=("SDt: %0.2f") % (SDt))
        Pl.plot_segments(seg_con, 133, format=('b', '.b', 'ob'), fcol='blue')


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

#        shape=ShapeClass(geos=[ LineGeo(Point(-4.522,1.066),Point(-8.486,-6.2)),
#                                LineGeo(Point(-8.486,-6.2),Point(-11.307,-1.828)),
#                                LineGeo(Point(-11.307,-1.828),Point(-12.45,-4.014)),
#                                LineGeo(Point(-12.45,-4.014),Point(-12.984,-2.794)),
#                                LineGeo(Point(-12.984,-2.794),Point(-11.409,0.354)),
#                                LineGeo(Point(-11.409,0.354),Point(-11.409,13.364)),
#                                LineGeo(Point(-11.409,13.364),Point(-11.51,13.364)),
#                                LineGeo(Point(-11.51,13.364),Point(-11.612,13.364)),
#                                LineGeo(Point(-11.612,13.364),Point(-11.714,13.364)),
#                                LineGeo(Point(-11.714,13.364),Point(-11.815,13.416)),
#                                LineGeo(Point(-11.815,13.416),Point(-11.917,13.416)),
#                                LineGeo(Point(-11.917,13.416),Point(-12.018,13.416)),
#                                LineGeo(Point(-12.018,13.416),Point(-12.12,13.466)),
#                                LineGeo(Point(-12.12,13.466),Point(-12.222,13.466)),
#                                LineGeo(Point(-12.222,13.466),Point(-12.222,15.144)),
#                                LineGeo(Point(-12.222,15.144),Point(-12.044,15.144)),
#                                LineGeo(Point(-12.044,15.144),Point(-11.891,15.092)),
#                                LineGeo(Point(-11.891,15.092),Point(-11.714,15.092)),
#                                LineGeo(Point(-11.714,15.092),Point(-11.586,15.042)),
#                                LineGeo(Point(-11.586,15.042),Point(-11.459,15.042)),
#                                LineGeo(Point(-11.459,15.042),Point(-11.332,14.99)),
#                                LineGeo(Point(-11.332,14.99),Point(-11.231,14.99)),
#                                LineGeo(Point(-11.231,14.99),Point(-11.154,14.99)),
#                                LineGeo(Point(-11.154,14.99),Point(-10.672,14.99)),
#                                LineGeo(Point(-10.672,14.99),Point(-10.189,15.092)),
#                                LineGeo(Point(-10.189,15.092),Point(-9.706,15.194)),
#                                LineGeo(Point(-9.706,15.194),Point(-9.249,15.296)),
#                                LineGeo(Point(-9.249,15.296),Point(-8.817,15.5)),
#                                LineGeo(Point(-8.817,15.5),Point(-8.385,15.702)),
#                                LineGeo(Point(-8.385,15.702),Point(-7.953,15.956)),
#                                LineGeo(Point(-7.953,15.956),Point(-7.546,16.262)),
#                                LineGeo(Point(-7.546,16.262),Point(-7.165,16.618)),
#                                LineGeo(Point(-7.165,16.618),Point(-6.784,16.972)),
#                                LineGeo(Point(-6.784,16.972),Point(-6.428,17.38)),
#                                LineGeo(Point(-6.428,17.38),Point(-6.072,17.836)),
#                                LineGeo(Point(-6.072,17.836),Point(-5.742,18.346)),
#                                LineGeo(Point(-5.742,18.346),Point(-5.412,18.854)),
#                                LineGeo(Point(-5.412,18.854),Point(-5.107,19.412)),
#                                LineGeo(Point(-5.107,19.412),Point(-4.522,1.066))],closed=True)

#        shape=ShapeClass(geos=[LineGeo(Point(-16.084,7.926),Point(-16.973,8.028)),
#                                LineGeo(Point(-16.973,8.028),Point(-17.914,8.282)),
#                                LineGeo(Point(-17.914,8.282),Point(-18.854,8.638)),
#                                LineGeo(Point(-18.854,8.638),Point(-19.794,9.096)),
#                                LineGeo(Point(-19.794,9.096),Point(-20.785,9.706)),
#                                LineGeo(Point(-20.785,9.706),Point(-21.75,10.366)),
#                                LineGeo(Point(-21.75,10.366),Point(-22.741,11.18)),
#                                LineGeo(Point(-22.741,11.18),Point(-23.732,12.044)),
#                                LineGeo(Point(-23.732,12.044),Point(-24.723,13.06)),
#                                LineGeo(Point(-24.723,13.06),Point(-25.714,14.126)),
#                                LineGeo(Point(-25.714,14.126),Point(-26.705,15.296)),
#                                LineGeo(Point(-26.705,15.296),Point(-27.696,16.566)),
#                                LineGeo(Point(-27.696,16.566),Point(-28.662,17.938)),
#                                LineGeo(Point(-28.662,17.938),Point(-29.628,19.362)),
#                                LineGeo(Point(-29.628,19.362),Point(-30.568,20.886)),
#                                LineGeo(Point(-30.568,20.886),Point(-31.482,22.512)),
#                                LineGeo(Point(-31.482,22.512),Point(-32.372,24.19)),
#                                LineGeo(Point(-32.372,24.19),Point(-33.261,25.918)),
#                                LineGeo(Point(-33.261,25.918),Point(-34.1,27.746)),
#                                LineGeo(Point(-34.1,27.746),Point(-34.913,29.628)),
#                                LineGeo(Point(-34.913,29.628),Point(-35.675,31.61)),
#                                LineGeo(Point(-35.675,31.61),Point(-36.437,33.592)),
#                                LineGeo(Point(-36.437,33.592),Point(-37.124,35.674)),
#                                LineGeo(Point(-37.124,35.674),Point(-37.784,37.81)),
#                                LineGeo(Point(-37.784,37.81),Point(-38.394,39.994)),
#                                LineGeo(Point(-38.394,39.994),Point(-38.953,42.23)),
#                                LineGeo(Point(-38.953,42.23),Point(-39.461,44.518)),
#                                LineGeo(Point(-39.461,44.518),Point(-39.893,46.856)),
#                                LineGeo(Point(-39.893,46.856),Point(-40.3,49.244)),
#                                LineGeo(Point(-40.3,49.244),Point(-40.63,51.682)),
#                                LineGeo(Point(-40.63,51.682),Point(-40.884,54.122)),
#                                LineGeo(Point(-40.884,54.122),Point(-41.087,56.612)),
#                                LineGeo(Point(-41.087,56.612),Point(-41.087,56.866)),
#                                LineGeo(Point(-41.087,56.866),Point(-41.138,57.172)),
#                                LineGeo(Point(-41.138,57.172),Point(-41.215,57.528)),
#                                LineGeo(Point(-41.215,57.528),Point(-41.316,57.882)),
#                                LineGeo(Point(-41.316,57.882),Point(-41.469,58.238)),
#                                LineGeo(Point(-41.469,58.238),Point(-41.646,58.492)),
#                                LineGeo(Point(-41.646,58.492),Point(-41.875,58.696)),
#                                LineGeo(Point(-41.875,58.696),Point(-42.155,58.746)),
#                                LineGeo(Point(-42.155,58.746),Point(-82.785,58.746)),
#                                LineGeo(Point(-82.785,58.746),Point(-93.102,76.484)),
#                                LineGeo(Point(-93.102,76.484),Point(-92.975,76.484)),
#                                LineGeo(Point(-92.975,76.484),Point(-92.594,76.484)),
#                                LineGeo(Point(-92.594,76.484),Point(-91.958,76.484)),
#                                LineGeo(Point(-91.958,76.484),Point(-91.12,76.484)),
#                                LineGeo(Point(-91.12,76.484),Point(-90.053,76.484)),
#                                LineGeo(Point(-90.053,76.484),Point(-88.782,76.484)),
#                                LineGeo(Point(-88.782,76.484),Point(-87.334,76.484)),
#                                LineGeo(Point(-87.334,76.484),Point(-85.733,76.484)),
#                                LineGeo(Point(-85.733,76.484),Point(-83.954,76.484)),
#                                LineGeo(Point(-83.954,76.484),Point(-82.023,76.484)),
#                                LineGeo(Point(-82.023,76.484),Point(-79.99,76.484)),
#                                LineGeo(Point(-79.99,76.484),Point(-77.805,76.484)),
#                                LineGeo(Point(-77.805,76.484),Point(-75.543,76.484)),
#                                LineGeo(Point(-75.543,76.484),Point(-73.18,76.484)),
#                                LineGeo(Point(-73.18,76.484),Point(-70.741,76.484)),
#                                LineGeo(Point(-70.741,76.484),Point(-68.251,76.484)),
#                                LineGeo(Point(-68.251,76.484),Point(-65.71,76.484)),
#                                LineGeo(Point(-65.71,76.484),Point(-63.118,76.484)),
#                                LineGeo(Point(-63.118,76.484),Point(-60.526,76.484)),
#                                LineGeo(Point(-60.526,76.484),Point(-57.909,76.484)),
#                                LineGeo(Point(-57.909,76.484),Point(-55.292,76.484)),
#                                LineGeo(Point(-55.292,76.484),Point(-52.7,76.484)),
#                                LineGeo(Point(-52.7,76.484),Point(-50.159,76.484)),
#                                LineGeo(Point(-50.159,76.484),Point(-47.643,76.484)),
#                                LineGeo(Point(-47.643,76.484),Point(-45.204,76.484)),
#                                LineGeo(Point(-45.204,76.484),Point(-42.841,76.484)),
#                                LineGeo(Point(-42.841,76.484),Point(-40.554,76.484)),
#                                LineGeo(Point(-40.554,76.484),Point(-38.369,76.484)),
#                                LineGeo(Point(-38.369,76.484),Point(-36.285,76.484)),
#                                LineGeo(Point(-36.285,76.484),Point(-34.354,76.484)),
#                                LineGeo(Point(-34.354,76.484),Point(-32.55,76.484)),
#                                LineGeo(Point(-32.55,76.484),Point(-30.898,76.484)),
#                                LineGeo(Point(-30.898,76.484),Point(-31.152,73.942)),
#                                LineGeo(Point(-31.152,73.942),Point(-31.33,71.452)),
#                                LineGeo(Point(-31.33,71.452),Point(-31.457,69.012)),
#                                LineGeo(Point(-31.457,69.012),Point(-31.508,66.624)),
#                                LineGeo(Point(-31.508,66.624),Point(-31.533,64.338)),
#                                LineGeo(Point(-31.533,64.338),Point(-31.482,62.102)),
#                                LineGeo(Point(-31.482,62.102),Point(-31.381,59.916)),
#                                LineGeo(Point(-31.381,59.916),Point(-31.228,57.782)),
#                                LineGeo(Point(-31.228,57.782),Point(-31.025,55.748)),
#                                LineGeo(Point(-31.025,55.748),Point(-30.746,53.766)),
#                                LineGeo(Point(-30.746,53.766),Point(-30.441,51.836)),
#                                LineGeo(Point(-30.441,51.836),Point(-30.085,49.956)),
#                                LineGeo(Point(-30.085,49.956),Point(-29.653,48.176)),
#                                LineGeo(Point(-29.653,48.176),Point(-29.196,46.5)),
#                                LineGeo(Point(-29.196,46.5),Point(-28.687,44.822)),
#                                LineGeo(Point(-28.687,44.822),Point(-28.128,43.246)),
#                                LineGeo(Point(-28.128,43.246),Point(-27.519,41.774)),
#                                LineGeo(Point(-27.519,41.774),Point(-26.858,40.35)),
#                                LineGeo(Point(-26.858,40.35),Point(-26.172,38.978)),
#                                LineGeo(Point(-26.172,38.978),Point(-25.435,37.708)),
#                                LineGeo(Point(-25.435,37.708),Point(-24.647,36.488)),
#                                LineGeo(Point(-24.647,36.488),Point(-23.809,35.37)),
#                                LineGeo(Point(-23.809,35.37),Point(-22.945,34.302)),
#                                LineGeo(Point(-22.945,34.302),Point(-22.03,33.286)),
#                                LineGeo(Point(-22.03,33.286),Point(-21.09,32.422)),
#                                LineGeo(Point(-21.09,32.422),Point(-20.099,31.558)),
#                                LineGeo(Point(-20.099,31.558),Point(-19.082,30.846)),
#                                LineGeo(Point(-19.082,30.846),Point(-18.015,30.186)),
#                                LineGeo(Point(-18.015,30.186),Point(-16.923,29.576)),
#                                LineGeo(Point(-16.923,29.576),Point(-15.779,29.068)),
#                                LineGeo(Point(-15.779,29.068),Point(-14.61,28.662)),
#                                LineGeo(Point(-14.61,28.662),Point(-13.416,28.306)),
#                                LineGeo(Point(-13.416,28.306),Point(-13.035,29.83)),
#                                LineGeo(Point(-13.035,29.83),Point(-12.603,31.558)),
#                                LineGeo(Point(-12.603,31.558),Point(-12.196,33.438)),
#                                LineGeo(Point(-12.196,33.438),Point(-11.79,35.37)),
#                                LineGeo(Point(-11.79,35.37),Point(-11.459,37.402)),
#                                LineGeo(Point(-11.459,37.402),Point(-11.205,39.486)),
#                                LineGeo(Point(-11.205,39.486),Point(-11.053,41.468)),
#                                LineGeo(Point(-11.053,41.468),Point(-11.002,43.45)),
#                                LineGeo(Point(-11.002,43.45),Point(-11.129,45.28)),
#                                LineGeo(Point(-11.129,45.28),Point(-11.434,47.008)),
#                                LineGeo(Point(-11.434,47.008),Point(-11.917,48.532)),
#                                LineGeo(Point(-11.917,48.532),Point(-12.654,49.802)),
#                                LineGeo(Point(-12.654,49.802),Point(-13.619,50.82)),
#                                LineGeo(Point(-13.619,50.82),Point(-14.864,51.48)),
#                                LineGeo(Point(-14.864,51.48),Point(-16.44,51.836)),
#                                LineGeo(Point(-16.44,51.836),Point(-18.32,51.734)),
#                                LineGeo(Point(-18.32,51.734),Point(-18.396,53.056)),
#                                LineGeo(Point(-18.396,53.056),Point(-18.473,54.428)),
#                                LineGeo(Point(-18.473,54.428),Point(-18.473,55.952)),
#                                LineGeo(Point(-18.473,55.952),Point(-18.422,57.528)),
#                                LineGeo(Point(-18.422,57.528),Point(-18.295,59.102)),
#                                LineGeo(Point(-18.295,59.102),Point(-18.117,60.728)),
#                                LineGeo(Point(-18.117,60.728),Point(-17.812,62.356)),
#                                LineGeo(Point(-17.812,62.356),Point(-17.431,63.93)),
#                                LineGeo(Point(-17.431,63.93),Point(-16.923,65.404)),
#                                LineGeo(Point(-16.923,65.404),Point(-16.287,66.828)),
#                                LineGeo(Point(-16.287,66.828),Point(-15.525,68.148)),
#                                LineGeo(Point(-15.525,68.148),Point(-14.61,69.318)),
#                                LineGeo(Point(-14.61,69.318),Point(-13.518,70.284)),
#                                LineGeo(Point(-13.518,70.284),Point(-12.273,71.148)),
#                                LineGeo(Point(-12.273,71.148),Point(-10.824,71.756)),
#                                LineGeo(Point(-10.824,71.756),Point(-9.198,72.112)),
#                                LineGeo(Point(-9.198,72.112),Point(-8.893,72.926)),
#                                LineGeo(Point(-8.893,72.926),Point(-8.563,73.688)),
#                                LineGeo(Point(-8.563,73.688),Point(-8.182,74.4)),
#                                LineGeo(Point(-8.182,74.4),Point(-7.75,75.06)),
#                                LineGeo(Point(-7.75,75.06),Point(-7.292,75.62)),
#                                LineGeo(Point(-7.292,75.62),Point(-6.784,76.128)),
#                                LineGeo(Point(-6.784,76.128),Point(-6.276,76.584)),
#                                LineGeo(Point(-6.276,76.584),Point(-5.717,76.94)),
#                                LineGeo(Point(-5.717,76.94),Point(-5.158,77.296)),
#                                LineGeo(Point(-5.158,77.296),Point(-4.548,77.602)),
#                                LineGeo(Point(-4.548,77.602),Point(-3.938,77.804)),
#                                LineGeo(Point(-3.938,77.804),Point(-3.303,78.008)),
#                                LineGeo(Point(-3.303,78.008),Point(-2.668,78.16)),
#                                LineGeo(Point(-2.668,78.16),Point(-2.007,78.262)),
#                                LineGeo(Point(-2.007,78.262),Point(-1.346,78.312)),
#                                LineGeo(Point(-1.346,78.312),Point(-0.66,78.364)),
#                                LineGeo(Point(-0.66,78.364),Point(0,78.364)),
#                                LineGeo(Point(0,78.364),Point(0.66,78.312)),
#                                LineGeo(Point(0.66,78.312),Point(1.321,78.21)),
#                                LineGeo(Point(1.321,78.21),Point(1.981,78.11)),
#                                LineGeo(Point(1.981,78.11),Point(2.617,78.008)),
#                                LineGeo(Point(2.617,78.008),Point(3.252,77.856)),
#                                LineGeo(Point(3.252,77.856),Point(3.862,77.652)),
#                                LineGeo(Point(3.862,77.652),Point(4.446,77.448)),
#                                LineGeo(Point(4.446,77.448),Point(5.031,77.246)),
#                                LineGeo(Point(5.031,77.246),Point(5.564,76.992)),
#                                LineGeo(Point(5.564,76.992),Point(6.098,76.738)),
#                                LineGeo(Point(6.098,76.738),Point(6.581,76.484)),
#                                LineGeo(Point(6.581,76.484),Point(7.038,76.178)),
#                                LineGeo(Point(7.038,76.178),Point(7.445,75.924)),
#                                LineGeo(Point(7.445,75.924),Point(7.826,75.62)),
#                                LineGeo(Point(7.826,75.62),Point(8.156,75.314)),
#                                LineGeo(Point(8.156,75.314),Point(9.401,73.586)),
#                                LineGeo(Point(9.401,73.586),Point(10.494,71.3)),
#                                LineGeo(Point(10.494,71.3),Point(11.434,68.504)),
#                                LineGeo(Point(11.434,68.504),Point(12.247,65.404)),
#                                LineGeo(Point(12.247,65.404),Point(12.959,61.948)),
#                                LineGeo(Point(12.959,61.948),Point(13.543,58.29)),
#                                LineGeo(Point(13.543,58.29),Point(14.051,54.528)),
#                                LineGeo(Point(14.051,54.528),Point(14.458,50.768)),
#                                LineGeo(Point(14.458,50.768),Point(14.788,47.008)),
#                                LineGeo(Point(14.788,47.008),Point(15.042,43.348)),
#                                LineGeo(Point(15.042,43.348),Point(15.246,39.944)),
#                                LineGeo(Point(15.246,39.944),Point(15.373,36.844)),
#                                LineGeo(Point(15.373,36.844),Point(15.5,34.15)),
#                                LineGeo(Point(15.5,34.15),Point(15.576,31.914)),
#                                LineGeo(Point(15.576,31.914),Point(15.627,30.236)),
#                                LineGeo(Point(15.627,30.236),Point(15.677,29.22)),
#                                LineGeo(Point(15.677,29.22),Point(15.754,28.052)),
#                                LineGeo(Point(15.754,28.052),Point(16.821,28.764)),
#                                LineGeo(Point(16.821,28.764),Point(17.863,29.526)),
#                                LineGeo(Point(17.863,29.526),Point(18.854,30.288)),
#                                LineGeo(Point(18.854,30.288),Point(19.794,31.152)),
#                                LineGeo(Point(19.794,31.152),Point(20.709,32.016)),
#                                LineGeo(Point(20.709,32.016),Point(21.598,32.93)),
#                                LineGeo(Point(21.598,32.93),Point(22.411,33.896)),
#                                LineGeo(Point(22.411,33.896),Point(23.224,34.862)),
#                                LineGeo(Point(23.224,34.862),Point(23.961,35.928)),
#                                LineGeo(Point(23.961,35.928),Point(24.673,37.046)),
#                                LineGeo(Point(24.673,37.046),Point(25.333,38.164)),
#                                LineGeo(Point(25.333,38.164),Point(25.969,39.384)),
#                                LineGeo(Point(25.969,39.384),Point(26.553,40.604)),
#                                LineGeo(Point(26.553,40.604),Point(27.112,41.926)),
#                                LineGeo(Point(27.112,41.926),Point(27.595,43.298)),
#                                LineGeo(Point(27.595,43.298),Point(28.052,44.72)),
#                                LineGeo(Point(28.052,44.72),Point(28.484,46.194)),
#                                LineGeo(Point(28.484,46.194),Point(28.84,47.718)),
#                                LineGeo(Point(28.84,47.718),Point(29.17,49.346)),
#                                LineGeo(Point(29.17,49.346),Point(29.475,51.022)),
#                                LineGeo(Point(29.475,51.022),Point(29.704,52.75)),
#                                LineGeo(Point(29.704,52.75),Point(29.907,54.528)),
#                                LineGeo(Point(29.907,54.528),Point(30.06,56.41)),
#                                LineGeo(Point(30.06,56.41),Point(30.187,58.34)),
#                                LineGeo(Point(30.187,58.34),Point(30.237,60.322)),
#                                LineGeo(Point(30.237,60.322),Point(30.263,62.406)),
#                                LineGeo(Point(30.263,62.406),Point(30.237,64.592)),
#                                LineGeo(Point(30.237,64.592),Point(30.187,66.776)),
#                                LineGeo(Point(30.187,66.776),Point(30.06,69.114)),
#                                LineGeo(Point(30.06,69.114),Point(29.907,71.502)),
#                                LineGeo(Point(29.907,71.502),Point(29.704,73.942)),
#                                LineGeo(Point(29.704,73.942),Point(29.45,76.484)),
#                                LineGeo(Point(29.45,76.484),Point(31.101,76.484)),
#                                LineGeo(Point(31.101,76.484),Point(32.905,76.484)),
#                                LineGeo(Point(32.905,76.484),Point(34.862,76.484)),
#                                LineGeo(Point(34.862,76.484),Point(36.971,76.484)),
#                                LineGeo(Point(36.971,76.484),Point(39.182,76.484)),
#                                LineGeo(Point(39.182,76.484),Point(41.519,76.484)),
#                                LineGeo(Point(41.519,76.484),Point(43.933,76.484)),
#                                LineGeo(Point(43.933,76.484),Point(46.424,76.484)),
#                                LineGeo(Point(46.424,76.484),Point(48.99,76.484)),
#                                LineGeo(Point(48.99,76.484),Point(51.607,76.484)),
#                                LineGeo(Point(51.607,76.484),Point(54.25,76.484)),
#                                LineGeo(Point(54.25,76.484),Point(56.918,76.484)),
#                                LineGeo(Point(56.918,76.484),Point(59.586,76.484)),
#                                LineGeo(Point(59.586,76.484),Point(62.254,76.484)),
#                                LineGeo(Point(62.254,76.484),Point(64.922,76.484)),
#                                LineGeo(Point(64.922,76.484),Point(67.539,76.484)),
#                                LineGeo(Point(67.539,76.484),Point(70.08,76.484)),
#                                LineGeo(Point(70.08,76.484),Point(72.596,76.484)),
#                                LineGeo(Point(72.596,76.484),Point(75.01,76.484)),
#                                LineGeo(Point(75.01,76.484),Point(77.348,76.484)),
#                                LineGeo(Point(77.348,76.484),Point(79.584,76.484)),
#                                LineGeo(Point(79.584,76.484),Point(81.693,76.484)),
#                                LineGeo(Point(81.693,76.484),Point(83.675,76.484)),
#                                LineGeo(Point(83.675,76.484),Point(85.504,76.484)),
#                                LineGeo(Point(85.504,76.484),Point(87.156,76.484)),
#                                LineGeo(Point(87.156,76.484),Point(88.655,76.484)),
#                                LineGeo(Point(88.655,76.484),Point(89.951,76.484)),
#                                LineGeo(Point(89.951,76.484),Point(91.044,76.484)),
#                                LineGeo(Point(91.044,76.484),Point(91.933,76.484)),
#                                LineGeo(Point(91.933,76.484),Point(92.568,76.484)),
#                                LineGeo(Point(92.568,76.484),Point(92.975,76.484)),
#                                LineGeo(Point(92.975,76.484),Point(93.102,76.484)),
#                                LineGeo(Point(93.102,76.484),Point(82.785,58.746)),
#                                LineGeo(Point(82.785,58.746),Point(42.155,58.746)),
#                                LineGeo(Point(42.155,58.746),Point(41.875,58.696)),
#                                LineGeo(Point(41.875,58.696),Point(41.646,58.492)),
#                                LineGeo(Point(41.646,58.492),Point(41.469,58.238)),
#                                LineGeo(Point(41.469,58.238),Point(41.316,57.882)),
#                                LineGeo(Point(41.316,57.882),Point(41.215,57.528)),
#                                LineGeo(Point(41.215,57.528),Point(41.138,57.172)),
#                                LineGeo(Point(41.138,57.172),Point(41.113,56.866)),
#                                LineGeo(Point(41.113,56.866),Point(41.087,56.612)),
#                                LineGeo(Point(41.087,56.612),Point(40.884,54.122)),
#                                LineGeo(Point(40.884,54.122),Point(40.63,51.682)),
#                                LineGeo(Point(40.63,51.682),Point(40.3,49.244)),
#                                LineGeo(Point(40.3,49.244),Point(39.919,46.856)),
#                                LineGeo(Point(39.919,46.856),Point(39.461,44.518)),
#                                LineGeo(Point(39.461,44.518),Point(38.953,42.23)),
#                                LineGeo(Point(38.953,42.23),Point(38.394,39.994)),
#                                LineGeo(Point(38.394,39.994),Point(37.784,37.81)),
#                                LineGeo(Point(37.784,37.81),Point(37.149,35.674)),
#                                LineGeo(Point(37.149,35.674),Point(36.437,33.592)),
#                                LineGeo(Point(36.437,33.592),Point(35.701,31.61)),
#                                LineGeo(Point(35.701,31.61),Point(34.913,29.628)),
#                                LineGeo(Point(34.913,29.628),Point(34.1,27.746)),
#                                LineGeo(Point(34.1,27.746),Point(33.261,25.918)),
#                                LineGeo(Point(33.261,25.918),Point(32.397,24.19)),
#                                LineGeo(Point(32.397,24.19),Point(31.482,22.512)),
#                                LineGeo(Point(31.482,22.512),Point(30.568,20.886)),
#                                LineGeo(Point(30.568,20.886),Point(29.628,19.362)),
#                                LineGeo(Point(29.628,19.362),Point(28.662,17.938)),
#                                LineGeo(Point(28.662,17.938),Point(27.696,16.566)),
#                                LineGeo(Point(27.696,16.566),Point(26.731,15.296)),
#                                LineGeo(Point(26.731,15.296),Point(25.74,14.126)),
#                                LineGeo(Point(25.74,14.126),Point(24.723,13.06)),
#                                LineGeo(Point(24.723,13.06),Point(23.732,12.044)),
#                                LineGeo(Point(23.732,12.044),Point(22.741,11.18)),
#                                LineGeo(Point(22.741,11.18),Point(21.75,10.366)),
#                                LineGeo(Point(21.75,10.366),Point(20.785,9.706)),
#                                LineGeo(Point(20.785,9.706),Point(19.794,9.096)),
#                                LineGeo(Point(19.794,9.096),Point(18.854,8.638)),
#                                LineGeo(Point(18.854,8.638),Point(17.914,8.282)),
#                                LineGeo(Point(17.914,8.282),Point(16.973,8.028)),
#                                LineGeo(Point(16.973,8.028),Point(16.084,7.926)),
#                                LineGeo(Point(16.084,7.926),Point(18.193,-50.818)),
#                                LineGeo(Point(18.193,-50.818),Point(0,-81.412)),
#                                LineGeo(Point(0,-81.412),Point(-18.193,-50.818)),
#                                LineGeo(Point(-18.193,-50.818),Point(-16.084,7.926))],closed=True)

#        shape=ShapeClass(geos=[LineGeo(Point(x=0,y=-1),Point(x=0,y=0)),
#                               LineGeo(Point(x=0,y=0),Point(x=2,y=2)),
#                               LineGeo(Point(x=2,y=2),Point(x=3,y=3)),
#                               LineGeo(Point(x=3,y=3),Point(x=3,y=0.5)),
#                               LineGeo(Point(x=3,y=0.5),Point(x=6,y=2)),
#                               LineGeo(Point(x=6,y=2),Point(x=6,y=-4)),
#                               LineGeo(Point(x=6,y=-4),Point(x=3,y=-0.5)),
#                               LineGeo(Point(x=3,y=-0.5),Point(x=0,y=-5)),
#                               LineGeo(Point(x=0,y=-5), Point(x=0,y=-4)),
#                               LineGeo(Point(x=0,y=-4), Point(x=0,y=-1))],
#                               closed=True)
        # offshape=offShapeClass(shape, offset=4, offtype='in')
        # offshape1=offShapeClass(shape, offset=8, offtype='in')

        shape = ShapeClass(geos=[LineGeo(Point(10, 29), Point(30, 29)),
                                LineGeo(Point(30, 29), Point(30, -29)),
                                LineGeo(Point(30, -29), Point(10, -29)),
                                ArcGeo(Pa=Point(10, -29), Pe=Point(-10, -29), O=Point(0, -29), r=10, direction=-1),  # ,s_ang=90/180*pi,e_ang=90/180*pi
                                LineGeo(Point(-10, -29), Point(-30, -29)),
                                LineGeo(Point(-30, -29), Point(-30, 29)),
                                LineGeo(Point(-30, 29), Point(-10, 29)),
                                ArcGeo(Pa=Point(-10, 29), Pe=Point(10, 29), O=Point(0, 29), r=10, direction=-1)],  # ,s_ang=270/180*pi,e_ang=-90/180*pi
                         closed=True)

        offshape2 = offShapeClass(shape, offset=5, offtype='out')
        # offshape3=offShapeClass(shape, offset=16, offtype='in')
        Pl.plot_lines_plot(offshape2.geos, 121, wtp=[True, True, True])
        # Pl.plot_segments(offshape2.plotshapes, 121, format=('b', '.b', '.b'), fcol='blue', wtp=[True, False, False])
        Pl.plot_segments(offshape2.rawoff, 121, format=('b', '.b', '.b'), fcol='blue', wtp=[True, False, False])
        
        Pl.plot_segments(offshape2.segments, 122, format=('m', '.m', '.m'), fcol='blue', wtp=[True, True, True])
        

        Pl.plot_segments(offshape2.interferingshapes, 122, format=('b', '.b', '.b'), fcol='blue', wtp=[True, False, False])



        # Pl.plot_segments(offshape2.rawoff, 122, format=('c', '.c', '.c'), fcol='blue', wtp=[True, False, False])
        # Pl.plot_segments(offshape3.rawoff,121,format=('b','.b','.b'),fcol='blue',wtp=[True,False,False])

        # Pl.plot_lines_plot(offshape.geos,132,wtp=[True,False,False])
        # Pl.plot_segments(offshape.rawoff,132,format=('b','.b','.b'),fcol='blue',wtp=[True,False,False])
#        Pl.plot_segments(offshape.segments,121,wtp=[True,False,True])
#        Pl.plot_segments(offshape.plotshapes,121,format=('b','.b','.b'),fcol='blue',wtp=[True,True,True])
#        Pl.plot_segments(offshape.interferingshapes,121,format=('c','xc','oc'),fcol='black',wtp=[True,True,True])

#        offshape=offShapeClass(shape, offset=3, offtype='out')
#        offshape1=offShapeClass(shape, offset=6, offtype='out')
#        offshape2=offShapeClass(shape, offset=9, offtype='out')
#        offshape3=offShapeClass(shape, offset=12, offtype='out')
#        offshape4=offShapeClass(shape, offset=15, offtype='out')
# #
#        Pl.plot_lines_plot(offshape.geos,122,wtp=[True,False,False])
#        Pl.plot_segments(offshape.rawoff,122,format=('b','.b','.b'),fcol='blue',wtp=[True,False,False])
#        Pl.plot_segments(offshape1.rawoff,122,format=('b','.b','.b'),fcol='blue',wtp=[True,False,False])
#        Pl.plot_segments(offshape2.rawoff,122,format=('b','.b','.b'),fcol='blue',wtp=[True,False,False])
#        Pl.plot_segments(offshape3.rawoff,122,format=('b','.b','.b'),fcol='blue',wtp=[True,False,False])
#        Pl.plot_segments(offshape4.rawoff,122,format=('b','.b','.b'),fcol='blue',wtp=[True,False,False])
#
#        Pl.canvas.show()

    def SweepLineTest(self):
        master.title("PWIDTest Check")
        shape = ShapeClass(geos=[LineGeo(Point(-16.084, 7.926), Point(-16.973, 8.028)),
                                LineGeo(Point(-16.973, 8.028), Point(-17.914, 8.282)),
                                LineGeo(Point(-17.914, 8.282), Point(-18.854, 8.638)),
                                LineGeo(Point(-18.854, 8.638), Point(-19.794, 9.096)),
                                LineGeo(Point(-19.794, 9.096), Point(-20.785, 9.706)),
                                LineGeo(Point(-20.785, 9.706), Point(-21.75, 10.366)),
                                LineGeo(Point(-21.75, 10.366), Point(-22.741, 11.18)),
                                LineGeo(Point(-22.741, 11.18), Point(-23.732, 12.044)),
                                LineGeo(Point(-23.732, 12.044), Point(-24.723, 13.06)),
                                LineGeo(Point(-24.723, 13.06), Point(-25.714, 14.126)),
                                LineGeo(Point(-25.714, 14.126), Point(-26.705, 15.296)),
                                LineGeo(Point(-26.705, 15.296), Point(-27.696, 16.566)),
                                LineGeo(Point(-27.696, 16.566), Point(-28.662, 17.938)),
                                LineGeo(Point(-28.662, 17.938), Point(-29.628, 19.362)),
                                LineGeo(Point(-29.628, 19.362), Point(-30.568, 20.886)),
                                LineGeo(Point(-30.568, 20.886), Point(-31.482, 22.512)),
                                LineGeo(Point(-31.482, 22.512), Point(-32.372, 24.19)),
                                LineGeo(Point(-32.372, 24.19), Point(-33.261, 25.918)),
                                LineGeo(Point(-33.261, 25.918), Point(-34.1, 27.746)),
                                LineGeo(Point(-34.1, 27.746), Point(-34.913, 29.628)),
                                LineGeo(Point(-34.913, 29.628), Point(-35.675, 31.61)),
                                LineGeo(Point(-35.675, 31.61), Point(-36.437, 33.592)),
                                LineGeo(Point(-36.437, 33.592), Point(-37.124, 35.674)),
                                LineGeo(Point(-37.124, 35.674), Point(-37.784, 37.81)),
                                LineGeo(Point(-37.784, 37.81), Point(-38.394, 39.994)),
                                LineGeo(Point(-38.394, 39.994), Point(-38.953, 42.23)),
                                LineGeo(Point(-38.953, 42.23), Point(-39.461, 44.518)),
                                LineGeo(Point(-39.461, 44.518), Point(-39.893, 46.856)),
                                LineGeo(Point(-39.893, 46.856), Point(-40.3, 49.244)),
                                LineGeo(Point(-40.3, 49.244), Point(-40.63, 51.682)),
                                LineGeo(Point(-40.63, 51.682), Point(-40.884, 54.122)),
                                LineGeo(Point(-40.884, 54.122), Point(-41.087, 56.612)),
                                LineGeo(Point(-41.087, 56.612), Point(-41.087, 56.866)),
                                LineGeo(Point(-41.087, 56.866), Point(-41.138, 57.172)),
                                LineGeo(Point(-41.138, 57.172), Point(-41.215, 57.528)),
                                LineGeo(Point(-41.215, 57.528), Point(-41.316, 57.882)),
                                LineGeo(Point(-41.316, 57.882), Point(-41.469, 58.238)),
                                LineGeo(Point(-41.469, 58.238), Point(-41.646, 58.492)),
                                LineGeo(Point(-41.646, 58.492), Point(-41.875, 58.696)),
                                LineGeo(Point(-41.875, 58.696), Point(-42.155, 58.746)),
                                LineGeo(Point(-42.155, 58.746), Point(-82.785, 58.746)),
                                LineGeo(Point(-82.785, 58.746), Point(-93.102, 76.484)),
                                LineGeo(Point(-93.102, 76.484), Point(-92.975, 76.484)),
                                LineGeo(Point(-92.975, 76.484), Point(-92.594, 76.484)),
                                LineGeo(Point(-92.594, 76.484), Point(-91.958, 76.484)),
                                LineGeo(Point(-91.958, 76.484), Point(-91.12, 76.484)),
                                LineGeo(Point(-91.12, 76.484), Point(-90.053, 76.484)),
                                LineGeo(Point(-90.053, 76.484), Point(-88.782, 76.484)),
                                LineGeo(Point(-88.782, 76.484), Point(-87.334, 76.484)),
                                LineGeo(Point(-87.334, 76.484), Point(-85.733, 76.484)),
                                LineGeo(Point(-85.733, 76.484), Point(-83.954, 76.484)),
                                LineGeo(Point(-83.954, 76.484), Point(-82.023, 76.484)),
                                LineGeo(Point(-82.023, 76.484), Point(-79.99, 76.484)),
                                LineGeo(Point(-79.99, 76.484), Point(-77.805, 76.484)),
                                LineGeo(Point(-77.805, 76.484), Point(-75.543, 76.484)),
                                LineGeo(Point(-75.543, 76.484), Point(-73.18, 76.484)),
                                LineGeo(Point(-73.18, 76.484), Point(-70.741, 76.484)),
                                LineGeo(Point(-70.741, 76.484), Point(-68.251, 76.484)),
                                LineGeo(Point(-68.251, 76.484), Point(-65.71, 76.484)),
                                LineGeo(Point(-65.71, 76.484), Point(-63.118, 76.484)),
                                LineGeo(Point(-63.118, 76.484), Point(-60.526, 76.484)),
                                LineGeo(Point(-60.526, 76.484), Point(-57.909, 76.484)),
                                LineGeo(Point(-57.909, 76.484), Point(-55.292, 76.484)),
                                LineGeo(Point(-55.292, 76.484), Point(-52.7, 76.484)),
                                LineGeo(Point(-52.7, 76.484), Point(-50.159, 76.484)),
                                LineGeo(Point(-50.159, 76.484), Point(-47.643, 76.484)),
                                LineGeo(Point(-47.643, 76.484), Point(-45.204, 76.484)),
                                LineGeo(Point(-45.204, 76.484), Point(-42.841, 76.484)),
                                LineGeo(Point(-42.841, 76.484), Point(-40.554, 76.484)),
                                LineGeo(Point(-40.554, 76.484), Point(-38.369, 76.484)),
                                LineGeo(Point(-38.369, 76.484), Point(-36.285, 76.484)),
                                LineGeo(Point(-36.285, 76.484), Point(-34.354, 76.484)),
                                LineGeo(Point(-34.354, 76.484), Point(-32.55, 76.484)),
                                LineGeo(Point(-32.55, 76.484), Point(-30.898, 76.484)),
                                LineGeo(Point(-30.898, 76.484), Point(-31.152, 73.942)),
                                LineGeo(Point(-31.152, 73.942), Point(-31.33, 71.452)),
                                LineGeo(Point(-31.33, 71.452), Point(-31.457, 69.012)),
                                LineGeo(Point(-31.457, 69.012), Point(-31.508, 66.624)),
                                LineGeo(Point(-31.508, 66.624), Point(-31.533, 64.338)),
                                LineGeo(Point(-31.533, 64.338), Point(-31.482, 62.102)),
                                LineGeo(Point(-31.482, 62.102), Point(-31.381, 59.916)),
                                LineGeo(Point(-31.381, 59.916), Point(-31.228, 57.782)),
                                LineGeo(Point(-31.228, 57.782), Point(-31.025, 55.748)),
                                LineGeo(Point(-31.025, 55.748), Point(-30.746, 53.766)),
                                LineGeo(Point(-30.746, 53.766), Point(-30.441, 51.836)),
                                LineGeo(Point(-30.441, 51.836), Point(-30.085, 49.956)),
                                LineGeo(Point(-30.085, 49.956), Point(-29.653, 48.176)),
                                LineGeo(Point(-29.653, 48.176), Point(-29.196, 46.5)),
                                LineGeo(Point(-29.196, 46.5), Point(-28.687, 44.822)),
                                LineGeo(Point(-28.687, 44.822), Point(-28.128, 43.246)),
                                LineGeo(Point(-28.128, 43.246), Point(-27.519, 41.774)),
                                LineGeo(Point(-27.519, 41.774), Point(-26.858, 40.35)),
                                LineGeo(Point(-26.858, 40.35), Point(-26.172, 38.978)),
                                LineGeo(Point(-26.172, 38.978), Point(-25.435, 37.708)),
                                LineGeo(Point(-25.435, 37.708), Point(-24.647, 36.488)),
                                LineGeo(Point(-24.647, 36.488), Point(-23.809, 35.37)),
                                LineGeo(Point(-23.809, 35.37), Point(-22.945, 34.302)),
                                LineGeo(Point(-22.945, 34.302), Point(-22.03, 33.286)),
                                LineGeo(Point(-22.03, 33.286), Point(-21.09, 32.422)),
                                LineGeo(Point(-21.09, 32.422), Point(-20.099, 31.558)),
                                LineGeo(Point(-20.099, 31.558), Point(-19.082, 30.846)),
                                LineGeo(Point(-19.082, 30.846), Point(-18.015, 30.186)),
                                LineGeo(Point(-18.015, 30.186), Point(-16.923, 29.576)),
                                LineGeo(Point(-16.923, 29.576), Point(-15.779, 29.068)),
                                LineGeo(Point(-15.779, 29.068), Point(-14.61, 28.662)),
                                LineGeo(Point(-14.61, 28.662), Point(-13.416, 28.306)),
                                LineGeo(Point(-13.416, 28.306), Point(-13.035, 29.83)),
                                LineGeo(Point(-13.035, 29.83), Point(-12.603, 31.558)),
                                LineGeo(Point(-12.603, 31.558), Point(-12.196, 33.438)),
                                LineGeo(Point(-12.196, 33.438), Point(-11.79, 35.37)),
                                LineGeo(Point(-11.79, 35.37), Point(-11.459, 37.402)),
                                LineGeo(Point(-11.459, 37.402), Point(-11.205, 39.486)),
                                LineGeo(Point(-11.205, 39.486), Point(-11.053, 41.468)),
                                LineGeo(Point(-11.053, 41.468), Point(-11.002, 43.45)),
                                LineGeo(Point(-11.002, 43.45), Point(-11.129, 45.28)),
                                LineGeo(Point(-11.129, 45.28), Point(-11.434, 47.008)),
                                LineGeo(Point(-11.434, 47.008), Point(-11.917, 48.532)),
                                LineGeo(Point(-11.917, 48.532), Point(-12.654, 49.802)),
                                LineGeo(Point(-12.654, 49.802), Point(-13.619, 50.82)),
                                LineGeo(Point(-13.619, 50.82), Point(-14.864, 51.48)),
                                LineGeo(Point(-14.864, 51.48), Point(-16.44, 51.836)),
                                LineGeo(Point(-16.44, 51.836), Point(-18.32, 51.734)),
                                LineGeo(Point(-18.32, 51.734), Point(-18.396, 53.056)),
                                LineGeo(Point(-18.396, 53.056), Point(-18.473, 54.428)),
                                LineGeo(Point(-18.473, 54.428), Point(-18.473, 55.952)),
                                LineGeo(Point(-18.473, 55.952), Point(-18.422, 57.528)),
                                LineGeo(Point(-18.422, 57.528), Point(-18.295, 59.102)),
                                LineGeo(Point(-18.295, 59.102), Point(-18.117, 60.728)),
                                LineGeo(Point(-18.117, 60.728), Point(-17.812, 62.356)),
                                LineGeo(Point(-17.812, 62.356), Point(-17.431, 63.93)),
                                LineGeo(Point(-17.431, 63.93), Point(-16.923, 65.404)),
                                LineGeo(Point(-16.923, 65.404), Point(-16.287, 66.828)),
                                LineGeo(Point(-16.287, 66.828), Point(-15.525, 68.148)),
                                LineGeo(Point(-15.525, 68.148), Point(-14.61, 69.318)),
                                LineGeo(Point(-14.61, 69.318), Point(-13.518, 70.284)),
                                LineGeo(Point(-13.518, 70.284), Point(-12.273, 71.148)),
                                LineGeo(Point(-12.273, 71.148), Point(-10.824, 71.756)),
                                LineGeo(Point(-10.824, 71.756), Point(-9.198, 72.112)),
                                LineGeo(Point(-9.198, 72.112), Point(-8.893, 72.926)),
                                LineGeo(Point(-8.893, 72.926), Point(-8.563, 73.688)),
                                LineGeo(Point(-8.563, 73.688), Point(-8.182, 74.4)),
                                LineGeo(Point(-8.182, 74.4), Point(-7.75, 75.06)),
                                LineGeo(Point(-7.75, 75.06), Point(-7.292, 75.62)),
                                LineGeo(Point(-7.292, 75.62), Point(-6.784, 76.128)),
                                LineGeo(Point(-6.784, 76.128), Point(-6.276, 76.584)),
                                LineGeo(Point(-6.276, 76.584), Point(-5.717, 76.94)),
                                LineGeo(Point(-5.717, 76.94), Point(-5.158, 77.296)),
                                LineGeo(Point(-5.158, 77.296), Point(-4.548, 77.602)),
                                LineGeo(Point(-4.548, 77.602), Point(-3.938, 77.804)),
                                LineGeo(Point(-3.938, 77.804), Point(-3.303, 78.008)),
                                LineGeo(Point(-3.303, 78.008), Point(-2.668, 78.16)),
                                LineGeo(Point(-2.668, 78.16), Point(-2.007, 78.262)),
                                LineGeo(Point(-2.007, 78.262), Point(-1.346, 78.312)),
                                LineGeo(Point(-1.346, 78.312), Point(-0.66, 78.364)),
                                LineGeo(Point(-0.66, 78.364), Point(0, 78.364)),
                                LineGeo(Point(0, 78.364), Point(0.66, 78.312)),
                                LineGeo(Point(0.66, 78.312), Point(1.321, 78.21)),
                                LineGeo(Point(1.321, 78.21), Point(1.981, 78.11)),
                                LineGeo(Point(1.981, 78.11), Point(2.617, 78.008)),
                                LineGeo(Point(2.617, 78.008), Point(3.252, 77.856)),
                                LineGeo(Point(3.252, 77.856), Point(3.862, 77.652)),
                                LineGeo(Point(3.862, 77.652), Point(4.446, 77.448)),
                                LineGeo(Point(4.446, 77.448), Point(5.031, 77.246)),
                                LineGeo(Point(5.031, 77.246), Point(5.564, 76.992)),
                                LineGeo(Point(5.564, 76.992), Point(6.098, 76.738)),
                                LineGeo(Point(6.098, 76.738), Point(6.581, 76.484)),
                                LineGeo(Point(6.581, 76.484), Point(7.038, 76.178)),
                                LineGeo(Point(7.038, 76.178), Point(7.445, 75.924)),
                                LineGeo(Point(7.445, 75.924), Point(7.826, 75.62)),
                                LineGeo(Point(7.826, 75.62), Point(8.156, 75.314)),
                                LineGeo(Point(8.156, 75.314), Point(9.401, 73.586)),
                                LineGeo(Point(9.401, 73.586), Point(10.494, 71.3)),
                                LineGeo(Point(10.494, 71.3), Point(11.434, 68.504)),
                                LineGeo(Point(11.434, 68.504), Point(12.247, 65.404)),
                                LineGeo(Point(12.247, 65.404), Point(12.959, 61.948)),
                                LineGeo(Point(12.959, 61.948), Point(13.543, 58.29)),
                                LineGeo(Point(13.543, 58.29), Point(14.051, 54.528)),
                                LineGeo(Point(14.051, 54.528), Point(14.458, 50.768)),
                                LineGeo(Point(14.458, 50.768), Point(14.788, 47.008)),
                                LineGeo(Point(14.788, 47.008), Point(15.042, 43.348)),
                                LineGeo(Point(15.042, 43.348), Point(15.246, 39.944)),
                                LineGeo(Point(15.246, 39.944), Point(15.373, 36.844)),
                                LineGeo(Point(15.373, 36.844), Point(15.5, 34.15)),
                                LineGeo(Point(15.5, 34.15), Point(15.576, 31.914)),
                                LineGeo(Point(15.576, 31.914), Point(15.627, 30.236)),
                                LineGeo(Point(15.627, 30.236), Point(15.677, 29.22)),
                                LineGeo(Point(15.677, 29.22), Point(15.754, 28.052)),
                                LineGeo(Point(15.754, 28.052), Point(16.821, 28.764)),
                                LineGeo(Point(16.821, 28.764), Point(17.863, 29.526)),
                                LineGeo(Point(17.863, 29.526), Point(18.854, 30.288)),
                                LineGeo(Point(18.854, 30.288), Point(19.794, 31.152)),
                                LineGeo(Point(19.794, 31.152), Point(20.709, 32.016)),
                                LineGeo(Point(20.709, 32.016), Point(21.598, 32.93)),
                                LineGeo(Point(21.598, 32.93), Point(22.411, 33.896)),
                                LineGeo(Point(22.411, 33.896), Point(23.224, 34.862)),
                                LineGeo(Point(23.224, 34.862), Point(23.961, 35.928)),
                                LineGeo(Point(23.961, 35.928), Point(24.673, 37.046)),
                                LineGeo(Point(24.673, 37.046), Point(25.333, 38.164)),
                                LineGeo(Point(25.333, 38.164), Point(25.969, 39.384)),
                                LineGeo(Point(25.969, 39.384), Point(26.553, 40.604)),
                                LineGeo(Point(26.553, 40.604), Point(27.112, 41.926)),
                                LineGeo(Point(27.112, 41.926), Point(27.595, 43.298)),
                                LineGeo(Point(27.595, 43.298), Point(28.052, 44.72)),
                                LineGeo(Point(28.052, 44.72), Point(28.484, 46.194)),
                                LineGeo(Point(28.484, 46.194), Point(28.84, 47.718)),
                                LineGeo(Point(28.84, 47.718), Point(29.17, 49.346)),
                                LineGeo(Point(29.17, 49.346), Point(29.475, 51.022)),
                                LineGeo(Point(29.475, 51.022), Point(29.704, 52.75)),
                                LineGeo(Point(29.704, 52.75), Point(29.907, 54.528)),
                                LineGeo(Point(29.907, 54.528), Point(30.06, 56.41)),
                                LineGeo(Point(30.06, 56.41), Point(30.187, 58.34)),
                                LineGeo(Point(30.187, 58.34), Point(30.237, 60.322)),
                                LineGeo(Point(30.237, 60.322), Point(30.263, 62.406)),
                                LineGeo(Point(30.263, 62.406), Point(30.237, 64.592)),
                                LineGeo(Point(30.237, 64.592), Point(30.187, 66.776)),
                                LineGeo(Point(30.187, 66.776), Point(30.06, 69.114)),
                                LineGeo(Point(30.06, 69.114), Point(29.907, 71.502)),
                                LineGeo(Point(29.907, 71.502), Point(29.704, 73.942)),
                                LineGeo(Point(29.704, 73.942), Point(29.45, 76.484)),
                                LineGeo(Point(29.45, 76.484), Point(31.101, 76.484)),
                                LineGeo(Point(31.101, 76.484), Point(32.905, 76.484)),
                                LineGeo(Point(32.905, 76.484), Point(34.862, 76.484)),
                                LineGeo(Point(34.862, 76.484), Point(36.971, 76.484)),
                                LineGeo(Point(36.971, 76.484), Point(39.182, 76.484)),
                                LineGeo(Point(39.182, 76.484), Point(41.519, 76.484)),
                                LineGeo(Point(41.519, 76.484), Point(43.933, 76.484)),
                                LineGeo(Point(43.933, 76.484), Point(46.424, 76.484)),
                                LineGeo(Point(46.424, 76.484), Point(48.99, 76.484)),
                                LineGeo(Point(48.99, 76.484), Point(51.607, 76.484)),
                                LineGeo(Point(51.607, 76.484), Point(54.25, 76.484)),
                                LineGeo(Point(54.25, 76.484), Point(56.918, 76.484)),
                                LineGeo(Point(56.918, 76.484), Point(59.586, 76.484)),
                                LineGeo(Point(59.586, 76.484), Point(62.254, 76.484)),
                                LineGeo(Point(62.254, 76.484), Point(64.922, 76.484)),
                                LineGeo(Point(64.922, 76.484), Point(67.539, 76.484)),
                                LineGeo(Point(67.539, 76.484), Point(70.08, 76.484)),
                                LineGeo(Point(70.08, 76.484), Point(72.596, 76.484)),
                                LineGeo(Point(72.596, 76.484), Point(75.01, 76.484)),
                                LineGeo(Point(75.01, 76.484), Point(77.348, 76.484)),
                                LineGeo(Point(77.348, 76.484), Point(79.584, 76.484)),
                                LineGeo(Point(79.584, 76.484), Point(81.693, 76.484)),
                                LineGeo(Point(81.693, 76.484), Point(83.675, 76.484)),
                                LineGeo(Point(83.675, 76.484), Point(85.504, 76.484)),
                                LineGeo(Point(85.504, 76.484), Point(87.156, 76.484)),
                                LineGeo(Point(87.156, 76.484), Point(88.655, 76.484)),
                                LineGeo(Point(88.655, 76.484), Point(89.951, 76.484)),
                                LineGeo(Point(89.951, 76.484), Point(91.044, 76.484)),
                                LineGeo(Point(91.044, 76.484), Point(91.933, 76.484)),
                                LineGeo(Point(91.933, 76.484), Point(92.568, 76.484)),
                                LineGeo(Point(92.568, 76.484), Point(92.975, 76.484)),
                                LineGeo(Point(92.975, 76.484), Point(93.102, 76.484)),
                                LineGeo(Point(93.102, 76.484), Point(82.785, 58.746)),
                                LineGeo(Point(82.785, 58.746), Point(42.155, 58.746)),
                                LineGeo(Point(42.155, 58.746), Point(41.875, 58.696)),
                                LineGeo(Point(41.875, 58.696), Point(41.646, 58.492)),
                                LineGeo(Point(41.646, 58.492), Point(41.469, 58.238)),
                                LineGeo(Point(41.469, 58.238), Point(41.316, 57.882)),
                                LineGeo(Point(41.316, 57.882), Point(41.215, 57.528)),
                                LineGeo(Point(41.215, 57.528), Point(41.138, 57.172)),
                                LineGeo(Point(41.138, 57.172), Point(41.113, 56.866)),
                                LineGeo(Point(41.113, 56.866), Point(41.087, 56.612)),
                                LineGeo(Point(41.087, 56.612), Point(40.884, 54.122)),
                                LineGeo(Point(40.884, 54.122), Point(40.63, 51.682)),
                                LineGeo(Point(40.63, 51.682), Point(40.3, 49.244)),
                                LineGeo(Point(40.3, 49.244), Point(39.919, 46.856)),
                                LineGeo(Point(39.919, 46.856), Point(39.461, 44.518)),
                                LineGeo(Point(39.461, 44.518), Point(38.953, 42.23)),
                                LineGeo(Point(38.953, 42.23), Point(38.394, 39.994)),
                                LineGeo(Point(38.394, 39.994), Point(37.784, 37.81)),
                                LineGeo(Point(37.784, 37.81), Point(37.149, 35.674)),
                                LineGeo(Point(37.149, 35.674), Point(36.437, 33.592)),
                                LineGeo(Point(36.437, 33.592), Point(35.701, 31.61)),
                                LineGeo(Point(35.701, 31.61), Point(34.913, 29.628)),
                                LineGeo(Point(34.913, 29.628), Point(34.1, 27.746)),
                                LineGeo(Point(34.1, 27.746), Point(33.261, 25.918)),
                                LineGeo(Point(33.261, 25.918), Point(32.397, 24.19)),
                                LineGeo(Point(32.397, 24.19), Point(31.482, 22.512)),
                                LineGeo(Point(31.482, 22.512), Point(30.568, 20.886)),
                                LineGeo(Point(30.568, 20.886), Point(29.628, 19.362)),
                                LineGeo(Point(29.628, 19.362), Point(28.662, 17.938)),
                                LineGeo(Point(28.662, 17.938), Point(27.696, 16.566)),
                                LineGeo(Point(27.696, 16.566), Point(26.731, 15.296)),
                                LineGeo(Point(26.731, 15.296), Point(25.74, 14.126)),
                                LineGeo(Point(25.74, 14.126), Point(24.723, 13.06)),
                                LineGeo(Point(24.723, 13.06), Point(23.732, 12.044)),
                                LineGeo(Point(23.732, 12.044), Point(22.741, 11.18)),
                                LineGeo(Point(22.741, 11.18), Point(21.75, 10.366)),
                                LineGeo(Point(21.75, 10.366), Point(20.785, 9.706)),
                                LineGeo(Point(20.785, 9.706), Point(19.794, 9.096)),
                                LineGeo(Point(19.794, 9.096), Point(18.854, 8.638)),
                                LineGeo(Point(18.854, 8.638), Point(17.914, 8.282)),
                                LineGeo(Point(17.914, 8.282), Point(16.973, 8.028)),
                                LineGeo(Point(16.973, 8.028), Point(16.084, 7.926)),
                                LineGeo(Point(16.084, 7.926), Point(18.193, -50.818)),
                                LineGeo(Point(18.193, -50.818), Point(0, -81.412)),
                                LineGeo(Point(0, -81.412), Point(-18.193, -50.818)),
                                LineGeo(Point(-18.193, -50.818), Point(-16.084, 7.926))], closed=True)

#        shape=ShapeClass(geos=[LineGeo(Point(x=0,y=-1),Point(x=0,y=0)),
#                               LineGeo(Point(x=0,y=0),Point(x=2,y=2)),
#                               LineGeo(Point(x=2,y=2),Point(x=3,y=3)),
#                               LineGeo(Point(x=3,y=3),Point(x=3,y=0.5)),
#                               LineGeo(Point(x=3,y=0.5),Point(x=6,y=2)),
#                               LineGeo(Point(x=6,y=2),Point(x=6,y=-4)),
#                               LineGeo(Point(x=6,y=-4),Point(x=3,y=-0.5)),
#                               LineGeo(Point(x=3,y=-0.5),Point(x=0,y=-5)),
#                               LineGeo(Point(x=0,y=-5), Point(x=0,y=-4)),
#                               LineGeo(Point(x=0,y=-4), Point(x=0,y=-1))],
#                               closed=True)


        offshape = offShapeClass(shape, offset=17.5, offtype='in')
        Pl.plot_lines_plot(offshape.geos, 111, wtp=[True, False, False])
        Pl.plot_segments(offshape.rawoff, 111, format=('b', '.b', '.b'), fcol='blue', wtp=[True, False, False])

        swpln = SweepLine(offshape.rawoff, offshape.closed)
        swpln.search_intersections()
        Pl.plot_segments(swpln.found, 111, wtp=[True, False, False])

logging.basicConfig(level=logging.DEBUG, format="%(funcName)-30s %(lineno)-6d: %(message)s")
master = Tk()
Pl = PlotClass(master)
Ex = ExampleClass()


# Ex.CheckColinearLines()
Ex.CheckForIntersections()
# Ex.SimplePolygonCheck()
# Ex.Distance_Check()
# cProfile.run("Ex.PWIDTest()",sort='cumtime')
# Ex.PWIDTest()
# Ex.SweepLineTest()
# self.make_offshape()



master.mainloop()




