#!/usr/bin/env python

############################################################################
#
#   Copyright (C) 2015
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


import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QFileDialog

from gui.canvas import GLWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("DXF2GCODE")
        self.glWidget = GLWidget()
        self.setCentralWidget(self.glWidget)

        self.menu = self.menuBar()
        self.menu.file = self.menu.addMenu('&File')
        self.menu.file.open = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.menu.file.close = QAction("&Close", self, shortcut="Ctrl+Q", triggered=self.close)
        self.menu.file.addAction(self.menu.file.open)
        self.menu.file.addSeparator()
        self.menu.file.addAction(self.menu.file.close)

        self.filename = ""

    def open(self):

        self.filename, _ = QFileDialog.getOpenFileName(self, 'Open File', '',
                                                       # "All supported files (*.dxf *.ps *.pdf);;"
                                                       "DXF files (*.dxf);;"
                                                       # "PS files (*.ps);;"
                                                       # "PDF files (*.pdf);;"
                                                       "All types (*.*)")

        if self.filename:
            print("File: %s selected" % self.filename)
            self.setWindowTitle("DXF2GCODE - [%s]" % self.filename)
            self.load(self.filename)

    def load(self, filename):
        """
        Loads the file given by filename.  Also calls the command to
        make the plot.
        @param filename: String containing filename which should be loaded
        """

        self.glWidget.setCursor(Qt.WaitCursor)

        print('Loading file: %s' % filename)

        values = ReadDXF(filename)

        #Output the information in the text window
        print('Loaded layers: %s' % len(values.layers))
        print('Loaded blocks: %s' % len(values.blocks.Entities))
        for i in range(len(values.blocks.Entities)):
            layers = values.blocks.Entities[i].get_used_layers()
            print('Block %i includes %i Geometries, reduced to %i Contours, used layers: %s'
                  % (i, len(values.blocks.Entities[i].geo), len(values.blocks.Entities[i].cont), layers))
        layers = values.entities.get_used_layers()
        insert_nr = values.entities.get_insert_nr()
        print('Loaded %i Entities geometries, reduced to %i Contours, used layers: %s, Number of inserts: %i'
              % (len(values.entities.geo), len(values.entities.cont), layers, insert_nr))

        #self.makeShapesAndPlot(values)

        self.glWidget.unsetCursor()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    fmt = QSurfaceFormat()
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
