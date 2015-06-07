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

from math import cos, sin, degrees
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
        logger.debug(self.tr("Analysing the shape for CW direction Nr: %s" % self.nr))
        # Optimization for closed shapes
        if self.closed:
            # Start value for the first sum
            start = self.geos[0].get_start_end_points(True)
            summe = 0.0
            for geo in self.geos:
                if isinstance(geo, LineGeo):
                    end = geo.get_start_end_points(False)
                    summe += (start.x + end.x) * (end.y - start.y) / 2
                    start = end
                elif isinstance(geo, ArcGeo):
                    segments = int((abs(degrees(geo.ext)) // 90) + 1)
                    for i in range(segments):
                        ang = geo.s_ang + (i + 1) * geo.ext / segments
                        end = Point(geo.O.x + cos(ang) * abs(geo.r),
                                    geo.O.y + sin(ang) * abs(geo.r))
                        summe += (start.x + end.x) * (end.y - start.y) / 2
                        start = end

            if summe > 0.0:
                self.reverse()
                logger.debug(self.tr("Had to reverse the shape to be cw"))

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
            self.geos = self.geos[min_geo_nr:len(self.geos)] + self.geos[0:min_geo_nr]

            start = self.get_start_end_points(True)
            logger.debug(self.tr("New Start Point: %s" % start))

    def reverse(self):
        self.geos.reverse()
        for geo in self.geos:
            geo.reverse()

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
            drawVerLine(geo.Ps.rot_sca_abs(parent=self.parentEntity), self.axis3_start_mill_depth, self.axis3_mill_depth)

            geo.make_path(self, drawHorLine)

            if self.topLeft is None:
                self.topLeft = deepcopy(geo.topLeft)
                self.bottomRight = deepcopy(geo.bottomRight)
            else:
                self.topLeft.detTopLeft(geo.topLeft)
                self.bottomRight.detBottomRight(geo.bottomRight)

        if not self.closed:
            drawVerLine(geo.Pe.rot_sca_abs(parent=self.parentEntity), self.axis3_start_mill_depth, self.axis3_mill_depth)

    def isHit(self, xy, tol):
        if self.topLeft.x - tol <= xy.x <= self.bottomRight.x + tol\
                and self.bottomRight.y - tol <= xy.y <= self.topLeft.y + tol:
            for geo in self.geos:
                if geo.isHit(self, xy, tol):
                    return True
        return False
       
    def Write_GCode(self, LayerContent=None, PostPro=None):
        """
        This method returns the string to be exported for this shape, including
        the defined start and end move of the shape.
        @param LayerContent: This parameter includes the parent LayerContent
        which includes tool and additional cutting parameters.
        @param PostPro: this is the Postprocessor class including the methods
        to export
        """

        if g.config.machine_type == 'drag_knife':
            return self.Write_GCode_Drag_Knife(LayerContent=LayerContent,
                                               PostPro=PostPro)

        # initialisation of the string
        exstr = ""

        # Create the Start_moves once again if something was changed.
        self.stmove.make_start_moves()

        # Calculate tool Radius.
        tool_rad = LayerContent.tool_diameter / 2

        # Get the mill settings defined in the GUI
        safe_retract_depth = LayerContent.axis3_retract
        safe_margin = LayerContent.axis3_safe_margin
        # If defined, choose the parameters from the Shape itself. Otherwise, choose the parameters from the parent Layer
        max_slice = LayerContent.axis3_slice_depth if self.axis3_slice_depth is None else self.axis3_slice_depth
        workpiece_top_Z = LayerContent.axis3_start_mill_depth if self.axis3_start_mill_depth is None else self.axis3_start_mill_depth
        # We want to mill the piece, even for the first pass, so remove one "slice"
        initial_mill_depth = workpiece_top_Z - abs(max_slice)
        depth = LayerContent.axis3_mill_depth if self.axis3_mill_depth is None else self.axis3_mill_depth
        f_g1_plane = LayerContent.f_g1_plane if self.f_g1_plane is None else self.f_g1_plane
        f_g1_depth = LayerContent.f_g1_depth if self.f_g1_depth is None else self.f_g1_depth

        # Save the initial Cutter correction in a variable
        has_reversed = 0

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
        exstr += self.stmove.geos[0].Write_GCode(parent=self.stmove.parent,
                                                 PostPro=PostPro)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_pre_shape_cut()

        # Cutter radius compensation when G41 or G42 is on, AND cutter compensation option is set to be done outside the piece
        if self.cut_cor != 40 and PostPro.vars.General["cc_outside_the_piece"]:
            # Calculate the starting point without tool compensation
            # and add the compensation
            start, start_ang = self.get_st_en_points(0)
            exstr += PostPro.set_cut_cor(self.cut_cor, start)

            exstr += PostPro.chg_feed_rate(f_g1_plane)  # Added by Xavier because of code move (see above)
            exstr += self.stmove.geos[1].Write_GCode(parent=self.stmove.parent, PostPro=PostPro)
            exstr += self.stmove.geos[2].Write_GCode(parent=self.stmove.parent, PostPro=PostPro)

        exstr += PostPro.rap_pos_z(
            workpiece_top_Z + abs(safe_margin))  # Compute the safe margin from the initial mill depth
        exstr += PostPro.chg_feed_rate(f_g1_depth)
        exstr += PostPro.lin_pol_z(mom_depth)
        exstr += PostPro.chg_feed_rate(f_g1_plane)

        # Cutter radius compensation when G41 or G42 is on, AND cutter compensation option is set to be done inside the piece
        if self.cut_cor != 40 and not PostPro.vars.General["cc_outside_the_piece"]:
            # Calculate the starting point without tool compensation
            # and add the compensation
            start, start_ang = self.get_st_en_points(0)
            exstr += PostPro.set_cut_cor(self.cut_cor, start)

            exstr += self.stmove.geos[1].Write_GCode(parent=self.stmove.parent, PostPro=PostPro)
            exstr += self.stmove.geos[2].Write_GCode(parent=self.stmove.parent, PostPro=PostPro)

        # Write the geometries for the first cut
        for geo in self.geos:
            exstr += geo.Write_GCode(self.parent, PostPro)

        # Turning the cutter radius compensation
        if (not (self.cut_cor == 40)) & (PostPro.vars.General["cancel_cc_for_depth"] == 1):
            ende, en_angle = self.get_st_en_points(1)
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
            if self.closed == 0:
                self.reverse()
                self.switch_cut_cor()
                has_reversed = 1 - has_reversed  # switch the "reversed" state (in order to restore it at the end)

            # If cutter correction is enabled
            if ((not (self.cut_cor == 40)) & (self.closed == 0)) or (PostPro.vars.General["cancel_cc_for_depth"] == 1):
                # Calculate the starting point without tool compensation
                # and add the compensation
                start, start_ang = self.get_st_en_points(0)
                exstr += PostPro.set_cut_cor(self.cut_cor, start)

            for geo_nr in range(len(self.geos)):
                exstr += self.geos[geo_nr].Write_GCode(self.parent, PostPro)

            # Calculate the contour values with cutter radius compensation and without
            ende, en_angle = self.get_st_en_points(1)
            if self.cut_cor == 41:
                pos_cut_out = ende.get_arc_point(en_angle - pi / 2, tool_rad)
            elif self.cut_cor == 42:
                pos_cut_out = ende.get_arc_point(en_angle + pi / 2, tool_rad)

            # Turning off the cutter radius compensation if needed
            if (not (self.cut_cor == 40)) & (PostPro.vars.General["cancel_cc_for_depth"] == 1):
                exstr += PostPro.deactivate_cut_cor(pos_cut_out)

        # Do the tool retraction
        exstr += PostPro.chg_feed_rate(f_g1_depth)
        exstr += PostPro.lin_pol_z(workpiece_top_Z + abs(safe_margin))
        exstr += PostPro.rap_pos_z(safe_retract_depth)

        # If cutter radius compensation is turned on.
        if (not (self.cut_cor == 40)) & (not (PostPro.vars.General["cancel_cc_for_depth"])):
            # Calculate the contour values - with cutter radius compensation and without
            ende, en_angle = self.get_st_en_points(1)
            exstr += PostPro.deactivate_cut_cor(ende)

        # Initial value of direction restored if necessary
        if has_reversed != 0:
            self.reverse()
            self.switch_cut_cor()

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_post_shape_cut()

        return exstr

    def Write_GCode_Drag_Knife(self, LayerContent=None, PostPro=None):
        """
        This method returns the string to be exported for this shape, including
        the defined start and end move of the shape. This function is used for
        Drag Knife cutting machine only.
        @param LayerContent: This parameter includes the parent LayerContent
        which includes tool and additional cutting parameters.
        @param PostPro: this is the Postprocessor class including the methods
        to export
        """

        # initialisation of the string
        exstr = ""

        # Create the Start_moves once again if something was changed.
        self.stmove.make_start_moves()

        # Get the mill settings defined in the GUI
        safe_retract_depth = LayerContent.axis3_retract
        safe_margin = LayerContent.axis3_safe_margin
        # If defined, choose the parameters from the Shape itself. Otherwise, choose the parameters from the parent Layer
        workpiece_top_Z = LayerContent.axis3_start_mill_depth if self.axis3_start_mill_depth is None else self.axis3_start_mill_depth
        f_g1_plane = LayerContent.f_g1_plane if self.f_g1_plane is None else self.f_g1_plane
        f_g1_depth = LayerContent.f_g1_depth if self.f_g1_depth is None else self.f_g1_depth

        """
        Cutting in slices is not supported for Swivel Knife tool. All is cut at once.
        """
        mom_depth = LayerContent.axis3_mill_depth if self.axis3_mill_depth is None else self.axis3_mill_depth
        drag_depth = LayerContent.axis3_slice_depth if self.axis3_slice_depth is None else self.axis3_slice_depth

        # Move the tool to the start.
        exstr += self.stmove.geos[0].Write_GCode(parent=self.stmove.parent, PostPro=PostPro)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_pre_shape_cut()

        # Move into workpiece and start cutting into Z
        exstr += PostPro.rap_pos_z(
            workpiece_top_Z + abs(safe_margin))  # Compute the safe margin from the initial mill depth
        exstr += PostPro.chg_feed_rate(f_g1_depth)

        # Write the geometries for the first cut
        if self.stmove.geos[1].type == "ArcGeo":
            if self.stmove.geos[1].drag:
                exstr += PostPro.lin_pol_z(drag_depth)
                drag = True
            else:
                exstr += PostPro.lin_pol_z(mom_depth)
                drag = False
        else:
            exstr += PostPro.lin_pol_z(mom_depth)
            drag = False
        exstr += PostPro.chg_feed_rate(f_g1_plane)

        exstr += self.stmove.geos[1].Write_GCode(parent=self.stmove.parent, PostPro=PostPro)

        for geo in self.stmove.geos[2:]:
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

            exstr += geo.Write_GCode(parent=self.stmove.parent, PostPro=PostPro)

        # Do the tool retraction
        exstr += PostPro.chg_feed_rate(f_g1_depth)
        exstr += PostPro.lin_pol_z(workpiece_top_Z + abs(safe_margin))
        exstr += PostPro.rap_pos_z(safe_retract_depth)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_post_shape_cut()

        return exstr