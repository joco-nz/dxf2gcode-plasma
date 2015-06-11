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

from math import cos, sin, degrees, pi
from copy import deepcopy
import logging

from PyQt5 import QtCore

import Global.Globals as g
from Core.Point import Point
from Core.LineGeo import LineGeo
from Core.ArcGeo import ArcGeo


logger = logging.getLogger("Core.Shape")


class Shape(object):
    """
    The Shape Class includes all plotting, GUI functionality and export functions
    related to the Shapes.
    """
    def __init__(self, nr, closed,
                 parentEntity):
        """
        Standard method to initialize the class
        @param nr: The number of the shape. Starting from 0 for the first one
        @param closed: Gives information about the shape, when it is closed this
        value becomes 1
        @param cut_cor: Gives the selected Curring Correction of the shape
        (40=None, 41=Left, 42= Right)
        @param length: The total length of the shape including all geometries
        @param parent: The parent EntitieContent Class of the shape
        @param geow: The list with all geometries included in the shape
        @param axis3_mill_depth: Optional parameter for the export of the shape.
        If this parameter is None the mill_depth of the parent layer will be used.
        """
        self.type = "Shape"
        self.nr = nr
        self.closed = closed
        self.cut_cor = 40
        self.parentEntity = parentEntity
        self.parentLayer = None
        self.geos = []

        self.drawObject = 0
        self.drawArrowsDirection = 0
        self.drawStMove = 0
        self.stMove = None

        self.topLeft = None
        self.bottomRight = None

        self.send_to_TSP = g.config.vars.Route_Optimisation['default_TSP']

        self.selected = False
        self.disabled = False
        self.allowedToChange = True

        # preset defaults
        self.axis3_start_mill_depth = g.config.vars.Depth_Coordinates['axis3_start_mill_depth']
        self.axis3_slice_depth = g.config.vars.Depth_Coordinates['axis3_slice_depth']
        self.axis3_mill_depth = g.config.vars.Depth_Coordinates['axis3_mill_depth']
        self.f_g1_plane = g.config.vars.Feed_Rates['f_g1_plane']
        self.f_g1_depth = g.config.vars.Feed_Rates['f_g1_depth']
        # Parameters for drag knife
        self.dragAngle = g.config.vars.Drag_Knife_Options['dragAngle'] * pi / 180

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\ntype:        %s" % self.type +\
               "\nnr:          %i" % self.nr +\
               "\nclosed:      %i" % self.closed +\
               "\ncut_cor:     %s" % self.cut_cor +\
               "\nlen(geos):   %i" % len(self.geos) +\
               "\ngeos:        %s" % self.geos

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return QtCore.QCoreApplication.translate("ShapeClass", string_to_translate, None)

    def setSelected(self, flag=False):
        self.selected = flag

    def isSelected(self):
        return self.selected

    def setDisable(self, flag=False):
        self.disabled = flag

    def isDisabled(self):
        return self.disabled

    def setToolPathOptimized(self, flag=False):
        self.send_to_TSP = flag

    def isToolPathOptimized(self):
        return self.send_to_TSP

    def AnalyseAndOptimize(self):
        self.setNearestStPoint(Point())
        logger.debug(self.tr("Analysing the shape for CW direction Nr: %s" % self.nr))
        # By calculating the area of the shape

        start = self.geos[0].get_start_end_points(True)
        summe = 0.0
        for geo in self.geos:
            if isinstance(geo, LineGeo):
                end = geo.get_start_end_points(False)
                summe += (start.x + end.x) * (end.y - start.y)
                start = end
            elif isinstance(geo, ArcGeo):
                segments = 10
                for i in range(1, segments + 1):
                    end = geo.get_point_from_start(i, segments)
                    summe += (end.x + start.x) * (end.y - start.y)
                    start = end
        if not self.closed:
            # if shape is not closed... simply treat it as closed
            end = self.geos[0].get_start_end_points(True)
            summe += (end.x + start.x) * (end.y - start.y)

        if summe == 0:  # inconclusive
            logger.debug(self.tr("Shoelace method cannot (directly) be applied to this shape"))
            # lets take it clock wise with relation to the workpiece zero

            start = self.get_start_end_points(True)
            # get the farthest end point with relation to the start
            end = start
            distance2 = 0
            for geo in self.geos:
                pos_end = geo.get_start_end_points(False)
                pos_distance2 = (start - pos_end).length_squared()
                if pos_distance2 > distance2:
                    end = pos_end
                    distance2 = pos_distance2
            direction = start.to3D().cross_product(end.to3D()).z
            if -1e-5 < direction < 1e-5:  # start and end are aligned wrt to wp zero
                direction = start.length_squared() - end.length_squared()
            summe = direction

        if summe > 0.0:
            self.reverse()
            logger.debug(self.tr("Had to reverse the shape to be CW"))

    def setNearestStPoint(self, stPoint):
        if self.closed:
            logger.debug(self.tr("Clicked Point: %s" % stPoint))
            start = self.get_start_end_points(True)
            min_distance = start.distance(stPoint)

            logger.debug(self.tr("Old Start Point: %s" % start))

            min_geo_nr = 0
            for geo_nr in range(1, len(self.geos)):
                start = self.geos[geo_nr].get_start_end_points(True)

                if start.distance(stPoint) < min_distance:
                    min_distance = start.distance(stPoint)
                    min_geo_nr = geo_nr

            # Overwrite the geometries in changed order.
            self.geos = self.geos[min_geo_nr:] + self.geos[:min_geo_nr]

            start = self.get_start_end_points(True)
            logger.debug(self.tr("New Start Point: %s" % start))

    def reverse(self):
        self.geos.reverse()
        for geo in self.geos:
            geo.reverse()

    def switch_cut_cor(self):
        """
        Switches the cutter direction between 41 and 42.

        G41 = Tool radius compensation left.
        G42 = Tool radius compensation right
        """
        if self.cut_cor == 41:
            self.cut_cor = 42
        elif self.cut_cor == 42:
            self.cut_cor = 41

    def append(self, geo):
        geo.make_abs_geo(self.parentEntity)
        self.geos.append(geo)

    def get_start_end_points(self, start_point=None, angles=None):
        if start_point is None:
            return (self.geos[0].get_start_end_points(True, angles),
                    self.geos[-1].get_start_end_points(False, angles))
        elif start_point:
            return self.geos[0].get_start_end_points(True, angles)
        else:
            return self.geos[-1].get_start_end_points(False, angles)

    def make_path(self, drawHorLine, drawVerLine):
        for geo in self.geos:
            drawVerLine(geo.get_start_end_points(True), self.axis3_start_mill_depth, self.axis3_mill_depth)

            geo.make_path(self, drawHorLine)

            if self.topLeft is None:
                self.topLeft = deepcopy(geo.topLeft)
                self.bottomRight = deepcopy(geo.bottomRight)
            else:
                self.topLeft.detTopLeft(geo.topLeft)
                self.bottomRight.detBottomRight(geo.bottomRight)

        if not self.closed:
            drawVerLine(geo.get_start_end_points(False), self.axis3_start_mill_depth, self.axis3_mill_depth)

    def isHit(self, xy, tol):
        if self.topLeft.x - tol <= xy.x <= self.bottomRight.x + tol\
                and self.bottomRight.y - tol <= xy.y <= self.topLeft.y + tol:
            for geo in self.geos:
                if geo.isHit(self, xy, tol):
                    return True
        return False

    def Write_GCode(self, PostPro=None):
        """
        This method returns the string to be exported for this shape, including
        the defined start and end move of the shape.
        @param PostPro: this is the Postprocessor class including the methods
        to export
        """

        if g.config.machine_type == 'drag_knife':
            return self.Write_GCode_Drag_Knife(PostPro)

        # initialisation of the string
        exstr = ""

        # Calculate tool Radius.
        tool_rad = self.parentLayer.tool_diameter / 2

        # Get the mill settings defined in the GUI
        safe_retract_depth = self.parentLayer.axis3_retract
        safe_margin = self.parentLayer.axis3_safe_margin

        max_slice = self.axis3_slice_depth
        workpiece_top_Z = self.axis3_start_mill_depth
        # We want to mill the piece, even for the first pass, so remove one "slice"
        initial_mill_depth = workpiece_top_Z - abs(max_slice)
        depth = self.axis3_mill_depth
        f_g1_plane = self.f_g1_plane
        f_g1_depth = self.f_g1_depth

        # Save the initial Cutter correction in a variable
        has_reversed = False

        # If the Output Format is DXF do not perform more then one cut.
        if PostPro.vars.General["output_type"] == 'dxf':
            depth = max_slice

        if max_slice == 0:
            logger.error(self.tr("ERROR: Z infeed depth is null!"))

        if initial_mill_depth < depth:
            logger.warning(self.tr(
                "WARNING: initial mill depth (%i) is lower than end mill depth (%i). Using end mill depth as final depth.") % (
                               initial_mill_depth, depth))

            # Do not cut below the depth.
            initial_mill_depth = depth

        mom_depth = initial_mill_depth

        # Move the tool to the start.
        exstr += self.stMove.geos[0].Write_GCode(PostPro)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_pre_shape_cut()

        # Cutter radius compensation when G41 or G42 is on, AND cutter compensation option is set to be done outside the piece
        if self.cut_cor != 40 and PostPro.vars.General["cc_outside_the_piece"]:
            # Calculate the starting point without tool compensation
            # and add the compensation
            start = self.get_start_end_points(True)
            exstr += PostPro.set_cut_cor(self.cut_cor, start)

            exstr += PostPro.chg_feed_rate(f_g1_plane)
            exstr += self.stMove.geos[1].Write_GCode(PostPro)
            exstr += self.stMove.geos[2].Write_GCode(PostPro)

        exstr += PostPro.rap_pos_z(
            workpiece_top_Z + abs(safe_margin))  # Compute the safe margin from the initial mill depth
        exstr += PostPro.chg_feed_rate(f_g1_depth)
        exstr += PostPro.lin_pol_z(mom_depth)
        exstr += PostPro.chg_feed_rate(f_g1_plane)

        # Cutter radius compensation when G41 or G42 is on, AND cutter compensation option is set to be done inside the piece
        if self.cut_cor != 40 and not PostPro.vars.General["cc_outside_the_piece"]:
            # Calculate the starting point without tool compensation
            # and add the compensation
            start = self.get_start_end_points(True)
            exstr += PostPro.set_cut_cor(self.cut_cor, start)

            exstr += self.stMove.geos[1].Write_GCode(PostPro)
            exstr += self.stMove.geos[2].Write_GCode(PostPro)

        # Write the geometries for the first cut
        for geo in self.geos:
            exstr += geo.Write_GCode(PostPro)

        # Turning the cutter radius compensation
        if self.cut_cor != 40 and PostPro.vars.General["cancel_cc_for_depth"]:
            ende, en_angle = self.get_start_end_points(False, True)
            if self.cut_cor == 41:
                pos_cut_out = ende.get_arc_point(en_angle - pi / 2, tool_rad)
            elif self.cut_cor == 42:
                pos_cut_out = ende.get_arc_point(en_angle + pi / 2, tool_rad)
            exstr += PostPro.deactivate_cut_cor(pos_cut_out)

        # Numbers of loops
        snr = 0
        # Loops for the number of cuts
        while mom_depth > depth and max_slice != 0.0:
            snr += 1
            mom_depth = mom_depth - abs(max_slice)
            if mom_depth < depth:
                mom_depth = depth

            # Erneutes Eintauchen
            exstr += PostPro.chg_feed_rate(f_g1_depth)
            exstr += PostPro.lin_pol_z(mom_depth)
            exstr += PostPro.chg_feed_rate(f_g1_plane)

            # If it is not a closed contour
            if not self.closed:
                self.reverse()
                self.switch_cut_cor()
                has_reversed = not has_reversed  # switch the "reversed" state (in order to restore it at the end)

                # If cutter radius compensation is turned on. Turn it off - because some interpreters cannot handle
                # a switch
                if self.cut_cor != 40 and not PostPro.vars.General["cancel_cc_for_depth"]:
                    # Calculate the contour values - with cutter radius compensation and without
                    ende = self.get_start_end_points(False)
                    exstr += PostPro.deactivate_cut_cor(ende)

            # If cutter correction is enabled
            if self.cut_cor != 40 and not self.closed or PostPro.vars.General["cancel_cc_for_depth"]:
                # Calculate the starting point without tool compensation
                # and add the compensation
                start = self.get_start_end_points(True)
                exstr += PostPro.set_cut_cor(self.cut_cor, start)

            for geo_nr in range(len(self.geos)):
                exstr += self.geos[geo_nr].Write_GCode(PostPro)

            # Turning off the cutter radius compensation if needed
            if self.cut_cor != 40 and PostPro.vars.General["cancel_cc_for_depth"]:
                ende, en_angle = self.get_start_end_points(False, True)
                if self.cut_cor == 41:
                    pos_cut_out = ende.get_arc_point(en_angle - pi / 2, tool_rad)
                elif self.cut_cor == 42:
                    pos_cut_out = ende.get_arc_point(en_angle + pi / 2, tool_rad)
                exstr += PostPro.deactivate_cut_cor(pos_cut_out)

        # Do the tool retraction
        exstr += PostPro.chg_feed_rate(f_g1_depth)
        exstr += PostPro.lin_pol_z(workpiece_top_Z + abs(safe_margin))
        exstr += PostPro.rap_pos_z(safe_retract_depth)

        # If cutter radius compensation is turned on.
        if self.cut_cor != 40 and not PostPro.vars.General["cancel_cc_for_depth"]:
            # Calculate the contour values - with cutter radius compensation and without
            ende = self.get_start_end_points(False)
            exstr += PostPro.deactivate_cut_cor(ende)

        # Initial value of direction restored if necessary
        if has_reversed:
            self.reverse()
            self.switch_cut_cor()

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_post_shape_cut()

        return exstr

    def Write_GCode_Drag_Knife(self, PostPro=None):
        """
        This method returns the string to be exported for this shape, including
        the defined start and end move of the shape. This function is used for
        Drag Knife cutting machine only.
        @param PostPro: this is the Postprocessor class including the methods
        to export
        """

        # initialisation of the string
        exstr = ""

        # Get the mill settings defined in the GUI
        safe_retract_depth = self.parentLayer.axis3_retract
        safe_margin = self.parentLayer.axis3_safe_margin

        workpiece_top_Z = self.axis3_start_mill_depth
        f_g1_plane = self.f_g1_plane
        f_g1_depth = self.f_g1_depth

        """
        Cutting in slices is not supported for Swivel Knife tool. All is cut at once.
        """
        mom_depth = self.axis3_mill_depth
        drag_depth = self.axis3_slice_depth

        # Move the tool to the start.
        exstr += self.stMove.geos[0].Write_GCode(PostPro)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_pre_shape_cut()

        # Move into workpiece and start cutting into Z
        exstr += PostPro.rap_pos_z(
            workpiece_top_Z + abs(safe_margin))  # Compute the safe margin from the initial mill depth
        exstr += PostPro.chg_feed_rate(f_g1_depth)

        # Write the geometries for the first cut
        if self.stMove.geos[1].type == "ArcGeo":
            if self.stMove.geos[1].drag:
                exstr += PostPro.lin_pol_z(drag_depth)
                drag = True
            else:
                exstr += PostPro.lin_pol_z(mom_depth)
                drag = False
        else:
            exstr += PostPro.lin_pol_z(mom_depth)
            drag = False
        exstr += PostPro.chg_feed_rate(f_g1_plane)

        exstr += self.stMove.geos[1].Write_GCode(PostPro)

        for geo in self.stMove.geos[2:]:
            if geo.type == "ArcGeo":
                if geo.drag:
                    exstr += PostPro.chg_feed_rate(f_g1_depth)
                    exstr += PostPro.lin_pol_z(drag_depth)
                    exstr += PostPro.chg_feed_rate(f_g1_plane)
                    drag = True
                elif drag:
                    exstr += PostPro.chg_feed_rate(f_g1_depth)
                    exstr += PostPro.lin_pol_z(mom_depth)
                    exstr += PostPro.chg_feed_rate(f_g1_plane)
                    drag = False
            elif drag:
                exstr += PostPro.chg_feed_rate(f_g1_depth)
                exstr += PostPro.lin_pol_z(mom_depth)
                exstr += PostPro.chg_feed_rate(f_g1_plane)
                drag = False

            exstr += geo.Write_GCode(PostPro)

        # Do the tool retraction
        exstr += PostPro.chg_feed_rate(f_g1_depth)
        exstr += PostPro.lin_pol_z(workpiece_top_Z + abs(safe_margin))
        exstr += PostPro.rap_pos_z(safe_retract_depth)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_post_shape_cut()

        return exstr
