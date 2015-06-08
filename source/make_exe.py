#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

PYTHONPATH = os.path.split(sys.executable)[0]
pyinpfad = os.path.join(PYTHONPATH, "Scripts\\pyinstaller-script.py")

pyt = os.path.join(PYTHONPATH, "pythonw.exe")
filepfad = os.path.realpath(os.path.dirname(sys.argv[0]))
exemakepfad = filepfad
file_ = "dxf2gcode"
icon = "%s\\dxf2gcode_pyQt4_ui\\images\\DXF2GCODE-001.ico" % filepfad

options = ("--noconsole --icon=%s" % (icon))
print options

cmd = ("%s %s %s %s\\%s.py" % (pyt, pyinpfad, options, filepfad, file_))
print cmd
retcode = subprocess.call(cmd)

print "\n!!!!!!!Do not forget the language folder!!!!!!"
print "\nREADY"
