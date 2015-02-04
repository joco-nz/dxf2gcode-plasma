#!/usr/bin/python
# -*- coding: utf-8 -*-

############################################################################
#   
#   Copyright (C) 2010-2014
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

# Import Qt modules

import os
import sys

from math import degrees, radians

import logging
logger = logging.getLogger()
from Core.Logger import LoggerClass

import time

from copy import copy, deepcopy

import subprocess, tempfile #webbrowser, gettext, tempfile

import argparse
from PyQt4 import QtGui, QtCore

# Import the compiled UI module
from dxf2gcode_pyQt4_ui.dxf2gcode_pyQt4_ui import Ui_MainWindow


from Core.Config import MyConfig
from Core.Point import Point
from Core.LayerContent import LayerContentClass
from Core.EntitieContent import EntitieContentClass
import Core.Globals as g
import Core.constants as c
from Core.Shape import ShapeClass

from PostPro.PostProcessor import MyPostProcessor
from PostPro.Breaks import Breaks

from DxfImport.Import import ReadDXF

from Gui.myCanvasClass import MyGraphicsScene
from Gui.TreeHandling import TreeHandler
from Gui.Dialog import myDialog
from Gui.AboutDialog import myAboutDialog

from PostPro.TspOptimisation import TSPoptimize

# Get folder of the main instance and write into globals
g.folder = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
if os.path.islink(sys.argv[0]):
    g.folder = os.path.dirname(os.readlink(sys.argv[0]))

# Create a class for our main window
class Main(QtGui.QMainWindow):
    """Main Class"""

    def __init__(self, app):
        """
        Initialization of the Main window. This is directly called after the 
        Logger has been initialized. The Function loads the GUI, creates the
        used Classes and connects the actions to the GUI.
        """
        
        QtGui.QMainWindow.__init__(self)
        
        # This is always the same
        self.app = app
        
        self.ui = Ui_MainWindow()
        
        self.ui.setupUi(self)
        
        self.createActions()
        
        self.MyGraphicsView = self.ui.MyGraphicsView
        
        self.myMessageBox = self.ui.myMessageBox
        
        self.MyPostProcessor = MyPostProcessor()
        
        self.TreeHandler = TreeHandler(self.ui)
        
        self.shapes = []
        self.LayerContents = []
        self.EntitieContents = []
        self.EntitiesRoot = []
        
        self.filename = "" #loaded file name
        
        QtCore.QObject.connect(self.TreeHandler,
                               QtCore.SIGNAL("exportOrderUpdated"),
                               self.updateExportRoute)
        
        if g.config.vars.General['live_update_export_route']:
            self.ui.actionLive_update_export_route.setChecked(True)
        
        if g.config.vars.General['default_SplitEdges']:
            self.ui.actionSplit_Edges.setChecked(True)
            
        if g.config.vars.General['default_AutomaticCutterCompensation']:
            self.ui.actionAutomatic_Cutter_Compensation.setChecked(True)
            
        self.updateMachineType()
            
        self.readSettings()
        
        g.config.metric = 1 # default drawing units: millimeters
        
    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string    
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtGui.QApplication.translate("Main",
                      string_to_translate, None,
                      QtGui.QApplication.UnicodeUTF8))
    
    
    def createActions(self):
        """
        Create the actions of the main toolbar.
        @purpose: Links the callbacks to the actions in the menu
        """
        
        self.ui.actionLoad_File.triggered.connect(self.showDialog)
        self.ui.actionReload_File.triggered.connect(self.reloadFile)
        
        self.ui.actionExit.triggered.connect(self.close)
        
        self.ui.actionOptimize_Shape.triggered.connect(self.optimize_TSP)
        self.ui.actionExport_Shapes.triggered.connect(self.exportShapes)
        self.ui.actionOptimize_and_Export_shapes.triggered.connect(self.optimizeAndExportShapes)
        
        self.ui.actionShow_WP_Zero.triggered.connect(self.setShow_wp_zero)
        self.ui.actionShow_path_directions.triggered.connect(self.setShow_path_directions)
        self.ui.actionShow_disabled_paths.triggered.connect(self.setShow_disabled_paths)
        self.ui.actionLive_update_export_route.toggled.connect(self.setUpdate_export_route)
        self.ui.actionAutoscale.triggered.connect(self.autoscale)
        self.ui.actionDelete_G0_paths.triggered.connect(self.deleteG0paths)
        
        self.ui.actionTolerances.triggered.connect(self.setTolerances)
        self.ui.actionRotate_all.triggered.connect(self.CallRotateAll)
        self.ui.actionScale_all.triggered.connect(self.CallScaleAll)
        self.ui.actionMove_WP_zero.triggered.connect(self.CallMoveWpZero)
        self.ui.actionSplit_Edges.triggered.connect(self.reloadFile)
        self.ui.actionAutomatic_Cutter_Compensation.triggered.connect(self.reloadFile)
        self.ui.actionMilling.triggered.connect(self.setMachineTypeToMilling)
        self.ui.actionDrag_Knife.triggered.connect(self.setMachineTypeToDragKnife)
        self.ui.actionLathe.triggered.connect(self.setMachineTypeToLathe)
        
        self.ui.actionAbout.triggered.connect(self.about)

    def keyPressEvent(self, event):
        """
        Rewritten KeyPressEvent to get other behavior while Shift is pressed.
        @purpose: Changes to ScrollHandDrag while Control pressed
        @param event:    Event Parameters passed to function
        """
        if event.isAutoRepeat():
            return
        if (event.key() == QtCore.Qt.Key_Shift):   
            self.MyGraphicsView.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        elif (event.key() == QtCore.Qt.Key_Control):
            self.MyGraphicsView.selmode = 1
           
    def keyReleaseEvent (self, event):
        """
        Rewritten KeyReleaseEvent to get other behavior while Shift is pressed.
        @purpose: Changes to RubberBandDrag while Control released
        @param event:    Event Parameters passed to function
        """
        if (event.key() == QtCore.Qt.Key_Shift):   
            self.MyGraphicsView.setDragMode(QtGui.QGraphicsView.NoDrag)
            #self.setDragMode(QtGui.QGraphicsView.RubberBandDrag )
        elif (event.key() == QtCore.Qt.Key_Control):
            self.MyGraphicsView.selmode = 0
        
    def enableplotmenu(self, status = True):
        """
        Enable the Toolbar buttons.
        @param status: Set True to enable, False to disable
        """
        
        self.ui.actionShow_WP_Zero.setEnabled(status)
        self.ui.actionShow_path_directions.setEnabled(status)
        self.ui.actionShow_disabled_paths.setEnabled(status)
        self.ui.actionLive_update_export_route.setEnabled(status)
        self.ui.actionAutoscale.setEnabled(status)
        
        self.ui.actionScale_all.setEnabled(status)
        self.ui.actionRotate_all.setEnabled(status)
        self.ui.actionMove_WP_zero.setEnabled(status)
        
    def showDialog(self):
        """
        This function is called by the menu "File/Load File" of the main toolbar.
        It creates the file selection dialog and calls the loadFile function to
        load the selected file.
        """
        
        self.filename = QtGui.QFileDialog.getOpenFileName(self,
                    self.tr("Open file"),
                    g.config.vars.Paths['import_dir'], self.tr(\
                    "All supported files (*.dxf *.ps *.pdf);;" \
                    "DXF files (*.dxf);;"\
                    "PS files (*.ps);;"\
                    "PDF files (*.pdf);;"\
                    "all files (*.*)"))
        
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))

        #If there is something to load then call the load function callback
        if not(self.filename == ""):
            logger.info(self.tr("File: %s selected") % self.filename)
            self.setWindowTitle(self.tr("DXF2GCODE - [%s]") % self.filename)
            #Initialize the scale, rotate and move coordinates
            self.cont_scale = 1.0
            self.cont_dx = 0.0
            self.cont_dy = 0.0
            self.rotate = 0.0
            self.loadFile(self.filename)
            
        QtGui.QApplication.restoreOverrideCursor()
    
    def reloadFile(self):
        """
        This function is called by the menu "File/Reload File" of the main toolbar.
        It reloads the previously loaded file (if any)
        """
        
        logger.info(self.tr("Reloading file: %s") % self.filename)
        
        #If there is something to load then call the load function callback
        if not(self.filename == ""):
            self.loadFile(self.filename)
    
    def optimize_TSP(self):
        """
        Method is called to optimize the order of the shapes. This is performed
        by solving the TSP Problem.
        """
        
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        
        logger.debug(self.tr('Optimize order of enabled shapes per layer'))
        self.MyGraphicsScene.resetexproutes()
        
        #Get the export order from the QTreeView
        logger.debug(self.tr('Updating order according to TreeView'))
        self.TreeHandler.updateExportOrder()
        self.MyGraphicsScene.addexproutest()
        
        for LayerContent in self.LayerContents:
            
            #Initial values for the Lists to export.
            self.shapes_to_write = []
            self.shapes_fixed_order = []
            shapes_st_en_points = []
            
            #Check all shapes of Layer which shall be exported and create List
            #for it.
            logger.debug(self.tr("Nr. of Shapes %s; Nr. of Shapes in Route %s") 
                                 % (len(LayerContent.shapes),
                                 len(LayerContent.exp_order)))
            logger.debug(self.tr("Export Order for start: %s") % LayerContent.exp_order)
            
            for shape_nr in range(len(LayerContent.exp_order)):
                if not(self.shapes[LayerContent.exp_order[shape_nr]].send_to_TSP):
                    self.shapes_fixed_order.append(shape_nr)
                
                self.shapes_to_write.append(shape_nr)
                shapes_st_en_points.append(self.shapes[LayerContent.exp_order[shape_nr]].get_st_en_points())
            
            #Perform Export only if the Number of shapes to export is bigger than 0
            if len(self.shapes_to_write)>0:
                        #Errechnen der Iterationen
                        #Calculate the iterations
                iter_ = min(g.config.vars.Route_Optimisation['max_iterations'],
                         len(self.shapes_to_write)*50)
                
                #Adding the Start and End Points to the List.
                x_st = g.config.vars.Plane_Coordinates['axis1_start_end']
                y_st = g.config.vars.Plane_Coordinates['axis2_start_end']
                start = Point(x = x_st, y = y_st)
                ende = Point(x = x_st, y = y_st)
                shapes_st_en_points.append([start, ende])
                
                TSPs = []
                TSPs.append(TSPoptimize(st_end_points = shapes_st_en_points,
                                        order = self.shapes_fixed_order))
                logger.info(self.tr("TSP start values initialised for Layer %s")
                                    % LayerContent.LayerName)
                logger.debug(self.tr("Shapes to write: %s")
                                     % self.shapes_to_write)
                logger.debug(self.tr("Fixed order: %s")
                                     % self.shapes_fixed_order)
                
                for it_nr in range(iter_):
                    #Only show each 50th step.
                    if (it_nr % 50) == 0:
                        TSPs[-1].calc_next_iteration()
                        new_exp_order = []
                        for nr in TSPs[-1].opt_route[1:len(TSPs[-1].opt_route)]:
                            new_exp_order.append(LayerContent.exp_order[nr])
                                          
                logger.debug(self.tr("TSP done with result: %s") % TSPs[-1])
                
                LayerContent.exp_order = new_exp_order
                
                self.MyGraphicsScene.addexproute(LayerContent.exp_order,
                                                 LayerContent.LayerNr)
                logger.debug(self.tr("New Export Order after TSP: %s")
                                     % new_exp_order)
                self.app.processEvents()
            else:
                LayerContent.exp_order = []
            
        if LayerContent:
            self.ui.actionDelete_G0_paths.setEnabled(True)
            self.MyGraphicsScene.addexprouteen()
            
        #Update order in the treeView, according to path calculation done by the TSP
        self.TreeHandler.updateTreeViewOrder()
        
        QtGui.QApplication.restoreOverrideCursor()
    
    
    def deleteG0paths(self):
        """
        Deletes the optimisation paths from the scene.
        """
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        
        self.MyGraphicsScene.delete_opt_path()
        self.ui.actionDelete_G0_paths.setEnabled(False)
        
        QtGui.QApplication.restoreOverrideCursor()
    
    def exportShapes(self, status=False, saveas=None):
        """
        This function is called by the menu "Export/Export Shapes". It may open
        a Save Dialog if used without LinuxCNC integration. Otherwise it's
        possible to select multiple postprocessor files, which are located
        in the folder.
        """
        
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        
        logger.debug(self.tr('Export the enabled shapes'))
        
        #Get the export order from the QTreeView
        self.TreeHandler.updateExportOrder()
        self.updateExportRoute()
        
        logger.debug(self.tr("Sorted layers:"))
        for i, layer in enumerate(self.LayerContents):
            logger.debug("LayerContents[%i] = %s" % (i, layer))
        
        if not(g.config.vars.General['write_to_stdout']):
            
            #Get the name of the File to export
            if saveas == None:
                filename = self.showSaveDialog()
                self.save_filename = str(filename[0].toUtf8()).decode("utf-8")
            else:
                filename = [None, None]
                self.save_filename = saveas
            
            #If Cancel was pressed
            if not self.save_filename:
            
                QtGui.QApplication.restoreOverrideCursor()
                
                return
            
            (beg, ende) = os.path.split(self.save_filename)
            (fileBaseName, fileExtension) = os.path.splitext(ende) 
            
            pp_file_nr = 0
            for i in range(len(self.MyPostProcessor.output_format)):
                name = "%s " % (self.MyPostProcessor.output_text[i])
                format_ = "(*%s)" % (self.MyPostProcessor.output_format[i])
                MyFormats = name + format_
                if filename[1] == MyFormats:
                    pp_file_nr = i
            if fileExtension != self.MyPostProcessor.output_format[pp_file_nr]:
                if not QtCore.QFile.exists(self.save_filename):
                    self.save_filename = self.save_filename + self.MyPostProcessor.output_format[pp_file_nr]
            
            self.MyPostProcessor.getPostProVars(pp_file_nr)
        else:
            self.save_filename = None
            self.MyPostProcessor.getPostProVars(0)
        
        """
        Export will be performed according to LayerContents and their order
        is given in this variable too.
        """
        
        self.MyPostProcessor.exportShapes(self.load_filename,
                                          self.save_filename,
                                          self.LayerContents)
        
        QtGui.QApplication.restoreOverrideCursor()
    
        if g.config.vars.General['write_to_stdout']:
            self.close()
    
    def optimizeAndExportShapes(self):
        """
        Optimize the tool path, then export the shapes
        """
        self.optimize_TSP()
        self.exportShapes()
    
    def updateExportRoute(self):
        """
        Update the drawing of the export route
        """
        self.MyGraphicsScene.resetexproutes()
        
        self.MyGraphicsScene.addexproutest()
        for LayerContent in self.LayerContents:
            if len(LayerContent.exp_order) > 0:
                self.MyGraphicsScene.addexproute(LayerContent.exp_order, LayerContent.LayerNr)
        if LayerContent:
            self.ui.actionDelete_G0_paths.setEnabled(True)
            self.MyGraphicsScene.addexprouteen()
        
    
    def showSaveDialog(self):
        """
        This function is called by the menu "Export/Export Shapes" of the main toolbar.
        It creates the selection dialog for the exporter
        @return: Returns the filename of the selected file.
        """
        MyFormats = ""
        for i in range(len(self.MyPostProcessor.output_format)):
            name = "%s " % (self.MyPostProcessor.output_text[i])
            format_ = "(*%s);;" % (self.MyPostProcessor.output_format[i])
            MyFormats = MyFormats + name + format_
            
        (beg, ende) = os.path.split(self.load_filename)
        (fileBaseName, fileExtension) = os.path.splitext(ende)
        
        default_name = os.path.join(g.config.vars.Paths['output_dir'], fileBaseName)
        
        selected_filter = self.MyPostProcessor.output_format[0]
        filename = QtGui.QFileDialog.getSaveFileNameAndFilter(self,
                    self.tr('Export to file'), default_name,
                    MyFormats, selected_filter)
        
        logger.info(self.tr("File: %s selected") % filename[0])
        
        return filename
        
    def autoscale(self):
        """
        This function is called by the menu "Autoscale" of the main. Forwards the
        call to MyGraphicsview.autoscale() 
        """
        self.MyGraphicsView.autoscale()
    
    def about(self):
        """
        This function is called by the menu "Help/About" of the main toolbar and 
        creates the About Window
        """
                
        message = self.tr("<html>"\
                "<h2><center>You are using</center></h2>"\
                "<body bgcolor="\
                "<center><img src='images/dxf2gcode_logo.png' border='1' color='white'></center></body>"\
                "<h2>Version:</h2>"\
                "<body>%s: %s<br>"\
                "Last change: %s<br>"\
                "Changed by: %s<br></body>"\
                "<h2>Where to get help:</h2>"\
                "For more information and updates, "\
                "please visit the Google Code Project: "\
                "<a href='http://code.google.com/p/dxf2gcode/'>http://code.google.com/p/dxf2gcode/</a><br>"\
                "For any questions on how to use dxf2gcode please use the<br>"\
                "<a href='https://groups.google.com/forum/?fromgroups#!forum/dxf2gcode-users'>mailing list</a><br><br>"\
                "To log bugs, or request features please use the <br>"\
                "<a href='http://code.google.com/p/dxf2gcode/issues/list'>issue tracking system</a><br>"\
                "<h2>License and copyright:</h2>"\
                "<body>This program is written in Python and is published under the "\
                "<a href='http://www.gnu.org/licenses/'>GNU GPLv3 license.</a><br>"\
                "</body></html>") % (c.VERSION, c.REVISION, c.DATE, c.AUTHOR)
        
        myAboutDialog(title = "About DXF2GCODE", message = message)
        
    def setShow_wp_zero(self):
        """
        This function is called by the menu "Show WP Zero" of the
        main and forwards the call to MyGraphicsView.setShow_wp_zero() 
        """
        flag = self.ui.actionShow_WP_Zero.isChecked()
        self.MyGraphicsView.setShow_wp_zero(flag)
        
    def setShow_path_directions(self):
        """
        This function is called by the menu "Show all path directions" of the
        main and forwards the call to MyGraphicsView.setShow_path_direction() 
        """
        flag = self.ui.actionShow_path_directions.isChecked()
        self.MyGraphicsView.setShow_path_direction(flag)
        
    def setShow_disabled_paths(self):
        """
        This function is called by the menu "Show disabled paths" of the
        main and forwards the call to MyGraphicsView.setShow_disabled_paths()
        """
        flag = self.ui.actionShow_disabled_paths.isChecked()
        self.MyGraphicsView.setShow_disabled_paths(flag)
    
    def setUpdate_export_route(self):
        """
        This function is called by the menu "Live update tool path" of the
        main and forwards the call to TreeHandler.setUpdateExportRoute()
        """
        flag = self.ui.actionLive_update_export_route.isChecked()
        if not flag:
            #Remove any existing export route, since it won't be updated anymore
            self.MyGraphicsScene.resetexproutes()
        
        self.TreeHandler.setUpdateExportRoute(flag)
        
    def setTolerances(self):
        """
        This function is called when the Option=>Tolerances Menu is clicked.
        """
        
        title = self.tr('Contour tolerances')
        if g.config.metric == 0:
            label = (self.tr("Tolerance for common points [in]:"), \
                   self.tr("Tolerance for curve fitting [in]:"))
        else:
            label = (self.tr("Tolerance for common points [mm]:"), \
                   self.tr("Tolerance for curve fitting [mm]:"))
        value = (g.config.point_tolerance,
               g.config.fitting_tolerance)
        
        logger.debug(self.tr("set Tolerances"))
        SetTolDialog = myDialog(title, label, value)
        
        if SetTolDialog.result == None:
            return
        
        g.config.point_tolerance = float(SetTolDialog.result[0])
        g.config.fitting_tolerance = float(SetTolDialog.result[1])
        
        self.reloadFile()
        #self.MyGraphicsView.update()
        
    def CallScaleAll(self):
        """
        This function is called when the Option=>Scale All Menu is clicked.
        """
        title = self.tr('Scale Contour')
        label = [self.tr("Scale Contour by factor:")]
        value = [self.cont_scale]
        ScaEntDialog = myDialog(title, label, value)
        
        if ScaEntDialog.result == None:
            return
        
        self.cont_scale = float(ScaEntDialog.result[0])
        self.EntitiesRoot.sca = self.cont_scale
        
        self.reloadFile()
        #self.MyGraphicsView.update()
        
    def CallRotateAll(self):
        """
        This function is called when the Option=>Rotate All Menu is clicked.
        """
        title = self.tr('Rotate Contour')
        label = [self.tr("Rotate Contour by deg:")]
        value = [degrees(self.rotate)]
        RotEntDialog = myDialog(title, label, value)
        
        if RotEntDialog.result == None:
            return
        
        self.rotate = radians(float(RotEntDialog.result[0]))
        self.EntitiesRoot.rot = self.rotate
        
        self.reloadFile()
        #self.MyGraphicsView.update()
    
    def CallMoveWpZero(self):
        """
        This function is called when the Option=>Move WP Zero Menu is clicked.
        """
        title = self.tr('Workpiece zero offset')
        label = ((self.tr("Offset %s axis by mm:") % g.config.vars.Axis_letters['ax1_letter']), \
               (self.tr("Offset %s axis by mm:") % g.config.vars.Axis_letters['ax2_letter']))
        value = (self.cont_dx, self.cont_dy)
        MoveWpzDialog = myDialog(title, label, value, True)
        
        if MoveWpzDialog.result == None:
            return
        
        if MoveWpzDialog.result == 'Auto':
            minx = sys.float_info.max
            maxy = - sys.float_info.max
            for shape in self.shapes:
                if not(shape.isDisabled()):
                    r = shape.boundingRect()
                    if r.left() < minx:
                        minx = r.left()
                    if r.bottom()  > maxy:
                        maxy = r.bottom()
            self.cont_dx = self.EntitiesRoot.p0.x - minx
            self.cont_dy = self.EntitiesRoot.p0.y + maxy
        else:
            self.cont_dx = float(MoveWpzDialog.result[0])
            self.cont_dy = float(MoveWpzDialog.result[1])
        
        self.EntitiesRoot.p0.x = self.cont_dx
        self.EntitiesRoot.p0.y = self.cont_dy
        
        self.reloadFile()
        #self.MyGraphicsView.update()
        
    def setMachineTypeToMilling(self):
        """
        This function is called by the menu when Machine Type -> Milling is clicked.
        """
        g.config.machine_type = 'milling'
        self.updateMachineType()
        self.reloadFile()
        
    def setMachineTypeToDragKnife(self):
        """
        This function is called by the menu when Machine Type -> Drag Knife is clicked.
        """
        g.config.machine_type = 'drag_knife'
        self.updateMachineType()
        self.reloadFile()
        
    def setMachineTypeToLathe(self):
        """
        This function is called by the menu when Machine Type -> Lathe is clicked.
        """
        g.config.machine_type = 'lathe'
        self.updateMachineType()
        self.reloadFile()
        
    def updateMachineType(self):
        if g.config.machine_type == 'milling':
            self.ui.actionAutomatic_Cutter_Compensation.setEnabled(True)
            self.ui.actionMilling.setChecked(True)
            self.ui.actionDrag_Knife.setChecked(False)
            self.ui.actionLathe.setChecked(False)
            self.ui.label_9.setText(self.tr("Z Infeed depth"))
        elif g.config.machine_type == 'lathe':
            self.ui.actionAutomatic_Cutter_Compensation.setEnabled(False)
            self.ui.actionMilling.setChecked(False)
            self.ui.actionDrag_Knife.setChecked(False)
            self.ui.actionLathe.setChecked(True)
            self.ui.label_9.setText(self.tr("No Z-Axis for lathe"))
        elif g.config.machine_type == "drag_knife":
            # TODO: Update of Maschine Type Lathe required. Z-Axis not available
            # But fields may be used for other purpose.
            self.ui.actionAutomatic_Cutter_Compensation.setEnabled(False)
            self.ui.actionMilling.setChecked(False)
            self.ui.actionDrag_Knife.setChecked(True)
            self.ui.actionLathe.setChecked(False)
            self.ui.label_9.setText(self.tr("Z Drag depth"))
            
    
    def loadFile(self, filename):
        """
        Loads the file given by filename.  Also calls the command to 
        make the plot.
        @param filename: String containing filename which should be loaded
        """
        
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        
        filename = str(filename).decode("utf-8")
        self.load_filename = filename
        (name, ext) = os.path.splitext(filename)
        
        if (ext.lower() == ".ps") or (ext.lower() == ".pdf"):
            logger.info(self.tr("Sending Postscript/PDF to pstoedit"))
            
            #Create temporary file which will be read by the program
            filename = os.path.join(tempfile.gettempdir(), 'dxf2gcode_temp.dxf')
           
            pstoedit_cmd = g.config.vars.Filters['pstoedit_cmd'] #"C:\Program Files (x86)\pstoedit\pstoedit.exe"
            pstoedit_opt = g.config.vars.Filters['pstoedit_opt'] #['-f','dxf','-mm']
            ps_filename = os.path.normcase(self.load_filename)
            cmd = [(('%s') % pstoedit_cmd)] + pstoedit_opt + [(('%s') % ps_filename), (('%s') % filename)]
            logger.debug(cmd)
            retcode = subprocess.call(cmd)
        
        #self.textbox.text.delete(7.0, END)
        logger.info(self.tr('Loading file: %s') % filename)
        #logger.info("<a href=file:%s>%s</a>" % (filename, filename))
        
        values = ReadDXF(filename)
        
        #Output the information in the text window
        logger.info(self.tr('Loaded layers: %s') % len(values.layers))
        logger.info(self.tr('Loaded blocks: %s') % len(values.blocks.Entities))
        for i in range(len(values.blocks.Entities)):
            layers = values.blocks.Entities[i].get_used_layers()
            logger.info(self.tr('Block %i includes %i Geometries, reduced to %i Contours, used layers: %s')\
                                     % (i, len(values.blocks.Entities[i].geo), len(values.blocks.Entities[i].cont), layers))
        layers = values.entities.get_used_layers()
        insert_nr = values.entities.get_insert_nr()
        logger.info(self.tr('Loaded %i Entities geometries, reduced to %i Contours, used layers: %s, Number of inserts: %i') \
                                 % (len(values.entities.geo), len(values.entities.cont), layers, insert_nr))
        
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
        
        self.makeShapesAndPlot(values)
        
        #After all is plotted enable the Menu entities
        self.enableplotmenu()
        self.ui.actionDelete_G0_paths.setEnabled(False)
        
        QtGui.QApplication.restoreOverrideCursor()
    
    def makeShapesAndPlot(self, values):
        """
        Plots all data stored in the values parameter to the Canvas
        @param values: Includes all values loaded from the dxf file
        """
        
        #Generate the Shapes
        self.makeShapes(values,
                        p0 = Point(x = self.cont_dx, y = self.cont_dy),
                        pb = Point(x = 0.0, y = 0.0),
                        sca = [self.cont_scale, self.cont_scale, self.cont_scale],
                        rot = self.rotate)
        
        # Automatic cutter compensation 
        self.automaticCutterCompensation()
        
        # Break insertion
        Breaks(self.LayerContents).process()
        
        #Populate the treeViews
        self.TreeHandler.buildEntitiesTree(self.EntitiesRoot)
        self.TreeHandler.buildLayerTree(self.LayerContents)
        
        #Print the values
        self.MyGraphicsView.clearScene()
        self.MyGraphicsScene = MyGraphicsScene()
        
        self.MyGraphicsScene.plotAll(self.shapes, self.EntitiesRoot)
        self.MyGraphicsView.setScene(self.MyGraphicsScene)
        self.setShow_wp_zero()
        self.setShow_path_directions()
        self.setShow_disabled_paths()
        self.setUpdate_export_route()
        self.MyGraphicsView.show()
        self.MyGraphicsView.setFocus()
        
        #Autoscale the Canvas
        self.MyGraphicsView.autoscale()
    
    
    def makeShapes(self, values, p0, pb, sca, rot):
        """
        Instance is called by the Main Window after the defined file is loaded.
        It generates all ploting functionality. The parameters are generally 
        used to scale or offset the base geometry (by Menu in GUI).
        
        @param values: The loaded dxf values from the dxf_import.py file
        @param p0: The Starting Point to plot (Default x=0 and y=0)
        @param bp: The Base Point to insert the geometry and base for rotation 
        (Default is also x=0 and y=0)
        @param sca: The scale of the basis function (default =1)
        @param rot: The rotation of the geometries around base (default =0)
        """
        self.values = values
        
        #Put back the contours
        del(self.shapes[:])
        del(self.LayerContents[:])
        del(self.EntitiesRoot)
        self.EntitiesRoot = EntitieContentClass(Nr = 0, Name = 'Entities',
                                                parent = None, children = [],
                                                p0 = p0, pb = pb,
                                                sca = sca, rot = rot)
        
        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        #Start with () means to assign the entities -1 = Default ???
        self.makeEntitiesShapes(parent = self.EntitiesRoot)
        self.LayerContents.sort()
        
    def makeEntitiesShapes(self, parent = None, ent_nr = -1):
        """
        Instance is called prior to plotting the shapes. It creates
        all shape classes which are later plotted into the graphics.
        
        @param parent: The parent of a shape is always an Entities. It may be root 
        or, if it is a Block, this is the Block. 
        @param ent_nr: The values given in self.values are sorted so
        that 0 is the Root Entities and 1 is beginning with the first block. 
        This value gives the index of self.values to be used.
        """
        
        if parent.Name == "Entities":
            entities = self.values.entities
        else:
            ent_nr = self.values.Get_Block_Nr(parent.Name)
            entities = self.values.blocks.Entities[ent_nr]
        
        #Zuweisen der Geometrien in die Variable geos & Konturen in cont
        #Assigning the geometries in the variables geos & contours in cont
        ent_geos = entities.geo
        
        #Loop for the number of contours
        for cont in entities.cont:
            #Abfrage falls es sich bei der Kontur um ein Insert eines Blocks handelt
            #Query if it is in the contour of an insert of a block
            if ent_geos[cont.order[0][0]].Typ == "Insert":
                ent_geo = ent_geos[cont.order[0][0]]
                
                #Zuweisen des Basispunkts f�r den Block
                #Assign the base point for the block
                new_ent_nr = self.values.Get_Block_Nr(ent_geo.BlockName)
                new_entities = self.values.blocks.Entities[new_ent_nr]
                pb = new_entities.basep
                
                #Skalierung usw. des Blocks zuweisen
                #Scaling, etc. assign the block
                p0 = ent_geos[cont.order[0][0]].Point
                sca = ent_geos[cont.order[0][0]].Scale
                rot = ent_geos[cont.order[0][0]].rot
                
                
                #Erstellen des neuen Entitie Contents f�r das Insert
                #Creating the new Entitie Contents for the insert
                NewEntitieContent = EntitieContentClass(Nr = 0,
                                        Name = ent_geo.BlockName,
                                        parent = parent, children = [],
                                        p0 = p0,
                                        pb = pb,
                                        sca = sca,
                                        rot = rot)
                
                parent.addchild(NewEntitieContent)
                
                self.makeEntitiesShapes(parent = NewEntitieContent,
                                        ent_nr = ent_nr)
                
            else:
                #Loop for the number of geometries
                self.shapes.append(ShapeClass(len(self.shapes),
                                              cont.closed,
                                              40,
                                              0.0,
                                              parent,
                                              []))
                
                for ent_geo_nr in range(len(cont.order)):
                    ent_geo = ent_geos[cont.order[ent_geo_nr][0]]
                    if cont.order[ent_geo_nr][1]:
                        ent_geo.geo.reverse()
                        for geo in ent_geo.geo:
                            geo = copy(geo)
                            geo.reverse()
                            self.appendshapes(geo)                       
                        ent_geo.geo.reverse()
                    else:
                        for geo in ent_geo.geo:
                            self.appendshapes(copy(geo))
                
                #All shapes have to be CCW direction.
                self.shapes[-1].AnalyseAndOptimize()
                self.shapes[-1].FindNearestStPoint()
                
                #Connect the shapeSelectionChanged and enableDisableShape signals to our treeView, so that selections of the shapes are reflected on the treeView
                self.shapes[-1].setSelectionChangedCallback(self.TreeHandler.updateShapeSelection)
                self.shapes[-1].setEnableDisableCallback(self.TreeHandler.updateShapeEnabling)
                
                self.addtoLayerContents(self.shapes[-1], ent_geo.Layer_Nr)
                parent.addchild(self.shapes[-1])

    def appendshapes(self, geo):
        """
        Documentation required
        """
        if self.ui.actionSplit_Edges.isChecked() == True:
            if geo.type == 'LineGeo':
                diff = (geo.Pe - geo.Pa) / 2.0
                geo_b = deepcopy(geo)
                geo_a = deepcopy(geo)
                geo_b.Pe -= diff
                geo_a.Pa += diff
                self.shapes[-1].geos.append(geo_b)
                self.shapes[-1].geos.append(geo_a)
            else:
                self.shapes[-1].geos.append(geo)
        else:
            self.shapes[-1].geos.append(geo)
            
    def addtoLayerContents(self, shape, lay_nr):
        """
        Instance is called while the shapes are created. This gives the 
        structure which shape is laying on which layer. It also writes into the
        shape the reference to the LayerContent Class.
        
        @param shape: The shape to be appended of the shape 
        @param lay_nr: The Nr. of the layer
        """

        # Disable shape by default, if it lives on an ignored layer        
        #if shape.LayerContent.should_ignore():
        #    shape.setDisable(True, True)
        
        #Check if the layer already exists and add shape if it is.
        for LayCon in self.LayerContents:
            if LayCon.LayerNr == lay_nr:
                LayCon.shapes.append(shape)
                shape.LayerContent = LayCon
                shape.setDisabledIfOnDisabledLayer()
                return
        
        #If the Layer does not exist create a new one.
        LayerName = self.values.layers[lay_nr].name
        self.LayerContents.append(LayerContentClass(lay_nr, LayerName, [shape]))
        shape.LayerContent = self.LayerContents[-1]
        shape.setDisabledIfOnDisabledLayer()
        

    def automaticCutterCompensation(self):
        if self.ui.actionAutomatic_Cutter_Compensation.isEnabled() == self.ui.actionAutomatic_Cutter_Compensation.isChecked() == True:
            for layerContent in self.LayerContents:
                if layerContent.automaticCutterCompensationEnabled():
                    newShapes = [];
                    for shape in layerContent.shapes:
                        shape.make_papath()
                    for shape in layerContent.shapes:
                        if shape.closed:
                            container = None
                            myBounds = shape.boundingRect()
                            for otherShape in layerContent.shapes :
                                if shape != otherShape and otherShape.boundingRect().contains(myBounds):
                                    logger.debug(self.tr("Shape: %s is contained in shape %s") % (shape.nr, otherShape.nr))
                                    container = otherShape
                            if container is None:
                                shape.cut_cor = 41
                                newShapes.append(shape)
                            else:
                                shape.cut_cor = 42
                                newShapes.insert(layerContent.shapes.index(container), shape)
                        else:
                            newShapes.append(shape)
                    layerContent.shapes = newShapes
                    logger.debug(self.tr("new order for layer %s:") % (layerContent.LayerName))
                    for shape in layerContent.shapes:
                        logger.debug(self.tr(">>Shape: %s") % (shape.nr))
                
    def closeEvent(self, e):
        logger.debug(self.tr("exiting"))
        self.writeSettings()
        e.accept()
    
    def readSettings(self):
        settings = QtCore.QSettings("dxf2gcode", "dxf2gcode")
        settings.beginGroup("MainWindow");
        self.resize(settings.value("size", QtCore.QSize(800, 600)).toSize());
        self.move(settings.value("pos", QtCore.QPoint(200, 200)).toPoint());
        settings.endGroup();
            
    def writeSettings(self):
        settings = QtCore.QSettings("dxf2gcode", "dxf2gcode")
        settings.beginGroup("MainWindow");
        settings.setValue("size", self.size());
        settings.setValue("pos", self.pos());
        settings.endGroup();   

    
if __name__ == "__main__":
    """
    The main function which is executed after program start.
    """
    Log=LoggerClass(logger)
    #Get local language and install if available.


    g.config = MyConfig()
    Log.set_console_handler_loglevel()
    Log.add_file_logger()

    app = QtGui.QApplication(sys.argv)
    
    locale = QtCore.QLocale.system().name()
    logger.debug("locale: %s" %locale)
    translator = QtCore.QTranslator()
    if translator.load("dxf2gcode_" + locale, "./i18n"):
        app.installTranslator(translator)    
    
    window = Main(app)
    g.window = window
    
    #shall be sent to. This Class needs a function "def write(self, charstr)
    Log.add_window_logger(window.myMessageBox)
    

        
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument("filename",nargs="?")

#    parser.add_argument("-f", "--file", dest = "filename",
#                      help = "read data from FILENAME")
    parser.add_argument("-e", "--export", dest = "export_filename",
                      help = "export data to FILENAME")
    parser.add_argument("-q", "--quiet", action = "store_true",
                      dest = "quiet", help = "no GUI")
    
#    parser.add_option("-v", "--verbose",
#                      action = "store_true", dest = "verbose")
    options = parser.parse_args()

    #(options, args) = parser.parse_args()
    logger.debug("Started with following options \n%s" % (parser))
    


    if not options.quiet:
        window.show()

    if not(options.filename is None):
        window.filename = options.filename
        #Initialize the scale, rotate and move coordinates
        window.cont_scale = 1.0
        window.cont_dx = 0.0
        window.cont_dy = 0.0
        window.rotate = 0.0
        
        window.loadFile(options.filename)
        
    if not(options.export_filename is None):
        window.exportShapes(None, options.export_filename)
        
    if not options.quiet:
        # It's exec_ because exec is a reserved word in Python
        sys.exit(app.exec_())
