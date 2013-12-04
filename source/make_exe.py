#!/usr/bin/python

import os, sys
import subprocess

pyinpfad = "C:/Python27/pyinstaller-2.0/pyinstaller.py"

pyt = "C:/Python27/pythonw.exe"
filepfad = os.path.realpath(os.path.dirname(sys.argv[0]))
exemakepfad = filepfad
file_ = "dxf2gcode"
icon = "%s/dxf2gcode_pyQt4_ui/images/DXF2GCODE-001.ico" % filepfad
upxdir = "C:/Python27/pyinstaller-2.0/upx309w"

#options = ("--noconsole --upx-dir=%s --icon=%s" % (upxdir, icon))
#uncomment line above to use upx
options = ("--noconsole --icon=%s" % (icon)) #comment to use upx
print options

#Verzwichniss wechseln
#Change Directory
exemakepfad = unicode( exemakepfad, "utf-8" )
os.chdir(exemakepfad.encode( "utf-8" ))


cmd = ("%s %s %s %s/%s.py\n" % (pyt, pyinpfad, options, filepfad, file_))
print cmd
retcode = subprocess.call(cmd)

#cmd = ("%s %s/Build.py %s/%s.spec\n" % (pyt, pyinpfad, exemakepfad, file_))
#print cmd
#retcode = subprocess.call(cmd)

print "\n!!!!!!!Do not forget the Bitmaps and Language folder!!!!!!"
print "\nREADY"
