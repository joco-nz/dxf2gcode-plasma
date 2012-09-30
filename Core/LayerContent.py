#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#Programmers:   Christian Kohl�ffel
#               Vinzenz Schulz
#
#Distributed under the terms of the GPL (GNU Public License)
#
#dxf2gcode is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import logging
logger=logging.getLogger("Core.LayerContent") 

class LayerContentClass:
    def __init__(self,LayerNr=None,LayerName='',shapes=[]):
        self.LayerNr=LayerNr
        self.LayerName=LayerName
        self.shapes=shapes
        self.exp_order=[]
        
    def __cmp__(self, other):
         return cmp(self.LayerNr, other.LayerNr)

    def __str__(self):
        return ('\ntype:          %s' %self.type) +\
               ('\nLayerNr :      %i' %self.LayerNr) +\
               ('\nLayerName:     %s' %self.LayerName)+\
               ('\nshapes:        %s' %self.shapes)+\
               ('\nexp_order:     %s' %self.exp_order)    
               
