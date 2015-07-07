# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
#    Jean-Paul Schouwstra
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from __future__ import division

from math import sqrt, pi
from copy import deepcopy

from core.point import Point
from core.boundingbox import BoundingBox

class LineGeo(object):
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """
    def __init__(self, Ps, Pe):
        """
        Standard Method to initialize the LineGeo.
        @param Ps: The Start Point of the line
        @param Pe: the End Point of the line
        """
        self.Ps = Ps
        self.Pe = Pe
        self.length = self.Ps.distance(self.Pe)
        
        self.inters = []
        self.calc_bounding_box()

        self.topLeft = None
        self.bottomRight = None

        self.abs_geo = None

    def __deepcopy__(self, memo):
        return LineGeo(deepcopy(self.Ps, memo),
                       deepcopy(self.Pe, memo))

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """
        return ("\nLineGeo(Ps=Point(x=%s ,y=%s),\n" % (self.Ps.x, self.Ps.y)) + \
               ("Pe=Point(x=%s, y=%s))" % (self.Pe.x, self.Pe.y))

    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        Ps = Point(x=min(self.Ps.x, self.Pe.x), y=min(self.Ps.y, self.Pe.y))
        Pe = Point(x=max(self.Ps.x, self.Pe.x), y=max(self.Ps.y, self.Pe.y))

        self.BB = BoundingBox(Ps=Ps, Pe=Pe)
        
    def colinear(self, other):
        """
        Check if two lines with same point self.Pe==other.Ps are colinear. For Point
        it check if the point is colinear with the line self.
        @param other: the possibly colinear line
        """
        if isinstance(other, LineGeo):
            return ((self.Ps.ccw(self.Pe, other.Pe) == 0) and
                    (self.Ps.ccw(self.Pe, other.Ps) == 0))
        elif isinstance(other, Point):
            """
            Return true iff a, b, and c all lie on the same line."
            """
            return self.Ps.ccw(self.Pe, other) == 0
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
            if self.Ps < self.Pe:
                A = self.Ps
                B = self.Pe
            else:
                A = self.Pe
                B = self.Ps
            if other.Ps < self.Pe:
                C = other.Ps
                D = other.Pe
            else:
                C = other.Pe
                D = other.Ps

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
        elif self.Ps == other.Ps:
            return True
        elif self.Pe == other.Ps:
            return True
        elif self.Ps == other.Pe:
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

        return min(self.distance_l_p(other.Ps),
                   self.distance_l_p(other.Pe),
                   other.distance_l_p(self.Ps),
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
            elif self.distance(other.Ps) < self.distance(other.Pe):
                    return self.get_nearest_point(other.Ps).distance(other.Ps)
            else:
                    return self.get_nearest_point(other.Pe).distance(other.Pe)

        # logger.debug("Nearest Point is Inside of arc")
        # logger.debug("self.distance(other.Ps): %s, self.distance(other.Pe): %s" %(self.distance(other.Ps),self.distance(other.Pe)))
        # The Line may be inside of the ARc or cross it
        if self.distance(other.Ps) < self.distance(other.Pe):
            dis_min = self.distance(other.Ps)
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
        else:
            dis_min = self.distance(other.Pe)
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))

        if ((other.PointAng_withinArc(self.Ps)) and
            abs(other.r - other.O.distance(self.Ps)) < dis_min):
            dis_min = abs(other.r - other.O.distance(self.Ps))
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
        d = self.Pe - self.Ps
        v = Point - self.Ps

        t = d.dotProd(v)

        if t <= 0:
            # our Point is lying "behind" the segment
            # so end Point 1 is closest to Point and distance is length of
            # vector from end Point 1 to Point.
            return self.Ps.distance(Point)
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


        dx1 = self.Pe.x - self.Ps.x
        dy1 = self.Pe.y - self.Ps.y

        dx2 = other.Pe.x - other.Ps.x
        dy2 = other.Pe.y - other.Ps.y

        dax = self.Ps.x - other.Ps.x
        day = self.Ps.y - other.Ps.y

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

        return Point(x=self.Ps.x + v1 * dx1,
                          y=self.Ps.y + v1 * dy1)

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

        Ldx = self.Pe.x - self.Ps.x
        Ldy = self.Pe.y - self.Ps.y

        # Mitternachtsformel zum berechnen der Nullpunkte der quadratischen
        # Gleichung
        a = pow(Ldx, 2) + pow(Ldy, 2)
        b = 2 * Ldx * (self.Ps.x - Arc.O.x) + 2 * Ldy * (self.Ps.y - Arc.O.y)
        c = pow(self.Ps.x - Arc.O.x, 2) + pow(self.Ps.y - Arc.O.y, 2) - pow(Arc.r, 2)
        root = pow(b, 2) - 4 * a * c

        # If the value under the sqrt is negative there is no intersection.
        if root < 0 or a == 0.0:
            return None

        v1 = (-b + sqrt(root)) / (2 * a)
        v2 = (-b - sqrt(root)) / (2 * a)

        Pi1 = Point(x=self.Ps.x + v1 * Ldx,
                       y=self.Ps.y + v1 * Ldy)

        Pi2 = Point(x=self.Ps.x + v2 * Ldx,
               y=self.Ps.y + v2 * Ldy)

        Pi1.v = Arc.dif_ang(Arc.Ps, Pi1, Arc.ext) / Arc.ext
        Pi2.v = Arc.dif_ang(Arc.Ps, Pi2, Arc.ext) / Arc.ext

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
        if min_dis == self.distance_l_p(other.Ps):
            return self.get_nearest_point_l_p(other.Ps)
        elif min_dis == self.distance_l_p(other.Pe):
            return self.get_nearest_point_l_p(other.Pe)
        elif min_dis == other.distance_l_p(self.Ps):
            return self.Ps
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
            elif self.distance(other.Ps) < self.distance(other.Pe):
                if ret == "line":
                    return self.get_nearest_point(other.Ps)
                elif ret == "arc":
                    return other.Ps
            else:
                if ret == "line":
                    return self.get_nearest_point(other.Pe)
                elif ret == "art":
                    return other.Pe

        # logger.debug("Nearest Point is Inside of arc")
        # logger.debug("self.distance(other.Ps): %s, self.distance(other.Pe): %s" %(self.distance(other.Ps),self.distance(other.Pe)))
        # The Line may be inside of the ARc or cross it
        if self.distance(other.Ps) < self.distance(other.Pe):
            Pnearest = self.get_nearest_point(other.Ps)
            Pnother = other.Ps
            dis_min = self.distance(other.Ps)
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
        else:
            Pnearest = self.get_nearest_point(other.Pe)
            Pnother = other.Pe
            dis_min = self.distance(other.Pe)
            # logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))

        if ((other.PointAng_withinArc(self.Ps)) and
            abs(other.r - other.O.distance(self.Ps)) < dis_min):

            Pnearest = self.Ps
            Pnother = other.O.get_arc_point(other.O.norm_angle(Pnearest), r=other.r)
            dis_min = abs(other.r - other.O.distance(self.Ps))
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

        if self.Ps.distance(other) < self.Pe.distance(other):
            return self.Ps
        else:
            return self.Pe

    def get_start_end_points(self, start_point, angles=None):
        if start_point:
            if angles is None:
                return self.Ps
            elif angles:
                return self.Ps, self.Ps.norm_angle(self.Pe)
            else:
                return self.Ps, (self.Pe - self.Ps).unit_vector()
        else:
            if angles is None:
                return self.Pe
            elif angles:
                return self.Pe, self.Pe.norm_angle(self.Ps)
            else:
                return self.Pe, (self.Pe - self.Ps).unit_vector()
    
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
        A = self.Ps
        B = self.Pe
        C = other.Ps
        D = other.Pe
        return A.ccw(C, D) != B.ccw(C, D) and A.ccw(B, C) != A.ccw(B, D)

    def intersect_l_p(self, Point):
        """
        Check if Point is colinear and within the Line
        @param Point: A Point which will be checked
        @return: True if point Point intersects the line segment from Ps to Pe.
        Refer to http://stackoverflow.com/questions/328107/how-can-you-determine-a-point-is-between-two-other-points-on-a-line-segment
        """
        # (or the degenerate case that all 3 points are coincident)
        # logger.debug(self.colinear(Point))
        return (self.colinear(Point)
                and (self.within(self.Ps.x, Point.x, self.Pe.x)
                     if self.Ps.x != self.Pe.x else
                     self.within(self.Ps.y, Point.y, self.Pe.y)))

    def isHit(self, caller, xy, tol):
        return xy.distance2_to_line(self.Ps, self.Pe) <= tol**2
    
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
            if self.Ps < self.Pe:
                newPs = min(self.Ps, other.Ps, other.Pe)
                newPe = max(self.Pe, other.Ps, other.Pe)
            else:
                newPs = max(self.Ps, other.Ps, other.Pe)
                newPe = min(self.Pe, other.Ps, other.Pe)
            return [LineGeo(newPs, newPe)]
        else:
            return [self, other]

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent. This
        is done for rotating and scaling purposes
        """
        Ps = self.Ps.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)

        self.abs_geo = LineGeo(Ps=Ps, Pe=Pe)

    def make_path(self, caller, drawHorLine):
        drawHorLine(caller, self.Ps, self.Pe)
        self.topLeft = deepcopy(self.Ps)
        self.bottomRight = deepcopy(self.Ps)
        self.topLeft.detTopLeft(self.Pe)
        self.bottomRight.detBottomRight(self.Pe)
        
    def perpedicular_on_line(self, other):
        """
        This function calculates the perpendicular point on a line (or ray of line)
        with the shortest distance to the point given with other
        @param other: The point to be perpendicular to
        @return: A point which is on line and perpendicular to Point other
        @see: http://stackoverflow.com/questions/1811549/perpendicular-on-a-line-from-a-given-point
        """
        # first convert line to normalized unit vector
        unit_vector = self.Ps.unit_vector(self.Pe)

        # translate the point and get the dot product
        lam = ((unit_vector.x * (other.x - self.Ps.x))
                + (unit_vector.y * (other.y - self.Ps.y)))
        return Point(x=(unit_vector.x * lam) + self.Ps.x,
                     y=(unit_vector.y * lam) + self.Ps.y)

    def reverse(self):
        """ 
        Reverses the direction of the arc (switch direction).
        """
        self.Ps, self.Pe = self.Pe, self.Ps
        if self.abs_geo:
            self.abs_geo.reverse()

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
            Li1 = LineGeo(Ps=self.Ps, Pe=ipoint)
            Li2 = LineGeo(Ps=ipoint, Pe=self.Pe)
            return [Li1, Li2]        
        else:
            return [self]

    def to_short_string(self):
        return "(%f, %f) -> (%f, %f)" % (self.Ps.x, self.Ps.y, self.Pe.x, self.Pe.y)

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
            new_line = LineGeo(self.Ps, newPoint)
            new_line.end_normal = self.end_normal
            new_line.start_normal = self.start_normal
            return new_line
        
    def update_start_end_points(self, start_point, value):
        prv_ang = self.Ps.norm_angle(self.Pe)
        if start_point:
            self.Ps = value
        else:
            self.Pe = value
        new_ang = self.Ps.norm_angle(self.Pe)

        if 2 * abs(((prv_ang - new_ang) + pi) % (2 * pi) - pi) >= pi:
            # seems very unlikely that this is what you want - the direction changed (too drastically)
            self.Ps, self.Pe = self.Pe, self.Ps

        self.length = self.Ps.distance(self.Pe)

    def Write_GCode(self, PostPro):
        """
        Writes the GCODE for a Line.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        Ps = self.get_start_end_points(True)
        Pe = self.get_start_end_points(False)
        return PostPro.lin_pol_xy(Ps, Pe)


 







