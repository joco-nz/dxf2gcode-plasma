#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
#
#dxf2gcode_b02_point
#Programmers:   Christian Kohlöffel
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



from point import PointClass
from copy import copy

            
class BoundingBox:
    """ 
    Bounding Box Class. This is the standard class which provides all std. 
    Bounding Box methods.
    """ 
    def __init__(self, Pa=PointClass(0, 0), Pe=PointClass(0, 0), hdl=[]):
        """ 
        Standard method to initialize the class
        """ 
        self.Pa = Pa
        self.Pe = Pe
        
    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        s = ("\nPa : %s" % (self.Pa)) + \
           ("\nPe : %s" % (self.Pe))
        return s
    
    def joinBB(self, other):
        """
        Joins two Bounding Box Classes and returns the new one
        @param other: The 2nd Bounding Box
        @return: Returns the joined Bounding Box Class
        """
        
        if type(self.Pa) == type(None) or type(self.Pe) == type(None):
            return BoundingBox(copy(other.Pa), copy(other.Pe))
        
        xmin = min(self.Pa.x, other.Pa.x)
        xmax = max(self.Pe.x, other.Pe.x)
        ymin = min(self.Pa.y, other.Pa.y)
        ymax = max(self.Pe.y, other.Pe.y)
        
        return BoundingBox(Pa=PointClass(xmin, ymin), Pe=PointClass(xmax, ymax))
    
    def hasintersection(self, other=None, tol=0.0):
        """
        Checks if the two bounding boxes have an intersection
        @param other: The 2nd Bounding Box
        @return: Returns true or false
        """        
        x_inter_pos = (self.Pe.x + tol > other.Pa.x) and \
        (self.Pa.x - tol < other.Pe.x)
        y_inter_pos = (self.Pe.y + tol > other.Pa.y) and \
        (self.Pa.y - tol < other.Pe.y)
     
        return x_inter_pos and y_inter_pos
    
    def pointisinBB(self, point=PointClass(), tol=0.01):
        """
        Checks if the point is within the bounding box
        @param point: The Point which shall be ckecke
        @return: Returns true or false
        """
        x_inter_pos = (self.Pe.x + tol > point.x) and \
        (self.Pa.x - tol < point.x)
        y_inter_pos = (self.Pe.y + tol > point.y) and \
        (self.Pa.y - tol < point.y)
        return x_inter_pos and y_inter_pos
     
    def plot2can(self, canvas=None, tag=None, col='red', hdl=[]):
        """
        Plots the geometry of self into the defined canvas.
        @param canvas: The canvas instance to plot in
        @param tag: the number of the parent shape
        @param col: The color in which the shape shall be ploted
        @param hdl: The existing hdls where to append the additional ones
        @return: Returns the hdl or hdls of the ploted objects.
        """
        hdl.append(Line(canvas,
                        self.Pa.x, -self.Pa.y, self.Pe.x, -self.Pa.y, tag=tag, fill=col))
        hdl.append(Line(canvas,
                        self.Pe.x, -self.Pa.y, self.Pe.x, -self.Pe.y, tag=tag, fill=col))
        hdl.append(Line(canvas,
                        self.Pe.x, -self.Pe.y, self.Pa.x, -self.Pe.y, tag=tag, fill=col))
        hdl.append(Line(canvas,
                        self.Pa.x, -self.Pe.y, self.Pa.x, -self.Pa.y, tag=tag, fill=col))
        return hdl
