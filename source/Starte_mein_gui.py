# -*- coding: utf-8 -*-

"""
The main
@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose:  program arguments & options handling, read the config file
@author: Christian Kohlöffel 
@since:  21.12.2010
@license: GPL
"""
#Test


# Import Qt modules

import os
import sys
import logging

from logger import Log
from optparse import OptionParser
from PyQt4 import QtCore, QtGui


# Import the compiled UI module
from dxf2gcode_pyQt4_ui.dxf2gcode_pyQt4_ui import Ui_MainWindow

import globals as g
import constants as c

from config import MyConfig
from dxf_import import ReadDXF

from myCanvasClass import *

# Get folder of the main instance and write into globals
g.folder = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
if os.path.islink(sys.argv[0]):
    g.folder = os.path.dirname(os.readlink(sys.argv[0]))


# Create a class for our main window
class Main(QtGui.QMainWindow):
    def __init__(self):
        logger=g.logger.logger

        QtGui.QMainWindow.__init__(self)
    
        # This is always the same
        self.ui = Ui_MainWindow()
        
        self.ui.setupUi(self)
        
        self.createActions()

        self.MyGraphicsView=self.ui.MyGraphicsView
        
        self.myMessageBox=myMessageBox(self.ui.myMessageBox)
 
      
        
    def createActions(self):
        """
        Create the actions of the main toolbar.
        @purpose: Links the callbacks to the actions in the menu
        """
        
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionLoad_File.triggered.connect(self.showDialog)
        self.ui.actionAbout.triggered.connect(self.about)
        self.ui.actionAutoscale.triggered.connect(self.autoscale)
        self.ui.actionShow_path_directions.triggered.connect(self.show_path_directions)
        self.ui.actionShow_WP_Zero.triggered.connect(self.show_wp_zero)
        
    def enableplotmenu(self,status=True):
        """
        Enable the Toolbar buttons.
        @param status: Set True to enable False to disable
        """
        
        self.ui.actionShow_path_directions.setEnabled(status)
        self.ui.actionShow_hiden_paths.setEnabled(status)
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
        
        config=g.config

        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                    g.config.vars.Paths['import_dir'],
                    "All supported files (*.dxf *.ps *.pdf);;" \
                    "DXF files (*.dxf);;"\
                    "PS files (*.ps);;"\
                    "PDF files (*.pdf);;"\
                    "all files (*.*)")
        
        logger=g.logger.logger
        logger.info("File: %s selected" %filename)
        
        #If there is something to load then call the load function callback
        if not(filename==""):
            values=self.loadFile(filename)
            
    def autoscale(self):
        """
        This function is called by the menu "Autoscal" of the main forwards the
        call to MyGraphicsview.autoscale() 
        """
        self.MyGraphicsView.autoscale()

    def autoscale(self):
        """
        This function is called by the menu "Autoscal" of the main forwards the
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
     
    def show_path_directions(self):
        """
        This function is called by the menu "Show all path directions" of the
        main and forwards the call to MyGraphicsview.show_path_directions() 
        """
        flag=self.ui.actionShow_path_directions.isChecked()
        self.MyGraphicsView.show_path_direction(flag)
        
    def show_wp_zero(self):
        """
        This function is called by the menu "Show WP Zero" of the
        main and forwards the call to MyGraphicsview.show_wp_zero() 
        """
        flag=self.ui.actionShow_WP_Zero.isChecked()
        self.MyGraphicsView.show_wp_zero(flag)
        
        
    def loadFile(self,filename):
        """
        Loads the defined file of filename also calls the command to 
        make the plot.
        @param filename: The string of the filename which should be loaded
        """

        #Setting up logger
        logger=g.logger.logger

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
                                    p0=PointClass(x=0.0, y=0.0),
                                    pb=PointClass(x=0, y=0),
                                    sca=[1.0,1.0,1.0],
                                    rot=0.0)
        
        
        self.MyGraphicsView.setScene(self.MyGraphicsScene)
        self.MyGraphicsView.show()
        self.MyGraphicsView.setFocus()
        
        #Autoscale des Canvas      
        self.MyGraphicsView.autoscale()

#        #Loeschen alter Route Menues
#        self.del_route_and_menuentry()
     
class myMessageBox(object):
    """
    The myMessageBox Class performs the write functions in the Message Window.
    The pervious defined MyMessageBox_org class is used as output (Within ui). 
    @sideeffect: None                            
    """
        
    def __init__(self, origobj):
        """
        Initialization of the myMessageBox class.
        @param origobj: This is the reference to to parent class initialized 
        previously.
        """
        self.myMessageBox_org=origobj
#        
#                #add a link with data
#        href = "http://christian-kohloeffel.homepage.t-online.de/index.html"
#        text.insert(END, _("You are using DXF2GCODE"))
#        text.insert(END, ("\nVersion %s (%s)" %(VERSION,DATE)))
#        text.insert(END, _("\nFor more information und updates about"))
#        text.insert(END, _("\nplease visit my homepage at:"))
#        text.insert(END, _("\nwww.christian-kohloeffel.homepage.t-online.de"), ("a", "href:"+href))
        #print((self.myMessageBox_org.verticalScrollBar().sliderPosition()))
        
    def write(self,charstr):
        """
        The function is called by the window logger to write the log message to
        the Messagebox
        @param charstr: The log message which will be written.
        """
#        self.prt(charstr)

#    def prt(self, charstr):
#        """
#        If you want to write something to the window use this function
#        @param charstr: The message which will be written.
#        """
        self.myMessageBox_org.append(charstr[0:-1])
        self.scrollbar=self.myMessageBox_org.verticalScrollBar().setValue(1e9)
        #print((self.myMessageBox_org.verticalScrollBar().sliderPosition()))
        


def setup_logging(myMessageBox):
    """
    Function to set up the logging to the myMessageBox Class. 
    This function can only be called if the myMessageBox Class has been created.
    @param myMessageBox: This is the handle to the GUI where the log message 
    shall be sent to. This Class needs a function "def write(self,charstr):"
    """
    # LogText window exists, setup logging
    g.logger.add_window_logger(log_level=logging.INFO)
    g.logger.set_window_logstream(myMessageBox)
    
 
def main():
    """
    The main function which is executed after program start. 
    """
    # Again, this is boilerplate, it's going to be the same on
    # almost every app you write
    g.logger = Log(c.APPNAME,console_loglevel=logging.DEBUG)

    app = QtGui.QApplication(sys.argv)
    window = Main()
    g.window=window
    
    window.show()
    
    setup_logging(window.myMessageBox)
    
    logger=g.logger.logger
    g.config=MyConfig()
    
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-f", "--file", dest="filename",
                      help="read data from FILENAME")
#    parser.add_option("-v", "--verbose",
#                      action="store_true", dest="verbose")
#    parser.add_option("-q", "--quiet",
#                      action="store_false", dest="verbose")

    
    (options, args) = parser.parse_args()
    g.logger.logger.debug("Started with following options \n%s" % (options))
    
    if not(options.filename is None):
        window.loadFile(options.filename)
     
    # It's exec_ because exec is a reserved word in Python
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

