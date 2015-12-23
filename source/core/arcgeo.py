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

from __future__ import absolute_import
from __future__ import division

from math import sqrt, sin, cos, pi, degrees, ceil, floor
from copy import deepcopy


from core.point import Point
#from core.linegeo import LineGeo
from core.boundingbox import BoundingBox
import globals.globals as g

from globals.six import text_type
import globals.constants as c
if c.PYQT5notPYQT4:
    from PyQt5 import QtCore
else:
    from PyQt4 import QtCore

import logging
logger = logging.getLogger("core.arcgeo")

eps=1e-12

class ArcGeo(object):
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """
    def __init__(self, Ps=None, Pe=None, O=None, r=1,
                 s_ang=None, e_ang=None, direction=1, drag=False):
        """
        Standard Method to initialize the ArcGeo. Not all of the parameters are
        required to fully define a arc. e.g. Ps and Pe may be given or s_ang and
        e_ang
        @param Ps: The Start Point of the arc
        @param Pe: the End Point of the arc
        @param O: The center of the arc
        @param r: The radius of the arc
        @param s_ang: The Start Angle of the arc
        @param e_ang: the End Angle of the arc
        @param direction: The arc direction where 1 is in positive direction
        """
        self.type = "ArcGeo"
        self.Ps = Ps
        self.Pe = Pe
        self.O = O
        self.r = abs(r)
        self.s_ang = s_ang
        self.e_ang = e_ang
        self.drag = drag

        # Get the Circle center point with known Start and End Points
        if self.O is None:

            if self.Ps is not None and\
               self.Pe is not None and\
               direction is not None:

                arc = self.Pe.norm_angle(self.Ps) - pi / 2
                m = self.Pe.distance(self.Ps) / 2

                if abs(self.r - m) < g.config.fitting_tolerance:
                    lo = 0.0
                else:
                    lo = sqrt(pow(self.r, 2) - pow(m, 2))

                d = -1 if direction < 0 else 1

                self.O = self.Ps + (self.Pe - self.Ps) / 2
                self.O.y += lo * sin(arc) * d
                self.O.x += lo * cos(arc) * d

            # Compute center point
            elif self.s_ang is not None:
                self.O.x = self.Ps.x - self.r * cos(self.s_ang)
                self.O.y = self.Ps.y - self.r * sin(self.s_ang)
            else:
                logger.error(self.tr("Missing value for Arc Geometry"))

        # Calculate start and end angles
        if self.s_ang is None:
            self.s_ang = self.O.norm_angle(self.Ps)
        if self.e_ang is None:
            self.e_ang = self.O.norm_angle(self.Pe)

        self.ext = self.dif_ang(self.Ps, self.Pe, direction)

        self.length = self.r * abs(self.ext)

        self.calc_bounding_box()

        self.topLeft = None
        self.bottomRight = None

        self.abs_geo = None

    def __deepcopy__(self, memo):
        return ArcGeo(deepcopy(self.Ps, memo),
                      deepcopy(self.Pe, memo),
                      deepcopy(self.O, memo),
                      deepcopy(self.r, memo),
                      deepcopy(self.s_ang, memo),
                      deepcopy(self.e_ang, memo),
                      deepcopy(self.ext, memo))

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """
        return ("\nArcGeo(Ps=Point(x=%s ,y=%s), \n" % (self.Ps.x, self.Ps.y)) + \
               ("Pe=Point(x=%s, y=%s),\n" % (self.Pe.x, self.Pe.y)) + \
               ("O=Point(x=%s, y=%s),\n" % (self.O.x, self.O.y)) + \
               ("s_ang=%s,e_ang=%s,\n" % (self.s_ang, self.e_ang)) + \
               ("r=%s, \n" % self.r) + \
               ("ext=%s)" % self.ext)

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

        Ps = Point(x=self.O.x - self.r, y=self.O.y - self.r)
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
            Pe.x = max(self.Ps.x, self.Pe.x)

        # If the positive Y Axis is crossed
        if not(self.wrap(s_ang - pi / 2, 0) >= self.wrap(e_ang - pi / 2, 1)):
            Pe.y = max(self.Ps.y, self.Pe.y)

        # If the negative X Axis is crossed
        if not(self.wrap(s_ang - pi, 0) >= self.wrap(e_ang - pi, 1)):
            Ps.x = min(self.Ps.x, self.Pe.x)

        # If the negative Y is crossed
        if not(self.wrap(s_ang - 1.5 * pi, 0) >= 
                self.wrap(e_ang - 1.5 * pi, 1)):
            Ps.y = min(self.Ps.y, self.Pe.y)

        self.BB = BoundingBox(Ps=Ps, Pe=Pe)

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
    
    
            #     def dif_ang(self, Ps, Pe, direction):
            #         """
            #         Calculated the angle between Pe and Ps with respect to the origin
            #         @param Ps: the start Point of the arc
            #         @param Pe: the end Point of the arc
            #         @param direction: the direction of the arc
            #         @return: Returns the angle between -2* pi and 2 *pi for the arc,
            #         0 excluded - we got a complete circle
            #         """
            #         dif_ang = (self.O.norm_angle(Pe) - self.O.norm_angle(Ps)) % (-2 * pi)
            # 
            #         if direction > 0:
            #             dif_ang += 2 * pi
            #         elif dif_ang == 0:
            #             dif_ang = -2 * pi
            # 
            #         return dif_ang

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
        from core.linegeo import LineGeo
        
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
            elif other.distance(self.Ps) < other.distance(self.Pe):
                    return other.distance(self.Ps)
            else:
                    return other.distance(self.Pe)

        # logger.debug("Nearest Point is Inside of arc")
        # logger.debug("self.distance(other.Ps): %s, self.distance(other.Pe): %s" %(self.distance(other.Ps),self.distance(other.Pe)))
        # The Line may be inside of the ARc or cross it
        if other.distance(self.Ps) < other.distance(self.Pe):
            dis_min = other.distance(self.Ps)
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
        from core.linegeo import LineGeo
        
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
            Pi1 = Point(x=self.Ps.x, y=self.Ps.y)
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

        Pi1.v1 = self.dif_ang(self.Ps, Pi1, self.ext) / self.ext
        Pi1.v2 = other.dif_ang(other.Ps, Pi1, other.ext) / other.ext

        Pi2 = Point(x=xbase - (other.O.y - self.O.y) / \
                         (2 * pow(O_dis, 2)) * root,
                    y=ybase + (other.O.x - self.O.x) / \
                    (2 * pow(O_dis, 2)) * root)

        Pi2.v1 = self.dif_ang(self.Ps, Pi2, self.ext) / self.ext
        Pi2.v2 = other.dif_ang(other.Ps, Pi2, other.ext) / other.ext


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
        from core.linegeo import LineGeo
        
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
        elif self.Ps.distance(other) < self.Pe.distance(other):
            return self.Ps
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
            if self.distance(other.Ps) < self.distance(other.Pe):
                if ret == "self":
                    return self.O.get_arc_point(self.O.norm_angle(other.Ps), r=self.r)
                elif ret == "other":
                    return other.Ps
            else:
                if ret == "self":
                    return self.O.get_arc_point(self.O.norm_angle(other.Pe), r=self.r)
                elif ret == "other":
                    return other.Pe
        # If Nearest point is on other Arc Segment but not self
        elif other.PointAng_withinArc(self.O):
            if other.distance(self.Ps) < other.distance(self.Pe):
                if ret == "self":
                    return self.Ps
                elif ret == "other":
                    return other.O.get_arc_point(other.O.norm_angle(self.Ps), r=other.r)
            else:
                if ret == "self":
                    return self.Pe
                elif ret == "other":
                    return other.O.get_arc_point(other.O.norm_angle(self.Pe), r=other.r)
        # If the min distance is not on any arc segemtn but other.Ps is nearer then other.Pe
        elif self.distance(other.Ps) < self.distance(other.Pe):
            if self.Ps.distance(other.Ps) < self.Pe.distance(other.Ps):
                if ret == "self":
                    return self.Ps
                elif ret == "other":
                    return other.Ps
            else:
                if ret == "self":
                    return self.Pe
                elif ret == "other":
                    return other.Ps
        else:
            if self.Ps.distance(other.Pe) < self.Pe.distance(other.Pe):
                if ret == "self":
                    return self.Ps
                elif ret == "other":
                    return other.Pe
            else:
                if ret == "self":
                    return self.Pe
                elif ret == "other":
                    return other.Pe

            #         #logger.debug("Nearest Point is Inside of arc")
            #         #logger.debug("self.distance(other.Ps): %s, self.distance(other.Pe): %s" %(self.distance(other.Ps),self.distance(other.Pe)))
            #         # The Line may be inside of the ARc or cross it
            #         if self.distance(other.Ps)<self.distance(other.Pe):
            #             Pnearest=self.get_nearest_point(other.Ps)
            #             Pnother=other.Ps
            #             dis_min=self.distance(other.Ps)
            #             #logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
            #         else:
            #             Pnearest=self.get_nearest_point(other.Pe)
            #             Pnother=other.Pe
            #             dis_min=self.distance(other.Pe)
            #             #logger.debug("Pnearest: %s, distance: %s" %(Pnearest, dis_min))
            #
            #         if ((other.PointAng_withinArc(self.Ps)) and
            #             abs(other.r-other.O.distance(self.Ps)) < dis_min):
            #
            #             Pnearest=self.Ps
            #             Pnother=other.O.get_arc_point(other.O.norm_angle(Pnearest),r=other.r)
            #             dis_min=abs(other.r-other.O.distance(self.Ps))
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

    def get_point_from_start(self, i, segments):
        ang = self.s_ang + i * self.ext / segments
        return self.O.get_arc_point(ang, self.r)
    
    def get_start_end_points(self, start_point, angles=None):
        if start_point:
            if angles is None:
                return self.Ps
            elif angles:
                return self.Ps, self.s_ang + pi/2 * self.ext / abs(self.ext)
            else:
                direction = (self.O - self.Ps).unit_vector()
                direction = -direction if self.ext >= 0 else direction
                return self.Ps, Point(-direction.y, direction.x)
        else:
            if angles is None:
                return self.Pe
            elif angles:
                return self.Pe, self.e_ang - pi/2 * self.ext / abs(self.ext)
            else:
                direction = (self.O - self.Pe).unit_vector()
                direction = -direction if self.ext >= 0 else direction
                return self.Pe, Point(-direction.y, direction.x)

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
        from core.linegeo import LineGeo
        
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

    def isHit(self, caller, xy, tol):
        tol2 = tol**2
        segments = int(abs(degrees(self.ext)) // 3 + 1)
        Ps = self.O.get_arc_point(self.s_ang, self.r)
        for i in range(1, segments + 1):
            Pe = self.get_point_from_start(i, segments)
            if xy.distance2_to_line(Ps, Pe) <= tol2:
                return True
            Ps = Pe
        return False  
      
    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent. This
        is done for rotating and scaling purposes
        """
        Ps = self.Ps.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)
        O = self.O.rot_sca_abs(parent=parent)
        r = self.scaled_r(self.r, parent)

        direction = 1 if self.ext > 0.0 else -1

        if parent is not None and parent.sca[0] * parent.sca[1] < 0.0:
            direction *= -1

        self.abs_geo = ArcGeo(Ps=Ps, Pe=Pe, O=O, r=r, direction=direction)
    
    def make_path(self, caller, drawHorLine):
        segments = int(abs(degrees(self.ext)) // 3 + 1)
        Ps = self.O.get_arc_point(self.s_ang, self.r)
        self.topLeft = deepcopy(Ps)
        self.bottomRight = deepcopy(Ps)
        for i in range(1, segments + 1):
            Pe = self.get_point_from_start(i, segments)
            drawHorLine(caller, Ps, Pe)
            self.topLeft.detTopLeft(Pe)
            self.bottomRight.detBottomRight(Pe)
            Ps = Pe

    def PointAng_withinArc(self, Point):
        """
        Check if the angle defined by Point is within the span of the arc.
        @param Point: The Point which angle to be checked 
        @return: True or False
        """
        v = self.dif_ang(self.Ps, Point, self.ext) / self.ext
        return v >= 0.0 and v <= 1.0

    def reverse(self):
        """ 
        Reverses the direction of the arc (switch direction).
        """
        self.Ps, self.Pe = self.Pe, self.Ps
        self.s_ang, self.e_ang = self.e_ang, self.s_ang
        self.ext = -self.ext
        if self.abs_geo:
            self.abs_geo.reverse()

    def scaled_r(self, r, parent):
        """
        Scales the radius based on the scale given in its parents. This is done
        recursively.
        @param r: The radius which shall be scaled
        @param parent: The parent Entity (Instance: EntityContentClass)
        @return: The scaled radius
        """
        # Rekursive Schleife falls mehrfach verschachtelt.
        # Recursive loop if nested.
        if parent is not None:
            r *= parent.sca[0]
            r = self.scaled_r(r, parent.parent)

        return r
    
    def split_into_2geos(self, ipoint=Point()):
        """
        Splits the given geometry into 2 geometries. The
        geometry will be splitted at ipoint.
        @param ipoint: The Point where the intersection occures
        @return: A list of 2 ArcGeo's will be returned.
        """


        # Generate the 2 geometries and their bounding boxes.
        Arc1 = ArcGeo(Ps=self.Ps, Pe=ipoint, r=self.r,
                       O=self.O, direction=self.ext)

        Arc2 = ArcGeo(Ps=ipoint, Pe=self.Pe, r=self.r,
                       O=self.O, direction=self.ext)
        return [Arc1, Arc2]

    def toShortString(self):
        return "(%f, %f) -> (%f, %f)" % (self.Ps.x, self.Ps.y, self.Pe.x, self.Pe.y)
    
    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return text_type(QtCore.QCoreApplication.translate('ArcGeo',
                                                           string_to_translate))
    
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

        # logger.debug("I'm getting trimmed: %s, %s, %s, %s" % (self, Point, dir, rev_norm))
        newPoint = self.O.get_arc_point(self.O.norm_angle(Point), r=self.r)
        new_normal = newPoint.unit_vector(self.O, r=1)
        
        # logger.debug(newPoint)
        [Arc1, Arc2] = self.split_into_2geos(newPoint)
         
        if dir == -1:
            new_arc = Arc1
            if hasattr(self, "end_normal"):
                # new_arc.end_normal = self.end_normal
                # new_arc.start_normal = new_normal
                
                new_arc.end_normal = new_normal
                new_arc.start_normal = self.start_normal
            # logger.debug(new_arc)
            return new_arc
        else:
            new_arc = Arc2
            if hasattr(self, "end_normal"):
                # new_arc.end_normal = new_normal
                # new_arc.start_normal = self.start_normal
                
                new_arc.end_normal = self.end_normal
                new_arc.start_normal = new_normal
            # logger.debug(new_arc)
            return new_arc
        # return self
        
    def update_start_end_points(self, start_point, value):
        prv_dir = self.ext
        if start_point:
            self.Ps = value
            self.s_ang = self.O.norm_angle(self.Ps)
        else:
            self.Pe = value
            self.e_ang = self.O.norm_angle(self.Pe)

        self.ext = self.dif_ang(self.Ps, self.Pe, self.ext)

        if 2 * abs(((prv_dir - self.ext) + pi) % (2 * pi) - pi) >= pi:
            # seems very unlikely that this is what you want - the direction changed (too drastically)
            self.Ps, self.Pe = self.Pe, self.Ps
            self.s_ang, self.e_ang = self.e_ang, self.s_ang
            self.ext = self.dif_ang(self.Ps, self.Pe, prv_dir)

        self.length = self.r * abs(self.ext)
        
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

    def Write_GCode(self, PostPro=None):
        """
        Writes the GCODE for an Arc.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        Ps, s_ang = self.get_start_end_points(True, True)
        Pe, e_ang = self.get_start_end_points(False, True)

        O = self.O
        r = self.r
        IJ = O - Ps

        # If the radius of the element is bigger than the max, radius export the element as an line.
        if r > PostPro.vars.General["max_arc_radius"]:
            string = PostPro.lin_pol_xy(Ps, Pe)
        else:
            if self.ext > 0:
                string = PostPro.lin_pol_arc("ccw", Ps, Pe, s_ang, e_ang, r, O, IJ,self.ext)
            elif self.ext < 0 and PostPro.vars.General["export_ccw_arcs_only"]:
                string = PostPro.lin_pol_arc("ccw", Pe, Ps, e_ang, s_ang, r, O, O - Pe,self.ext)
            else:
                string = PostPro.lin_pol_arc("cw", Ps, Pe, s_ang, e_ang, r, O, IJ,self.ext)
        return string


















