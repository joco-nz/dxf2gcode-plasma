#!/usr/bin/env python

############################################################################
#
#   Copyright (C) 2010-2015
#    Christian Kohlöffel
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

import sys
import os
import logging
from math import degrees, radians
from copy import copy, deepcopy

from PyQt5.QtCore import Qt, QLocale, QTranslator, QCoreApplication
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog

from Core.EntityContent import EntityContent
from Core.LayerContent import LayerContent
from Core.Shape import Shape
from Core.LineGeo import LineGeo
from Core.HoleGeo import HoleGeo
import Global.Globals as g
from Global.config import MyConfig
from Global.logger import LoggerClass
from Core.Point import Point
from DxfImport.Import import ReadDXF
from Gui.PopUpDialog import PopUpDialog
from Gui.TreeHandling import TreeHandler
from dxf2gcode_ui import Ui_MainWindow


logger = logging.getLogger()

# Get folder of the main instance and write into globals
g.folder = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
if os.path.islink(sys.argv[0]):
    g.folder = os.path.dirname(os.readlink(sys.argv[0]))


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.ui = Ui_MainWindow()

        self.ui.setupUi(self)

        self.glWidget = self.ui.canvas

        self.TreeHandler = TreeHandler(self.ui)

        self.createActions()
        self.connectToolbarToConfig()

        self.filename = ""

        self.shapes = []
        self.entityRoot = None
        self.layerContents = []

        self.cont_dx = 0.0
        self.cont_dy = 0.0
        self.cont_rotate = 0.0
        self.cont_scale = 1.0

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return QCoreApplication.translate("Main", string_to_translate, None)

    def createActions(self):
        # File
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionReload.triggered.connect(self.reload)
        self.ui.actionClose.triggered.connect(self.close)

        # View
        self.ui.actionAutoscale.triggered.connect(self.glWidget.autoScale)
        self.ui.actionTopView.triggered.connect(self.glWidget.topView)
        self.ui.actionIsometricView.triggered.connect(self.glWidget.isometricView)

        # Options
        self.ui.actionTolerances.triggered.connect(self.setTolerances)
        self.ui.actionRotateAll.triggered.connect(self.rotateAll)
        self.ui.actionScaleAll.triggered.connect(self.scaleAll)
        self.ui.actionMoveWorkpieceZero.triggered.connect(self.moveWorkpieceZero)
        self.ui.actionSplitLineSegments.triggered.connect(self.reload)  # TODO no need to redo the importing
        self.ui.actionMilling.triggered.connect(self.setMachineTypeToMilling)
        self.ui.actionDragKnife.triggered.connect(self.setMachineTypeToDragKnife)
        self.ui.actionLathe.triggered.connect(self.setMachineTypeToLathe)

    def connectToolbarToConfig(self):
        # Options
        if g.config.vars.General['split_line_segments']:
            self.ui.actionSplitLineSegments.setChecked(True)
        if g.config.vars.General['automatic_cutter_compensation']:
            self.ui.actionAutomaticCutterCompensation.setChecked(True)
        self.updateMachineType()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.glWidget.isMultiSelect = True
        elif event.key() == Qt.Key_Shift:
            self.glWidget.isPanning = True
            self.glWidget.setCursor(Qt.OpenHandCursor)
        elif event.key() == Qt.Key_Alt:
            self.glWidget.isRotating = True
            self.glWidget.setCursor(Qt.PointingHandCursor)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.glWidget.isMultiSelect = False
        elif event.key() == Qt.Key_Shift:
            self.glWidget.isPanning = False
            self.glWidget.unsetCursor()
        elif event.key() == Qt.Key_Alt:
            self.glWidget.isRotating = False
            if -5 < self.glWidget.rotX < 5 and\
               -5 < self.glWidget.rotY < 5 and\
               -5 < self.glWidget.rotZ < 5:
                self.glWidget.rotX = 0
                self.glWidget.rotY = 0
                self.glWidget.rotZ = 0
                self.glWidget.update()
            self.glWidget.unsetCursor()

    def enableToolbarButtons(self, status=True):
        # File
        self.ui.actionReload.setEnabled(status)

        # Export
        self.ui.actionOptimizePaths.setEnabled(status)
        self.ui.actionExportShapes.setEnabled(status)
        self.ui.actionOptimizeAndExportShapes.setEnabled(status)

        # View
        self.ui.actionAutoscale.setEnabled(status)
        self.ui.actionTopView.setEnabled(status)
        self.ui.actionIsometricView.setEnabled(status)

        # Options
        self.ui.actionTolerances.setEnabled(status)
        self.ui.actionRotateAll.setEnabled(status)
        self.ui.actionScaleAll.setEnabled(status)
        self.ui.actionMoveWorkpieceZero.setEnabled(status)

    def setTolerances(self):
        title = self.tr('Contour tolerances')
        units = "[in]" if g.config.metric == 0 else "[mm]"
        label = [self.tr("Tolerance for common points %s:") % units,
                 self.tr("Tolerance for curve fitting %s:") % units]
        value = [g.config.point_tolerance,
                 g.config.fitting_tolerance]

        logger.debug(self.tr("set Tolerances"))
        SetTolDialog = PopUpDialog(title, label, value)

        if SetTolDialog.result == None:
            return

        g.config.point_tolerance = float(SetTolDialog.result[0])
        g.config.fitting_tolerance = float(SetTolDialog.result[1])

        self.reload()

    def scaleAll(self):
        title = self.tr('Scale Contour')
        label = [self.tr("Scale Contour by factor:")]
        value = [self.cont_scale]
        ScaEntDialog = PopUpDialog(title, label, value)

        if ScaEntDialog.result == None:
            return

        self.cont_scale = float(ScaEntDialog.result[0])
        self.entityRoot.sca = self.cont_scale

        self.reload()

    def rotateAll(self):
        title = self.tr('Rotate Contour')
        label = [self.tr("Rotate Contour by deg:")]  # TODO should we support radians for drawing unit non metric?
        value = [degrees(self.cont_rotate)]
        RotEntDialog = PopUpDialog(title, label, value)

        if RotEntDialog.result is None:
            return

        self.cont_rotate = radians(float(RotEntDialog.result[0]))
        self.entityRoot.rot = self.cont_rotate

        self.reload()

    def moveWorkpieceZero(self):
        title = self.tr('Workpiece zero offset')
        units = "[in]" if g.config.metric == 0 else "[mm]"
        label = [self.tr("Offset %s axis %s:") % (g.config.vars.Axis_letters['ax1_letter'], units),
                 self.tr("Offset %s axis %s:") % (g.config.vars.Axis_letters['ax2_letter'], units)]
        value = [self.cont_dx, self.cont_dy]
        MoveWpzDialog = PopUpDialog(title, label, value, True)

        if MoveWpzDialog.result is None:
            return

        if MoveWpzDialog.result == 'Auto':
            minx = sys.float_info.max
            miny = sys.float_info.max
            for shape in self.shapes:
                if not(shape.isDisabled()):
                    minx = min(minx, shape.topLeft.x)
                    miny = min(miny, shape.bottomRight.y)
            self.cont_dx = self.entityRoot.p0.x - minx
            self.cont_dy = self.entityRoot.p0.y - miny
        else:
            self.cont_dx = float(MoveWpzDialog.result[0])
            self.cont_dy = float(MoveWpzDialog.result[1])

        self.entityRoot.p0.x = self.cont_dx
        self.entityRoot.p0.y = self.cont_dy

        self.reload()

    def setMachineTypeToMilling(self):
        g.config.machine_type = 'milling'
        self.updateMachineType()
        self.reload()

    def setMachineTypeToDragKnife(self):
        g.config.machine_type = 'drag_knife'
        self.updateMachineType()
        self.reload()

    def setMachineTypeToLathe(self):
        g.config.machine_type = 'lathe'
        self.updateMachineType()
        self.reload()

    def updateMachineType(self):
        if g.config.machine_type == 'milling':
            self.ui.actionAutomaticCutterCompensation.setEnabled(True)
            self.ui.actionMilling.setChecked(True)
            self.ui.actionDragKnife.setChecked(False)
            self.ui.actionLathe.setChecked(False)
            self.ui.label_9.setText(self.tr("Z Infeed depth"))
        elif g.config.machine_type == 'lathe':
            self.ui.actionAutomaticCutterCompensation.setEnabled(False)
            self.ui.actionMilling.setChecked(False)
            self.ui.actionDragKnife.setChecked(False)
            self.ui.actionLathe.setChecked(True)
            self.ui.label_9.setText(self.tr("No Z-Axis for lathe"))
        elif g.config.machine_type == "drag_knife":
            self.ui.actionAutomaticCutterCompensation.setEnabled(False)
            self.ui.actionMilling.setChecked(False)
            self.ui.actionDragKnife.setChecked(True)
            self.ui.actionLathe.setChecked(False)
            self.ui.label_9.setText(self.tr("Z Drag depth"))

    def open(self):
        self.filename, _ = QFileDialog.getOpenFileName(self, 'Open File', '',
                                                       # "All supported files (*.dxf *.ps *.pdf);;"
                                                       "DXF files (*.dxf);;"
                                                       # "PS files (*.ps);;"
                                                       # "PDF files (*.pdf);;"
                                                       "All types (*.*)")

        if self.filename:
            logger.info(self.tr("File: %s selected" % self.filename))
            self.setWindowTitle("DXF2GCODE - [%s]" % self.filename)
            self.load(self.filename)

    def load(self, filename):
        """
        Loads the file given by filename.  Also calls the command to
        make the plot.
        @param filename: String containing filename which should be loaded
        """
        self.glWidget.setCursor(Qt.WaitCursor)
        self.glWidget.resetAll()

        logger.info(self.tr('Loading file: %s' % filename))

        values = ReadDXF(filename)

        # Output the information in the text window
        logger.info(self.tr('Loaded layers: %s' % len(values.layers)))
        logger.info(self.tr('Loaded blocks: %s' % len(values.blocks.Entities)))
        for i in range(len(values.blocks.Entities)):
            layers = values.blocks.Entities[i].get_used_layers()
            logger.info(self.tr('Block %i includes %i Geometries; reduced to %i Contours; used layers %s'
                        % (i, len(values.blocks.Entities[i].geo), len(values.blocks.Entities[i].cont), layers)))
        layers = values.entities.get_used_layers()
        insert_nr = values.entities.get_insert_nr()
        logger.info(self.tr('Loaded %i entity geometries; reduced to %i contours; used layers %s; number of inserts %i'
                    % (len(values.entities.geo), len(values.entities.cont), layers, insert_nr)))

        if g.config.metric == 0:
            logger.info("Drawing units: inches")
            self.ui.unitLabel_3.setText("[in]")
            self.ui.unitLabel_4.setText("[in]")
            self.ui.unitLabel_5.setText("[in]")
            self.ui.unitLabel_6.setText("[in]")
            self.ui.unitLabel_7.setText("[in]")
            self.ui.unitLabel_8.setText("[IPM]")
            self.ui.unitLabel_9.setText("[IPM]")
        else:
            logger.info("Drawing units: millimeters")
            self.ui.unitLabel_3.setText("[mm]")
            self.ui.unitLabel_4.setText("[mm]")
            self.ui.unitLabel_5.setText("[mm]")
            self.ui.unitLabel_6.setText("[mm]")
            self.ui.unitLabel_7.setText("[mm]")
            self.ui.unitLabel_8.setText("[mm/min]")
            self.ui.unitLabel_9.setText("[mm/min]")

        self.makeShapes(values, Point(self.cont_dx, self.cont_dy), Point(),
                        [self.cont_scale, self.cont_scale, self.cont_scale],
                        self.cont_rotate)

        # Populate the treeViews
        self.TreeHandler.buildEntitiesTree(self.entityRoot)
        self.TreeHandler.buildLayerTree(self.layerContents)

        # Paint the canvas
        for shape in self.shapes:
            self.glWidget.addShape(shape)
        self.glWidget.drawWpZero()
        self.glWidget.drawOrientationArrows()
        self.glWidget.autoScale()

        self.enableToolbarButtons()

        self.glWidget.unsetCursor()

    def reload(self):
        """
        This function is called by the menu "File/Reload File" of the main toolbar.
        It reloads the previously loaded file (if any)
        """

        logger.info(self.tr("Reloading file: %s") % self.filename)
        self.load(self.filename)

    def makeShapes(self, values, p0, pb, sca, rot):
        self.entityRoot = EntityContent(nr=0, name='Entities',
                                        parent=None,
                                        p0=p0, pb=pb, sca=sca, rot=rot)
        del (self.layerContents[:])
        del (self.shapes[:])

        self.makeEntityShapes(values, self.entityRoot)

        self.layerContents.sort(key=lambda x: x.nr)

    def makeEntityShapes(self, values, parent):
        """
        Instance is called prior to plotting the shapes. It creates
        all shape classes which are plotted into the canvas.

        @param parent: The parent of a shape is always an Entity. It may be the root
        or, if it is a Block, this is the Block.
        """

        if parent.name == "Entities":
            entities = values.entities
        else:
            ent_nr = values.Get_Block_Nr(parent.name)
            entities = values.blocks.Entities[ent_nr]

        # Assigning the geometries in the variables geos & contours in cont
        ent_geos = entities.geo

        # Loop for the number of contours
        for cont in entities.cont:
            # Query if it is in the contour of an insert or of a block
            if ent_geos[cont.order[0][0]].Typ == "Insert":
                ent_geo = ent_geos[cont.order[0][0]]

                # Assign the base point for the block
                new_ent_nr = values.Get_Block_Nr(ent_geo.BlockName)
                new_entities = values.blocks.Entities[new_ent_nr]
                pb = new_entities.basep

                # Scaling, etc. assign the block
                p0 = ent_geos[cont.order[0][0]].Point
                sca = ent_geos[cont.order[0][0]].Scale
                rot = ent_geos[cont.order[0][0]].rot

                # Creating the new Entitie Contents for the insert
                newEntityContent = EntityContent(nr=0,
                                                 name=ent_geo.BlockName,
                                                 parent=parent,
                                                 p0=p0,
                                                 pb=pb,
                                                 sca=sca,
                                                 rot=rot)

                parent.append(newEntityContent)

                self.makeEntityShapes(values, newEntityContent)

            else:
                # Loop for the number of geometries
                tmp_shape = Shape(len(self.shapes),
                                  cont.closed,
                                  parent)

                for ent_geo_nr in range(len(cont.order)):
                    ent_geo = ent_geos[cont.order[ent_geo_nr][0]]
                    if cont.order[ent_geo_nr][1]:
                        ent_geo.geo.reverse()
                        for geo in ent_geo.geo:
                            geo = copy(geo)
                            geo.reverse()
                            self.append_geo_to_shape(tmp_shape, geo)
                        ent_geo.geo.reverse()
                    else:
                        for geo in ent_geo.geo:
                            self.append_geo_to_shape(tmp_shape, copy(geo))

                if len(tmp_shape.geos) > 0:
                    # All shapes have to be CCW direction.
                    tmp_shape.AnalyseAndOptimize()
                    tmp_shape.setNearestStPoint(parent.pb)

                    self.shapes.append(tmp_shape)
                    self.addtoLayerContents(values, tmp_shape, ent_geo.Layer_Nr)
                    parent.append(tmp_shape)

    def append_geo_to_shape(self, shape, geo):
        if geo.length == 0:  # TODO adjust import for this
            return

        if self.ui.actionSplitLineSegments.isChecked():
            if isinstance(geo, LineGeo):
                diff = (geo.Pe - geo.Ps) / 2.0
                geo_b = deepcopy(geo)
                geo_a = deepcopy(geo)
                geo_b.Pe -= diff
                geo_a.Ps += diff
                shape.append(geo_b)
                shape.append(geo_a)
            else:
                shape.append(geo)
        else:
            shape.append(geo)

        if isinstance(geo, HoleGeo):
            shape.type = 'Hole'
            shape.closed = 1  # TODO adjust import for holes?
            if g.config.machine_type == 'drag_knife':
                shape.disabled = True
                shape.allowedToChange = False

    def addtoLayerContents(self, values, shape, lay_nr):
        # Check if the layer already exists and add shape if it is.
        for LayCon in self.layerContents:
            if LayCon.nr == lay_nr:
                LayCon.shapes.append(shape)
                shape.parentLayer = LayCon
                return

        # If the Layer does not exist create a new one.
        LayerName = values.layers[lay_nr].name
        self.layerContents.append(LayerContent(lay_nr, LayerName, [shape]))
        shape.parentLayer = self.layerContents[-1]


if __name__ == '__main__':
    app = QApplication(sys.argv)

    fmt = QSurfaceFormat()
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    Log = LoggerClass(logger)

    g.config = MyConfig()
    Log.set_console_handler_loglevel()
    Log.add_file_logger()

    #Get local language and install if available.
    locale = QLocale.system().name()
    logger.debug("locale: %s" %locale)
    translator = QTranslator()
    if translator.load("dxf2gcode_" + locale, "./i18n"):
        app.installTranslator(translator)

    window = MainWindow()
    g.window = window
    Log.add_window_logger(window.ui.messageBox)
    window.show()

    sys.exit(app.exec_())
