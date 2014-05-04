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
logger = logging.getLogger("Core.HoleGeo") 

class HoleGeo(QtCore.QObject):
    """
    HoleGeo represents drilling holes.
    """ 
    def __init__(self, Pa):
        """
        Standard Method to initialise the HoleGeo
        """
        QtCore.QObject.__init__(self)
        self.type = "HoleGeo"
        self.Pa = Pa

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return "\nHoleGeo at (%s) " % (self.Pa)        

    def reverse(self):
        """ 
        Reverses the direction.
        """ 
        pass

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string    
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtGui.QApplication.translate("HoleGeo",
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
        abs_geo = self.make_abs_geo(parent, 0)
        radius = 2
        if layerContent is not None:
            radius = layerContent.getToolRadius()
        papath.addRoundedRect(abs_geo.Pa.x - radius, -abs_geo.Pa.y - radius, 2*radius, 2*radius, radius, radius)
        
    def make_abs_geo(self, parent=None, reverse=0):
        """
        Generates the absolute geometry based on the geometry self and the
        parent. If reverse 1 is given the geometry may be reversed.
        @param parent: The parent of the geometry (EntitieContentClass)
        @param reverse: If 1 the geometry direction will be switched.
        @return: A new LineGeoClass will be returned.
        """ 
        
        Pa = self.Pa.rot_sca_abs(parent=parent)
        abs_geo = HoleGeo(Pa)
        return abs_geo
        
    def get_start_end_points(self, direction, parent=None):
        """
        Returns the start/end Point and its direction
        @param direction: 0 to return start Point and 1 to return end Point
        @return: a list of Point and angle 
        """
        return self.Pa.rot_sca_abs(parent=parent), 0
        

    def Write_GCode(self, parent=None, PostPro=None):
        """
        To be called if a HoleGeo shall be written to the PostProcessor.
        @param PostPro: The used Posprocessor instance
        @return: a string to be written into the file
        """        
        return PostPro.make_print_str("(Drilled hole)%nl")
