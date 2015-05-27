# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2011-2015
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

"""
Special purpose canvas including all required plotting function etc.

@purpose:  Plotting all
"""

#from copy import copy

from PyQt4 import QtCore, QtGui
from Core.Point import Point
#from Core.Shape import ShapeClass

from Gui.WpZero import WpZero
from Gui.Arrow import Arrow
from Gui.StMove import StMove
from Gui.RouteText import RouteText
#import math
import Core.Globals as g
#import Core.constants as c

import logging
logger = logging.getLogger("DxfImport.myCanvasClass")

class MyGraphicsView(QtGui.QGraphicsView):
    """
    This is the used Canvas to print the graphical interface of dxf2gcode.
    All GUI things should be performed in the View and plotting functions in
    the scene
    @sideeffect: None
    """

    def __init__(self, parent=None):
        """
        Initialisation of the View Object. This is called by the gui created
        with the QTDesigner.
        @param parent: Main is passed as a pointer for reference.
        """
        super(MyGraphicsView, self).__init__(parent)
        self.currentItem = None

        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)

        #self.setDragMode(QtGui.QGraphicsView.RubberBandDrag )
        self.setDragMode(QtGui.QGraphicsView.NoDrag)

        self.parent = parent
        self.mppos = None
        self.selmode = 0

        self.rubberBand = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self)

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtCore.QCoreApplication.translate('MyGraphicsView',
                                                         string_to_translate,
                                                         encoding=QtCore.QCoreApplication.UnicodeUTF8))

    def contextMenuEvent(self, event):
        """
        Create the contextmenu.
        @purpose: Links the new Class of ContextMenu to Graphicsview.
        """
        menu = MyDropDownMenu(self, self.scene(), event.pos())

    def wheelEvent(self, event):
        """
        With Mouse Wheel the object is scaled
        @purpose: Scale by mouse wheel
        @param event: Event Parameters passed to function
        """
        scale = (1000+event.delta())/1000.0
        self.scale(scale, scale)

    def mousePressEvent(self, event):
        """
        Right Mouse click shall have no function, Therefore pass only left
        click event
        @purpose: Change inherited mousePressEvent
        @param event: Event Parameters passed to function
        """

        if self.dragMode() == 1:
            super(MyGraphicsView, self).mousePressEvent(event)
        elif event.button() == QtCore.Qt.LeftButton:
            self.mppos = event.pos()
        else:
            pass

    def mouseReleaseEvent(self, event):
        """
        Right Mouse click shall have no function, Therefore pass only left
        click event
        @purpose: Change inherited mousePressEvent
        @param event: Event Parameters passed to function
        """
        delta = 2

        if(self.dragMode()) == 1:
            #if (event.key() == QtCore.Qt.Key_Shift):
            #self.setDragMode(QtGui.QGraphicsView.NoDrag)
            super(MyGraphicsView, self).mouseReleaseEvent(event)

        #Selection only enabled for left Button
        elif event.button() == QtCore.Qt.LeftButton:
            self.currentItems = []
            scene = self.scene()
            if self.selmode == 0:
                for item in scene.selectedItems():
#                    item.starrow.setSelected(False)
#                    item.stmove.setSelected(False)
#                    item.enarrow.setSelected(False)
                    item.setSelected(False)
            #If the mouse button is pressed without movement of rubberband
            if self.rubberBand.isHidden():
                rect = QtCore.QRect(event.pos().x()-delta,
                          event.pos().y()-delta,
                          2*delta, 2*delta)
                #logger.debug(rect)

                point = self.mapToScene(event.pos())
                min_distance = float(0x7fffffff)
                for item in self.items(rect):
                    itemDistance = item.contains_point(point)
                    if itemDistance < min_distance:
                        min_distance = itemDistance
                        self.currentItems = item
                if self.currentItems:
                    if self.currentItems.isSelected():
                        self.currentItems.setSelected(False)
                    else:
                        #print (self.currentItems.flags())
                        self.currentItems.setSelected(True)
#                it = self.itemAt(event.pos())
#                if it == None:
#                    self.currentItems=[]
#                else:
#                    self.currentItems=[it]
                #self.currentItems = [self.itemAt(event.pos())]
                #logger.debug("No Rubberband")
            #If movement is bigger and rubberband is enabled
            else:
                rect = self.rubberBand.geometry()
                #All items in the selection mode = QtCore.Qt.ContainsItemShape
                self.currentItems = self.items(rect)
                self.rubberBand.hide()
                #logger.debug("Rubberband Selection")

                #All items in the selection
                #self.currentItems = self.items(rect)
                #print self.currentItems
                #logger.debug(rect)


                for item in self.currentItems:
                    if item.isSelected():
                        item.setSelected(False)
                    else:
                        #print (item.flags())
                        item.setSelected(True)

        else:
            pass

        self.mppos = None
        #super(MyGraphicsView, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """
        MouseMoveEvent of the Graphiscview. May also be used for the Statusbar.
        @purpose: Get the MouseMoveEvent and use it for the Rubberband Selection
        @param event: Event Parameters passed to function
        """
        if not(self.mppos is None):
            Point = event.pos() - self.mppos
            if (Point.manhattanLength() > 3):
                #print 'the mouse has moved more than 3 pixels since the oldPosition'
                #print "Mouse Pointer is currently hovering at: ", event.pos()
                self.rubberBand.show()
                self.rubberBand.setGeometry(QtCore.QRect(self.mppos, event.pos()).normalized())

        scpoint = self.mapToScene(event.pos())

        #self.setStatusTip('X: %3.1f; Y: %3.1f' %(scpoint.x(), -scpoint.y()))
        #works not as supposed to
        self.setToolTip('X: %3.1f; Y: %3.1f' %(scpoint.x(), -scpoint.y()))

        super(MyGraphicsView, self).mouseMoveEvent(event)

    def autoscale(self):
        """
        Automatically zooms to the full extend of the current GraphicsScene
        """
        scene = self.scene()
        scext = scene.itemsBoundingRect()
        self.fitInView(scext, QtCore.Qt.KeepAspectRatio)
        logger.debug(self.tr("Autoscaling to extend: %s") % (scext))

    def setShow_path_direction(self, flag):
        """
        This function is called by the Main Window from the Menubar.
        @param flag: This flag is true if all Path Direction shall be shown
        """
        scene = self.scene()
        for shape in scene.shapes:
            shape.starrow.setallwaysshow(flag)
            shape.enarrow.setallwaysshow(flag)
            shape.stmove.setallwaysshow(flag)

    def setShow_wp_zero(self, flag):
        """
        This function is called by the Main Window from the Menubar.
        @param flag: This flag is true if all Path Direction shall be shown
        """
        scene = self.scene()
        if flag is True:
            scene.wpzero.show()
        else:
            scene.wpzero.hide()

    def setShow_disabled_paths(self, flag):
        """
        This function is called by the Main Window from the Menubar.
        @param flag: This flag is true if hidden paths shall be shown
        """
        scene = self.scene()
        scene.setShow_disabled_paths(flag)

    def clearScene(self):
        """
        Deletes the existing GraphicsScene.
        """
        scene = self.scene()
        del(scene)

class MyDropDownMenu(QtGui.QMenu):
    """
    class MyDropDownMenu
    """
    def __init__(self, MyGraphicsView, MyGraphicsScene, position):

        QtGui.QMenu.__init__(self)

        self.position = MyGraphicsView.mapToGlobal(position)
        GVPos = MyGraphicsView.mapToScene(position)
        self.PlotPos = Point(x=GVPos.x(), y=-GVPos.y())

        self.MyGraphicsScene = MyGraphicsScene
        self.MyGraphicsView = MyGraphicsView

        if len(self.MyGraphicsScene.selectedItems()) == 0:
            return

        invertAction = self.addAction(self.tr("Invert Selection"))
        disableAction = self.addAction(self.tr("Disable Selection"))
        enableAction = self.addAction(self.tr("Enable Selection"))

        self.addSeparator()

        swdirectionAction = self.addAction(self.tr("Switch Direction"))
        SetNxtStPAction = self.addAction(self.tr("Set Nearest StartPoint"))


        if g.config.machine_type == 'drag_knife':
            pass
        else:
            self.addSeparator()
            submenu1 = QtGui.QMenu(self.tr('Cutter Compensation'), self)
            self.noCompAction = submenu1.addAction(self.tr("G40 No Compensation"))
            self.noCompAction.setCheckable(True)
            self.leCompAction = submenu1.addAction(self.tr("G41 Left Compensation"))
            self.leCompAction.setCheckable(True)
            self.reCompAction = submenu1.addAction(self.tr("G42 Right Compensation"))
            self.reCompAction.setCheckable(True)

            logger.debug(self.tr("The selected shapes have the following direction: %i") % (self.calcMenuDir()))
            self.checkMenuDir(self.calcMenuDir())

            self.addMenu(submenu1)

        invertAction.triggered.connect(self.invertSelection)
        disableAction.triggered.connect(self.disableSelection)
        enableAction.triggered.connect(self.enableSelection)

        swdirectionAction.triggered.connect(self.switchDirection)
        SetNxtStPAction.triggered.connect(self.setNearestStP)

        if g.config.machine_type == 'drag_knife':
            pass
        else:
            self.noCompAction.triggered.connect(self.setNoComp)
            self.leCompAction.triggered.connect(self.setLeftComp)
            self.reCompAction.triggered.connect(self.setRightComp)

        self.exec_(self.position)

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtCore.QCoreApplication.translate('MyDropDownMenu',
                                                         string_to_translate,
                                                         encoding=QtCore.QCoreApplication.UnicodeUTF8))

    def calcMenuDir(self):
        """
        This method returns the direction of the selected items. If there are
        different cutter directions in the selection 0 is returned, else
        1 for Left and 2 for right.
        """

        items = self.MyGraphicsScene.selectedItems()
        if len(items) == 0:
            return 0

        dir = items[0].cut_cor
        for item in items:
            if not(dir == item.cut_cor):
                return 0

        return dir-40

    def checkMenuDir(self, dir):
        """
        This method checks the buttons in the Contextmenu for the direction of
        the selected items.
        @param dir: The direction of the items -1=different, 0=None, 1=left, 2=right
        """
        self.noCompAction.setChecked(False)
        self.leCompAction.setChecked(False)
        self.reCompAction.setChecked(False)

        if dir == 0:
            self.noCompAction.setChecked(True)
        elif dir == 1:
            self.leCompAction.setChecked(True)
        elif dir == 2:
            self.reCompAction.setChecked(True)

    def invertSelection(self):
        """
        This function is called by the Contextmenu of the Graphicsview.
        @purpose: Inverts the selection of all shapes.
        """
        #scene = self.scene()
        for shape in self.MyGraphicsScene.shapes:
            if shape.isSelected():
                shape.setSelected(False)
            else:
                shape.setSelected(True)

    def disableSelection(self):
        """
        Disable all shapes which are currently selected. Based on the view
        options they are not shown, or showed in a different color
        """
        for shape in self.MyGraphicsScene.shapes:
            if shape.isSelected() and shape.allowedToChange:
                shape.setDisable(True)
        self.MyGraphicsScene.update()

    def enableSelection(self):
        """
        Enable all shapes which are currently selected. Based on the view
        options they are not shown, or showed in a different color
        """
        for shape in self.MyGraphicsScene.shapes:
            if shape.isSelected() and shape.allowedToChange:
                shape.setDisable(False)
        self.MyGraphicsScene.update()

    def switchDirection(self):
        """
        Switch the Direction of all items. For example from CW direction to CCW
        """
        for shape in self.MyGraphicsScene.shapes:
            if shape.isSelected():
                shape.reverse()
                shape.reverseGUI()

                logger.debug(self.tr('Switched Direction at Shape Nr: %i')\
                                %(shape.nr))

                shape.updateCutCor()
                shape.updateCCplot()

    def setNearestStP(self):
        """
        Search the nearest StartPoint to the clicked position of all selected
        shapes.
        """
        shapes = self.MyGraphicsScene.selectedItems()

        for shape in shapes:
            shape.FindNearestStPoint(self.PlotPos)
            #self.MyGraphicsScene.plot_shape(shape)
            shape.update_plot()

    def setNoComp(self):
        """
        Sets the compensation to 40, which is none, for the selected shapes.
        """
        shapes = self.MyGraphicsScene.selectedItems()
        for shape in shapes:
            shape.cut_cor = 40
            logger.debug(self.tr('Changed Cutter Correction to None Shape Nr: %i')\
                             %(shape.nr))

            shape.updateCutCor()
            shape.updateCCplot()

    def setLeftComp(self):
        """
        Sets the compensation to 41, which is Left, for the selected shapes.
        """
        shapes = self.MyGraphicsScene.selectedItems()
        for shape in shapes:
            shape.cut_cor = 41
            logger.debug(self.tr('Changed Cutter Correction to left Shape Nr: %i')\
                             %(shape.nr))
            shape.updateCutCor()
            shape.updateCCplot()

    def setRightComp(self):
        """
        Sets the compensation to 42, which is Right, for the selected shapes.
        """
        shapes = self.MyGraphicsScene.selectedItems()
        for shape in shapes:
            shape.cut_cor = 42
            logger.debug(self.tr('Changed Cutter Correction to right Shape Nr: %i')\
                             %(shape.nr))
            shape.updateCutCor()
            shape.updateCCplot()

class MyGraphicsScene(QtGui.QGraphicsScene):
    """
    This is the Canvas used to print the graphical interface of dxf2gcode.
    The Scene is rendered into the previously defined mygraphicsView class.
    All performed plotting functions should be defined here.
    @sideeffect: None
    """
    def __init__(self):
        QtGui.QGraphicsScene.__init__(self)

        self.shapes = []
        self.wpzero = []
#        self.LayerContents = []
        self.routearrows = []
        self.routetext = []
        self.showDisabled = False
        self.expprv = []
        self.expcol = []
#        self.EntitiesRoot = EntityContentClass(Nr=-1, Name='Base',
#                                              parent=None, children=[],
#                                              p0=Point(0,0), pb=Point(0,0),
#                                              sca=1,rot=0)
#        self.BaseEntities = EntityContentClass()

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtCore.QCoreApplication.translate('MyGraphicsScene',
                                                         string_to_translate,
                                                         encoding=QtCore.QCoreApplication.UnicodeUTF8))

    def plotAll(self, shapes, EntitiesRoot):
        """
        Instance is called by the Main Window after the defined file is loaded.
        It generates all ploting functionality. The parameters are generally
        used to scale or offset the base geometry (by Menu in GUI).

        @param values: The loaded dxf values fro mthe dxf_import.py file
        @param p0: The Starting Point to plot (Default x=0 and y=0)
        @param bp: The Base Point to insert the geometry and base for rotation
        (Default is also x=0 and y=0)
        @param sca: The scale of the basis function (default =1)
        @param rot: The rotation of the geometries around base (default =0)
        """

        self.shapes = shapes
        self.EntitiesRoot = EntitiesRoot

        del(self.wpzero)

        self.plot_shapes()
        self.plot_wp_zero()
        self.update()

    def plot_wp_zero(self):
        """
        This function is called while the drawing of all items is done. It plots
        the WPZero to the Point x=0 and y=0. This item will be enabled or
        disabled to be shown or not.
        """
        self.wpzero = WpZero(QtCore.QPointF(0, 0))
        self.addItem(self.wpzero)

    def plot_shapes(self):
        """
        This function performs all plotting for the shapes. This may also
        get an instance of the shape later on.
        FIXME
        """
        for shape in self.shapes:
            self.addItem(shape)
            self.plot_shape(shape)
        logger.debug(self.tr("Update GrapicsScene"))

    def plot_shape(self, shape):
        """
        Create all plotting related parts of one shape.
        @param shape: The shape to be plotted.
        """
        shape.make_papath()
        shape.starrow = self.createstarrow(shape)
        shape.enarrow = self.createenarrow(shape)
        shape.stmove = self.createstmove(shape)
        shape.starrow.setParentItem(shape)
        shape.enarrow.setParentItem(shape)
        shape.stmove.setParentItem(shape)


    def createstarrow(self, shape):
        """
        This function creates the Arrows at the end point of a shape when the
        shape is selected.
        @param shape: The shape for which the Arrow shall be created.
        """

        length = 20
        start, start_ang = shape.get_st_en_points(0)
        arrow = Arrow(startp=start,
                      length=length,
                      angle=start_ang,
                      color=QtGui.QColor(50, 200, 255),
                      pencolor=QtGui.QColor(50, 100, 255))
        arrow.hide()
        return arrow


    def createenarrow(self, shape):
        """
        This function creates the Arrows at the end point of a shape when the
        shape is selected.
        @param shape: The shape for which the Arrow shall be created.
        """
        length = 20
        end, end_ang = shape.get_st_en_points(1)
        arrow = Arrow(startp=end,
                      length=length, angle=end_ang,
                      color=QtGui.QColor(0, 245, 100),
                      pencolor=QtGui.QColor(0, 180, 50),
                      dir=1)
        arrow.hide()
        return arrow


    def createstmove(self, shape):
        """
        This function creates the Additional Start and End Moves in the plot
        window when the shape is selected
        @param shape: The shape for which the Move shall be created.
        """
        start, start_ang = shape.get_st_en_points(0)
        stmove = StMove(start,
                      start_ang,
                      QtGui.QColor(50, 100, 255),
                      shape,self.EntitiesRoot)
        stmove.hide()
        return stmove

    def resetexproutes(self):
        """
        This function resets all of the export route
        """
        self.delete_opt_path()

    def addexproutest(self):
        """
        This function initialises the Arrows of the export route order and
        its numbers.
        @param shapes_st_en_points: The start and end points of the shapes.
        @param route: The order of the shapes to be plotted.
        """

        x_st = g.config.vars.Plane_Coordinates['axis1_start_end']
        y_st = g.config.vars.Plane_Coordinates['axis2_start_end']
        self.expprv = Point(x=x_st, y=y_st)
        self.expcol = QtCore.Qt.darkRed

    def addexproute(self, exp_order, layer_nr):
        """
        This function initialises the Arrows of the export route order and
        its numbers.
        @param shapes_st_en_points: The start and end points of the shapes.
        @param route: The order of the shapes to be plotted.
        """

        x_st = g.config.vars.Plane_Coordinates['axis1_start_end']
        y_st = g.config.vars.Plane_Coordinates['axis2_start_end']
        start = Point(x=x_st, y=y_st)
        ende = Point(x=x_st, y=y_st)

        #shapes_st_en_points.append([start,ende])

        #Print the optimised route
        for shape_nr in range(len(exp_order)):
            st = self.expprv
            en, self.expprv = self.shapes[exp_order[shape_nr]].get_st_en_points()

#            st=shapes_st_en_points[route[st_nr]][1]
#            en=shapes_st_en_points[route[en_nr]][0]

            self.routearrows.append(Arrow(startp=st,
                                          endp=en,
                                          color=self.expcol,
                                          pencolor=self.expcol))

            self.expcol = QtCore.Qt.darkGray

            self.routetext.append(RouteText(text=("%s,%s" % (layer_nr, shape_nr+1)),
                                            startp=en))

            #self.routetext[-1].ItemIgnoresTransformations

            self.addItem(self.routetext[-1])
            self.addItem(self.routearrows[-1])


    def addexprouteen(self):
        """
        This function initialises the Arrows of the export route order and
        its numbers.
        @param shapes_st_en_points: The start and end points of the shapes.
        @param route: The order of the shapes to be plotted.
        """

        x_st = g.config.vars.Plane_Coordinates['axis1_start_end']
        y_st = g.config.vars.Plane_Coordinates['axis2_start_end']
        st = self.expprv
        en = Point(x=x_st, y=y_st)
        self.expcol = QtCore.Qt.darkRed

        self.routearrows.append(Arrow(startp=st,
                                      endp=en,
                                      color=self.expcol,
                                      pencolor=self.expcol))

        self.addItem(self.routearrows[-1])

    def delete_opt_path(self):
        """
        This function deletes all the plotted export routes.
        """
        while self.routearrows:
            item = self.routearrows.pop()
            item.hide()
            #self.removeItem(item)
            del item

        while self.routetext:
            item = self.routetext.pop()
            item.hide()
            #self.removeItem(item)
            del item

    def setShow_disabled_paths(self, flag):
        """
        This function is called by the Main Menu and is passed from Main to
        MyGraphicsView to the Scene. It performs the showing or hiding
        of enabled/disabled shapes.

        @param flag: This flag is true if hidden paths shall be shown
        """
        self.showDisabled = flag

        for shape in self.shapes:
            if flag and shape.isDisabled():
                shape.show()
            elif not(flag) and shape.isDisabled():
                shape.hide()

