# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2014-2015
#    Robert Lichtenberger
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

from __future__ import absolute_import
import logging
import copy

from PyQt4 import QtCore


logger = logging.getLogger("Core.BreakGeo")


class BreakGeo(QtCore.QObject):
    """
    BreakGeo interrupts another geometry item by changing the Z-Position.
    """
    def __init__(self, inter, height, xyfeed, zfeed):
        QtCore.QObject.__init__(self)

        self.type = "BreakGeo"
        self.inter = inter
        self.height = height
        self.xyfeed = xyfeed
        self.zfeed = zfeed

    def __deepcopy__(self, memo):
        return BreakGeo(copy.deepcopy(self.inter, memo),
                        copy.deepcopy(self.height, memo),
                        copy.deepcopy(self.xyfeed, memo),
                        copy.deepcopy(self.zfeed, memo))

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nBreakGeo" +\
               "\ninter:  %s" % self.inter +\
               "\nheight: %0.5f" % self.height

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtCore.QCoreApplication.translate('BreakGeo',
                                                         string_to_translate,
                                                         encoding=QtCore.QCoreApplication.UnicodeUTF8))

    def reverse(self):
        """
        Reverses the direction.
        """
        self.inter.reverse()

    def add2path(self, papath=None, parent=None, layerContent=None):
        """
        Plots the geometry of self into defined path for hit testing.
        @param papath: The hitpath to add the geometrie
        @param parent: The parent of the shape
        """
        self.inter.add2path(papath, parent)

    def Write_GCode(self, parent=None, PostPro=None):
        """
        Writes the GCODE for a Break.
        @param parent: This is the parent LayerContentClass
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        oldZ = PostPro.ze
        oldFeed = PostPro.feed
        return (
            PostPro.chg_feed_rate(self.zfeed) +
            PostPro.lin_pol_z(self.height) +
            PostPro.chg_feed_rate(self.xyfeed) +
            self.inter.Write_GCode(parent, PostPro) +
            PostPro.chg_feed_rate(self.zfeed) +
            PostPro.lin_pol_z(oldZ) +
            PostPro.chg_feed_rate(oldFeed)
        )
