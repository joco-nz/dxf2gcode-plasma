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

from PyQt4 import QtGui, QtCore
import logging
logger = logging.getLogger("Gui.AboutDialog") 

class myAboutDialog(QtGui.QDialog):
    """
    class myAboutDialog
    """
    
    def __init__(self, title="Test", message="Test Text"):
        super(myAboutDialog, self).__init__()

        self.title = title
        self.message = message
        
        self.initUI()
        
    def initUI(self):
        """
        initUI()
        """
        
        vbox = QtGui.QVBoxLayout(self)
        grid1 = QtGui.QGridLayout()
        grid1.setSpacing(10)
        
        self.text = QtGui.QTextBrowser()
        self.text.setReadOnly(True)
        self.text.setOpenExternalLinks(True)
        self.text.append(self.message)
        self.text.moveCursor(QtGui.QTextCursor.Start)
        self.text.ensureCursorVisible()
        
        vbox.addWidget(self.text)
        
        self.setLayout(vbox)
        self.setMinimumSize(550, 450)
        self.resize(550, 600)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(self.title)
        iconWT = QtGui.QIcon()
        iconWT.addPixmap(QtGui.QPixmap(":images/DXF2GCODE-001.ico"),
                         QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(QtGui.QIcon(iconWT))
        
        self.exec_()
        
