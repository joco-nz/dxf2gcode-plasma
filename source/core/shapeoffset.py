
# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohl�ffel
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

from math import sin, cos, pi, sqrt
from copy import deepcopy
import logging

import globals.globals as g
from core.linegeo import LineGeo
from core.arcgeo import ArcGeo
from core.point import Point
from core.shape import Geos
from core.shape import Shape

logger = logging.getLogger('core.shapeoffset')

class offShapeClass(Shape):
    """
    This Class is used to generate The fofset aof a shape according to:
    "A pair-wise offset Algorithm for 2D point sequence curve"
    http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.101.8855
    """
    def __init__(self, parent=Shape(), offset=1, offtype='in'):
        """ 
        Standard method to initialize the class
        @param closed: Gives information about the shape, when it is closed this
        value becomes 1. Closed means it is a Polygon, otherwise it is a Polyline
        @param length: The total length of the shape including all geometries
        @param geos: The list with all geometries included in the shape. May 
        also contain arcs. These will be reflected by multiple lines in order 
        to easy calclations.
        """

        super(offShapeClass, self).__init__(nr=parent.nr,
                                            closed=parent.closed,
                                            geos=deepcopy(parent.geos))

        
        self.offset = offset
        self.offtype = offtype
        self.segments = []
        self.rawoff = []

        self.make_shape_ccw()
        self.join_colinear_lines()

        self.make_segment_types()
        nextConvexPoint = [e for e in self.segments if isinstance(e, ConvexPoint)]
        # logger.debug(nextConvexPoint)
        # nextConvexPoint=[nextConvexPoint[31]]
        self.counter = 0

        while len(nextConvexPoint):  # [self.convex_vertex[-1]]:
            convex_vertex_nr = self.segments.index(nextConvexPoint[0])
            # logger.debug(len(self.segments))
            # logger.debug("convex_vertex_nr: %s" % convex_vertex_nr)
                 
            forward, backward = self.PairWiseInterferenceDetection(convex_vertex_nr + 1, convex_vertex_nr - 1)
            # logger.debug("forward: %s, backward: %s" % (forward, backward))
 
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
 
            
 
 
 
            if iPoint is None:
                logger.debug("fw_rawoff_seg: %s, bw_rawoff_seg: %s" %(fw_rawoff_seg,bw_rawoff_seg))
            # logger.debug("forward: %s, backward: %s, iPoint: %s =====================================" %(forward,backward,iPoint))
                logger.error("No intersection found?!")
                raise Exception("No intersection found?!")
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
        
    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        
        return "\nnr:          %i" % self.nr +\
               "\nclosed:      %s" % self.closed +\
               "\ngeos:        %s" % self.geos +\
               "\nofftype:     %s" % self.offtype +\
               "\noffset:      %s" % self.offset +\
               "\nsegments:    %s" % self.segments +\
               "\nrawoff       %s" % self.rawoff

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
            Ps = seg.Ps + seg.start_normal * offset
            Pe = seg.Pe + seg.end_normal * offset
            return LineGeo(Ps, Pe)

        elif isinstance(seg, Point):
            Ps = seg + seg.start_normal * offset
            Pe = seg + seg.end_normal * offset

            return ArcGeo(Ps=Ps, Pe=Pe, O=deepcopy(seg), r=self.offset, direction=offset)
        elif isinstance(seg, ArcGeo):
            Ps = seg.Ps + seg.start_normal * offset
            Pe = seg.Pe + seg.end_normal * offset

            if seg.ext > 0:
                return ArcGeo(Ps=Ps, Pe=Pe, O=seg.O, r=seg.r + offset, direction=seg.ext)
            else:
                return ArcGeo(Ps=Ps, Pe=Pe, O=seg.O, r=seg.r - offset, direction=seg.ext)

        elif isinstance(seg, ConvexPoint):
            Ps = seg + seg.start_normal * offset
            Pe = seg + seg.end_normal * offset
            return ArcGeo(Ps=Ps, Pe=Pe, O=deepcopy(seg), r=self.offset, direction=offset)
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
                    geo1.start_normal = geo1.Ps.get_normal_vector(geo1.Pe)
                    geo1.end_normal = geo1.Ps.get_normal_vector(geo1.Pe)
                else:
                    geo1.start_normal = geo1.O.unit_vector(geo1.Ps, r = 1)
                    geo1.end_normal = geo1.O.unit_vector(geo1.Pe, r = 1)
                    if geo1.ext < 0:
                        geo1.start_normal = geo1.start_normal * -1
                        geo1.end_normal = geo1.end_normal * -1

            if isinstance(geo2, LineGeo):
                geo2.start_normal = geo2.Ps.get_normal_vector(geo2.Pe)
                geo2.end_normal = geo2.Ps.get_normal_vector(geo2.Pe)
            elif isinstance(geo2, ArcGeo):
                geo2.start_normal = geo2.O.unit_vector(geo2.Ps, r = 1)
                geo2.end_normal = geo2.O.unit_vector(geo2.Pe, r = 1)
                if geo2.ext < 0:
                        geo2.start_normal = geo2.start_normal * -1
                        geo2.end_normal = geo2.end_normal * -1

            # logger.debug("geo1: %s, geo2: %s" % (geo1, geo2))
            # logger.debug("geo1.end_normal: %s, geo2.start_normal: %s" % (geo1.end_normal, geo2.start_normal))

            # If it is a reflex vertex add a reflex segemnt (single point)

            # Add a Reflex Point if radius becomes below zero.

#             if isinstance(geo2, ArcGeo):
#                 logger.debug(geo2)
#                 geo2_off = self.make_rawoff_seg(geo2)
#                 logger.debug(geo2_off)
#
            if ((isinstance(geo2, ArcGeo)) and
                ((self.offtype == "out" and geo2.ext > 0) or
                 (self.offtype == "in" and geo2.ext < 0)) and
                ((geo2.r - abs(self.offset)) <= 0.0)):

                newgeo2 = ConvexPoint(geo2.O.x, geo2.O.y)
                newgeo2.start_normal = geo2.start_normal
                newgeo2.end_normal = geo2.end_normal
                geo2 = newgeo2

#             logger.debug(geo1.Pe.ccw(geo1.Pe + geo1.end_normal,
#                              geo1.Pe + geo1.end_normal +
#                              geo2.start_normal))
#             logger.debug(geo1)
#             logger.debug(geo2)
#             logger.debug(geo1.end_normal)
#             logger.debug(geo2.start_normal)
            if (((geo1.Pe.ccw(geo1.Pe + geo1.end_normal,
                              geo1.Pe + geo1.end_normal +
                              geo2.start_normal) == 1) and
                 self.offtype == "in") or
                (geo1.Pe.ccw(geo1.Pe + geo1.end_normal,
                             geo1.Pe + geo1.end_normal +
                             geo2.start_normal) == -1 and
                 self.offtype == "out") or
                 (geo1.Pe.ccw(geo1.Pe + geo1.end_normal,
                             geo1.Pe + geo1.end_normal +
                             geo2.start_normal) == 0)):

                # logger.debug("reflex")

                geo1.Pe.start_normal = geo1.end_normal
                geo1.Pe.end_normal = geo2.start_normal
                self.segments += [geo1.Pe, geo2]


            # Add the linear segment which is a line connecting 2 vertices
            else:
                # logger.debug("convex")
                self.segments += [ConvexPoint(geo1.Pe.x, geo1.Pe.y), geo2]
        self.segments_plot = deepcopy(self.segments)

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
            Pe = segment1.Ps
        elif isinstance(segment1, ConvexPoint):
            return False
        elif isinstance(segment1, Point):
            Pe = segment1
        elif isinstance(segment1, ArcGeo) and dir == 1:
            Pe = segment1.Pe
        elif isinstance(segment1, ArcGeo) and dir == -1:
            Pe = segment1.Ps
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
                                            Ps=Pe, Pe=Pe ,
                                            s_ang=0, e_ang=2 * pi, r=self.offset)]
        else:
            # logger.debug(Pe)
            # logger.debug(segment1)
            # logger.debug(segment1.start_normal)
            distance = segment2.distance(Pe + segment1.start_normal * offset)
            self.interferingshapes += [LineGeo(Pe, Pe + segment1.start_normal * offset),
                                     segment2,
                                     ArcGeo(O=Pe + segment1.start_normal * offset,
                                            Ps=Pe, Pe=Pe,
                                            s_ang=0, e_ang=2 * pi, r=self.offset)]

        # logger.debug("Full distance: %s" % distance)


        # If the distance from the Segment to the Center of the Tangential Circle
        # is smaller then the radius we have an intersection
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

        # offGeo=LineGeo(Ps,Pe)
        # logger.debug(segment2)
        # logger.debug(offGeo)
        # logger.debug("Partly distance: %s" % segment2.distance(offGeo))
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

        # logger.debug("\nChecking: segment1: %s, \nsegment2: %s" % (segment1, segment2))

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

        # logger.debug("Start Status: L1_status: %s,L2_status: %s" % (L1_status, L2_status))

        return [L1_status, L2_status]

    def PairWiseInterferenceDetection(self, forward, backward,):
        """
        Returns the first forward and backward segment nr. for which both
        interfering conditions are partly.
        @param foward: The nr of the first forward segment
        @param backward: the nr. of the first backward segment
        @return: forward, backward
        """
        val = 2000
        # self.counter = 0
        L1_status, L2_status = "full", "full"
        # Repeat until we reached the Partial-interfering-relation
        while not(L1_status == "partial" and L2_status == "partial"):
            self.interferingshapes = []
            self.counter += 1

            if forward >= len(self.segments):
                forward = 0

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
        if backward > forward:
            pop_range = self.segments[backward + 1:len(self.segments)] 
            pop_range += self.segments[0:forward]
        elif backward<0:
            pop_range = self.segments[len(self.segments)+backward + 1:len(self.segments)] 
            pop_range += self.segments[0:forward]
        else:
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
            geo.iPoints = []
            y_val = (geo.BB.Ps.y + geo.BB.Pe.y) / 2

            geo.neighbors = []
            geo.nr = geo_nr
            geo.Point = Point(x=geo.BB.Ps.x, y=y_val)

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

            y_val = (geo.BB.Ps.y + geo.BB.Pe.y) / 2
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
          
    def cmp_asscending_arc(self, P1, P2):
        """
        Compare Function for the sorting of Intersection Points on one common ARC
        @param P1: The first Point to be compared
        @param P2: The secon Point to be compared
        @return: 1 if the distance to the start point of P1 is bigger
        """  
        
        # The angle between startpoint and where the intersection occures
        d_ang1 = (self.O.norm_angle(P1) - self.s_ang) % (2 * pi)
        d_ang2 = (self.O.norm_angle(P2) - self.s_ang) % (2 * pi)
        
        # Correct by 2*pi if the direction is wrong
        if self.ext < 0.0:
            d_ang1 -= 2 * pi
            d_ang2 -= 2 * pi
                
        if d_ang1 > d_ang2:
            return 1
        elif d_ang1 == d_ang2:
            return 0
        else:
            return -1
        
    def cmp_asscending_line(self, P1, P2):
        """
        Compare Function for the sorting of Intersection points on one common LINE
        @param P1: The first Point to be compared
        @param P2: The secon Point to be compared
        @return: 1 if the distance to the start point of P1 is bigger
        """  
        d1 = P1.distance(self.Ps)
        d2 = P2.distance(self.Ps)
              
        if d1 > d2:
            return 1
        elif d1 == d2:
            return 0
        else:
            return -1

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
            
            iPoint.geo = [geo1, geo2]

            # if there is only one instersection
            if isinstance(iPoint, Point):
                self.found.append(iPoint)
                geo1.iPoints += [iPoint]
                geo2.iPoints += [iPoint]
                
                self.sweep_array.append(SweepElement(Point=iPoint, add=[], remove=[], swoop=[[geo1, geo2]]))

            else:
                self.found += iPoint
                geo1.iPoints += iPoint
                geo2.iPoints += iPoint
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
               
class ConvexPoint(Point):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


        Point.__init__(self, x=x, y=y)
