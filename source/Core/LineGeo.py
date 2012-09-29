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


from math import sqrt, degrees

#Length of the cross.
dl = 0.2
DEBUG = 1

class LineGeo:
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """ 
    def __init__(self, Pa, Pe):
        """
        Standard Method to initialise the LineGeo
        """
        self.type = "LineGeo"
        self.Pa = Pa
        self.Pe = Pe
        self.col = 'Black'
        self.length = self.Pa.distance(self.Pe)
        
    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\nLineGeo") + \
               ("\nPa : %s" % self.Pa) + \
               ("\nPe : %s" % self.Pe) + \
               ("\nlength: %0.5f" % self.length)        

    def reverse(self):
        """ 
        Reverses the direction of the arc (switch direction).
        """ 
        Pa = self.Pa
        Pe = self.Pe
        
        self.Pa = Pe
        self.Pe = Pa
   
    def make_abs_geo(self, parent=None, reverse=0):
        """
        Generates the absolut geometry based on the geometry self and the
        parent. If reverse 1 is given the geometry may be reversed.
        @param parent: The parent of the geometry (EntitieContentClass)
        @param reverse: If 1 the geometry direction will be switched.
        @return: A new LineGeoClass will be returned.
        """ 
        Pa = self.Pa.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)
        abs_geo = LineGeo(Pa=Pa, Pe=Pe)
        if reverse:
            abs_geo.reverse()
        return abs_geo
    
    
        
    def add2path(self, papath=None, parent=None): 
        """
        Plots the geometry of self into the defined canvas.
        @param canvas: The canvas instance to plot in
        @param tag: the number of the parent shape
        @param col: The color in which the shape shall be ploted
        @param plotoption: Additional option for Debug print use
        @return: Returns the hdl or hdls of the ploted objects.
        """

        abs_geo=self.make_abs_geo(parent, 0)
        papath.lineTo(abs_geo.Pe.x, -abs_geo.Pe.y)


    def get_start_end_points(self, direction, parent=None):
        """
        Returns the start/end Point and its direction
        @param direction: 0 to return start Point and 1 to return end Point
        @return: a list of Point and angle 
        """
        if not(direction):
            punkt=self.Pa.rot_sca_abs(parent=parent)
            punkt_e=self.Pe.rot_sca_abs(parent=parent)
            angle=degrees(punkt.norm_angle(punkt_e))
        elif direction:
            punkt_a=self.Pa.rot_sca_abs(parent=parent)
            punkt=self.Pe.rot_sca_abs(parent=parent)
            angle=degrees(punkt.norm_angle(punkt_a))
        return punkt, angle
    
    def Write_GCode(self,parent=None, PostPro=None):
        """
        To be calles if a LineGeo shall be wirtten to the PostProcessor.
        @param pospro: The used Posprocessor instance
        @return: a string to be written into the file
        """
        anf, anf_ang=self.get_start_end_points(0,parent)
        ende, end_ang=self.get_start_end_points(1,parent)

        return PostPro.lin_pol_xy(anf,ende)

    def distance2point(self, Point):
        """
        Returns the distance between a line and a given Point
        @param Point: The Point which shall be checked
        @return: returns the distance to the Line
        """
        try:
            AE = self.Pa.distance(self.Pe)
            AP = self.Pa.distance(Point)
            EP = self.Pe.distance(Point)
            AEPA = (AE + AP + EP) / 2
            return abs(2 * sqrt(abs(AEPA * (AEPA - AE) * \
                                     (AEPA - AP) * (AEPA - EP))) / AE)
        except:
            return 1e10
            
