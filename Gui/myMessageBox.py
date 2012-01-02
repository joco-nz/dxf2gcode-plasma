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
from PyQt4 import QtCore, QtGui

class myMessageBox(QtGui.QTextBrowser):
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
        super(myMessageBox, self).__init__() 
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
        self.append(charstr[0:-1])
        self.verticalScrollBar().setValue(1e9)
        #print((self.myMessageBox_org.verticalScrollBar().sliderPosition()))
        