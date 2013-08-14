from PyQt4 import QtGui, QtCore
import logging
logger=logging.getLogger("Gui.AboutDialog") 

class myAboutDialog(QtGui.QDialog):
    
    def __init__(self,title="Test",message="Test Text"):
        super(myAboutDialog, self).__init__()

        self.title=title
        self.message=message
        
        self.initUI()
        
    def initUI(self):      

        vbox = QtGui.QVBoxLayout(self)
        grid1 = QtGui.QGridLayout()
        grid1.setSpacing(10)

        self.text=QtGui.QTextBrowser()
        self.text.setReadOnly(True)
        self.text.setOpenExternalLinks(True)
        self.text.append(self.message)
        self.text.moveCursor(QtGui.QTextCursor.Start)
        self.text.ensureCursorVisible()
        
        vbox.addWidget(self.text)
       
        self.setLayout(vbox)
        self.setMinimumSize(550, 450)
        self.resize(550, 600)
        self.setWindowTitle(self.title)
        iconWT = QtGui.QIcon()
        iconWT.addPixmap(QtGui.QPixmap("DXF2GCODE-001.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(QtGui.QIcon(iconWT))
        
        self.exec_()
    
