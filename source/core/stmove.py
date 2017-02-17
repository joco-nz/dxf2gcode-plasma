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

from math import sin, cos, pi, sqrt
from copy import deepcopy


import globals.globals as g

from core.linegeo import LineGeo
from core.arcgeo import ArcGeo
from core.holegeo import HoleGeo
from core.point import Point
from core.intersect import Intersect
from core.shape import Geos
from core.shape import Shape
from core.shapeoffset import *

import logging
logger = logging.getLogger('core.stmove')


class StMove(object):
    """
    This Function generates the StartMove for each shape. It
    also performs the Plotting and Export of this moves. It is linked
    to the shape of its parent
    """
    # only need default arguments here because of the change of usage with super in QGraphicsLineItem
    def __init__(self, shape=None):
        if shape is None:
            return

        self.shape = shape

        self.start, self.angle = self.shape.get_start_end_points(True, True)
        self.end = self.start

        self.geos = Geos([])

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
        self.geos = Geos([])

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
        
        #set the proper direction for the tool path
        if self.shape.cw ==True:
            direction = -1;
        else:
            direction = 1;

        # Pocket Milling - draw toolpath
        if self.shape.Pocket == True:
            #for circular pocket
            if isinstance(self.shape.geos[0],ArcGeo):
                numberofrotations = int((self.shape.geos[0].r - tool_rad)/self.shape.OffsetXY)-1
                if ((self.shape.geos[0].r - tool_rad)/self.shape.OffsetXY)> numberofrotations :
                    numberofrotations += 1
                logger.debug("stmove:make_start_moves:Tool Radius: %f" % (tool_rad))
                logger.debug("stmove:make_start_moves:StepOver XY: %f" % (self.shape.OffsetXY))
                logger.debug("stmove:make_start_moves:Shape Radius: %f" % (self.shape.geos[0].r))
                logger.debug("stmove:make_start_moves:Shape Origin at: %f,%f" % (self.shape.geos[0].O.x, self.shape.geos[0].O.y))
                logger.debug("stmove:make_start_moves:Number of Arcs: %f" % (numberofrotations+1))
                for i in range(0, numberofrotations + 1):
                    st_point = Point(self.shape.geos[0].O.x,self.shape.geos[0].O.y)
                    Ps_point = Point(self.shape.geos[0].O.x +(tool_rad + (i*self.shape.OffsetXY)) ,self.shape.geos[0].O.y)
                    Pe_point = Ps_point
                    if ((Ps_point.x - self.shape.geos[0].O.x + tool_rad) < self.shape.geos[0].r):
                        self.append(ArcGeo(Ps=Ps_point, Pe=Pe_point, O=st_point, r=(tool_rad + (i*self.shape.OffsetXY)), direction=direction))
                    else:
                        Ps_point = Point(self.shape.geos[0].O.x + self.shape.geos[0].r - tool_rad  ,self.shape.geos[0].O.y)
                        Pe_point = Ps_point
                        self.append(ArcGeo(Ps=Ps_point, Pe=Pe_point, O=st_point, r=(Ps_point.x - self.shape.geos[0].O.x), direction=direction))
                    logger.debug("stmove:make_start_moves:Toolpath Arc at: %f,%f" % (Ps_point.x,Ps_point.x))   
                    if i<numberofrotations:
                        st_point = Point(Ps_point.x,Ps_point.y)
                        if ((Ps_point.x + self.shape.OffsetXY - self.shape.geos[0].O.x + tool_rad) < self.shape.geos[0].r):
                            en_point = Point(Ps_point.x + self.shape.OffsetXY,Ps_point.y)
                        else:
                            en_point = Point(self.shape.geos[0].O.x + self.shape.geos[0].r - tool_rad,Ps_point.y)
                            
                        self.append(LineGeo(st_point,en_point))
            
            #for rectangular pocket
            if isinstance(self.shape.geos[0],LineGeo):
                #get Rectangle width and height
                firstgeox = abs(self.shape.geos[0].Ps.x - self.shape.geos[0].Pe.x)
                firstgeoy = abs(self.shape.geos[0].Ps.y - self.shape.geos[0].Pe.y)
                secondgeox = abs(self.shape.geos[1].Ps.x - self.shape.geos[1].Pe.x)
                secondgeoy = abs(self.shape.geos[1].Ps.y - self.shape.geos[1].Pe.y)
                if firstgeox > secondgeox:
                    Pocketx = firstgeox
                    if self.shape.geos[0].Ps.x < self.shape.geos[0].Pe.x:
                        minx = self.shape.geos[0].Ps.x
                    else:
                        minx = self.shape.geos[0].Pe.x
                else:
                    Pocketx = secondgeox
                    if self.shape.geos[1].Ps.x < self.shape.geos[1].Pe.x:
                        minx = self.shape.geos[1].Ps.x
                    else:
                        minx = self.shape.geos[1].Pe.x
                if firstgeoy > secondgeoy:
                    Pockety = firstgeoy
                    if self.shape.geos[0].Ps.y < self.shape.geos[0].Pe.y:
                        miny = self.shape.geos[0].Ps.y
                    else:
                        miny = self.shape.geos[0].Pe.y
                else:
                    Pockety = secondgeoy
                    if self.shape.geos[1].Ps.y < self.shape.geos[1].Pe.y:
                        miny = self.shape.geos[1].Ps.y
                    else:
                        miny = self.shape.geos[1].Pe.y
                Centerpt = Point(Pocketx/2 + minx, Pockety/2 +miny)
                # calc number of rotations
                if Pockety > Pocketx:
                    numberofrotations = int(((Pocketx/2) - tool_rad)/self.shape.OffsetXY)#+1
                    if (((Pocketx/2) - tool_rad)/self.shape.OffsetXY)> int(((Pocketx/2) - tool_rad)/self.shape.OffsetXY)+0.5 :
                        numberofrotations += 1
                else:
                    numberofrotations = int(((Pockety/2) - tool_rad)/self.shape.OffsetXY)#+1
                    if (((Pockety/2) - tool_rad)/self.shape.OffsetXY)> int(((Pockety/2) - tool_rad)/self.shape.OffsetXY)+0.5 :
                        numberofrotations += 1
                logger.debug("stmove:make_start_moves:Shape Center at: %f,%f" % (Centerpt.x, Centerpt.y))        
                for i in range(0, numberofrotations):
                    # for CCW Climb milling
                    if Pockety > Pocketx: 
                        if (Centerpt.y - (Pockety-Pocketx)/2 - (tool_rad + (i*self.shape.OffsetXY)) - tool_rad >= miny):
                            Ps_point1 = Point(Centerpt.x +(tool_rad + (i*self.shape.OffsetXY)) ,Centerpt.y + ((Pockety-Pocketx)/2 +(tool_rad + (i*self.shape.OffsetXY))) )
                            Pe_point1 = Point(Centerpt.x -(tool_rad + (i*self.shape.OffsetXY)) ,Centerpt.y + ((Pockety-Pocketx)/2 +(tool_rad + (i*self.shape.OffsetXY))) )
                            Ps_point2 = Pe_point1
                            Pe_point2 = Point(Centerpt.x -(tool_rad + (i*self.shape.OffsetXY)) ,Centerpt.y - ((Pockety-Pocketx)/2 +(tool_rad + (i*self.shape.OffsetXY))) )
                            Ps_point3 = Pe_point2
                            Pe_point3 = Point(Centerpt.x +(tool_rad + (i*self.shape.OffsetXY)) ,Centerpt.y - ((Pockety-Pocketx)/2 +(tool_rad + (i*self.shape.OffsetXY))) )
                            Ps_point4 = Pe_point3
                            Pe_point4 = Ps_point1
                        else:
                            Ps_point1 = Point(Centerpt.x + Pocketx/2 - tool_rad ,Centerpt.y + Pockety/2 - tool_rad )
                            Pe_point1 = Point(Centerpt.x - Pocketx/2 + tool_rad ,Centerpt.y + Pockety/2 - tool_rad )
                            Ps_point2 = Pe_point1
                            Pe_point2 = Point(Centerpt.x - Pocketx/2 + tool_rad ,Centerpt.y - Pockety/2 + tool_rad )
                            Ps_point3 = Pe_point2
                            Pe_point3 = Point(Centerpt.x + Pocketx/2 - tool_rad ,Centerpt.y - Pockety/2 + tool_rad )
                            Ps_point4 = Pe_point3
                            Pe_point4 = Ps_point1
                        logger.debug("stmove:make_start_moves:Starting point at: %f,%f" % (Ps_point1.x, Ps_point1.y))
                        if direction == 1: # this is CCW
                            self.append(LineGeo(Ps_point1,Pe_point1))
                            self.append(LineGeo(Ps_point2,Pe_point2))
                            self.append(LineGeo(Ps_point3,Pe_point3))
                            self.append(LineGeo(Ps_point4,Pe_point4))
                        else: # this is CW
                            self.append(LineGeo(Pe_point4,Ps_point4))
                            self.append(LineGeo(Pe_point3,Ps_point3))
                            self.append(LineGeo(Pe_point2,Ps_point2))
                            self.append(LineGeo(Pe_point1,Ps_point1))
                            
                        if i<numberofrotations-1:
                            if direction == 1: # this is CCW
                                st_point = Point(Ps_point1.x,Ps_point1.y)
                            else: # this is CW
                                st_point = Point(Pe_point4.x,Pe_point4.y)
                            if (Centerpt.y - (Pockety-Pocketx)/2 - (tool_rad + ((i+1)*self.shape.OffsetXY)) - tool_rad >= miny):
                                en_point = Point(Ps_point1.x + self.shape.OffsetXY,Ps_point1.y + self.shape.OffsetXY)
                            else:
                                en_point = Point(Centerpt.x + Pocketx/2 - tool_rad,Centerpt.y + Pockety/2 - tool_rad)
                                 
                            self.append(LineGeo(st_point,en_point))
                    elif Pocketx > Pockety:
                        if (Centerpt.x - (Pocketx-Pockety)/2 - (tool_rad + (i*self.shape.OffsetXY)) - tool_rad >= minx):
                            Ps_point1 = Point(Centerpt.x + ((Pocketx-Pockety)/2 +(tool_rad + (i*self.shape.OffsetXY))) ,Centerpt.y + (tool_rad + (i*self.shape.OffsetXY)) )
                            Pe_point1 = Point(Centerpt.x - ((Pocketx-Pockety)/2 +(tool_rad + (i*self.shape.OffsetXY))) ,Centerpt.y + (tool_rad + (i*self.shape.OffsetXY)) )
                            Ps_point2 = Pe_point1
                            Pe_point2 = Point(Centerpt.x - ((Pocketx-Pockety)/2 +(tool_rad + (i*self.shape.OffsetXY))) ,Centerpt.y - (tool_rad + (i*self.shape.OffsetXY)) )
                            Ps_point3 = Pe_point2
                            Pe_point3 = Point(Centerpt.x + ((Pocketx-Pockety)/2 +(tool_rad + (i*self.shape.OffsetXY))) ,Centerpt.y - (tool_rad + (i*self.shape.OffsetXY)) )
                            Ps_point4 = Pe_point3
                            Pe_point4 = Ps_point1
                        else:
                            Ps_point1 = Point(Centerpt.x + Pocketx/2 - tool_rad ,Centerpt.y + Pockety/2 - tool_rad )
                            Pe_point1 = Point(Centerpt.x - Pocketx/2 + tool_rad ,Centerpt.y + Pockety/2 - tool_rad )
                            Ps_point2 = Pe_point1
                            Pe_point2 = Point(Centerpt.x - Pocketx/2 + tool_rad ,Centerpt.y - Pockety/2 + tool_rad )
                            Ps_point3 = Pe_point2
                            Pe_point3 = Point(Centerpt.x + Pocketx/2 - tool_rad ,Centerpt.y - Pockety/2 + tool_rad )
                            Ps_point4 = Pe_point3
                            Pe_point4 = Ps_point1
                        logger.debug("stmove:make_start_moves:Starting point at: %f,%f" % (Ps_point1.x, Ps_point1.y))
                        if direction == 1: # this is CCW
                            self.append(LineGeo(Ps_point1,Pe_point1))
                            self.append(LineGeo(Ps_point2,Pe_point2))
                            self.append(LineGeo(Ps_point3,Pe_point3))
                            self.append(LineGeo(Ps_point4,Pe_point4))
                        else: # this is CW
                            self.append(LineGeo(Pe_point4,Ps_point4))
                            self.append(LineGeo(Pe_point3,Ps_point3))
                            self.append(LineGeo(Pe_point2,Ps_point2))
                            self.append(LineGeo(Pe_point1,Ps_point1))
                        if i<numberofrotations-1:
                            if direction == 1: # this is CCW
                                st_point = Point(Ps_point1.x,Ps_point1.y)
                            else: # this is CW
                                st_point = Point(Pe_point4.x,Pe_point4.y)
                            if (Centerpt.x - (Pocketx-Pockety)/2 - (tool_rad + ((i+1)*self.shape.OffsetXY)) - tool_rad >= minx):
                                en_point = Point(Ps_point1.x + self.shape.OffsetXY,Ps_point1.y + self.shape.OffsetXY)
                            else:
                                en_point = Point(Centerpt.x + Pocketx/2 - tool_rad,Centerpt.y + Pockety/2 - tool_rad)
                                 
                            self.append(LineGeo(st_point,en_point))
                    elif Pocketx == Pockety:
                        if (Centerpt.x - (tool_rad + (i*self.shape.OffsetXY)) - tool_rad >= minx):
                            Ps_point1 = Point(Centerpt.x + (tool_rad + (i*self.shape.OffsetXY)) ,Centerpt.y + (tool_rad + (i*self.shape.OffsetXY)) )
                            Pe_point1 = Point(Centerpt.x - (tool_rad + (i*self.shape.OffsetXY)) ,Centerpt.y + (tool_rad + (i*self.shape.OffsetXY)) )
                            Ps_point2 = Pe_point1
                            Pe_point2 = Point(Centerpt.x - (tool_rad + (i*self.shape.OffsetXY)) ,Centerpt.y - (tool_rad + (i*self.shape.OffsetXY)) )
                            Ps_point3 = Pe_point2
                            Pe_point3 = Point(Centerpt.x + (tool_rad + (i*self.shape.OffsetXY)) ,Centerpt.y - (tool_rad + (i*self.shape.OffsetXY)) )
                            Ps_point4 = Pe_point3
                            Pe_point4 = Ps_point1
                        else:
                            Ps_point1 = Point(Centerpt.x + Pocketx/2 - tool_rad ,Centerpt.y + Pockety/2 - tool_rad )
                            Pe_point1 = Point(Centerpt.x - Pocketx/2 + tool_rad ,Centerpt.y + Pockety/2 - tool_rad )
                            Ps_point2 = Pe_point1
                            Pe_point2 = Point(Centerpt.x - Pocketx/2 + tool_rad ,Centerpt.y - Pockety/2 + tool_rad )
                            Ps_point3 = Pe_point2
                            Pe_point3 = Point(Centerpt.x + Pocketx/2 - tool_rad ,Centerpt.y - Pockety/2 + tool_rad )
                            Ps_point4 = Pe_point3
                            Pe_point4 = Ps_point1
                        logger.debug("stmove:make_start_moves:Starting point at: %f,%f" % (Ps_point1.x, Ps_point1.y)) 
                        if direction == 1: # this is CCW
                            self.append(LineGeo(Ps_point1,Pe_point1))
                            self.append(LineGeo(Ps_point2,Pe_point2))
                            self.append(LineGeo(Ps_point3,Pe_point3))
                            self.append(LineGeo(Ps_point4,Pe_point4))
                        else: # this is CW
                            self.append(LineGeo(Pe_point4,Ps_point4))
                            self.append(LineGeo(Pe_point3,Ps_point3))
                            self.append(LineGeo(Pe_point2,Ps_point2))
                            self.append(LineGeo(Pe_point1,Ps_point1))
                        if i<numberofrotations-1:
                            if direction == 1: # this is CCW
                                st_point = Point(Ps_point1.x,Ps_point1.y)
                            else: # this is CW
                                st_point = Point(Pe_point4.x,Pe_point4.y)
                            if (Centerpt.x - (tool_rad + ((i+1)*self.shape.OffsetXY)) - tool_rad >= minx):
                                en_point = Point(Ps_point1.x + self.shape.OffsetXY,Ps_point1.y + self.shape.OffsetXY)
                            else:
                                en_point = Point(Centerpt.x + Pocketx/2 - tool_rad,Centerpt.y + Pockety/2 - tool_rad)
                                 
                            self.append(LineGeo(st_point,en_point))
                      
        if self.shape.Drill == True:
            st_point = Point(self.shape.geos[0].O.x,self.shape.geos[0].O.y)
            en_point = st_point
            myholegeo = HoleGeo(self.shape.geos[0].O)
            myholegeo.z_pos = self.shape.axis3_mill_depth
            myholegeo.Q = self.shape.axis3_mill_depth
            myholegeo.R = self.shape.parentLayer.axis3_safe_margin
            myholegeo.DrillType = self.shape.DrillType
            myholegeo.DFeed = self.shape.f_g1_depth
            self.append(myholegeo)
            self.append(RapidPos(st_point))
            
        if self.shape.cut_cor == 40:
            if self.shape.Pocket == False:
                self.append(RapidPos(start))
            
        elif self.shape.cut_cor != 40 and not g.config.vars.Cutter_Compensation["done_by_machine"]:

            toolwidth = self.shape.parentLayer.getToolRadius()
            offtype = "in"  if self.shape.cut_cor == 42 else "out"
            offshape = offShapeClass(parent = self.shape, offset = toolwidth, offtype = offtype)

            if len(offshape.rawoff) > 0:
                start, angle = offshape.rawoff[0].get_start_end_points(True, True)

                self.append(RapidPos(start))
                self.geos += offshape.rawoff

        # Cutting Compensation Left
        elif self.shape.cut_cor == 41:
            # Center of the Starting Radius.
            Oein = start.get_arc_point(angle + pi/2, start_rad + tool_rad)
            # Start Point of the Radius
            Ps_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            # Start Point of the straight line segment at begin.
            Pg_ein = Ps_ein.get_arc_point(angle + pi/2, start_rad)

            # Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.append(RapidPos(start_ein))

            # generate the Start Line and append it including the compensation.
            start_line = LineGeo(start_ein, Ps_ein)
            self.append(start_line)

            # generate the start rad. and append it.
            start_rad = ArcGeo(Ps=Ps_ein, Pe=start, O=Oein,
                               r=start_rad + tool_rad, direction=1)
            self.append(start_rad)

        # Cutting Compensation Right
        elif self.shape.cut_cor == 42:
            # Center of the Starting Radius.
            Oein = start.get_arc_point(angle - pi/2, start_rad + tool_rad)
            # Start Point of the Radius
            Ps_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            # Start Point of the straight line segment at begin.
            Pg_ein = Ps_ein.get_arc_point(angle - pi/2, start_rad)

            # Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.append(RapidPos(start_ein))

            # generate the Start Line and append it including the compensation.
            start_line = LineGeo(start_ein, Ps_ein)
            self.append(start_line)

            # generate the start rad. and append it.
            start_rad = ArcGeo(Ps=Ps_ein, Pe=start, O=Oein,
                               r=start_rad + tool_rad, direction=0)
            self.append(start_rad)

    def make_swivelknife_move(self):
        """
        Set these variables for your tool and material
        @param offset: knife tip distance from tool centerline. The radius of the
        tool is used for this.
        """
        offset = self.shape.parentLayer.getToolRadius()
        drag_angle = self.shape.drag_angle

        startnorm = offset*Point(1, 0)  # TODO make knife direction a config setting
        prvend, prvnorm = Point(), Point()
        first = True

        for geo in self.shape.geos.abs_iter():
            if isinstance(geo, LineGeo):
                geo_b = deepcopy(geo)
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
                    swivel.drag = drag_angle < abs(swivel.ext)
                    self.append(swivel)
                self.append(geo_b)

                prvend = geo_b.Pe
                prvnorm = norm
            elif isinstance(geo, ArcGeo):
                geo_b = deepcopy(geo)
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
                    swivel.drag = drag_angle < abs(swivel.ext)
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

        self.geos.insert(0, RapidPos(self.geos.abs_el(0).Ps))
        self.geos[0].make_abs_geo()


    def make_path(self, drawHorLine, drawVerLine):
        for geo in self.geos.abs_iter():
            drawVerLine(self.shape, geo.get_start_end_points(True))
            geo.make_path(self.shape, drawHorLine)
        if len(self.geos):
            drawVerLine(self.shape, geo.get_start_end_points(False))


class RapidPos(Point):
    def __init__(self, point):
        Point.__init__(self, point.x, point.y)
        self.abs_geo = None

    def get_start_end_points(self, start_point, angles=None):
        if angles is None:
            return self
        elif angles:
            return self, 0
        else:
            return self, Point(0, -1) if start_point else Point(0, -1)

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent. This
        is done for rotating and scaling purposes
        """
        self.abs_geo = RapidPos(self.rot_sca_abs(parent=parent))

    def make_path(self, caller, drawHorLine):
        pass

    def Write_GCode(self, PostPro):
        """
        Writes the GCODE for a rapid position.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        return PostPro.rap_pos_xy(self)



