#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generates the tr file based on the defined PyQt Project File
"""

import os
import subprocess
import sys
import getopt


def which(program):
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


#
# Linenumbers may be of a little help while doing translations,
# but are a big problem in a multiple-developer environment.
#
# A change to almost any source file will trigger a change in .ts
# files, this leads to many conflicts while merging branches and
# submitting patches.
#
# Thus, the default behavior is to remove <location> tags in all
# .ts files (and keep the Git repository clean of them), but if
# you're going to do translation work, run make_tr.py with the
# --keep-ln option, then translate everythin, and run make_tr.py
# without options again before you commit.
#
def remove_linenumbers(fpath):
    print("Removing <location> tags in", fpath)

    inf = open(fpath, "r")
    outf = open(fpath + "~", "w")
    for line in inf.readlines():
        if line.find ("<location ") < 0:
            outf.write(line)

    inf.close()
    outf.close()
    os.unlink(fpath)
    os.rename(fpath + "~", fpath)


if "linux" in sys.platform.lower() or "unix" in sys.platform.lower() or "darwin" in sys.platform.lower():
    # On Linux, the executable are normaly on the PATH
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
    # using lupdate instead of pylupdate will ruin translation files
    # since it doesn't know Python.
    names = ["pylupdate5"] #, "lupdate-qt5", "lupdate5", "lupdate"
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
    LREPATH = os.path.join(PYTHONPATH, "Scripts/lrelease.exe")
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

try:
    (opts, left) = getopt.getopt(sys.argv[1:], "h", ["help", "no-pylupdate", "keep-ln"])
except getopt.GetoptError as e:
    print(e)
    sys.exit(1)

if left != list():
    print("unrecognized name on command line:", left [0])
    sys.exit(1)

OPTIONS = "-ts"
SKIP_PYLUPDATE = False
KEEP_LINENUMBERS = False

for opt,val in opts:
    if opt == "-h" or opt == "--help":
        print ("""\
Usage: %s [options]
    -U --no-pylupdate Don't update TS files by running 'pylupdate'
    -k --keep-ln      Keep line numbers in TS files, use this if
                      you're planning to use 'linguist'.
""" % sys.argv[0])
        sys.exit(1)
    elif opt == "--no-pylupdate":
        SKIP_PYLUPDATE = True
    elif opt == "--keep-ln":
        KEEP_LINENUMBERS = True

if SKIP_PYLUPDATE:
    print("skipping pylupdate")
else:
    cmd1 = ("%s %s %s %s\n" % (PYLPATH, FILESSTR, OPTIONS, TSFILESTR))
    print(cmd1)
    subprocess.check_call(cmd1, shell=True)

    if not KEEP_LINENUMBERS:
        for ts in TSFILES:
            fpath = "%s/i18n/%s" % (FILEPATH, ts)
            remove_linenumbers(fpath)

cmd2 = ("%s %s\n" % (LREPATH, TSFILESTR))
print(cmd2)
subprocess.check_call(cmd2, shell=True)

print("\nREADY")
