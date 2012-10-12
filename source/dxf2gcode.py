# -*- coding: utf-8 -*-

"""
The main
@newfield purpose: Purpose

@purpose:  program arguments & options handling, read the config file
@author: Christian Kohlöffel 
@since:  21.12.2010
@license: GPL
"""



# Import Qt modules

import os
import sys
import logging
logger=logging.getLogger() 

from copy import copy

from optparse import OptionParser
from PyQt4 import QtGui

# Import the compiled UI module
from dxf2gcode_pyQt4_ui.dxf2gcode_pyQt4_ui import Ui_MainWindow

from Core.Logger import LoggerClass
from Core.Config import MyConfig
from Core.Point import Point
from Core.LayerContent import LayerContentClass
from Core.EntitieContent import EntitieContentClass
import Core.Globals as g
import Core.constants as c
from Core.Shape import ShapeClass

from PostPro.PostProcessor import MyPostProcessor

from DxfImport.Import import ReadDXF

from Gui.myCanvasClass import MyGraphicsScene
from Gui.TreeHandling import TreeHandler

from PostPro.TspOptimisation import TSPoptimize


#from Gui.myCanvasClass import *

# Get folder of the main instance and write into globals
g.folder = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
if os.path.islink(sys.argv[0]):
    g.folder = os.path.dirname(os.readlink(sys.argv[0]))

# Create a class for our main window
class Main(QtGui.QMainWindow):
    def __init__(self,app):
        """
        Initialization of the Main window. This is directly called after the 
        Logger has been initialized. The Function loads the GUI, creates the
        used Classes  and connects the actions to the GUI.
        """

        QtGui.QMainWindow.__init__(self)
    
        # This is always the same
        self.app =app
        
        self.ui = Ui_MainWindow()
        
        self.ui.setupUi(self)
        
        self.createActions()

        self.MyGraphicsView=self.ui.MyGraphicsView
        
        self.myMessageBox=self.ui.myMessageBox 
<<<<<<< .working
        
        self.MyPostProcessor=MyPostProcessor()
        
        self.shapes=[]
        self.LayerContents=[]
        self.EntitieContents=[]
        self.EntitiesRoot=[]
=======
        
        self.MyPostProcessor=MyPostProcessor()
        
        self.TreeHandler=TreeHandler(self.ui)

        self.shapes=[]
        self.LayerContents=[]
        self.EntitieContents=[]
        self.EntitiesRoot=[]
>>>>>>> .merge-right.r304
       
    def createActions(self):
        """
        Create the actions of the main toolbar.
        @purpose: Links the callbacks to the actions in the menu
        """
        
        self.ui.actionLoad_File.triggered.connect(self.showDialog)
        
        self.ui.actionExit.triggered.connect(self.close)
        
        self.ui.actionOptimize_Shape.triggered.connect(self.optimize_TSP)
        self.ui.actionExport_Shapes.triggered.connect(self.exportShapes)
       
        self.ui.actionAutoscale.triggered.connect(self.autoscale)
        self.ui.actionShow_path_directions.triggered.connect(self.setShow_path_directions)
        self.ui.actionShow_WP_Zero.triggered.connect(self.setShow_wp_zero)
        self.ui.actionShow_disabled_paths.triggered.connect(self.setShow_disabled_paths)
        self.ui.actionDelete_G0_paths.triggered.connect(self.deleteG0paths)
        
        self.ui.actionAbout.triggered.connect(self.about)
        
    def enableplotmenu(self,status=True):
        """
        Enable the Toolbar buttons.
        @param status: Set True to enable False to disable
        """
        
        self.ui.actionShow_path_directions.setEnabled(status)
        self.ui.actionShow_disabled_paths.setEnabled(status)
        self.ui.actionAutoscale.setEnabled(status)
        
        self.ui.actionScale_all.setEnabled(status)
        self.ui.actionRotate_all.setEnabled(status)
        self.ui.actionMove_WP_zero.setEnabled(status)
        self.ui.actionShow_WP_Zero.setEnabled(status)
        
    def showDialog(self):
        """
        This function is called by the menu "File\Load File" of the main toolbar
        it creates the file selection dialog and calls the loadFile function to
        load the selected file.
        """

        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                    g.config.vars.Paths['import_dir'],
                    "All supported files (*.dxf *.ps *.pdf);;" \
                    "DXF files (*.dxf);;"\
                    "PS files (*.ps);;"\
                    "PDF files (*.pdf);;"\
                    "all files (*.*)")
        
        logger.info("File: %s selected" %filename)
        
        #If there is something to load then call the load function callback
        if not(filename==""):
            self.loadFile(filename)
                
    def optimize_TSP(self):
        """
        Method is called to optimize the order of the shapes. This is performed
        by solving the TSP Problem.
        """
        logger.debug('Optimize order of enabled shapes per layer')
        self.MyGraphicsScene.resetexproutes()

        for  LayerContent in self.LayerContents:

            #Initial values for the Lists to export.
            self.shapes_to_write=[]
            shapes_st_en_points=[]
            
            #Check all shapes of Layer which shall be exported and create List
            #for it.
            for shape in LayerContent.shapes:
                
                if not(shape.isDisabled()):
                    self.shapes_to_write.append(shape)
                    shapes_st_en_points.append(shape.get_st_en_points())
            
            #Perform Export only if the Number of shapes to export is bigger 0     
            if len(self.shapes_to_write)>0:     
                        #Errechnen der Iterationen
                iter =min(g.config.vars.Route_Optimisation['max_iterations'],
                          len(self.shapes_to_write)*50)
                
                #Adding the Start and End Points to the List.
                x_st=g.config.vars.Plane_Coordinates['axis1_start_end']
                y_st=g.config.vars.Plane_Coordinates['axis2_start_end']
                start=Point(x=x_st,y=y_st)
                ende=Point(x=x_st,y=y_st)
                shapes_st_en_points.append([start,ende])
        
                #Optimieren der Reihenfolge
                logger.info("")    
                    
                TSPs=[]
                TSPs.append(TSPoptimize(shapes_st_en_points))
                logger.info("TSP start values initialised for Layer %s" %LayerContent.LayerName)
                
                self.MyGraphicsScene.addexproute(TSPs[-1].st_end_points,
                                                          TSPs[-1].opt_route,
                                                          LayerContent.LayerNr)
               
                for it_nr in range(iter):
                    #Only show each 50 step.
                    if (it_nr%100)==0:
                        logger.info("TSP Iteration nr: %i Start route length: %0.1f" 
                                    %(it_nr,TSPs[-1].Fittness.best_fittness[-1]))
                          
                        TSPs[-1].calc_next_iteration()
                        self.MyGraphicsScene.updateexproute(TSPs[-1].st_end_points,
                                                          TSPs[-1].opt_route)
                        self.app.processEvents()                   
                    
                logger.debug("TSP done with result: %s" %TSPs[-1])
                
    
                
                LayerContent.exp_order=TSPs[-1].opt_route[1:len(TSPs[-1].opt_route)]
                #logger.debug(TSPs[-1].opt_route[1:len(TSPs[-1].opt_route)])
            else:
                LayerContent.exp_order=[]
            
            self.ui.actionDelete_G0_paths.setEnabled(True)           

    def deleteG0paths(self):
        """
        Delets the optimisation paths from the scene.
        """
        self.MyGraphicsScene.delete_opt_path()
        self.ui.actionDelete_G0_paths.setEnabled(False)
    
    def exportShapes(self):
        """
        This function is called by the menu "Export\Export Shapes". It may open
        up a Save Dialog it it is used without EMC2 integration. Otherwise it's
        possible to select multiple postprocessor files, which are located
        in the folder.
        """
        logger.debug('Export the enabled shapes')
<<<<<<< .working
=======

        #Get the export order from the QTreeView
        self.TreeHandler.updateExportOrder()
        logger.debug("Sorted layers:")
        for i, layer in enumerate(self.LayerContents):
            logger.debug("LayerContents[%i] = %s" %(i, layer))

>>>>>>> .merge-right.r304

        if not(g.config.vars.General['write_to_stdout']):
           
                #Get the name of the File to export
                self.save_filename=self.showSaveDialog()
            
                #If Cancel was pressed
                if not self.save_filename:
                    return
    
                (beg, ende)=os.path.split(str(self.save_filename))
                (fileBaseName, fileExtension)=os.path.splitext(ende) 
        
                pp_file_nr=self.MyPostProcessor.output_format.index(fileExtension)
                
                self.MyPostProcessor.getPostProVars(pp_file_nr)
        else:
                self.MyPostProcessor.getPostProVars(0)
        
        """
        Export will be performed according to LayerContents and their order
        is given in this variable too.
        """
        
        self.MyPostProcessor.exportShapes(self.load_filename,
                                          self.save_filename,
                                          self.LayerContents)
      

    def showSaveDialog(self):
        """
        This function is called by the menu "Export\Export Shapes" of the main toolbar
        it creates the selection dialog for the exporter
        @return: Returns the filename of the selected file.
        """
        MyFormats=""
        for i in range(len(self.MyPostProcessor.output_format)):
            name="%s " %(self.MyPostProcessor.output_text[i])
            format="(*%s);;" %(self.MyPostProcessor.output_format[i])
            MyFormats=MyFormats+name+format
            
<<<<<<< .working
        (beg, ende)=os.path.split(self.load_filename)
=======
        (beg, ende)=os.path.split(str(self.load_filename))
>>>>>>> .merge-right.r304
        (fileBaseName, fileExtension)=os.path.splitext(ende)
        
        default_name=os.path.join(g.config.vars.Paths['output_dir'],fileBaseName)

        selected_filter = self.MyPostProcessor.output_format[0]
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Export to file',
                    default_name,
<<<<<<< .working
                    MyFormats)
=======
                    MyFormats, selected_filter)
>>>>>>> .merge-right.r304
        
        logger.info("File: %s selected" %filename+selected_filter)
        
        return filename+selected_filter
        
    def autoscale(self):
        """
        This function is called by the menu "Autoscale" of the main forwards the
        call to MyGraphicsview.autoscale() 
        """
        self.MyGraphicsView.autoscale()
            
    def about(self):
        """
        This function is called by the menu "Help\About" of the main toolbar and 
        creates the About Window
        """
        QtGui.QMessageBox.about(self, "About Diagram Scene",
                "The <b>Diagram Scene</b> example shows use" +\
                " of the graphics framework.")
     
    def setShow_path_directions(self):
        """
        This function is called by the menu "Show all path directions" of the
        main and forwards the call to MyGraphicsview.show_path_directions() 
        """
        flag=self.ui.actionShow_path_directions.isChecked()
        self.MyGraphicsView.setShow_path_direction(flag)
        
    def setShow_wp_zero(self):
        """
        This function is called by the menu "Show WP Zero" of the
        main and forwards the call to MyGraphicsview.set_Show_wp_zero() 
        """
        flag=self.ui.actionShow_WP_Zero.isChecked()
        self.MyGraphicsView.setShow_wp_zero(flag)
        
    def setShow_disabled_paths(self):
        """
        This function is called by the menu "Show disabled paths" of the
        main and forwards the call to MyGraphicsview.setShow_disabled_paths() 
        """
        flag=self.ui.actionShow_disabled_paths.isChecked()
        self.MyGraphicsView.setShow_disabled_paths(flag)
        
    def loadFile(self,filename):
        """
        Loads the defined file of filename also calls the command to 
        make the plot.
        @param filename: The string of the filename which should be loaded
        """

        self.load_filename=str(filename)
        (name, ext) = os.path.splitext(str(filename))

        if (ext.lower() == ".ps")or(ext.lower() == ".pdf"):
            logger.info(_("Sending Postscript/PDF to pstoedit"))
            
            #Create temporary file which will be read by the program
            filename = os.path.join(tempfile.gettempdir(), 'dxf2gcode_temp.dxf').encode("cp1252")
            pstoedit_cmd = self.config.pstoedit_cmd.encode("cp1252") #"C:\Program Files (x86)\pstoedit\pstoedit.exe"
            pstoedit_opt = eval(self.config.pstoedit_opt) #['-f','dxf','-mm']
            ps_filename = os.path.normcase(self.load_filename.encode("cp1252"))
            cmd = [(('%s') % pstoedit_cmd)] + pstoedit_opt + [(('%s') % ps_filename), (('%s') % filename)]
            retcode = subprocess.call(cmd)

        #self.textbox.text.delete(7.0, END)
        logger.info(('Loading file: %s') % filename)
        
        values = ReadDXF(filename)
        
        #Ausgabe der Informationen im Text Fenster
        logger.info(_('Loaded layers: %s') % len(values.layers))
        logger.info(_('Loaded blocks: %s') % len(values.blocks.Entities))
        for i in range(len(values.blocks.Entities)):
            layers = values.blocks.Entities[i].get_used_layers()
            logger.info(_('Block %i includes %i Geometries, reduced to %i Contours, used layers: %s ')\
                               % (i, len(values.blocks.Entities[i].geo), len(values.blocks.Entities[i].cont), layers))
        layers = values.entities.get_used_layers()
        insert_nr = values.entities.get_insert_nr()
        logger.info(_('Loaded %i Entities geometries, reduced to %i Contours, used layers: %s ,Number of inserts: %i') \
                             % (len(values.entities.geo), len(values.entities.cont), layers, insert_nr))
        
        self.makeShapesAndPlot(values)
        
        #After all is plotted enable the Menu entities
        self.enableplotmenu()
        self.ui.actionDelete_G0_paths.setEnabled(False)

    def makeShapesAndPlot(self,values):
        """
        Plots all data stored in the values paramter to the Canvas
        @param values: Includes all values loaded from the dxf file
        """
    
        #Skalierung der Kontur
        self.cont_scale = 1.0
        
        #Verschiebung der Kontur
        self.cont_dx = 0.0
        self.cont_dy = 0.0
        
        #Rotieren um den WP zero
        self.rotate = 0.0
<<<<<<< .working
      
        #Generate the Shapes  
        self.makeShapes(values,
                            p0=Point(x=0.0, y=0.0),
                            pb=Point(x=0.0, y=0.0),
                            sca=[1.0,1.0,1.0],
                            rot=0.0)
=======
      
        #Generate the Shapes  
        self.makeShapes(values,
                            p0=Point(x=0.0, y=0.0),
                            pb=Point(x=0.0, y=0.0),
                            sca=[1.0,1.0,1.0],
                            rot=0.0)

        print("\033[31;1mEntitieRoot = %s\033[m" %self.EntitiesRoot) #TODO : remove
        for i, forme in enumerate(self.EntitiesRoot.children): #TODO : remove
            print("\033[32mEntitieRoot.children[%i] = %s\033[m" %(i, forme)) #TODO : remove

#        print("\033[31;1mLayerContents = %s\033[m" %self.LayerContents) #TODO : remove
        print("\n") #TODO : remove
        for i, layer in enumerate(self.LayerContents): #TODO : remove
            print("\033[31;1mLayerContents[%i] = %s\033[m" %(i, layer)) #TODO : remove

            for j, forme in enumerate(self.LayerContents[i].shapes): #TODO : remove
                print("\033[32mLayerContents[%i].shape[%i] = %s\033[m" %(i, j, forme)) #TODO : remove


        #Populate the treeViews
        self.TreeHandler.buildEntitiesTree(self.EntitiesRoot)
        self.TreeHandler.buildLayerTree(self.LayerContents)
>>>>>>> .merge-right.r304

        #Ausdrucken der Werte     
        self.MyGraphicsView.clearScene()
        self.MyGraphicsScene=MyGraphicsScene()   
        
        self.MyGraphicsScene.plotAll(self.shapes, self.EntitiesRoot)
        self.MyGraphicsView.setScene(self.MyGraphicsScene)
        self.MyGraphicsView.show()
        self.MyGraphicsView.setFocus()
        
        #Autoscale des Canvas      
        self.MyGraphicsView.autoscale()
<<<<<<< .working
               
        """FIXME
        Export will be performed in the order of the Structure self.LayerContents
        You can sort the Layers and the Shapes of LayerContent itself in the correct
        order. With this sort function it is sorted in increasing number of Layer only"""
        self.LayerContents.sort()
        
        for LayerContent in self.LayerContents:
            LayerContent.exp_order=range(len(LayerContent.shapes))
   
        """FIXME
        Here are the two structures which give the things to show in the treeview"""
        logger.debug(self.LayerContents)
        logger.debug(self.EntitiesRoot)
        
               
    def makeShapes(self,values,p0,pb,sca,rot):
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
        del(self.LayerContents[:])
        del(self.EntitiesRoot)
        self.EntitiesRoot=EntitieContentClass(Nr=0,Name='Entities',parent=None,children=[],
                                            p0=p0,pb=pb,sca=sca,rot=rot)

        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        self.makeEntitiesShapes(parent=self.EntitiesRoot)
        self.LayerContents.sort()
        
    def makeEntitiesShapes(self,parent=None,ent_nr=-1):
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
                
                logger.debug(new_entities)
                
                #Erstellen des neuen Entitie Contents f�r das Insert
                NewEntitieContent=EntitieContentClass(Nr=0,Name=ent_geo.BlockName,
                                        parent=parent,children=[],
                                        p0=p0,
                                        pb=pb,
                                        sca=sca,
                                        rot=rot)

                parent.addchild(NewEntitieContent)
            
                self.makeEntitiesShapes(parent=NewEntitieContent,ent_nr=ent_nr)
                
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
                
                #All shapes have to be CCW direction.         
                self.shapes[-1].AnalyseAndOptimize()
                self.shapes[-1].FindNearestStPoint()
                
                self.addtoLayerContents(self.shapes[-1],ent_geo.Layer_Nr)
                parent.addchild(self.shapes[-1])
                
    def addtoLayerContents(self,shape,lay_nr):
        """
        Instance is called while the shapes are created. This gives the 
        structure which shape is laying on which layer. It also writes into the
        shape the reference to the LayerContent Class.
        
        @param shape: The shape to be appended of the shape 
        @param lay_nr: The Nr. of the layer
        """
        #Check if the layer is already existing and add shape if it is.
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.shapes.append(shape)
                shape.LayerContent=LayCon
                return

        #If the Layer is not existing create a new one.
        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(LayerContentClass(lay_nr,LayerName,[shape]))
        shape.LayerContent=self.LayerContents[-1]
        
if __name__ == "__main__":
=======


    def makeShapes(self,values,p0,pb,sca,rot):
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
        del(self.LayerContents[:])
        del(self.EntitiesRoot)
        self.EntitiesRoot=EntitieContentClass(Nr=0,Name='Entities',parent=None,children=[],
                                            p0=p0,pb=pb,sca=sca,rot=rot)

        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        self.makeEntitiesShapes(parent=self.EntitiesRoot)
        self.LayerContents.sort()
        
    def makeEntitiesShapes(self,parent=None,ent_nr=-1):
        """
        Instance is called prior to the plotting of the shapes. It creates
        all shape classes which are later plotted into the graphics.
        
        @param parent: The parent of a shape is always a Entities. It may be root 
        or if it is a Block this is the Block. 
        @param ent_nr: The values given in self.values are sorted in that way 
        that 0 is the Root Entities and  1 is beginning with the first block. 
        This value gives the index of self.values to be used.
        """
        print("\033[37;1mmakeEntitiesShapes() ; parent = %s\033[m" %parent.Name) #TODO : remove

        if parent.Name=="Entities":      
            entities=self.values.entities
        else:
            ent_nr=self.values.Get_Block_Nr(parent.Name)
            entities=self.values.blocks.Entities[ent_nr]
            
        #Zuweisen der Geometrien in die Variable geos & Konturen in cont
        #Assigning the geometries in the variables geos & contours in cont
        ent_geos=entities.geo
               
        #Schleife fuer die Anzahl der Konturen 
        #Loop for the number of contours
        for cont in entities.cont:
            print("\033[37;1mcont in entities.cont\033[m") #TODO : remove
            #Abfrage falls es sich bei der Kontur um ein Insert eines Blocks handelt
            #Query if it is in the contour of an insert of a block
            if ent_geos[cont.order[0][0]].Typ=="Insert":
                ent_geo=ent_geos[cont.order[0][0]]
                
                #Zuweisen des Basispunkts f�r den Block
                #Assign the base point for the block
                new_ent_nr=self.values.Get_Block_Nr(ent_geo.BlockName)
                new_entities=self.values.blocks.Entities[new_ent_nr]
                pb=new_entities.basep
                
                #Skalierung usw. des Blocks zuweisen
                #Scaling, etc. assign the block
                p0=ent_geos[cont.order[0][0]].Point
                sca=ent_geos[cont.order[0][0]].Scale
                rot=ent_geos[cont.order[0][0]].rot
                
                logger.debug(new_entities)
                
                #Erstellen des neuen Entitie Contents f�r das Insert
                #Creating the new Entitie Contents for the insert
                NewEntitieContent=EntitieContentClass(Nr=0,Name=ent_geo.BlockName,
                                        parent=parent,children=[],
                                        p0=p0,
                                        pb=pb,
                                        sca=sca,
                                        rot=rot)

                parent.addchild(NewEntitieContent)
            
                self.makeEntitiesShapes(parent=NewEntitieContent,ent_nr=ent_nr)
                
            else:
                #Schleife fuer die Anzahl der Geometrien
                #Loop for the number of geometries
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
                
                #All shapes have to be CCW direction.         
                self.shapes[-1].AnalyseAndOptimize()
                self.shapes[-1].FindNearestStPoint()
                
                #Connect the shapeSelectionChanged and enableDisableShape signals to our treeView, so that selections of the shapes are reflected on the treeView
                self.shapes[-1].setSelectionChangedCallback(self.TreeHandler.updateShapeSelection)
                self.shapes[-1].setEnableDisableCallback(self.TreeHandler.updateShapeEnabling)
                
                self.addtoLayerContents(self.shapes[-1],ent_geo.Layer_Nr)
                parent.addchild(self.shapes[-1])
                
    def addtoLayerContents(self,shape,lay_nr):
        """
        Instance is called while the shapes are created. This gives the 
        structure which shape is laying on which layer. It also writes into the
        shape the reference to the LayerContent Class.
        
        @param shape: The shape to be appended of the shape 
        @param lay_nr: The Nr. of the layer
        """
        #Check if the layer is already existing and add shape if it is.
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.shapes.append(shape)
                shape.LayerContent=LayCon
                return

        #If the Layer is not existing create a new one.
        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(LayerContentClass(lay_nr,LayerName,[shape]))
        shape.LayerContent=self.LayerContents[-1]
        
if __name__ == "__main__":
>>>>>>> .merge-right.r304
    """
    The main function which is executed after program start. 
    """
    Log=LoggerClass(rootlogger=logger, console_loglevel=logging.DEBUG)

    app = QtGui.QApplication(sys.argv)
    window = Main(app)
    g.window=window
    
    window.show()
    
    # LogText window exists, setup logging
    Log.add_window_logger(log_level=logging.INFO)
    #This is the handle to the GUI where the log message 
    #shall be sent to. This Class needs a function "def write(self,charstr)
    Log.set_window_logstream(window.myMessageBox)
    
    g.config=MyConfig()

    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-f", "--file", dest="filename",
                      help="read data from FILENAME")
    
#    parser.add_option("-v", "--verbose",
#                      action="store_true", dest="verbose")
#    parser.add_option("-q", "--quiet",
#                      action="store_false", dest="verbose")

    (options, args) = parser.parse_args()
    logger.debug("Started with following options \n%s" %(options))
    
    if not(options.filename is None):
        window.loadFile(options.filename)
     
    # It's exec_ because exec is a reserved word in Python
    sys.exit(app.exec_())



