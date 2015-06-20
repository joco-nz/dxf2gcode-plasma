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

from math import sin, cos, pi, sqrt
from copy import deepcopy
import logging

import globals.globals as g
from core.linegeo import LineGeo
from core.arcgeo import ArcGeo
from core.point import Point
from core.entitycontent import EntityContent
from gui.arrow import Arrow

try:
    from PyQt4 import QtCore, QtGui
except ImportError:
    raise Exception("PyQt4 import error")

logger = logging.getLogger('Gui.StMove')


class StMove(QtGui.QGraphicsLineItem):
    """
    This Function generates the StartMove for each shape. It
    also performs the Plotting and Export of this moves. It is linked
    to the shape of its parent
    """
    def __init__(self, startp, angle,
                 pencolor=QtCore.Qt.green,
                 shape=None, parent=None):
        """
        Initialisation of the class.
        @param startp: Startpoint of the shape where to add the move.
        The coordinates are given in scaled coordinates.
        @param angle: Angle of the Startmove to end with.
        @param pencolor: Used only for plotting purposes
        @param shape: Shape for which the start move is created
        @param parent: parent EntityContentClass on which the
        geometries are added.
        """
        self.sc = 1
        super(StMove, self).__init__()

        self.startp = startp
        self.endp = startp
        self.angle = angle
        self.shape = shape
        self.parent = parent
        self.allwaysshow = False
        self.geos = []
        self.path = QtGui.QPainterPath()

        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)

        self.pen = QtGui.QPen(pencolor, 1, QtCore.Qt.SolidLine,
                      QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.pen.setCosmetic(True)

        self.make_start_moves()
        self.createccarrow()
        self.make_papath()

    def append(self, geo):
        # we don't want to additional scale / rotate the stmove geo
        # so no geo.make_abs_geo(self.shape.parentEntity)
        geo.make_abs_geo()
        self.geos.append(geo)

    def contains_point(self, point):
        """
        StMove cannot be selected. Return maximal distance
        """
        return float(0x7fffffff)

    def make_start_moves(self):
        """
        This function called to create the start move. It will
        be generated based on the given values for start and angle.
        """
        del(self.geos[:])

        if g.config.machine_type == 'drag_knife':
            self.make_swivelknife_move()
            return

        # BaseEntitie created to add the StartMoves etc. This Entitie must not
        # be offset or rotated etc.
        BaseEntitie = EntityContent(nr= -1, name='BaseEntitie',
                                          parent=None,
                                          p0=Point(x=0.0, y=0.0),
                                          pb=Point(x=0.0, y=0.0),
                                          sca=[1, 1, 1],
                                          rot=0.0)

        self.parent = BaseEntitie

        # Get the start rad. and the length of the line segment at begin.
        start_rad = self.shape.shape.parentLayer.start_radius
        start_ver = start_rad

        # Get tool radius based on tool diameter.
        tool_rad = self.shape.shape.parentLayer.tool_diameter/2

        # Calculate the starting point with and without compensation.
        start = self.startp
        angle = self.angle

        if self.shape.shape.cut_cor == 40:
            self.append(RapidPos(start))

        # Cutting Compensation Left
        elif self.shape.cut_cor == 41:
            # Center of the Starting Radius.
            Oein = start.get_arc_point(angle + pi/2, start_rad + tool_rad)
            # Start Point of the Radius
            Pa_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            # Start Point of the straight line segment at begin.
            Pg_ein = Pa_ein.get_arc_point(angle + pi/2, start_ver)

            # Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.append(start_ein)

            # generate the Start Line and append it including the compensation.
            start_line = LineGeo(Pg_ein, Pa_ein)
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
            Pg_ein = Pa_ein.get_arc_point(angle - pi/2, start_ver)

            # Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.append(start_ein)

            # Generate the Start Line and append it including the compensation.
            start_line = LineGeo(Pg_ein, Pa_ein)
            self.append(start_line)

            # Generate the start rad. and append it.
            start_rad = ArcGeo(Ps=Pa_ein, Pe=start, O=Oein,
                               r=start_rad + tool_rad, direction=0)
            self.append(start_rad)

    def make_swivelknife_move(self):
        """
        Set these variables for your tool and material
        @param offset: knife tip distance from tool centerline. The radius of the
        tool is used for this.
        """
        offset = self.shape.LayerContent.tool_diameter/2
        drag_angle = self.shape.dragAngle

        startnorm = offset*Point(1, 0, 0)  # TODO make knife direction a config setting
        prvend, prvnorm = Point(), Point()
        first = 1

        # Use The same parent as for the shape
        self.parent = self.shape.parent

        for geo in self.shape.geos:
            if geo.type == 'LineGeo':
                geo_b = deepcopy(geo)
                if first:
                    first = 0
                    prvend = geo_b.Ps + startnorm
                    prvnorm = startnorm
                if geo_b.Ps != geo_b.Pe:  # TODO this "fix" should be done during import
                    norm = offset * geo_b.Ps.unit_vector(geo_b.Pe)
                    geo_b.Ps += norm
                    geo_b.Pe += norm
                    if not prvnorm == norm:
                        swivel = ArcGeo(Ps=prvend, Pe=geo_b.Ps, r=offset, direction=prvnorm.cross_product(norm).z)
                        swivel.drag = drag_angle < abs(swivel.ext)
                        self.append(swivel)
                    self.append(geo_b)

                    prvend = geo_b.Pe
                    prvnorm = norm
            elif geo.type == 'ArcGeo':
                geo_b = deepcopy(geo)
                if first:
                    first = 0
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
                    swivel = ArcGeo(Ps=prvend, Pe=geo_b.Ps, r=offset, direction=prvnorm.cross_product(norma).z)
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
            self.append(ArcGeo(Ps=prvend, Pe=prvend-prvnorm+startnorm, r=offset, direction=prvnorm.cross_product(startnorm).z))

        self.insert(0, RapidPos(self.geos[0].Ps))

    def updateCutCor(self, cutcor):
        """
        This function is called to update the Cutter Correction, and therefore
        the start moves, if something has changed or it needs generated for
        first time.
        """
        logger.debug("Updating CutterCorrection of Selected shape")

        self.cutcor = cutcor
        self.make_start_moves()

    def updateCCplot(self):
        """
        This function is called to update the Cutter Correction plotting, and
        therefore the start moves, if something has changed or it needs
        generated for first time.
        """
        logger.debug("Updating CutterCorrection of Selected shape plotting")

        if not(self.ccarrow is None):
            logger.debug("Removing ccarrow from scene")
            self.ccarrow.hide()
            logger.debug("Parent Item: %s" %self.ccarrow.parentItem())
            del(self.ccarrow)
            self.ccarrow = None

        self.createccarrow()
        self.make_papath()
        self.update()

    def createccarrow(self):
        """
        createccarrow()
        """
        length = 20
        if self.shape.shape.cut_cor == 40:
            self.ccarrow = None
        elif self.shape.cut_cor == 41:
            self.ccarrow = Arrow(startp=self.startp,
                          length=length,
                          angle=self.angle+pi/2,
                          color=QtGui.QColor(200, 200, 255),
                          pencolor=QtGui.QColor(200, 100, 255))
            self.ccarrow.setParentItem(self)
        else:
            self.ccarrow = Arrow(startp=self.startp,
                          length=length,
                          angle=self.angle-pi/2,
                          color=QtGui.QColor(200, 200, 255),
                          pencolor=QtGui.QColor(200, 100, 255))
            self.ccarrow.setParentItem(self)

    def update_plot(self, startp, angle):
        """
        Method is called after update of the Shapes Startpoint
        @param startp: The new startpoint
        @param angle: the new Angle of the Startpoint
        """
        self.startp = startp
        self.endp = startp
        self.angle = angle

        if self.shape.cut_cor == 40:
            self.ccarrow = None
        elif self.shape.cut_cor == 41:
            self.ccarrow.updatepos(startp, angle=angle+pi/2)
        else:
            self.ccarrow.updatepos(startp, angle=angle-pi/2)

        self.make_start_moves()
        self.make_papath()

    def make_papath(self):
        """
        To be called if a Shape shall be printed to the canvas
        @param canvas: The canvas to be printed in
        @param pospro: The color of the shape
        """
        self.hide()
        del(self.path)
        self.path = QtGui.QPainterPath()

        drawHorLine = lambda st, en, z: self.path.lineTo(en.x, -en.y)
        for geo in self.geos:
            geo.make_path(self.shape.shape, drawHorLine)
        self.show()

    def setSelected(self, flag=True):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        if self.allwaysshow:
            pass
        elif flag is True:
            self.show()
        else:
            self.hide()

        self.update(self.boundingRect())

    def reverseshape(self, startp, angle):
        """
        Method is called when the shape direction is changed and therefore the
        arrow gets new Point and direction
        @param startp: The new startpoint
        @param angle: The new angle of the arrow
        """
        self.startp = startp
        self.angle = angle
        self.update_plot(startp, angle)

    def setallwaysshow(self, flag=False):
        """
        If the directions shall be allwaysshown the parameter will be set and
        all paths will be shown.
        @param flag: The flag to enable or disable Selection
        """
        self.allwaysshow = flag
        if flag is True:
            self.show()
        elif flag is True and self.isSelected():
            self.show()
        else:
            self.hide()
        self.update(self.boundingRect())

    def paint(self, painter, option, widget=None):
        """
        Method for painting the arrow.
        """
        painter.setPen(self.pen)
        painter.drawPath(self.path)

    def boundingRect(self):
        """
        Required method for painting. Inherited by Painterpath
        @return: Gives the Bounding Box
        """
        return self.path.boundingRect()


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

    def Write_GCode(self, PostPro):
        """
        Writes the GCODE for a rapid position.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        return PostPro.rap_pos_xy(self.abs_geo)

