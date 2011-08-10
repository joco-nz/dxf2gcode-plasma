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

import globals as g
import constants as c

class myCanvasClass:
    def __init__(self,myGraphicsView,parent):
        
        self.myGraphicsView=myGraphicsView
        self.myGraphicsScene=None
        self.parent=parent
        
        self.createContextMenu()

        self.Shapes=[]
        self.LayerContents=[]
        self.EntitiesRoot=EntitieContentClass()
        self.BaseEntities=EntitieContentClass()
        self.Selected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]
        

    def __str__(self):
        s='\nNr. of Shapes -> %s' %len(self.Shapes)
        for lay in self.LayerContents:
            s=s+'\n'+str(lay)
        for ent in self.EntitieContents:
            s=s+'\n'+str(ent)
        s=s+'\nSelected -> %s'%(self.Selected)\
           +'\nDisabled -> %s'%(self.Disabled)
        return s

    def calc_dir_var(self):
        if len(self.Selected)==0:
            return -1
        dir=self.Shapes[self.Selected[0]].cut_cor
        for shape_nr in self.Selected[1:len(self.Selected)]: 
            if not(dir==self.Shapes[shape_nr].cut_cor):
                return -1   
        return dir-40
                
    #Erstellen des Gesamten Ausdrucks      
    def makeplot(self,values,p0,pb,sca,rot):
        self.values=values

        #Loeschen des Inhalts
        self.clearScene()
        
        self.myGraphicsScene = myGraphicsScene(self.myGraphicsView)
        self.myGraphicsView.setScene(self.myGraphicsScene)
        self.myGraphicsView.show()
        
        #Standardwerte fuer scale, dx, dy zuweisen
        #self.Canvas.scale=1
        #self.Canvas.dx=0
        #self.Canvas.dy=-self.Canvas.canvas.winfo_height()

        #Zuruecksetzen der Konturen
        self.Shapes=[]
        self.LayerContents=[]
        self.EntitiesRoot=EntitieContentClass(Nr=0,Name='Entities',parent=None,children=[],
                                            p0=p0,pb=pb,sca=sca,rot=rot)
        self.Selected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]

        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        self.makeshapes(parent=self.EntitiesRoot)
        self.plot_shapes()
        self.LayerContents.sort()
        #self.EntitieContents.sort()

        #Autoscale des Canvas      
        self.autoscale()

   
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
                self.Shapes.append(ShapeClass(len(self.Shapes),\
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
                            self.Shapes[-1].geos.append(geo)

                        ent_geo.geo.reverse()
                    else:
                        for geo in ent_geo.geo:
                            self.Shapes[-1].geos.append(copy(geo))
                        
                self.addtoLayerContents(self.Shapes[-1],ent_geo.Layer_Nr)
                parent.addchild(self.Shapes[-1])

    def plot_shapes(self):
        for shape in self.Shapes:
            self.myGraphicsScene.addPath(shape.make_papath())
        
        #g.logger.logger.debug("Update GrapicsScene %s:" % (dir(self.myGraphicsScene)))
        
        #self.myGraphicsScene.update()
        
    #Verschieben des Werkst�cknullpunkts auf die momentane Cursor Position
    def set_wp_zero(self):
        #print("Hier gehts dann")
        #print ("X %0.2f Y %0.2f" %(self.Canvas.x, self.Canvas.y))
        self.Canvas.window.Move_WP_zero(x=self.Canvas.x, y=self.Canvas.y)
            
    #Drucken des Werkstuecknullpunkts
    def plot_wp_zero(self):
        for hdl in self.wp_zero_hdls:
            self.Canvas.canvas.delete(hdl) 
        self.wp_zero_hdls=[]
        if self.toggle_wp_zero.get(): 
            x_zero,y_zero=self.Canvas.get_can_coordinates(0,0)
            xy=x_zero-8,-y_zero-8,x_zero+8,-y_zero+8
            hdl=Oval(self.Canvas.canvas,xy,outline="gray")
            self.wp_zero_hdls.append(hdl)

            xy=x_zero-6,-y_zero-6,x_zero+6,-y_zero+6
            hdl=Arc(self.Canvas.canvas,xy,start=0,extent=180,style="pieslice",outline="gray")
            self.wp_zero_hdls.append(hdl)
            hdl=Arc(self.Canvas.canvas,xy,start=90,extent=180,style="pieslice",outline="gray")
            self.wp_zero_hdls.append(hdl)
            hdl=Arc(self.Canvas.canvas,xy,start=270,extent=90,style="pieslice",outline="gray",fill="gray")
            self.wp_zero_hdls.append(hdl)
    def plot_cut_info(self):
        for hdl in self.dir_hdls:
            self.Canvas.canvas.delete(hdl) 
        self.dir_hdls=[]

        if not(self.toggle_start_stop.get()):
            draw_list=self.Selected[:]
        else:
            draw_list=range(len(self.Shapes))
               
        for shape_nr in draw_list:
            if not(shape_nr in self.Disabled):
                self.dir_hdls+=self.Shapes[shape_nr].plot_cut_info(self.Canvas,self.config)


    def plot_opt_route(self,shapes_st_en_points,route):
        #Ausdrucken der optimierten Route
        for en_nr in range(len(route)):
            if en_nr==0:
                st_nr=-1
                col='gray'
            elif en_nr==1:
                st_nr=en_nr-1
                col='gray'
            else:
                st_nr=en_nr-1
                col='peru'
                
            st=shapes_st_en_points[route[st_nr]][1]
            en=shapes_st_en_points[route[en_nr]][0]

            x_ca_s,y_ca_s=self.Canvas.get_can_coordinates(st.x,st.y)
            x_ca_e,y_ca_e=self.Canvas.get_can_coordinates(en.x,en.y)

            self.path_hdls.append(Line(self.Canvas.canvas,x_ca_s,-y_ca_s,x_ca_e,-y_ca_e,fill=col,arrow='last'))
        self.Canvas.canvas.update()


    #Hinzufuegen der Kontur zum Layer        
    def addtoLayerContents(self,shape_nr,lay_nr):
        #Abfrage of der gesuchte Layer schon existiert
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.Shapes.append(shape_nr)
                return

        #Falls er nicht gefunden wurde neuen erstellen
        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(LayerContentClass(lay_nr,LayerName,[shape_nr]))
        
    #Hinzufuegen der Kontur zu den Entities
    def addtoEntitieContents(self,shape_nr,ent_nr,c_nr):
        
        for EntCon in self.EntitieContents:
            if EntCon.EntNr==ent_nr:
                if c_nr==0:
                    EntCon.Shapes.append([])
                
                EntCon.Shapes[-1].append(shape_nr)
                return

        #Falls er nicht gefunden wurde neuen erstellen
        if ent_nr==-1:
            EntName='Entities'
        else:
            EntName=self.values.blocks.Entities[ent_nr].Name
            
        self.EntitieContents.append(EntitieContentClass(ent_nr,EntName,[[shape_nr]]))

    def delete_opt_path(self):
        for hdl in self.path_hdls:
            self.Canvas.canvas.delete(hdl)
            
        self.path_hdls=[]
        
    def deselect(self): 
        self.set_shapes_color(self.Selected,'deselected')
        
        if not(self.toggle_start_stop.get()):
            for hdl in self.dir_hdls:
                self.Canvas.canvas.delete(hdl) 
            self.dir_hdls=[]
        
    def addselection(self,items,mode):
        for item in items:
            
            try:
                tag=int(self.Canvas.canvas.gettags(item)[-1])
                if not(tag in self.Selected):
                    self.Selected.append(tag)

                    self.textbox.prt(_('\n\nAdded shape to selection %s:')%(self.Shapes[tag]),3)
                    
                    if mode=='single':
                        break
            except:
                pass
            
        self.plot_cut_info()
        self.set_shapes_color(self.Selected,'selected')
 
    def invert_selection(self):
        new_sel=[]
        for shape_nr in range(len(self.Shapes)):
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
            self.Shapes[shape_nr].reverse()
            self.textbox.prt(_('\n\nSwitched Direction at Shape: %s')\
                             %(self.Shapes[shape_nr]),3)
        self.plot_cut_info()
        
    def set_cut_cor(self,correction):
        for shape_nr in self.Selected: 
            self.Shapes[shape_nr].cut_cor=correction
            
            self.textbox.prt(_('\n\nChanged Cutter Correction at Shape: %s')\
                             %(self.Shapes[shape_nr]),3)
        self.plot_cut_info() 
        
    def set_shapes_color(self,shape_nrs,state):
        s_shape_nrs=[]
        d_shape_nrs=[]
        for shape in shape_nrs:
            if not(shape in self.Disabled):
                s_shape_nrs.append(shape)
            else:
                d_shape_nrs.append(shape)
        
        s_hdls=self.get_shape_hdls(s_shape_nrs)
        d_hdls=self.get_shape_hdls(d_shape_nrs)
    
        if state=='deselected':
            s_color='black'
            d_color='gray'
            self.Selected=[]
        elif state=='selected':
            s_color='red'
            d_color='blue'
        elif state=='disabled':
            s_color='gray'
            d_color='gray'
            
        self.set_color(s_hdls,s_color)
        self.set_color(d_hdls,d_color)

        if (self.toggle_show_disabled.get()==0):
            self.set_hdls_hidden(d_shape_nrs)
        
    def set_color(self,hdls,color):
        for hdl in hdls:
            if (self.Canvas.canvas.type(hdl)=="oval") :
                self.Canvas.canvas.itemconfig(hdl, outline=color)
            else:
                self.Canvas.canvas.itemconfig(hdl, fill=color)

    def set_hdls_hidden(self,shape_nrs):
        hdls=self.get_shape_hdls(shape_nrs)
        for hdl in hdls:
            self.Canvas.canvas.itemconfig(hdl,state='hidden')

    def set_hdls_normal(self,shape_nrs):
        hdls=self.get_shape_hdls(shape_nrs)
        for hdl in hdls:
            self.Canvas.canvas.itemconfig(hdl,state='normal')            
        
    def get_shape_hdls(self,shape_nrs):        
        hdls=[]
        for s_nr in shape_nrs:
            if type(self.Shapes[s_nr].geos_hdls[0]) is list:
                for subcont in self.Shapes[s_nr].geos_hdls:
                    hdls=hdls+subcont
            else:
                hdls=hdls+self.Shapes[s_nr].geos_hdls
        return hdls   
    def autoscale(self):
        """
        Automatically zooms to the full extend of the current GraphicsScene
        """
        scext=self.myGraphicsScene.itemsBoundingRect()
        self.myGraphicsView.fitInView(scext,QtCore.Qt.KeepAspectRatio)
        g.logger.logger.debug("Autoscaling to extend: %s" % (scext))
        
    def clearScene(self):
        """
        Deletes the existing GraphicsScene.
        """
        del(self.myGraphicsScene) 
        

    def createContextMenu(self):
        """
        Create the actions of the main toolbar.
        @purpose: Links the callbacks to the actions in the menu
        """

        self.myGraphicsView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        quitAction = QtGui.QAction("Quit", self.parent)
        quitAction.triggered.connect(self.close)
        
        quitAction2 = QtGui.QAction("Quit", self.parent)
        quitAction2.triggered.connect(self.close)
        
        self.myGraphicsView.addAction(quitAction)
        self.myGraphicsView.addAction(quitAction2)
        
    def close(self):
        pass
                         
                         
class myGraphicsScene(QtGui.QGraphicsScene): 
    """
    This is the used Canvas to print the graphical interface of dxf2gcode.
    The Scene is rendered into the previously defined mygraphicsView class. 
    All performed plotting functions should be defined here.
    @sideeffect: None                            
    """       
    def __init__(self, myGraphicsView):
        QtGui.QGraphicsScene.__init__(self)
        self.myGraphicsView=myGraphicsView
        
        self.myGraphicsView.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        #self.myGraphicsView.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)


                
        
    def wheelEvent(self,event):


        scale=(1000+event.delta())/1000.0
        #screenpos=event.screenPos()
        
        #screenpos2=self.myGraphicsView.mapToScene(screenpos.x(),screenpos.y())
        #self.myGraphicsView.centerOn(screenpos2.x(),screenpos2.y())
        
        #self.myGraphicsView.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse) 
        #self.myGraphicsView.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter) 
        self.myGraphicsView.scale(scale,scale)
        
        #print screenpos
        #print screenpos2
        matrix=self.myGraphicsView.matrix()
        self.scale=matrix.m11()

        print ('m11: %s' %matrix.m11())



        
        

#    def mouse_move_motion(self,event):
#        self.moving(event)
#        dx=event.x-self.lastevent.x
#        dy=event.y-self.lastevent.y
#        self.dx=self.dx-dx/self.scale
#        self.dy=self.dy+dy/self.scale
#        self.canvas.move(ALL,dx,dy)
#        self.lastevent=event
#
#    def mouse_move_release(self,event):
#        self.master.config(cursor="")      
#
#    #Callback fuer das Zoomen des Bildes     
#    def mouse_zoom(self,event):
#        self.canvas.focus_set()
#        self.master.config(cursor="sizing")
#        self.firstevent=event
#        self.lastevent=event
#
#    def mouse_zoom_motion(self,event):
#        self.moving(event)
#        dy=self.lastevent.y-event.y
#        sca=(1+(dy*3)/float(self.canvas.winfo_height()))
#       
#        self.dx=(self.firstevent.x+((-self.dx*self.scale)-self.firstevent.x)*sca)/sca/-self.scale
#        eventy=self.canvas.winfo_height()-self.firstevent.y
#        self.dy=(eventy+((-self.dy*self.scale)-eventy)*sca)/sca/-self.scale
#        
#        self.scale=self.scale*sca
#        self.canvas.scale( ALL, self.firstevent.x,self.firstevent.y,sca,sca)
#        self.lastevent=event
#
#        self.Content.plot_cut_info() 
#        self.Content.plot_wp_zero()
#
#    def mouse_zoom_release(self,event):
#        self.master.config(cursor="")
        
            
class LayerContentClass:
    def __init__(self,LayerNr=None,LayerName='',Shapes=[]):
        self.LayerNr=LayerNr
        self.LayerName=LayerName
        self.Shapes=Shapes
        
    def __cmp__(self, other):
         return cmp(self.LayerNr, other.LayerNr)

    def __str__(self):
        return ('\ntype:        %s' %self.type) +\
               ('\nLayerNr :      %i' %self.LayerNr) +\
               ('\nLayerName:     %s' %self.LayerName)+\
               ('\nShapes:    %s' %self.Shapes)       
               
   
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
                      