# -*- coding: utf-8 -*-

"""
Special purpose canvas including all required plotting function etc.
@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose:  Plotting all
@author: Christian Kohl�ffel 
@since:  22.04.2011
@license: GPL
"""
from copy import copy

from PyQt4 import QtCore, QtGui
from Core.Point import Point
from Core.Shape import ShapeClass

from Gui.WpZero import WpZero
from Gui.Arrow import Arrow
from Gui.StMove import StMove
from Gui.RouteText import RouteText
#import math
import Core.Globals as g
import Core.constants as c

import logging
logger=logging.getLogger("DxfImport.myCanvasClass") 
       
class MyGraphicsView(QtGui.QGraphicsView): 
    """
    This is the used Canvas to print the graphical interface of dxf2gcode. 
    All GUI things should be performed in the View and plotting functions in 
    the scene
    @sideeffect: None                            
    """  

    def __init__(self, parent = None): 
        """
        Initialisation of the View Object. This is called by the ui created
        with the QTDesigner.
        @param parent: Main is passed as a pointer for reference.
        """
        super(MyGraphicsView, self).__init__(parent) 
        self.currentItem=None
        
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse) 
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter) 
        
        #self.setDragMode(QtGui.QGraphicsView.RubberBandDrag )
        self.setDragMode(QtGui.QGraphicsView.NoDrag)
        
        self.parent=parent
        self.mppos=None
        self.selmode=0
        
        self.rubberBand = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self)
    
    def contextMenuEvent(self, event):
        """
        Create the contextmenu.
        @purpose: Links the new Class of ContextMenu to Graphicsview.
        """
        menu=MyDropDownMenu(self,self.scene(),self.mapToGlobal(event.pos()))

    def keyPressEvent(self,event):
        """
        Rewritten KeyPressEvent to get other behavior while Shift is pressed.
        @purpose: Changes to ScrollHandDrag while Control pressed
        @param event:    Event Parameters passed to function
        """
        if (event.key()==QtCore.Qt.Key_Shift):   
            self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        elif (event.key()==QtCore.Qt.Key_Control):
            self.selmode=1
        else:
            pass
        
        super(MyGraphicsView, self).keyPressEvent(event)  
           
    def keyReleaseEvent (self,event):
        """
        Rewritten KeyReleaseEvent to get other behavior while Shift is pressed.
        @purpose: Changes to RubberBandDrag while Control released
        @param event:    Event Parameters passed to function
        """
        if (event.key()==QtCore.Qt.Key_Shift):   
            self.setDragMode(QtGui.QGraphicsView.NoDrag)
            #self.setDragMode(QtGui.QGraphicsView.RubberBandDrag )
        elif (event.key()==QtCore.Qt.Key_Control):
            self.selmode=0
        else:
            pass
        
        super(MyGraphicsView, self).keyPressEvent(event)  

    def wheelEvent(self,event):
        """
        With Mouse Wheel the Thing is scaled
        @purpose: Scale by mouse wheel
        @param event: Event Parameters passed to function
        """
        scale=(1000+event.delta())/1000.0
        self.scale(scale,scale)
        
    def mousePressEvent(self, event):
        """
        Right Mouse click shall have no function, Therefore pass only left 
        click event
        @purpose: Change inherited mousePressEvent
        @param event: Event Parameters passed to function
        """
        
        if(self.dragMode())==1:
            super(MyGraphicsView, self).mousePressEvent(event)
        elif event.button() == QtCore.Qt.LeftButton:
            self.mppos=event.pos() 
        else:
            pass
        
    def mouseReleaseEvent(self, event):
        """
        Right Mouse click shall have no function, Therefore pass only left 
        click event
        @purpose: Change inherited mousePressEvent
        @param event: Event Parameters passed to function
        """
        delta=2
        
        if(self.dragMode())==1:
            #if (event.key()==QtCore.Qt.Key_Shift):   
            #self.setDragMode(QtGui.QGraphicsView.NoDrag)
            super(MyGraphicsView, self).mouseReleaseEvent(event)
        
        #Selection only enabled for left Button
        elif event.button() == QtCore.Qt.LeftButton:
            #If the mouse button is pressed without movement of rubberband
            if self.rubberBand.isHidden():
                rect=QtCore.QRect(event.pos().x()-delta,event.pos().y()-delta,
                          2*delta,2*delta)
            #If movement is bigger and rubberband is enabled
            else:
                rect=self.rubberBand.geometry()
                self.rubberBand.hide()

            #All items in the selection
            self.currentItems=self.items(rect)
            #print self.currentItems
            scene=self.scene()
            
            if self.selmode==0:
                for item in scene.selectedItems():
                    item.starrow.setSelected(False)
                    item.stmove.setSelected(False)
                    item.enarrow.setSelected(False)
                    item.setSelected(False)
                
            
            for item in self.currentItems:
                if item.isSelected():
                    item.setSelected(False)
                else:
                    #print (item.flags())
                    item.setSelected(True)
                    
        else:
            pass
        
        self.mppos=None
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
                
        self.setStatusTip('X: %3.1f; Y: %3.1f' %(event.pos().x(),event.pos().y()))
        self.setToolTip('X: %3.1f; Y: %3.1f' %(event.pos().x(),event.pos().y()))
            
        super(MyGraphicsView, self).mouseMoveEvent(event)        
         
    def autoscale(self):
        """
        Automatically zooms to the full extend of the current GraphicsScene
        """
        scene=self.scene()
        scext=scene.itemsBoundingRect()
        self.fitInView(scext,QtCore.Qt.KeepAspectRatio)
        logger.debug("Autoscaling to extend: %s" % (scext))
        
    def setShow_path_direction(self,flag):
        """
        This function is called by the Main Window from the Menubar.
        @param flag: This flag is true if all Path Direction shall be shown
        """
        scene=self.scene()
        for shape in scene.shapes:
            shape.starrow.setallwaysshow(flag)
            shape.enarrow.setallwaysshow(flag)
            shape.stmove.setallwaysshow(flag)
            
    def setShow_wp_zero(self,flag):
        """
        This function is called by the Main Window from the Menubar.
        @param flag: This flag is true if all Path Direction shall be shown
        """
        scene=self.scene()
        if flag is True:
            scene.wpzero.show()
        else:
            scene.wpzero.hide()
            
    def setShow_disabled_paths(self,flag):
        """
        This function is called by the Main Window from the Menubar.
        @param flag: This flag is true if hidden paths shall be shown
        """
        scene=self.scene()
        scene.setShow_disabled_paths(flag)
         
    def clearScene(self):
        """
        Deletes the existing GraphicsScene.
        """
        scene=self.scene()
        del(scene) 

class MyDropDownMenu(QtGui.QMenu):
    def __init__(self,MyGraphicsView,MyGraphicsScene,position):
        
        QtGui.QMenu.__init__(self)
        
        self.MyGraphicsScene=MyGraphicsScene
        self.MyGraphicsView=MyGraphicsView
             
        if len(self.MyGraphicsScene.selectedItems())==0:
            return
       
        invertAction = self.addAction("Invert Selection")
        disableAction = self.addAction("Disable Selection")
        enableAction = self.addAction("Enable Selection")
        
        self.addSeparator()
        
        swdirectionAction = self.addAction("Switch Direction")
        
        
        submenu1= QtGui.QMenu('Cutter Compensation',self)
        self.noCompAction = submenu1.addAction("G40 No Compensation")
        self.noCompAction.setCheckable(True)
        self.leCompAction = submenu1.addAction("G41 Left Compensation")
        self.leCompAction.setCheckable(True)
        self.reCompAction = submenu1.addAction("G42 Right Compensation")
        self.reCompAction.setCheckable(True)
        
        logger.debug("The selected shapes have the following direction: %i" % (self.calcMenuDir()))
        self.checkMenuDir(self.calcMenuDir())
        
        self.addMenu(submenu1)
        
        invertAction.triggered.connect(self.invertSelection)
        disableAction.triggered.connect(self.disableSelection)
        enableAction.triggered.connect(self.enableSelection)
        
        swdirectionAction.triggered.connect(self.switchDirection)
        
        self.noCompAction.triggered.connect(self.setNoComp)
        self.leCompAction.triggered.connect(self.setLeftComp)
        self.reCompAction.triggered.connect(self.setRightComp)
        

        self.exec_(position)
        
            
    def calcMenuDir(self):
        """
        This method returns the direction of the selected items. If there are 
        different cutter direction in the selection 0 is returned. 1 for Left
        and 2 for right.
        """
        
        items=self.MyGraphicsScene.selectedItems()
        if len(items)==0:
            return 0
            
        dir=items[0].cut_cor
        for item in items: 
            if not(dir==item.cut_cor):
                return 0
               
        return dir-40

    def checkMenuDir(self,dir):
        """
        This method checks the buttons in the Contextmenu for the direction of 
        the selected items.
        @param dir: The direction of the items -1= different 0=None, 1=left, 2 =right 
        """
        self.noCompAction.setChecked(False)
        self.leCompAction.setChecked(False)
        self.reCompAction.setChecked(False)
        
        if dir==0:
            self.noCompAction.setChecked(True)    
        elif dir==1:
            self.leCompAction.setChecked(True)    
        elif dir==2:
            self.reCompAction.setChecked(True)    
        
    def invertSelection(self):
        """
        This function is called by the Contextmenu of the Graphicsview.
        @purpose: It is used to invert the selection of all shapes. 
        """
        #scene=self.scene()
        for shape in self.MyGraphicsScene.shapes: 
            if shape.isSelected():
                shape.setSelected(False)
            else:
                shape.setSelected(True)
                      
    def disableSelection(self):
        """
        Disables all shapes which are currently selected. Based on the view
        options they are not shown or shown in a different color and pointed
        """
        #scene=self.scene()
        for shape in self.MyGraphicsScene.shapes:
            if shape.isSelected():
                shape.setDisable(True)
        self.MyGraphicsScene.update()

    def enableSelection(self):
        """
        Enables all shapes which are currently selected. Based on the view
        options they are not shown or shown in a different color and pointed
        """
        #scene=self.scene()
        for shape in self.MyGraphicsScene.shapes:
            if shape.isSelected():
                shape.setDisable(False)
        self.MyGraphicsScene.update()

    def switchDirection(self):
        """
        Switched the Direction of all items. Example from CW direction to CCW
        """
        for shape in self.MyGraphicsScene.shapes:
            shape.reverse()

            logger.debug(_('Switched Direction at Shape Nr: %i')\
                             %(shape.nr))
        
            shape.updateCutCor()
            
            
    def setNoComp(self):
        """
        Sets the compensation 40, which is none for the selected items.
        """
        items=self.MyGraphicsScene.selectedItems()
        for item in items:
            item.cut_cor=40
            logger.debug(_('Changed Cutter Correction to None Shape Nr: %i')\
                             %(item.nr))
            
            item.updateCutCor()
            
    def setLeftComp(self):
        """
        Sets the compensation 41, which is Left for the selected items.
        """
        items=self.MyGraphicsScene.selectedItems()
        for item in items:
            item.cut_cor=41
            logger.debug(_('Changed Cutter Correction to left Shape Nr: %i')\
                             %(item.nr))
            item.updateCutCor()
            
    def setRightComp(self):
        """
        Sets the compensation 42, which is Right for the selected items.
        """
        items=self.MyGraphicsScene.selectedItems()
        for item in items:
            item.cut_cor=42
            logger.debug(_('Changed Cutter Correction to right Shape Nr: %i')\
                             %(item.nr))
            item.updateCutCor()
 
class MyGraphicsScene(QtGui.QGraphicsScene): 
    """
    This is the used Canvas to print the graphical interface of dxf2gcode.
    The Scene is rendered into the previously defined mygraphicsView class. 
    All performed plotting functions should be defined here.
    @sideeffect: None                            
    """       
    def __init__(self):
        QtGui.QGraphicsScene.__init__(self)
       
        self.shapes=[]
        self.wpzero=[]
        self.LayerContents=[]
        self.routearrows=[]
        self.routetext=[]
        self.showDisabled=False
        self.EntitiesRoot=EntitieContentClass(Nr=-1, Name='Base',parent=None,children=[],
                                              p0=Point(0,0),pb=Point(0,0),
                                              sca=1,rot=0)
        self.BaseEntities=EntitieContentClass()
               
    def makeplot(self,values,p0,pb,sca,rot):
        """
        Instance is called by the Main Window after the defined file is loaded.
        It generates all ploting functionallity. The parameters are generally 
        used to scale or offset the base geometry (by Menu in GUI).
        
        @param values: The loaded dxf values fro mthe dxf_import.py file
        @param p0: The Starting Point to plot (Default x=0 and y=0)
        @param bp: The Base Point to insert the geometry and base for rotation 
        (Default is also x=0 and y=0)
        @param sca: The scale of the basis function (default =1)
        @param rot: The rotation of the geometries around base (default =0)
        """
        self.values=values

        #Zuruecksetzen der Konturen
        del(self.shapes[:])
        del(self.wpzero)
        del(self.LayerContents[:])
        del(self.EntitiesRoot)
        self.EntitiesRoot=EntitieContentClass(Nr=0,Name='Entities',parent=None,children=[],
                                            p0=p0,pb=pb,sca=sca,rot=rot)

        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        self.makeshapes(parent=self.EntitiesRoot)
        self.plot_shapes()
        self.plot_wp_zero()
        self.LayerContents.sort()
        #self.EntitieContents.sort()
        
        self.update()

    def plot_wp_zero(self):
        """
        This function is called while the drawing of all items is done. I plots 
        the WPZero to the Point x=0 and y=0. This Item will be enabled or 
        disabled to be shown or not.
        """  
        self.wpzero=WpZero(QtCore.QPointF(0,0))
        self.addItem(self.wpzero)

    def makeshapes(self,parent=None,ent_nr=-1):
        """
        Instance is called prior to the plotting of the shapes. It creates
        all shape classes which are later plotted into the graphics.
        
        @param parent: The parent of a shape is always a Entities. It may be root 
        or if it is a Block this is the Block. 
        @param ent_nr: The values given in self.values are sorted in that way 
        that 0 is the Root Entities and  1 is beginning with the first block. 
        This value gives the index of self.values to be used.
        """

        if parent.Name=="Entities":      
            entities=self.values.entities
        else:
            ent_nr=self.values.Get_Block_Nr(parent.Name)
            entities=self.values.blocks.Entities[ent_nr]
            
        #Zuweisen der Geometrien in die Variable geos & Konturen in cont
        ent_geos=entities.geo
               
        #Schleife fuer die Anzahl der Konturen 
        for cont in entities.cont:
            #Abfrage falls es sich bei der Kontur um ein Insert eines Blocks handelt
            if ent_geos[cont.order[0][0]].Typ=="Insert":
                ent_geo=ent_geos[cont.order[0][0]]
                
                #Zuweisen des Basispunkts f�r den Block
                new_ent_nr=self.values.Get_Block_Nr(ent_geo.BlockName)
                new_entities=self.values.blocks.Entities[new_ent_nr]
                pb=new_entities.basep
                
                #Skalierung usw. des Blocks zuweisen
                p0=ent_geos[cont.order[0][0]].Point
                sca=ent_geos[cont.order[0][0]].Scale
                rot=ent_geos[cont.order[0][0]].rot
                
                #Erstellen des neuen Entitie Contents f�r das Insert
                NewEntitieContent=EntitieContentClass(Nr=0,Name=ent_geo.BlockName,
                                        parent=parent,children=[],
                                        p0=p0,
                                        pb=pb,
                                        sca=sca,
                                        rot=rot)

                parent.addchild(NewEntitieContent)
            
                self.makeshapes(parent=NewEntitieContent,ent_nr=ent_nr)
                
            else:
                #Schleife fuer die Anzahl der Geometrien
                self.shapes.append(ShapeClass(len(self.shapes),\
                                                cont.closed,\
                                                40,\
                                                0.0,\
                                                parent,\
                                                []))
                for ent_geo_nr in range(len(cont.order)):
                    ent_geo=ent_geos[cont.order[ent_geo_nr][0]]
                    if cont.order[ent_geo_nr][1]:
                        ent_geo.geo.reverse()
                        for geo in ent_geo.geo:
                            geo=copy(geo)
                            geo.reverse()
                            self.shapes[-1].geos.append(geo)

                        ent_geo.geo.reverse()
                    else:
                        for geo in ent_geo.geo:
                            self.shapes[-1].geos.append(copy(geo))
                        
                self.addtoLayerContents(self.shapes[-1],ent_geo.Layer_Nr)
                parent.addchild(self.shapes[-1])

    def plot_shapes(self):
        """
        This function is performing all plotting for the shapes. This may also 
        get a Instance of the shape later on.
        FIXME
        """
        for shape in self.shapes:
            shape.make_papath()
            self.addItem(shape)

            shape.starrow=self.createstarrow(shape)
            shape.enarrow=self.createenarrow(shape)
            shape.stmove=self.createstmove(shape)
            shape.starrow.setParentItem(shape)
            shape.enarrow.setParentItem(shape)
            shape.stmove.setParentItem(shape)
 
        logger.debug("Update GrapicsScene")
        
            #Hinzufuegen der Kontur zum Layer
            
        #Erstellen des Gesamten Ausdrucks      

    def createstarrow(self,shape):
        
        length=20
        start, start_ang = shape.get_st_en_points(0)
        arrow=Arrow(startp=start,
                    length=length,
                    angle=start_ang,
                    color=QtGui.QColor(50, 200, 255),
                    pencolor=QtGui.QColor(50, 100, 255))
        arrow.hide()
        return arrow
        
    def createenarrow(self,shape):
        
        length=20
        end, end_ang = shape.get_st_en_points(1)
        arrow=Arrow(startp=end,
                    length=length,angle=end_ang,
                    color=QtGui.QColor(0, 245, 100),
                    pencolor=QtGui.QColor(0, 180, 50),
                    dir=1)
        arrow.hide()
        return arrow
    

    def createstmove(self,shape):
        
        start, start_ang = shape.get_st_en_points(0)
        stmove=StMove(start,
                    start_ang,
                    QtGui.QColor(50, 100, 255),
                    shape.cut_cor,self.EntitiesRoot)
        stmove.hide()
        return stmove
    
    def iniexproute(self,shapes_st_en_points,route):
        
        self.delete_opt_path()

        #Ausdrucken der optimierten Route
        for en_nr in range(len(route)):
            if en_nr==0:
                st_nr=-1
                #col='gray'
            elif en_nr==1:
                st_nr=en_nr-1
                col='gray'
            else:
                st_nr=en_nr-1
                #col='peru'
                
            st=shapes_st_en_points[route[st_nr]][1]
            en=shapes_st_en_points[route[en_nr]][0]

            self.routearrows.append(Arrow(startp=st,
                  endp=en,
                  color=QtCore.Qt.red,
                  pencolor=QtCore.Qt.red))
            
            self.routetext.append(RouteText(text=("%s" %en_nr),startp=st)) 
            
            #self.routetext[-1].ItemIgnoresTransformations 
            
            self.addItem(self.routetext[-1])   
            self.addItem(self.routearrows[-1])

    def updateexproute(self,shapes_st_en_points,route):
        
        
        for en_nr in range(len(route)):
            if en_nr==0:
                st_nr=-1
            elif en_nr==1:
                st_nr=en_nr-1
            else:
                st_nr=en_nr-1
            
            st=shapes_st_en_points[route[st_nr]][1]
            en=shapes_st_en_points[route[en_nr]][0]
            
            self.routearrows[en_nr].updatepos(st,en)
            self.routetext[en_nr].updatepos(st)
        

    def delete_opt_path(self):

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
           
    def addtoLayerContents(self,shape_nr,lay_nr):
        #Abfrage of der gesuchte Layer schon existiert
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.shapes.append(shape_nr)
                return

        #Falls er nicht gefunden wurde neuen erstellen
        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(LayerContentClass(lay_nr,LayerName,[shape_nr]))
        
    def addtoEntitieContents(self,shape_nr,ent_nr,c_nr):
        
        for EntCon in self.EntitieContents:
            if EntCon.EntNr==ent_nr:
                if c_nr==0:
                    EntCon.shapes.append([])
                
                EntCon.shapes[-1].append(shape_nr)
                return

        #Falls er nicht gefunden wurde neuen erstellen
        if ent_nr==-1:
            EntName='Entities'
        else:
            EntName=self.values.blocks.Entities[ent_nr].Name
            
        self.EntitieContents.append(EntitieContentClass(ent_nr,EntName,[[shape_nr]]))
        
    def setShow_disabled_paths(self,flag):
        """
        This function is called by the Main Menu and is passed from Main to 
        MyGraphicsView to the Scene. It shall perform the showing or hidding 
        of enabled/disabled shapes.
        
        @param flag: This flag is true if hidden paths shall be shown
        """
        self.showDisabled=flag

        for shape in self.shapes:
            if flag and shape.isDisabled():
                shape.show()
            elif not(flag) and shape.isDisabled():
                shape.hide()

#        
#    #Verschieben des Werkst�cknullpunkts auf die momentane Cursor Position
#    def set_wp_zero(self):
#        #print("Hier gehts dann")
#        #print ("X %0.2f Y %0.2f" %(self.Canvas.x, self.Canvas.y))
#        self.Canvas.window.Move_WP_zero(x=self.Canvas.x, y=self.Canvas.y)
#            

#    def plot_cut_info(self):
#        for hdl in self.dir_hdls:
#            self.Canvas.canvas.delete(hdl) 
#        self.dir_hdls=[]
#
#        if not(self.toggle_start_stop.get()):
#            draw_list=self.Selected[:]
#        else:
#            draw_list=range(len(self.shapes))
#               
#        for shape_nr in draw_list:
#            if not(shape_nr in self.Disabled):
#                self.dir_hdls+=self.shapes[shape_nr].plot_cut_info(self.Canvas,self.config)
#
#
#    def plot_opt_route(self,shapes_st_en_points,route):
#        #Ausdrucken der optimierten Route
#        for en_nr in range(len(route)):
#            if en_nr==0:
#                st_nr=-1
#                col='gray'
#            elif en_nr==1:
#                st_nr=en_nr-1
#                col='gray'
#            else:
#                st_nr=en_nr-1
#                col='peru'
#                
#            st=shapes_st_en_points[route[st_nr]][1]
#            en=shapes_st_en_points[route[en_nr]][0]
#
#            x_ca_s,y_ca_s=self.Canvas.get_can_coordinates(st.x,st.y)
#            x_ca_e,y_ca_e=self.Canvas.get_can_coordinates(en.x,en.y)
#
#            self.path_hdls.append(Line(self.Canvas.canvas,x_ca_s,-y_ca_s,x_ca_e,-y_ca_e,fill=col,arrow='last'))
#        self.Canvas.canvas.update()


            
class LayerContentClass:
    def __init__(self,LayerNr=None,LayerName='',shapes=[]):
        self.LayerNr=LayerNr
        self.LayerName=LayerName
        self.shapes=shapes
        
    def __cmp__(self, other):
         return cmp(self.LayerNr, other.LayerNr)

    def __str__(self):
        return ('\ntype:        %s' %self.type) +\
               ('\nLayerNr :      %i' %self.LayerNr) +\
               ('\nLayerName:     %s' %self.LayerName)+\
               ('\nshapes:    %s' %self.shapes)       
               
class EntitieContentClass:
    def __init__(self,type="Entitie",Nr=None,Name='',parent=None,children=[],
                p0=Point(x=0.0,y=0.0),pb=Point(x=0.0,y=0.0),sca=[1,1,1],rot=0.0):
                    
        self.type=type
        self.Nr=Nr
        self.Name=Name
        self.children=children
        self.p0=p0
        self.pb=pb
        self.sca=sca
        self.rot=rot
        self.parent=parent

    def __cmp__(self, other):
         return cmp(self.EntNr, other.EntNr)        
        
    def __str__(self):
        return ('\ntype:        %s' %self.type) +\
               ('\nNr :      %i' %self.Nr) +\
               ('\nName:     %s' %self.Name)+\
               ('\np0:          %s' %self.p0)+\
               ('\npb:          %s' %self.pb)+\
               ('\nsca:         %s' %self.sca)+\
               ('\nrot:         %s' %self.rot)+\
               ('\nchildren:    %s' %self.children)
            
    #Hinzufuegen der Kontur zu den Entities
    def addchild(self,child):
        self.children.append(child)
  