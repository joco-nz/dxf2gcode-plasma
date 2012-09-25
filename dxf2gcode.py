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

from optparse import OptionParser
from PyQt4 import QtGui

# Import the compiled UI module
from dxf2gcode_pyQt4_ui.dxf2gcode_pyQt4_ui import Ui_MainWindow

from Core.Logger import LoggerClass
from Core.Config import MyConfig
from Core.Point import Point
import Core.Globals as g
import Core.constants as c

from PostPro.PostProcessor import MyPostProcessor

from DxfImport.Import import ReadDXF

from Gui.myCanvasClass import MyGraphicsScene

from PostPro.TspOptimisation import TSPoptimize


#from Gui.myCanvasClass import *

# Get folder of the main instance and write into globals
g.folder = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
if os.path.islink(sys.argv[0]):
    g.folder = os.path.dirname(os.readlink(sys.argv[0]))


# Create a class for our main window
class Main(QtGui.QMainWindow):
    def __init__(self,app):

        QtGui.QMainWindow.__init__(self)
    
        # This is always the same
        self.app =app
        
        self.ui = Ui_MainWindow()
        
        self.ui.setupUi(self)
        
        self.createActions()

        self.MyGraphicsView=self.ui.MyGraphicsView
        
        self.myMessageBox=self.ui.myMessageBox 
       
    def createActions(self):
        """
        Create the actions of the main toolbar.
        @purpose: Links the callbacks to the actions in the menu
        """
        
        
        self.ui.actionLoad_File.triggered.connect(self.showDialog)
        
        self.ui.actionExit.triggered.connect(self.close)
        
        self.ui.actionOptimize_Shape.triggered.connect(self.optimize_TSP)
        self.ui.actionExport_Shapes.triggered.connect(self.export_shapes)
       
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
        logger.debug('Optimize order of enabled shapes')

        #Errechnen der Iterationen
        iter =min(g.config.vars.Route_Optimisation['max_iterations'],
                  len(self.MyGraphicsScene.shapes)*50)
        
        #Anfangswerte fuer das Sortieren der Shapes
        self.shapes_to_write=[]
        shapes_st_en_points=[]
        
        #Alle Shapes die geschrieben werden zusammenfassen
        for shape in self.MyGraphicsScene.shapes:
            
            if not(shape.isDisabled()):
                self.shapes_to_write.append(shape)
                shapes_st_en_points.append(shape.get_st_en_points())
                
        #Hinzufuegen des Start- Endpunkte ausserhalb der Geometrie
        x_st=g.config.vars.Plane_Coordinates['axis1_start_end']
        y_st=g.config.vars.Plane_Coordinates['axis2_start_end']
        start=Point(x=x_st,y=y_st)
        ende=Point(x=x_st,y=y_st)
        shapes_st_en_points.append([start,ende])

        #Optimieren der Reihenfolge
        logger.info("")    
            
        TSP=TSPoptimize(shapes_st_en_points)
        logger.info("TSP start values initialised")
        
        self.MyGraphicsScene.iniexproute(shapes_st_en_points,
                                                  TSP.opt_route)
       
        for it_nr in range(iter):
            #Jeden 10ten Schrit rausdrucken
            if (it_nr%50)==0:
                logger.info("TSP Iteration nr: %i Start route length: %0.1f" 
                            %(it_nr,TSP.Fittness.best_fittness[-1]))
                  
                TSP.calc_next_iteration()
                self.MyGraphicsScene.updateexproute(shapes_st_en_points,
                                                  TSP.opt_route)
                self.app.processEvents()                   
            
        logger.debug("TSP done with result: %s" %TSP)
        self.ui.actionDelete_G0_paths.setEnabled(True)

    def deleteG0paths(self):
        """
        Delets the optimisation paths from the scene.
        """
        self.MyGraphicsScene.delete_opt_path()
        self.ui.actionDelete_G0_paths.setEnabled(False)
    
    def export_shapes(self):
        """
        This method is called to export the shapes with the selected postprocessor.
        """
        logger.debug('Export the enabled shapes')
        
        
        #Config & postpro in einen kurzen Namen speichern
        logger.debug(dir(g.config))

        if not(g.config.vars.General['write_to_stdout']):
           
                #Abfrage des Namens um das File zu speichern
                self.save_filename=self.showSaveDialog()
                
                
                 #Wenn Cancel gedrueckt wurde
                if not self.save_filename:
                    return
                
                (beg, ende)=os.path.split(self.save_filename)
                (fileBaseName, fileExtension)=os.path.splitext(ende) 
        
                pp_file_nr=postpro.output_format.index(fileExtension)
                
                postpro.get_all_vars(pp_file_nr)
        else:
                postpro.get_all_vars(0)
        
               
        #Funktion zum optimieren des Wegs aufrufen
        #self.opt_export_route()

#        #Initial Status fuer den Export
#        status=1
#
#        #Schreiben der Standardwert am Anfang        
#        postpro.write_gcode_be(postpro,self.load_filename)
#
#        #Maschine auf die Anfangshoehe bringen
#        postpro.rap_pos_z(config.axis3_retract.get())
#
#        #Bei 1 starten da 0 der Startpunkt ist
#        for nr in range(1,len(self.TSP.opt_route)):
#            shape=self.shapes_to_write[self.TSP.opt_route[nr]]
#            self.textbox.prt((_("\nWriting Shape: %s") %shape),1)
#                
#
#
#            #Drucken falls die Shape nicht disabled ist
#            if not(shape.nr in self.CanvasContent.Disabled):
#                #Falls sich die Fräserkorrektur verändert hat diese in File schreiben
#                stat =shape.Write_GCode(config,postpro)
#                status=status*stat
#
#        #Maschine auf den Endwert positinieren
#        postpro.rap_pos_xy(PointClass(x=config.axis1_st_en.get(),\
#                                              y=config.axis2_st_en.get()))
#
#        #Schreiben der Standardwert am Ende        
#        string=postpro.write_gcode_en(postpro)
#
#        if status==1:
#            self.textbox.prt(_("\nSuccessfully generated G-Code"))
#            self.master.update_idletasks()
#
#        else:
#            self.textbox.prt(_("\nError during G-Code Generation"))
#            self.master.update_idletasks()
#
#                    
#        #Drucken in den Stdout, speziell fuer EMC2 
#        if config.write_to_stdout:
#            print(string)
#            self.ende()     
#        else:
#            #Exportieren der Daten
#                try:
#                    #Das File oeffnen und schreiben    
#                    f = open(self.save_filename, "w")
#                    f.write(string)
#                    f.close()       
#                except IOError:
#                    showwarning(_("Save As"), _("Cannot save the file."))
#            

    def showSaveDialog(self):
        """
        This function is called by the menu "Export\Export Shapes" of the main toolbar
        it creates the selection dialog for the exporter
        @return: Returns the filename of the selected file.
        """
        
        MyFormats=""
        for i in range(len(g.postpro.output_format)):
            name="%s " %(g.postpro.output_text[i])
            format="(*%s);;" %(g.postpro.output_format[i])
            MyFormats=MyFormats+name+format
            
        logger.debug(MyFormats)

        (beg, ende)=os.path.split(self.load_filename)
        (fileBaseName, fileExtension)=os.path.splitext(ende)
        
        logger.debug(fileBaseName)
        logger.debug(g.config.vars.Paths['output_dir'])
        
        default_name=os.path.join(g.config.vars.Paths['output_dir'],fileBaseName)
        
        logger.debug(default_name)
        

        filename = QtGui.QFileDialog.getSaveFileName(self, 'Export to file',
                    default_name,
                    MyFormats)

        
        logger.info("File: %s selected" %filename)
        
        return filename
        
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

        self.load_filename=filename
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
        
        self.plotall(values)
        
        #After all is plotted enable the Menu entities
        self.enableplotmenu()
        self.ui.actionDelete_G0_paths.setEnabled(False)

    def plotall(self,values):
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

        #Ausdrucken der Werte     
        self.MyGraphicsView.clearScene()
        self.MyGraphicsScene=MyGraphicsScene()   
        self.MyGraphicsScene.makeplot(values,
                                    p0=Point(x=0.0, y=0.0),
                                    pb=Point(x=0, y=0),
                                    sca=[1.0,1.0,1.0],
                                    rot=0.0)
        
        self.MyGraphicsView.setScene(self.MyGraphicsScene)
        self.MyGraphicsView.show()
        self.MyGraphicsView.setFocus()
        
        #Autoscale des Canvas      
        self.MyGraphicsView.autoscale()
     
def setup_logging(Log,myMessageBox):
    """
    Function to set up the logging to the myMessageBox Class. 
    This function can only be called if the myMessageBox Class has been created.
    @param myMessageBox: This is the handle to the GUI where the log message 
    shall be sent to. This Class needs a function "def write(self,charstr):"
    """
    # LogText window exists, setup logging
    Log.add_window_logger(log_level=logging.INFO)
    Log.set_window_logstream(myMessageBox)
    
def main():
    """
    The main function which is executed after program start. 
    """
    # Again, this is boilerplate, it's going to be the same on
    # almost every app you write
    Log=LoggerClass(rootlogger=logger, console_loglevel=logging.DEBUG)

    app = QtGui.QApplication(sys.argv)
    window = Main(app)
    g.window=window
    
    window.show()
    
    setup_logging(Log, window.myMessageBox)
    
    g.config=MyConfig()
    g.postpro=MyPostProcessor()
    
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-f", "--file", dest="filename",
                      help="read data from FILENAME")
#    parser.add_option("-v", "--verbose",
#                      action="store_true", dest="verbose")
#    parser.add_option("-q", "--quiet",
#                      action="store_false", dest="verbose")

    (options, args) = parser.parse_args()
    logger.debug("Started with following options \n%s" % (options))
    
    if not(options.filename is None):
        window.loadFile(options.filename)
     
    # It's exec_ because exec is a reserved word in Python
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()




