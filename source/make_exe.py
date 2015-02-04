#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import subprocess

pyinpfad = "C:\Python27\Scripts\pyinstaller-script.py"

pyt = "C:/Python27/pythonw.exe"
filepfad = os.path.realpath(os.path.dirname(sys.argv[0]))
exemakepfad = filepfad
file_ = "dxf2gcode"
icon = "%s/dxf2gcode_pyQt4_ui/images/DXF2GCODE-001.ico" % filepfad
#upxdir = "C:/Python27/pyinstaller-2.0/upx309w"

#options = ("--noconsole --upx-dir=%s --icon=%s" % (upxdir, icon))
#upx is not advised, since it will cause some locations errors
options = ("--noconsole --icon=%s" % (icon)) #comment to use upx
print options

cmd = ("%s %s %s %s\%s.py" % (pyt, pyinpfad, options, filepfad, file_))
print cmd
retcode = subprocess.call(cmd)

print "\n!!!!!!!Do not forget the Bitmaps and Language folder!!!!!!"
print "\nREADY"
