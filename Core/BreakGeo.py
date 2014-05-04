# -*- coding: utf-8 -*-

############################################################################
#   
#   Copyright (C) 2014-2014
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

from PyQt4 import QtCore, QtGui

import logging
logger = logging.getLogger("Core.BreakGeo") 

import copy

class BreakGeo(QtCore.QObject):
    """
    BreakGeo decorates another geometry item by changing the Z-Position.
    """ 
    def __init__(self, inner, height, xyfeed, zfeed):
        self.type = "BreakGeo"
        self.inner = inner
        self.height = height
        self.xyfeed = xyfeed
        self.zfeed = zfeed

    def __deepcopy__(self, memo):
        return BreakGeo(copy.deepcopy(self.inner, memo),
                       copy.deepcopy(self.height, memo),
                       copy.deepcopy(self.xyfeed, memo), 
                       copy.deepcopy(self.zfeed, memo))

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return "\nBreakGeo (height= %s), decorating %s" % (self.height, self.inner)        

    def reverse(self):
        """ 
        Reverses the direction.
        """ 
        self.inner.reverse()

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string    
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtGui.QApplication.translate("BreakGeo",
                                                    string_to_translate,
                                                    None,
                                                    QtGui.QApplication.UnicodeUTF8))
        
    def add2path(self, papath=None, parent=None, layerContent=None):
        """
        Plots the geometry of self into defined path for hit testing..
        @param hitpath: The hitpath to add the geometrie
        @param parent: The parent of the shape
        @param tolerance: The tolerance to be added to geometrie for hit
        testing.
        """
        self.inner.add2path(papath, parent)

    def Write_GCode(self, parent=None, PostPro=None):
        """
        To be called if a BreakGeo shall be written to the PostProcessor.
        @param pospro: The used Posprocessor instance
        @return: a string to be written into the file
        """        
        oldZ = PostPro.ze
        oldFeed = PostPro.feed
        return (
            PostPro.chg_feed_rate(self.zfeed) + 
            PostPro.lin_pol_z(self.height) + 
            PostPro.chg_feed_rate(self.xyfeed) + 
            self.inner.Write_GCode(parent, PostPro) + 
            PostPro.chg_feed_rate(self.zfeed) + 
            PostPro.lin_pol_z(oldZ) +
            PostPro.chg_feed_rate(oldFeed)  
        )
