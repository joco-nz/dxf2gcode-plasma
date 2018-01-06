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

    PLYPATH = None
    names = ["pylupdate5", "lupdate5", "lupdate"]
    for name in names:
        if which(name):
            PLYPATH = name
            break

    if not PLYPATH:
        print("ERROR: Cannot file pylupdate5 tool.")
        print("Please consider to install lupdate tool - to use this script.")
        sys.exit(1)

    print("Using platform tools \"%s\" and \"%s\"\n" % (PLYPATH, LREPATH))
else:
    PYTHONPATH = os.path.split(sys.executable)[0]
    # To get pylupdate5.exe use: pip3.exe install PyQt5
    PLYPATH = os.path.join(PYTHONPATH, "scripts/pylupdate5.exe")
    # To get lrelease.exe use: pip3.exe install pyqt5-tools
    LREPATH = os.path.join(PYTHONPATH, "Lib/site-packages/pyqt5-tools/lrelease.exe")
    print("Using Windows platform tools \"%s\" and \"%s\"\n" % (PLYPATH, LREPATH))

FILEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

FILES = ("../core/arcgeo.py",
         "../core/project.py",
         "../core/shape.py",
         "../dxfimport/geoent_arc.py",
         "../dxfimport/geoent_circle.py",
         "../dxfimport/geoent_line.py",
         "../dxfimport/importer.py",
         "../globals/config.py",
         "../gui/canvas.py",
         "../gui/canvas2d.py",
         "../gui/canvas3d.py",
         "../gui/configwindow.py",
         "../gui/messagebox.py",
         "../gui/popupdialog.py",
         "../gui/treehandling.py",
         "../postpro/postprocessor.py",
         "../postpro/postprocessorconfig.py",
         "../postpro/tspoptimisation.py",
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

cmd1 = ("%s %s %s %s\n" % (PLYPATH, FILESSTR, OPTIONS, TSFILESTR))
print(cmd1)
print(subprocess.call(cmd1, shell=True))

cmd2 = ("%s %s\n" % (LREPATH, TSFILESTR))
print(cmd2)
print(subprocess.call(cmd2, shell=True))

print("\nREADY")

