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

from DxfImport.Import import ReadDXF

from Gui.myCanvasClass import MyGraphicsScene


#from Gui.myCanvasClass import *

# Get folder of the main instance and write into globals
g.folder = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
if os.path.islink(sys.argv[0]):
    g.folder = os.path.dirname(os.readlink(sys.argv[0]))


# Create a class for our main window
class Main(QtGui.QMainWindow):
    def __init__(self):

        QtGui.QMainWindow.__init__(self)
    
        # This is always the same
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
        
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionLoad_File.triggered.connect(self.showDialog)
        self.ui.actionAbout.triggered.connect(self.about)
        self.ui.actionAutoscale.triggered.connect(self.autoscale)
        self.ui.actionShow_path_directions.triggered.connect(self.setShow_path_directions)
        self.ui.actionShow_WP_Zero.triggered.connect(self.setShow_wp_zero)
        self.ui.actionShow_disabled_paths.triggered.connect(self.setShow_disabled_paths)
        
    def enableplotmenu(self,status=True):
        """
        Enable the Toolbar buttons.
        @param status: Set True to enable False to disable
        """
        
        self.ui.actionShow_path_directions.setEnabled(status)
        self.ui.actionShow_disabled_paths.setEnabled(status)
        self.ui.actionAutoscale.setEnabled(status)
        #self.ui.actionDelete_G0_paths.setEnabled(status)
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

        #Setting up logger
        #logger=g.logger.logger

        #Check File Extension
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

#        #Loeschen alter Route Menues
#        self.del_route_and_menuentry()
     



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
    window = Main()
    g.window=window
    
    window.show()
    
    setup_logging(Log, window.myMessageBox)
    
    g.config=MyConfig()
    
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

