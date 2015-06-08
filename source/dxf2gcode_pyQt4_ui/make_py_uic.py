#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Generates the python file based on the defined uifile
"""

import os
import sys
import subprocess

PYTHONPATH = os.path.split(sys.executable)[0]
UICPATH = os.path.join(PYTHONPATH, "Lib\\site-packages\\PyQt4")
FILEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

UIFILE = "dxf2gcode_pyQt4_ui.ui"
PYFILE = "dxf2gcode_pyQt4_ui.py"

RCFILE = "dxf2gcode_images.qrc"
RCPYFILE = "dxf2gcode_images_rc.py"

OPTIONS = ("-o")

CMD1 = ("%s\\pyuic4.bat %s %s %s" % (UICPATH, UIFILE, OPTIONS, PYFILE))
CMD2 = ("%s\\pyrcc4.exe %s %s %s" % (UICPATH, OPTIONS, RCPYFILE, RCFILE))

print(CMD1)
print(subprocess.call(CMD1))

print(CMD2)
print(subprocess.call(CMD2))

print("\nREADY")
