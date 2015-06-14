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

from math import sin, cos, pi, sqrt
from copy import deepcopy, copy
import logging

import Global.Globals as g
from Core.LineGeo import LineGeo
from Core.ArcGeo import ArcGeo
from Core.Point import Point
from Core.HoleGeo import HoleGeo


logger = logging.getLogger('Gui.StMove')


class StMove(object):
    """
    This Function generates the StartMove for each shape. It
    also performs the Plotting and Export of this moves. It is linked
    to the shape of its parent
    """
    def __init__(self, shape):
        self.shape = shape

        self.start, self.angle = self.shape.get_start_end_points(True, True)
        self.end = self.start

        self.geos = []

        self.make_start_moves()

    def append(self, geo):
        # we don't want to additional scale / rotate the stmove geo
        # so no geo.make_abs_geo(self.shape.parentEntity)
        geo.make_abs_geo()
        self.geos.append(geo)

    def make_start_moves(self):
        """
        This function called to create the start move. It will
        be generated based on the given values for start and angle.
        """
        self.geos = []

        self.make_own_cutter_compensation()
        return

        if g.config.machine_type == 'drag_knife':
            self.make_swivelknife_move()
            return

        # Get the start rad. and the length of the line segment at begin.
        start_rad = self.shape.parentLayer.start_radius

        # Get tool radius based on tool diameter.
        tool_rad = self.shape.parentLayer.getToolRadius()

        # Calculate the starting point with and without compensation.
        start = self.start
        angle = self.angle

        if self.shape.cut_cor == 40:
            self.append(RapidPos(start))

        # Cutting Compensation Left
        elif self.shape.cut_cor == 41:
            # Center of the Starting Radius.
            Oein = start.get_arc_point(angle + pi/2, start_rad + tool_rad)
            # Start Point of the Radius
            Pa_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            # Start Point of the straight line segment at begin.
            Pg_ein = Pa_ein.get_arc_point(angle + pi/2, start_rad)

            # Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.append(RapidPos(start_ein))

            # generate the Start Line and append it including the compensation.
            start_line = LineGeo(start_ein, Pa_ein)
            self.append(start_line)

            # generate the start rad. and append it.
            start_rad = ArcGeo(Ps=Pa_ein, Pe=start, O=Oein,
                               r=start_rad + tool_rad, direction=1)
            self.append(start_rad)

        # Cutting Compensation Right
        elif self.shape.cut_cor == 42:
            # Center of the Starting Radius.
            Oein = start.get_arc_point(angle - pi/2, start_rad + tool_rad)
            # Start Point of the Radius
            Pa_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            # Start Point of the straight line segment at begin.
            Pg_ein = Pa_ein.get_arc_point(angle - pi/2, start_rad)

            # Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.append(RapidPos(start_ein))

            # generate the Start Line and append it including the compensation.
            start_line = LineGeo(start_ein, Pa_ein)
            self.append(start_line)

            # generate the start rad. and append it.
            start_rad = ArcGeo(Ps=Pa_ein, Pe=start, O=Oein,
                               r=start_rad + tool_rad, direction=0)
            self.append(start_rad)

    def make_swivelknife_move(self):
        offset = self.shape.parentLayer.getToolRadius()
        dragAngle = self.shape.dragAngle

        startnorm = offset*Point(1, 0)  # TODO make knife direction a config setting
        prvend, prvnorm = Point(), Point()
        first = True

        for geo in self.shape.geos:
            if isinstance(geo, LineGeo):
                geo_b = deepcopy(geo.abs_geo)
                if first:
                    first = False
                    prvend = geo_b.Ps + startnorm
                    prvnorm = startnorm
                norm = offset * (geo_b.Pe - geo_b.Ps).unit_vector()
                geo_b.Ps += norm
                geo_b.Pe += norm
                if not prvnorm == norm:
                    direction = prvnorm.to3D().cross_product(norm.to3D()).z
                    swivel = ArcGeo(Ps=prvend, Pe=geo_b.Ps, r=offset, direction=direction)
                    swivel.drag = dragAngle < abs(swivel.ext)
                    self.append(swivel)
                self.append(geo_b)

                prvend = geo_b.Pe
                prvnorm = norm
            elif isinstance(geo, ArcGeo):
                geo_b = deepcopy(geo.abs_geo)
                if first:
                    first = False
                    prvend = geo_b.Ps + startnorm
                    prvnorm = startnorm
                if geo_b.ext > 0.0:
                    norma = offset*Point(cos(geo_b.s_ang+pi/2), sin(geo_b.s_ang+pi/2))
                    norme = Point(cos(geo_b.e_ang+pi/2), sin(geo_b.e_ang+pi/2))
                else:
                    norma = offset*Point(cos(geo_b.s_ang-pi/2), sin(geo_b.s_ang-pi/2))
                    norme = Point(cos(geo_b.e_ang-pi/2), sin(geo_b.e_ang-pi/2))
                geo_b.Ps += norma
                if norme.x > 0:
                    geo_b.Pe = Point(geo_b.Pe.x+offset/(sqrt(1+(norme.y/norme.x)**2)),
                                     geo_b.Pe.y+(offset*norme.y/norme.x)/(sqrt(1+(norme.y/norme.x)**2)))
                elif norme.x == 0:
                    geo_b.Pe = Point(geo_b.Pe.x,
                                     geo_b.Pe.y)
                else:
                    geo_b.Pe = Point(geo_b.Pe.x-offset/(sqrt(1+(norme.y/norme.x)**2)),
                                     geo_b.Pe.y-(offset*norme.y/norme.x)/(sqrt(1+(norme.y/norme.x)**2)))
                if prvnorm != norma:
                    direction = prvnorm.to3D().cross_product(norma.to3D()).z
                    swivel = ArcGeo(Ps=prvend, Pe=geo_b.Ps, r=offset, direction=direction)
                    swivel.drag = dragAngle < abs(swivel.ext)
                    self.append(swivel)
                prvend = geo_b.Pe
                prvnorm = offset*norme
                if -pi < geo_b.ext < pi:
                    self.append(ArcGeo(Ps=geo_b.Ps, Pe=geo_b.Pe, r=sqrt(geo_b.r**2+offset**2), direction=geo_b.ext))
                else:
                    geo_b = ArcGeo(Ps=geo_b.Ps, Pe=geo_b.Pe, r=sqrt(geo_b.r**2+offset**2), direction=-geo_b.ext)
                    geo_b.ext = -geo_b.ext
                    self.append(geo_b)
            # TODO support different geos, or disable them in the GUI
            # else:
            #     self.append(copy(geo))
        if not prvnorm == startnorm:
            direction = prvnorm.to3D().cross_product(startnorm.to3D()).z
            self.append(ArcGeo(Ps=prvend, Pe=prvend-prvnorm+startnorm, r=offset, direction=direction))

        self.geos.insert(0, RapidPos(self.geos[0].Ps))
        self.geos[0].make_abs_geo(self.shape.parentEntity)

    def make_own_cutter_compensation(self):
        toolwidth = self.shape.parentLayer.getToolRadius()

        geos = []

        if self.shape.closed:
            end, end_dir = self.shape.get_start_end_points(False, False)
            end_proj = Point(end_dir.y, -end_dir.x)
            prv_Pe = end + toolwidth * end_proj
        else:
            prv_Pe = None
        for geo_nr, geo in enumerate(self.shape.geos):
            start, start_dir = geo.get_start_end_points(True, False)
            end, end_dir = geo.get_start_end_points(False, False)
            start_proj = Point(start_dir.y, -start_dir.x)
            end_proj = Point(end_dir.y, -end_dir.x)
            Ps = start + toolwidth * start_proj
            Pe = end + toolwidth * end_proj
            if Ps == Pe:
                continue
            if prv_Pe:
                r = geo.abs_geo.Ps.distance(Ps)
                d = -(Ps - geo.abs_geo.Ps).to3D().cross_product((prv_Pe - geo.abs_geo.Ps).to3D()).z
                if d > 0 and prv_Pe != Ps:
                    geos.append(ArcGeo(Ps=prv_Pe, Pe=Ps, O=geo.abs_geo.Ps, r=r, direction=d))
                    geos[-1].geo_nr = geo_nr
                # else:
                #     geos.append(LineGeo(Ps=prv_Pe, Pe=Ps))
            if isinstance(geo, LineGeo):
                geos.append(LineGeo(Ps, Pe))
                geos[-1].geo_nr = geo_nr
            elif isinstance(geo, ArcGeo):
                O = geo.abs_geo.O
                r = O.distance(Ps)
                geos.append(ArcGeo(Ps=Ps, Pe=Pe, O=O, r=r, direction=geo.abs_geo.ext))
                geos[-1].geo_nr = geo_nr
            # TODO other geos are not supported disable them in gui for this option
            # else:
            #     geos.append(geo)
            prv_Pe = Pe

        tot_length = 0
        for geo in geos:
            tot_length += geo.length

        reorder_shape = False
        for start_geo_nr in range(len(geos)):
            geos_adj = deepcopy(geos[start_geo_nr:]) + deepcopy(geos[:start_geo_nr])
            new_geos = []
            i = 0
            while i in range(len(geos_adj)):
                geo = geos_adj[i]
                intersections = []
                for j in range(i+1, len(geos_adj)):
                    intersection = get_intersection_point(geos_adj[j], geos_adj[i])
                    if intersection and intersection != geos_adj[i].Ps:
                        intersections.append([j, intersection])
                if len(intersections) > 0:
                    intersection = intersections[-1]
                    change_end_of_geo = True
                    if i == 0 and intersection[0] >= len(geos_adj)//2:
                        geo.Ps = intersection[1]
                        geos_adj[intersection[0]].Pe = intersection[1]
                        if len(intersections) > 1:
                            intersection = intersections[-2]
                        else:
                            change_end_of_geo = False
                            i += 1
                    if change_end_of_geo:
                        geo.Pe = intersection[1]
                        i = intersection[0]
                        geos_adj[i].Ps = intersection[1]
                else:
                    i += 1
                new_geos.append(geo)
                if new_geos[0].Ps == new_geos[-1].Pe:
                    break

            new_length = 0
            for geo in new_geos:
                new_length += geo.length

            if new_length > tot_length * 0.5:
                for geo in new_geos:
                    self.append(geo)
                reorder_shape = True
                break
        if reorder_shape:
            self.shape.geos = self.shape.geos[geos[start_geo_nr].geo_nr:] + self.shape.geos[:geos[start_geo_nr].geo_nr]

    def make_path(self, drawHorLine, drawVerLine):
        for geo in self.geos:
            drawVerLine(geo.get_start_end_points(True), self.shape.axis3_start_mill_depth, self.shape.axis3_mill_depth)
            geo.make_path(self.shape, drawHorLine)
        if len(self.geos) > 0:
            drawVerLine(geo.get_start_end_points(False), self.shape.axis3_start_mill_depth, self.shape.axis3_mill_depth)

def get_intersection_point(prv_geo, geo):
    intersection = None
    if isinstance(prv_geo, LineGeo) and isinstance(geo, LineGeo):
        intersection = line_line_intersection(prv_geo, geo)
    elif isinstance(prv_geo, LineGeo) and isinstance(geo, ArcGeo):
        intersection = line_arc_intersection(prv_geo, geo, prv_geo.Pe)
    elif isinstance(prv_geo, ArcGeo) and isinstance(geo, LineGeo):
        intersection = line_arc_intersection(geo, prv_geo, prv_geo.Pe)
    elif isinstance(prv_geo, ArcGeo) and isinstance(geo, ArcGeo):
        intersection = arc_arc_intersection(geo, prv_geo, prv_geo.Pe)
    return intersection

def point_belongs_to_line(point, line):
    linex = sorted([line.Ps.x, line.Pe.x])
    liney = sorted([line.Ps.y, line.Pe.y])
    return (linex[0] - 1e-8 <= point.x <= linex[1] + 1e-8 and
            liney[0] - 1e-8 <= point.y <= liney[1] + 1e-8)

def point_belongs_to_arc(point, arc):
    ang = arc.dif_ang(arc.Ps, point, arc.ext)
    return (arc.ext + 1e-8 >= ang >= -1e-8 if arc.ext > 0 else
            arc.ext - 1e-8 <= ang <= 1e-8)

def line_line_intersection(line1, line2):
    # based on
    # http://stackoverflow.com/questions/20677795/find-the-point-of-intersecting-lines
    xydiff1 = line1.Ps - line1.Pe
    xydiff2 = line2.Ps - line2.Pe
    xdiff = (xydiff1.x, xydiff2.x)
    ydiff = (xydiff1.y, xydiff2.y)

    det = lambda a, b: a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div != 0:
        d = (det((line1.Ps.x, line1.Ps.y), (line1.Pe.x, line1.Pe.y)),
             det((line2.Ps.x, line2.Ps.y), (line2.Pe.x, line2.Pe.y)))

        intersection = Point(det(d, xdiff) / div,
                             det(d, ydiff) / div)

        if point_belongs_to_line(intersection, line1) and point_belongs_to_line(intersection, line2):
            return intersection
    return None

def line_arc_intersection(line, arc, refpoint):
    # based on
    # http://stackoverflow.com/questions/13053061/circle-line-intersection-points
    baX = line.Pe.x - line.Ps.x
    baY = line.Pe.y - line.Ps.y
    caX = arc.O.x - line.Ps.x
    caY = arc.O.y - line.Ps.y

    a = baX * baX + baY * baY
    bBy2 = baX * caX + baY * caY
    c = caX * caX + caY * caY - arc.r * arc.r

    if a == 0:
        return None

    pBy2 = bBy2 / a
    q = c / a

    disc = pBy2 * pBy2 - q
    if disc > 0:
        tmpSqrt = sqrt(disc)
        abScalingFactor1 = -pBy2 + tmpSqrt
        abScalingFactor2 = -pBy2 - tmpSqrt

        p1 = Point(line.Ps.x - baX * abScalingFactor1,
                   line.Ps.y - baY * abScalingFactor1)
        p2 = Point(line.Ps.x - baX * abScalingFactor2,
                   line.Ps.y - baY * abScalingFactor2)

        intersections = []
        if point_belongs_to_arc(p1, arc) and point_belongs_to_line(p1, line):
            intersections.append(p1)
        if point_belongs_to_arc(p2, arc) and point_belongs_to_line(p2, line):
            intersections.append(p2)
        intersections.sort(key=lambda x: (refpoint - x).length_squared())
        if len(intersections) > 0:
            return intersections[0]
    return None

def arc_arc_intersection(arc1, arc2, refpoint):
    # based on
    # http://stackoverflow.com/questions/3349125/circle-circle-intersection-points
    d = arc1.O.distance(arc2.O)

    if d > (arc1.r + arc2.r):  # there are no solutions, the circles are separate
        return None
    elif d + 1e-5 < abs(arc1.r - arc2.r):  # there are no solutions because one circle is contained within the other
        return None
    elif d == 0:  # then the circles are coincident and there are an infinite number of solutions
        return None
    else:
        a = (arc1.r**2 - arc2.r**2 + d**2) / (2 * d)
        if arc1.r**2 - a**2 < 0:
            return None
        h = sqrt(arc1.r**2 - a**2)
        P2 = arc1.O + a * (arc2.O - arc1.O) / d

        p1 = Point(P2.x + h * (arc2.O.y - arc1.O.y) / d,
                   P2.y - h * (arc2.O.x - arc1.O.x) / d)
        p2 = Point(P2.x - h * (arc2.O.y - arc1.O.y) / d,
                   P2.y + h * (arc2.O.x - arc1.O.x) / d)

        intersections = []
        if point_belongs_to_arc(p1, arc1) and point_belongs_to_arc(p1, arc2):
            intersections.append(p1)
        if point_belongs_to_arc(p2, arc1) and point_belongs_to_arc(p2, arc2):
            intersections.append(p2)
        intersections.sort(key=lambda x: (refpoint - x).length_squared())
        if len(intersections) > 0:
            return intersections[0]
        return None

class RapidPos(Point):
    def __init__(self, point):
        Point.__init__(self, point.x, point.y)
        self.abs_geo = None

    def get_start_end_points(self, start_point, angles=None):
        if angles is None:
            return self.abs_geo
        elif angles:
            return self.abs_geo, 0
        else:
            return self.abs_geo, Point(0, -1) if start_point else Point(0, -1)

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent. This
        is done for rotating and scaling purposes
        """
        self.abs_geo = self.rot_sca_abs(parent=parent)

    def make_path(self, caller, drawHorLine):
        pass

    def Write_GCode(self, PostPro=None):
        """
        Writes the GCODE for a rapid position.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        return PostPro.rap_pos_xy(self.abs_geo)
