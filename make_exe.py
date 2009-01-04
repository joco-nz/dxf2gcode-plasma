#!/usr/bin/python

import os
import subprocess

pyinpfad = "C:\Python25\pyinstaller_1.3"
exemakepfad = "E:\dxf2gcode_exe"
pyt = "C:\Python25\pythonw.exe"
filepfad="E:/DXF2GCODE/trunk/source/"
file = "dxf2gcode_wx28"

options="--noconsole --upx"

#Verzwichniss wechseln
exemakepfad = unicode( exemakepfad, "utf-8" )
os.chdir(exemakepfad.encode( "utf-8" ))


cmd=("%s %s\Makespec.py %s %s\%s.py" %(pyt,pyinpfad,options,filepfad,file))
#print cmd
retcode=subprocess.call(cmd)

cmd=("%s %s\Build.py %s\%s.spec" %(pyt,pyinpfad,exemakepfad,file))
#print cmd
retcode=subprocess.call(cmd)

print "\n!!!!!!!Bitmaps und Languagues Ordner nicht vergessen!!!!!!"
print "\nFertig"