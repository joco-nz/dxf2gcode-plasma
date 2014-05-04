# -*- coding: utf-8 -*-

############################################################################
#   
#   Copyright (C) 2008-2014
#    Christian Kohlöffel
#    Vinzenz Schulz
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

from Core.Point import Point

import logging
logger = logging.getLogger("Core.EntitieContent")

class EntitieContentClass:
    def __init__(self, type="Entitie", Nr=None, Name='', parent=None,
                children=[], p0=Point(x=0.0, y=0.0), pb=Point(x=0.0, y=0.0),
                sca=[1, 1, 1], rot=0.0):
        
        self.type = type
        self.Nr = Nr
        self.Name = Name
        self.children = children
        self.p0 = p0
        self.pb = pb
        self.sca = sca
        self.rot = rot
        self.parent = parent
    
    def __cmp__(self, other):
        return cmp(self.EntNr, other.EntNr)
    
    def __str__(self):
        return ('\ntype:        %s' % self.type) +\
               ('\nNr :      %i' % self.Nr) +\
               ('\nName:     %s' % self.Name)+\
               ('\np0:          %s' % self.p0)+\
               ('\npb:          %s' % self.pb)+\
               ('\nsca:         %s' % self.sca)+\
               ('\nrot:         %s' % self.rot)+\
               ('\nchildren:    %s' % self.children)
    
    #Add the contour of the Entities
    def addchild(self, child):
        """
        addchild()
        """
        self.children.append(child)

