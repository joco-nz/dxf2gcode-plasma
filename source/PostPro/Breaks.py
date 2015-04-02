# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2014-2014
#    Robert Lichtenberger
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

from PyQt4 import QtCore

from Core.LineGeo import LineGeo
from Core.ArcGeo import ArcGeo
from Core.BreakGeo import BreakGeo
from Core.Point import Point
from math import sqrt, copysign

import logging
logger = logging.getLogger("PostPro.Breaks")

class Breaks(QtCore.QObject):
    """
    The Breaks Class includes the functions for processing shapes on layers named BREAKS: to break closed shapes so that
    the resulting G-Code will contain rests for the workpiece.
    """
    def __init__(self, layerContents):
        self.layerContents = layerContents

    def process(self):
        """
        Process layerContents: Each non-BREAKS: layers shapes are checked against all the shapes in all BREAKS: layers.
        If a shape is intersected twice by a break-shape, the shape will be broken.
        """
        breakLayers = []
        processLayers = []
        for layerContent in self.layerContents:
            if layerContent.isBreakLayer():
                breakLayers.append(layerContent)
            elif not layerContent.should_ignore():
                processLayers.append(layerContent)

        logger.debug("Found %d break layers and %d processing layers" % (len(breakLayers), len(processLayers)) )
        if (len(breakLayers) > 0 and len(processLayers) > 0):
            self.doProcess(breakLayers, processLayers)

    def doProcess(self, breakLayers, processLayers):
        for layer in processLayers:
            for shape in layer.shapes:
                self.breakShape(shape, breakLayers)

    # TODO :: algorithm is broken; if a shape is broken more than once, we will get multiple geos for a single original line, depending on the order of the original geos
    def breakShape(self, shape, breakLayers):
        newGeos = []
        for geo in shape.geos:
            if (isinstance(geo, LineGeo)):
                newGeos.extend(self.breakLineGeo(geo, breakLayers))
            elif isinstance(geo, ArcGeo):
                newGeos.extend(self.breakArcGeo(geo, breakLayers))
            else:
                newGeos.append(geo)
        shape.geos = newGeos

    def breakLineGeo(self, lineGeo, breakLayers):
        """
        Try to break passed lineGeo with any of the shapes on a break layers.
        Will break lineGeos recursively.
        @return: The list of geometries after breaking (lineGeo itself if no breaking happened)
        """
        newGeos = []
        for breakLayer in breakLayers:
            for breakShape in breakLayer.shapes:
                intersections = self.intersectLineGeometry(lineGeo, breakShape)
                if len(intersections) == 2:
                    (near, far) = self.classifyIntersections(lineGeo, intersections)
                    logger.debug("Line %s broken from (%f, %f) to (%f, %f)" % (lineGeo.toShortString(), near.x, near.y, far.x, far.y))
                    newGeos.extend(self.breakLineGeo(LineGeo(lineGeo.Pa, near), breakLayers))
                    newGeos.append(BreakGeo(LineGeo(near, far), breakLayer.axis3_mill_depth, breakLayer.f_g1_plane, breakLayer.f_g1_depth))
                    newGeos.extend(self.breakLineGeo(LineGeo(far, lineGeo.Pe), breakLayers))
                    return newGeos
        return [lineGeo]

    def breakArcGeo(self, arcGeo, breakLayers):
        """
        Try to break passed arcGeo with any of the shapes on a break layers.
        @return: The list of geometries after breaking (arcGeo itself if no breaking happened)
        """
        newGeos = []
        for breakLayer in breakLayers:
            for breakShape in breakLayer.shapes:
                intersections = self.intersectArcGeometry(arcGeo, breakShape)
                if len(intersections) == 2:
                    (near, far) = self.classifyIntersections(arcGeo, intersections)
                    logger.debug("Arc %s broken from (%f, %f) to (%f, %f)" % (arcGeo.toShortString(), near.x, near.y, far.x, far.y))
                    newGeos.append(ArcGeo(Pa=arcGeo.Pa, Pe=near, O=arcGeo.O, r=arcGeo.r, direction=arcGeo.ext))
                    newGeos.append(BreakGeo(LineGeo(near, far), breakLayer.axis3_mill_depth, breakLayer.f_g1_plane, breakLayer.f_g1_depth))
                    newGeos.append(ArcGeo(Pa=far, Pe=arcGeo.Pe, O=arcGeo.O, r=arcGeo.r, direction=arcGeo.ext))
                    return newGeos
        return [arcGeo]

    def intersectLineGeometry(self, lineGeo, breakShape):
        """
        Try to break lineGeo with the given breakShape. Will return the intersection points of lineGeo with breakShape.
        """
        intersections = []
        line = QtCore.QLineF(lineGeo.Pa.x, lineGeo.Pa.y, lineGeo.Pe.x, lineGeo.Pe.y)
        for breakGeo in breakShape.geos:
            if isinstance(breakGeo, LineGeo):
                breakLine = QtCore.QLineF(breakGeo.Pa.x, breakGeo.Pa.y, breakGeo.Pe.x, breakGeo.Pe.y)
                intersection = QtCore.QPointF(0, 0)  # values do not matter
                res = line.intersect(breakLine, intersection)
                if res == QtCore.QLineF.BoundedIntersection:
                    intersections.append(Point(intersection.x(), intersection.y()))
        return intersections

    def intersectArcGeometry(self, arcGeo, breakShape):
        intersections = []
        for breakGeo in breakShape.geos:
            if isinstance(breakGeo, LineGeo):
                # http://stackoverflow.com/questions/13053061/circle-line-intersection-points
                baX = breakGeo.Pe.x - breakGeo.Pa.x
                baY = breakGeo.Pe.y - breakGeo.Pa.y
                caX = arcGeo.O.x - breakGeo.Pa.x
                caY = arcGeo.O.y - breakGeo.Pa.y

                a = baX * baX + baY * baY
                bBy2 = baX * caX + baY * caY
                c = caX * caX + caY * caY - arcGeo.r * arcGeo.r

                pBy2 = bBy2 / a
                q = c / a

                disc = pBy2 * pBy2 - q
                if disc > 0:
                    tmpSqrt = sqrt(disc)
                    abScalingFactor1 = -pBy2 + tmpSqrt
                    abScalingFactor2 = -pBy2 - tmpSqrt

                    p1 = Point(breakGeo.Pa.x - baX * abScalingFactor1, breakGeo.Pa.y
                        - baY * abScalingFactor1)
                    p2 = Point(breakGeo.Pa.x - baX * abScalingFactor2, breakGeo.Pa.y
                        - baY * abScalingFactor2)
                    intersections.append(self.determinePointForArcLineIntesection(arcGeo.Pa, p1, p2))
        return intersections

    def determinePointForArcLineIntesection(selfself, refpoint, point1, point2):
        return point1 if refpoint.distance(point1) < refpoint.distance(point2) else point2

    def classifyIntersections(self, geo, intersection):
        """
        Investigate the array intersection (which contains exactly two Point instances) and return (near, far) tuple, depending on the distance of the points to the start point of the geometry geo.
        """
        if geo.Pa.distance(intersection[0]) < geo.Pa.distance(intersection[1]):
            return (intersection[0], intersection[1])
        else:
            return (intersection[1], intersection[0])
