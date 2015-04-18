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

from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction

from gui.canvas import GLWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Hello GL")
        self.glWidget = GLWidget()
        self.setCentralWidget(self.glWidget)

        self.menu = self.menuBar()
        self.menu.file = self.menu.addMenu('&File')
        self.menu.file.close = QAction("&Close", self, shortcut="Ctrl+Q", triggered=self.close)
        self.menu.file.addAction(self.menu.file.close)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    fmt = QSurfaceFormat()
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
