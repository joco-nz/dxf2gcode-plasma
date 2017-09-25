############################################################################
#
#   Copyright (C) 2017
#    Damian Wrobel <dwrobel@ertelnet.rybnik.pl>
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

from setuptools import setup
import glob

import distutils.command.install_scripts
import shutil

class install_scripts(distutils.command.install_scripts.install_scripts):
    def run(self):
        distutils.command.install_scripts.install_scripts.run(self)
        for script in self.get_outputs():
            if script.endswith(".py"):
                shutil.move(script, script[:-3])

setup(
    name='dxf2gcode',

    version='20170925',

    description='2D drawings to CNC machine compatible G-Code converter.',

    long_description=('DXF2GCODE is a tool for converting 2D (dxf, pdf, ps)'
                      ' drawings to CNC machine compatible GCode.'),

    url='https://sourceforge.net/p/dxf2gcode/wiki/Home/',

    author='Christian Kohloffel',

    author_email='christian-kohloeffel@t-online.de',

    license='GPLv3',

    packages=[
        'core',
        'dxfimport',
        'globals',
        'globals.configobj',
        'gui',
        'postpro'
    ],

    py_modules=[
        "dxf2gcode_images5_rc",
        "dxf2gcode_ui5"
    ],

    install_requires=[
        'PyQt5',
        'PyOpenGL'
    ],

    include_package_data=True,

    data_files=[
        ('share/appdata', ['dxf2gcode.appdata.xml']),
        ('share/applications', ['dxf2gcode.desktop']),
        ('share/dxf2gcode/i18n', glob.glob('i18n/*.qm')),
        ('share/icons/hicolor/scalable/apps/', ['images/dxf2gcode.svg'])
    ],

    cmdclass = {"install_scripts": install_scripts},

    scripts=['dxf2gcode.py']
)
