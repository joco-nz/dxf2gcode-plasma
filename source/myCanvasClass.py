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
from point import PointClass
from shape import ShapeClass

import math
import globals as g
import constants as c

       
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
        #self.origin = QPoint()
        
        #self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        #self.createContextMenu()
    
    def contextMenuEvent(self, event):
        """
        Create the contextmenu.
        @purpose: Links the callbacks to the actions in the menu
        """
        
        scene=self.scene()
        items=scene.selectedItems()
        
        if  len(items):
            menu = QtGui.QMenu(self)
            invertAction = menu.addAction("Invert Selection")
            disableAction = menu.addAction("Disable Selection")
            enableAction = menu.addAction("Enable Selection")
            
            menu.addSeparator()
            
            swdirectionAction = menu.addAction("Switch Directtion")
            
            quitAction.triggered.connect(self.close)
    
#            action = menu.exec_(self.mapToGlobal(event.pos()))
#            if action == quitAction:
#                pass



#        popup.add_command(label=_('Invert Selection'),command=self.Content.invert_selection)
#        popup.add_command(label=_('Disable Selection'),command=self.Content.disable_selection)
#        popup.add_command(label=_('Enable Selection'),command=self.Content.enable_selection)
#
#        popup.add_separator()
#        popup.add_command(label=_('Switch Direction'),command=self.Content.switch_shape_dir)
#        
#        #Untermenu fuer die Fräserkorrektur
#        self.dir_var.set(self.Content.calc_dir_var())
#        cut_cor_menu = Menu(popup,tearoff=0)
#        cut_cor_menu.add_checkbutton(label=_("G40 No correction"),\
#                                     variable=self.dir_var,onvalue=0,\
#                                     command=lambda:self.Content.set_cut_cor(40))
#        cut_cor_menu.add_checkbutton(label=_("G41 Cutting left"),\
#                                     variable=self.dir_var,onvalue=1,\
#                                     command=lambda:self.Content.set_cut_cor(41))
#        cut_cor_menu.add_checkbutton(label=_("G42 Cutting right"),\
#                                     variable=self.dir_var,onvalue=2,\
#                                     command=lambda:self.Content.set_cut_cor(42))
#        popup.add_cascade(label=_('Set Cutter Correction'),menu=cut_cor_menu)
#


#            
    def close(self):
        print 'Jaja'

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
            super(MyGraphicsView, self).mousePressEvent(event)
        
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
            point = event.pos() - self.mppos
            if (point.manhattanLength() > 3):
                #print 'the mouse has moved more than 3 pixels since the oldPosition'
                #print "Mouse Pointer is currently hovering at: ", event.pos() 
                self.rubberBand.show()
                self.rubberBand.setGeometry(QtCore.QRect(self.mppos, event.pos()).normalized())
            
        super(MyGraphicsView, self).mouseMoveEvent(event)        
         
    def autoscale(self):
        """
        Automatically zooms to the full extend of the current GraphicsScene
        """
        scene=self.scene()
        scext=scene.itemsBoundingRect()
        self.fitInView(scext,QtCore.Qt.KeepAspectRatio)
        g.logger.logger.debug("Autoscaling to extend: %s" % (scext))
        
    def show_path_direction(self,flag):
        """
        This function is called by the Main Window from the Menubar.
        @param flag: This flag is true if all Path Direction shall be shown
        """
        scene=self.scene()
        for shape in scene.shapes:
            shape.starrow.setallwaysshow(flag)
            shape.enarrow.setallwaysshow(flag)
            
    def show_wp_zero(self,flag):
        """
        This function is called by the Main Window from the Menubar.
        @param flag: This flag is true if all Path Direction shall be shown
        """
        scene=self.scene()
        if flag is True:
            scene.wpzero.show()
        else:
            scene.wpzero.hide()
        
      
    def clearScene(self):
        """
        Deletes the existing GraphicsScene.
        """
        scene=self.scene()
        del(scene) 
        
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
        self.EntitiesRoot=EntitieContentClass()
        self.BaseEntities=EntitieContentClass()

                   
    def makeplot(self,values,p0,pb,sca,rot):
        self.values=values


        #Zuruecksetzen der Konturen
        self.shapes=[]
        self.wpzero=[]
        self.LayerContents=[]
        self.EntitiesRoot=EntitieContentClass(Nr=0,Name='Entities',parent=None,children=[],
                                            p0=p0,pb=pb,sca=sca,rot=rot)

        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        self.makeshapes(parent=self.EntitiesRoot)
        self.plot_shapes()
        self.plot_wp_zero()
        self.LayerContents.sort()
        #self.EntitieContents.sort()


       #Drucken des Werkstuecknullpunkts
    def plot_wp_zero(self):
        
        self.wpzero=WpZero(QtCore.QPointF(0,0))
        self.addItem(self.wpzero)
        
        
        #self.wpzero.hide()


    def makeshapes(self,parent=None,ent_nr=-1):

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
                                                [],\
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
        for shape in self.shapes:
            shape.make_papath()
            self.addItem(shape)

            shape.starrow=self.createstarrow(shape)
            shape.enarrow=self.createenarrow(shape)
            
           
            
        g.logger.logger.debug("Update GrapicsScene %s:" % (dir(self)))
        self.update()
        
            #Hinzufuegen der Kontur zum Layer
            
        #Erstellen des Gesamten Ausdrucks      

    def createstarrow(self,shape):
        
        length=20
        start, start_ang = shape.get_st_en_points(0)
        arrow=Arrow(QtCore.QPointF(start.x,-start.y),
                    length,start_ang,
                    QtGui.QColor(50, 200, 255),
                    QtGui.QColor(50, 100, 255))
        arrow.hide()
        self.addItem(arrow)
        return arrow
        
        
    def createenarrow(self,shape):
        
        length=20
        end, end_ang = shape.get_st_en_points(1)
        arrow=Arrow(QtCore.QPointF(end.x,-end.y),
                    length,end_ang,
                    QtGui.QColor(0, 245, 100),
                    QtGui.QColor(0, 180, 50),1)
        arrow.hide()
        self.addItem(arrow)
        return arrow
           
    def addtoLayerContents(self,shape_nr,lay_nr):
        #Abfrage of der gesuchte Layer schon existiert
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.shapes.append(shape_nr)
                return

        #Falls er nicht gefunden wurde neuen erstellen
        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(LayerContentClass(lay_nr,LayerName,[shape_nr]))
        
    #Hinzufuegen der Kontur zu den Entities
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
        
        
        
#    def calc_dir_var(self):
#        if len(self.Selected)==0:
#            return -1
#        dir=self.shapes[self.Selected[0]].cut_cor
#        for shape_nr in self.Selected[1:len(self.Selected)]: 
#            if not(dir==self.shapes[shape_nr].cut_cor):
#                return -1   
#        return dir-40
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




    def delete_opt_path(self):
        for hdl in self.path_hdls:
            self.Canvas.canvas.delete(hdl)
            
        self.path_hdls=[]
        
    def invert_selection(self):
        new_sel=[]
        for shape_nr in range(len(self.shapes)):
            if (not(shape_nr in self.Disabled)) & (not(shape_nr in self.Selected)):
                new_sel.append(shape_nr)

        self.deselect()
        self.Selected=new_sel
        self.set_shapes_color(self.Selected,'selected')
        self.plot_cut_info()

        self.textbox.prt(_('\nInverting Selection'),3)
        

    def disable_selection(self):
        for shape_nr in self.Selected:
            if not(shape_nr in self.Disabled):
                self.Disabled.append(shape_nr)
        self.set_shapes_color(self.Selected,'disabled')
        self.Selected=[]
        self.plot_cut_info()

    def enable_selection(self):
        for shape_nr in self.Selected:
            if shape_nr in self.Disabled:
                nr=self.Disabled.index(shape_nr)
                del(self.Disabled[nr])
        self.set_shapes_color(self.Selected,'deselected')
        self.Selected=[]
        self.plot_cut_info()

    def show_disabled(self):
        if (self.toggle_show_disabled.get()==1):
            self.set_hdls_normal(self.Disabled)
            self.show_dis=1
        else:
            self.set_hdls_hidden(self.Disabled)
            self.show_dis=0

    def switch_shape_dir(self):
        for shape_nr in self.Selected:
            self.shapes[shape_nr].reverse()
            self.textbox.prt(_('\n\nSwitched Direction at Shape: %s')\
                             %(self.shapes[shape_nr]),3)
        self.plot_cut_info()
        
    def set_cut_cor(self,correction):
        for shape_nr in self.Selected: 
            self.shapes[shape_nr].cut_cor=correction
            
            self.textbox.prt(_('\n\nChanged Cutter Correction at Shape: %s')\
                             %(self.shapes[shape_nr]),3)
        self.plot_cut_info() 
        
         
                         

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
                p0=PointClass(x=0.0,y=0.0),pb=PointClass(x=0.0,y=0.0),sca=[1,1,1],rot=0.0):
                    
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
                      
                      
class Arrow(QtGui.QGraphicsLineItem):
    def __init__(self, startp, length, angle, 
                 color=QtCore.Qt.red,pencolor=QtCore.Qt.green,
                 dir=0):
        self.sc=1
        super(Arrow, self).__init__()

        self.startp=startp
        self.endp=startp
        self.length=length
        self.angle=angle
        self.dir=dir
        self.allwaysshow=False
        
        
        self.arrowHead = QtGui.QPolygonF()
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
        self.myColor=color
        self.pen=QtGui.QPen(pencolor, 1, QtCore.Qt.SolidLine,
                QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.arrowSize = 8.0
        
        self.pen.setCosmetic(True)
        
    def setSelected(self,flag=True):
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
        
    def setallwaysshow(self,flag=False):
        """
        If the directions shall be allwaysshown the paramerter will be set and 
        all paths will be shown.
        @param flag: The flag to enable or disable Selection
        """
        self.allwaysshow=flag
        if flag is True:
            self.show()
        elif flag is True and self.isSelected():
            self.show()
        else:
            self.hide()
        self.update(self.boundingRect())
            
               
    def paint(self, painter, option, widget=None):
        demat=painter.deviceTransform()
        self.sc=demat.m11()
        
        dx = math.cos(math.radians(self.angle)) * self.length/self.sc
        dy = math.sin(math.radians(self.angle)) * self.length/self.sc
        
        self.endp=QtCore.QPointF(self.startp.x()+dx,self.startp.y()-dy)
        
        
        arrowSize=self.arrowSize/self.sc
        #print(demat.m11())
       
    
        painter.setPen(self.pen)
        painter.setBrush(self.myColor)

        centerLine = QtCore.QLineF(self.startp, self.endp)
        

        
        self.setLine(QtCore.QLineF(self.endp,self.startp))
        line = self.line()

        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = (math.pi * 2.0) - angle

        if self.dir==0:
            arrowP1 = line.p1() + QtCore.QPointF(math.sin(angle + math.pi / 3.0) * arrowSize,
                                            math.cos(angle + math.pi / 3) * arrowSize)
            arrowP2 = line.p1() + QtCore.QPointF(math.sin(angle + math.pi - math.pi / 3.0) * arrowSize,
                                            math.cos(angle + math.pi - math.pi / 3.0) * arrowSize)
            self.arrowHead.clear()
            for point in [line.p1(), arrowP1, arrowP2]:
                self.arrowHead.append(point)
                
        else:
            arrowP1 = line.p2() - QtCore.QPointF(math.sin(angle + math.pi / 3.0) * arrowSize,
                                            math.cos(angle + math.pi / 3) * arrowSize)
            arrowP2 = line.p2() - QtCore.QPointF(math.sin(angle + math.pi - math.pi / 3.0) * arrowSize,
                                            math.cos(angle + math.pi - math.pi / 3.0) * arrowSize)
            self.arrowHead.clear()
            for point in [line.p2(), arrowP1, arrowP2]:
                self.arrowHead.append(point)

        

        painter.drawLine(line)
        painter.drawPolygon(self.arrowHead)


    def boundingRect(self):
        """
        Override inherited function to enlarge selection of Arrow to include all
        @param flag: The flag to enable or disable Selection
        """
        
        #print("super: %s" %super(Arrow, self).boundingRect())
        arrowSize=self.arrowSize/self.sc
        extra = (self.pen.width() + arrowSize) / 2.0
      
        return QtCore.QRectF(self.startp,
                              QtCore.QSizeF(self.endp.x()-self.startp.x(),
                                             self.endp.y()-self.startp.y())).normalized().adjusted(-extra, -extra, extra, extra)

class WpZero(QtGui.QGraphicsItem):
    def __init__(self, center,color=QtCore.Qt.gray):
        self.sc=1
        super(WpZero, self).__init__()

        self.center=center
        self.allwaysshow=False
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
        self.color=color
        self.pen=QtGui.QPen(self.color, 1, QtCore.Qt.SolidLine,
                QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.pen.setCosmetic(True)
        
        self.diameter = 20.0
 
    def setSelected(self,flag=True):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        pass
        
    def setallwaysshow(self,flag=False):
        """
        If the directions shall be allwaysshown the paramerter will be set and 
        all paths will be shown.
        @param flag: The flag to enable or disable Selection
        """
        self.allwaysshow=flag
        if flag is True:
            self.show()
        else:
            self.hide()
        self.update(self.boundingRect())
               
    def paint(self, painter, option, widget=None):
        demat=painter.deviceTransform()
        self.sc=demat.m11()
        
        diameter1=self.diameter/self.sc
        diameter2=(self.diameter-4)/self.sc
       
        rectangle1=QtCore.QRectF(-diameter1/2, -diameter1/2, diameter1, diameter1)
        rectangle2=QtCore.QRectF(-diameter2/2, -diameter2/2, diameter2, diameter2)
        startAngle1 = 90 * 16
        spanAngle = 90 * 16
        startAngle2 = 270 * 16
    
        painter.drawEllipse(rectangle1)
        painter.drawEllipse(rectangle2)
        painter.drawPie(rectangle2, startAngle1, spanAngle)

        painter.setBrush(self.color)
        painter.drawPie(rectangle2, startAngle2, spanAngle)
        
    def boundingRect(self):
        """
        Override inherited function to enlarge selection of Arrow to include all
        @param flag: The flag to enable or disable Selection
        """
        diameter=self.diameter/self.sc
        return QtCore.QRectF(-20, -20.0, 40.0, 40.0)

 