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
logger = logging.getLogger("Gui.Dialog") 

class myDialog(QtGui.QDialog):
    """
    class myDialog
    """
    
    def __init__(self, title="Test", label=('Value1'), value=(1.0), haveAuto=False):
        super(myDialog, self).__init__()
        
        logger.debug(title)
        logger.debug(label)
        logger.debug(value)
        
        self.title = title
        self.label = label
        self.value = value
        
        self.result = None
        
        if not(len(label) == len(value)):
            raise Exception, "Number of labels different to number of values"
        
        self.initUI(haveAuto)
    
    def initUI(self, haveAuto):
        """
        initUI()
        """
        
        vbox = QtGui.QVBoxLayout(self)
        
        top = QtGui.QFrame(self)
        top.setFrameShape(QtGui.QFrame.StyledPanel)
        
        bottom = QtGui.QFrame(self)
        bottom.setFrameShape(QtGui.QFrame.StyledPanel)
        
        grid1 = QtGui.QGridLayout()
        grid1.setSpacing(10)
        self.lineLabel = []
        self.lineEdit = []
        
        for i in range(len(self.label)):
            self.lineLabel.append(QtGui.QLabel(self.label[i]))
            self.lineEdit.append(QtGui.QLineEdit('%s' %self.value[i]))
            
            grid1.addWidget(self.lineLabel[i], i, 0)
            grid1.addWidget(self.lineEdit[i], i, 1)
        
        top.setLayout(grid1) 
        
        grid2 = QtGui.QGridLayout()
        grid2.setSpacing(5)
        
        autoButton = QtGui.QPushButton("Auto")        
        okButton = QtGui.QPushButton("OK")
        cancelButton = QtGui.QPushButton("Cancel")
        
        autoButton.clicked.connect(self.cbAuto)
        okButton.clicked.connect(self.cbOK)
        cancelButton.clicked.connect(self.cbCancel)
        
        if haveAuto:
            grid2.addWidget(autoButton, 0, 0)
        grid2.addWidget(okButton, 0, 1)
        grid2.addWidget(cancelButton, 0, 2) # 5, 1
        
        bottom.setLayout(grid2) 
        
        vbox.addWidget(top)
        vbox.addWidget(bottom)
        
        self.setLayout(vbox)
        
        self.resize(50, 50)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(self.title)
        iconWT = QtGui.QIcon()
        iconWT.addPixmap(QtGui.QPixmap(":images/DXF2GCODE-001.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(QtGui.QIcon(iconWT))
        
        self.exec_()
        
    def cbAuto(self):
        """
        Determine WP zero automatically by finding the left/bottom-most shape
        """
        self.result = 'Auto'
        self.close()
        
    def cbOK(self):
        """
        cbOK()
        """

        self.result = []
        for lineEdit in self.lineEdit:
            self.result.append(lineEdit.text())
        self.close()
        
    def cbCancel(self):
        """
        cbCancel()
        """
        logger.debug('Cancel')
        self.close()
        
