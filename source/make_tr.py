#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generates the tr file based on the defined PyQt Project File
"""

import os, sys
import subprocess

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


if "linux" in sys.platform.lower() or "unix" in sys.platform.lower() or "darwin" in sys.platform.lower():
    #On Linux, the executable are normaly on the PATH
    LREPATH = None
    names = ["lrelease-qt5", "lrelease5", "lrelease"]
    for name in names:
        if which(name):
            LREPATH = name
            break

    if not LREPATH:
        print("ERROR: Cannot file lrelease tool.")
        print("Please consider to install lrelease tool - to use this script.")
        sys.exit(1)

    PYLPATH = None
    names = ["pylupdate5", "lupdate5", "lupdate"]
    for name in names:
        if which(name):
            PYLPATH = name
            break

    if not PYLPATH:
        print("ERROR: Cannot file pylupdate5 tool.")
        print("Please consider to install lupdate tool - to use this script.")
        sys.exit(1)

    print("Using platform tools \"%s\" and \"%s\"\n" % (PYLPATH, LREPATH))
else:
    PYTHONPATH = os.path.split(sys.executable)[0]
    # To get pylupdate5.exe use: pip3.exe install PyQt5
    PYLPATH = os.path.join(PYTHONPATH, "Scripts/pylupdate5.exe")
    # To get lrelease.exe use: pip3.exe install pyqt5-tools
    LREPATH = os.path.join(PYTHONPATH, "Lib/site-packages/pyqt5-tools/lrelease.exe")
    print("Using Windows platform tools \"%s\" and \"%s\"\n" % (PYLPATH, LREPATH))

FILEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

FILES = ("../dxf2gcode/core/arcgeo.py",
         "../dxf2gcode/core/project.py",
         "../dxf2gcode/core/shape.py",
         "../dxf2gcode/dxfimport/geoent_arc.py",
         "../dxf2gcode/dxfimport/geoent_circle.py",
         "../dxf2gcode/dxfimport/geoent_line.py",
         "../dxf2gcode/dxfimport/importer.py",
         "../dxf2gcode/globals/config.py",
         "../dxf2gcode/gui/canvas.py",
         "../dxf2gcode/gui/canvas2d.py",
         "../dxf2gcode/gui/canvas3d.py",
         "../dxf2gcode/gui/configwindow.py",
         "../dxf2gcode/gui/messagebox.py",
         "../dxf2gcode/gui/popupdialog.py",
         "../dxf2gcode/gui/treehandling.py",
         "../dxf2gcode/postpro/postprocessor.py",
         "../dxf2gcode/postpro/postprocessorconfig.py",
         "../dxf2gcode/postpro/tspoptimisation.py",
         "../dxf2gcode.py",
         "../dxf2gcode.ui"
         )


TSFILES = ("dxf2gcode_de_DE.ts",
           "dxf2gcode_fr.ts",
           "dxf2gcode_ru.ts")

FILESSTR = ""
for FILE in FILES:
    FILESSTR += ("%s/i18n/%s " % (FILEPATH, FILE))

TSFILESTR = ""
for TSFILE in TSFILES:
    TSFILESTR += ("%s/i18n/%s " % (FILEPATH, TSFILE))

OPTIONS = "-ts"

if len(sys.argv) >= 2 and sys.argv[1] == '--no-pylupdate':
    print("skipping pylupdate")
else:
    cmd1 = ("%s %s %s %s\n" % (PYLPATH, FILESSTR, OPTIONS, TSFILESTR))
    print(cmd1)
    subprocess.check_call(cmd1, shell=True)

cmd2 = ("%s %s\n" % (LREPATH, TSFILESTR))
print(cmd2)
subprocess.check_call(cmd2, shell=True)

print("\nREADY")

