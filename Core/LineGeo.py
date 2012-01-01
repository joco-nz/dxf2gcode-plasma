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


from Canvas import Line
from math import sqrt, sin, cos, atan2, radians, degrees, pi, floor, ceil, copysign
from point import PointClass
from copy import copy

#Length of the cross.
dl = 0.2
DEBUG = 1

class ArcGeo:
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """ 
    def __init__(self, Pa=None, Pe=None, O=None, r=1,
                 s_ang=None, e_ang=None, direction=1):
        """
        Standard Method to initialise the LineGeo
        """
        self.type = "ArcGeo"
        self.Pa = Pa
        self.Pe = Pe
        self.O = O
        self.r = abs(r)
        self.s_ang = s_ang
        self.e_ang = e_ang
        self.col = 'Black'
        
       
        # Kreismittelpunkt bestimmen wenn Pa,Pe,r,und direction bekannt
        if type(self.O) == type(None):
           
            if (type(Pa) != type(None)) and \
            (type(Pe) != type(None)) and \
            (type(direction) != type(None)):
               
                arc = self.Pe.norm_angle(Pa) - pi / 2
                Ve = Pe - Pa
                m = (sqrt(pow(Ve.x, 2) + pow(Ve.y, 2))) / 2
                lo = sqrt(pow(r, 2) - pow(m, 2))
                if direction < 0:
                    d = -1
                else:
                    d = 1
                self.O = Pa + 0.5 * Ve
                self.O.y += lo * sin(arc) * d
                self.O.x += lo * cos(arc) * d
                
              
        # Falls nicht übergeben Mittelpunkt ausrechnen  
            elif (type(self.s_ang) != type(None)) and (type(self.e_ang) != type(None)):
                self.O.x = self.Pa.x - r * cos(self.s_ang)
                self.O.y = self.Pa.y - r * sin(self.s_ang)
            else:
                print('Missing value for Arc Geometry')

        #Falls nicht übergeben dann Anfangs- und Endwinkel ausrechen            
        if type(self.s_ang) == type(None):
            self.s_ang = self.O.norm_angle(Pa)
            
        if type(self.e_ang) == type(None):
            self.e_ang = self.O.norm_angle(Pe)
        
        self.ext=self.dif_ang(self.Pa, self.Pe, direction)
        #self.get_arc_extend(direction)

        #Falls es ein Kreis ist Umfang 2pi einsetzen        
        if self.ext == 0.0:
            self.ext = 2 * pi
                   
        
        self.length = self.r * abs(self.ext)

#    def get_arc_extend(self,direction):
#        #Aus dem Vorzeichen von direction den extend ausrechnen
#        self.ext = self.e_ang - self.s_ang
#        if direction > 0.0:
#            self.ext = self.ext % (-2 * pi)
#            self.ext -= floor(self.ext / (2 * pi)) * (2 * pi)
#        else:
#            self.ext = self.ext % (-2 * pi)
#            self.ext += ceil(self.ext / (2 * pi)) * (2 * pi)

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\nArcGeo") + \
               ("\nPa : %s; s_ang: %0.5f" % (self.Pa, self.s_ang)) + \
               ("\nPe : %s; e_ang: %0.5f" % (self.Pe, self.e_ang)) + \
               ("\nO  : %s; r: %0.3f" % (self.O, self.r)) + \
               ("\next  : %0.5f; length: %0.5f" % (self.ext, self.length))

    
    def add2path(self, papath=None, parent=None):
        """
        Plots the geometry of self into the defined canvas. Arcs will be ploted
        as line segments.
        @param canvas: The canvas instance to plot in
        @param tag: the number of the parent shape
        @param col: The color in which the shape shall be ploted
        @param plotoption: Additional option for Debug print use
        @return: Returns the hdl or hdls of the ploted objects.
        """
        
        abs_geo=self.make_abs_geo(parent, 0)
        #papath.arcTo(abs_geo.O.x-abs_geo.r, -abs_geo.O.y-self.r,
        #                  2*abs_geo.r, 2*abs_geo.r, degrees(abs_geo.s_ang), degrees(abs_geo.ext))

        #papath.lineTo(abs_geo.Pe.x, -abs_geo.Pe.y)

                        
        x = []; y = []; hdl = []
        #Alle 10 Grad ein Segment => 120 Segmente für einen Kreis !!
        segments = int((abs(degrees(abs_geo.ext)) // 10) + 1)
        
        for i in range(segments + 1):
            
            ang = abs_geo.s_ang + i * abs_geo.ext / segments
            p_cur = PointClass(x=(abs_geo.O.x + cos(ang) * abs(abs_geo.r)), \
                       y=(abs_geo.O.y + sin(ang) * abs(abs_geo.r)))

            if i >= 1:
                papath.lineTo(p_cur.x, -p_cur.y)    
               


    
    def dif_ang(self, P1, P2, direction,tol=0.005):
        """
        Calculated the angle of extend based on the 3 given points. Center Point,
        P1 and P2.
        @param P1: the start point of the arc 
        @param P2: the end point of the arc
        @param direction: the direction of the arc
        @return: Returns the angle between -2* pi and 2 *pi for the arc extend
        """ 
        
        #FIXME Das könnte Probleme geben bei einem reelen Kreis
#        if P1.isintol(P2,tol):
#            return 0.0
#        
        sa = self.O.norm_angle(P1)
        ea = self.O.norm_angle(P2)

        if(direction > 0.0):     # GU
            dif_ang = (ea-sa)%(-2*pi)
            dif_ang -= floor(dif_ang / (2 * pi)) * (2 * pi)     
        else:
            dif_ang = (ea-sa)%(-2*pi)
            dif_ang += ceil(dif_ang / (2 * pi)) * (2 * pi)    
            
        return dif_ang
    
    def reverse(self):
        """ 
        Reverses the direction of the arc (switch direction).
        """ 
        Pa = self.Pa
        Pe = self.Pe
        ext = self.ext
        s_ang = self.e_ang
        e_ang = self.s_ang
        
        
        self.Pa = Pe
        self.Pe = Pa
        self.ext = ext * -1
        self.s_ang = s_ang
        self.e_ang = e_ang
        
    def make_abs_geo(self, parent=None, reverse=0):
        """
        Generates the absolut geometry based on the geometry self and the
        parent. If reverse 1 is given the geometry may be reversed.
        @param parent: The parent of the geometry (EntitieContentClass)
        @param reverse: If 1 the geometry direction will be switched.
        @return: A new ArcGeoClass will be returned.
        """ 
        Pa = self.Pa.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)
        O = self.O.rot_sca_abs(parent=parent)
        r = self.scaleR(self.r, parent)
        direction = copysign(1, self.ext)
        #s_ang=self.rot_angle(self.s_ang,parent)
        #e_ang=self.rot_angle(self.e_ang,parent)
        abs_geo = ArcGeo(Pa=Pa, Pe=Pe, O=O, r=r, direction=direction)
        if reverse:
            abs_geo.reverse()
        return abs_geo
    
   
    def get_start_end_points(self, direction,parent=None):
        """
        Returns the start/end point and its direction
        @param direction: 0 to return start point and 1 to return end point
        @return: a list of point and angle Returns the hdl or hdls of the ploted objects.
        """
        
        if not(direction):
            punkt=self.Pa.rot_sca_abs(parent=parent)
            angle=self.rot_angle(degrees(self.s_ang)+90*self.ext/abs(self.ext),parent)
        elif direction:
            punkt=self.Pe.rot_sca_abs(parent=parent)
            angle=self.rot_angle(degrees(self.e_ang)-90*self.ext/abs(self.ext),parent)
        return punkt,angle
        
          

    def angle_between(self, min_ang, max_ang, angle):
        """
        Returns if the angle is in the range between 2 other angles
        @param min_ang: The starting angle
        @param parent: The end angel. Always in ccw direction from min_ang
        @return: True or False
        """
        if min_ang < 0.0:
            min_ang += 2 * pi
        
        while max_ang < min_ang:
            max_ang += 2 * pi
            
        while angle < min_ang:
            angle += 2 * pi
                    
        return (min_ang < angle) and (angle <= max_ang)
   
    def rot_angle(self, angle, parent):
        """
        Rotates the given angle based on the rotations given in its parents.
        @param angle: The angle which shall be rotated
        @param parent: The parent Entitie (Instance: EntitieContentClass)
        @return: The rotated angle.
        """

        #Rekursive Schleife falls mehrfach verschachtelt.
        if type(parent) != type(None):
            angle = angle + degrees(parent.rot)
            angle = self.rot_angle(angle, parent.parent)
                
        return angle
    
    def scaleR(self, sR, parent):
        """
        Scales the radius based on the scale given in its parents. This is done
        recursively.
        @param sR: The radius which shall be scaled
        @param parent: The parent Entitie (Instance: EntitieContentClass)
        @return: The scaled radius
        """
        
        #Rekursive Schleife falls mehrfach verschachtelt.
        if type(parent) != type(None):
            sR = sR * parent.sca[0]
            sR = self.scaleR(sR, parent.parent)
                
        return sR

    def Write_GCode(self, postpro=None):
        """
        Writes the GCODE for a ARC.
        @param postpro: The postprocessor instance to be used
        @return: Returns the string to be written to a file.
        """
       
        #If the radius of the element is bigger then the max. radius export
        #the element as an line.
        if self.r > postpro.max_arc_radius:
            string = postpro.lin_pol_xy(self.Pa, self.Pe)
        else:
            if (self.ext > 0):
                string = postpro.lin_pol_arc("ccw", self.Pa, self.Pe,
                                           self.s_ang, self.e_ang,
                                           self.r, self.O, self.O - self.Pa)
                
            elif (self.ext < 0) and postpro.export_ccw_arcs_only:
                string = postpro.lin_pol_arc("ccw", self.Pe, self.Pa,
                                           self.e_ang, self.s_ang,
                                           self.r, self.O, self.O - self.Pe)
            else:
                string = postpro.lin_pol_arc("cw", self.Pa, self.Pe,
                                           self.s_ang, self.e_ang,
                                           self.r, self.O, self.O - self.Pa)
        return string  


    
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
    #plot2can(self, canvas=None, tag=None, col='black', plotoption=0):
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
#        hdl = []
#
#        hdl.append(Line(canvas, self.Pa.x, -self.Pa.y,
#                        self.Pe.x, -self.Pe.y, tag=tag, fill=col))
#        
#        if plotoption:
#            hdl.append(Line(canvas, self.Pa.x - dl, -self.Pa.y - dl,
#                            self.Pa.x + dl, -self.Pa.y + dl, tag=tag, fill=col))
#            hdl.append(Line(canvas, self.Pa.x + dl, -self.Pa.y - dl,
#                            self.Pa.x - dl, -self.Pa.y + dl, tag=tag, fill=col))
#            hdl.append(Line(canvas, self.Pe.x - dl, -self.Pe.y - dl,
#                            self.Pe.x + dl, -self.Pe.y + dl, tag=tag, fill=col))
#            hdl.append(Line(canvas, self.Pe.x + dl, -self.Pe.y - dl,
#                            self.Pe.x - dl, -self.Pe.y + dl, tag=tag, fill=col))
#         
#        #if DEBUG:   
#            #self.BB.plot2can(canvas=canvas, tag=tag, col='red', hdl=hdl)
#            
#        return hdl

    def get_start_end_points(self, direction, parent=None):
        """
        Returns the start/end point and its direction
        @param direction: 0 to return start point and 1 to return end point
        @return: a list of point and angle 
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
    
    def Write_GCode(self, postpro=None):
        """
        To be calles if a LineGeo shall be wirtten to the postprocessor.
        @param pospro: The used Posprocessor instance
        @return: a string to be written into the file
        """
        return postpro.lin_pol_xy(self.Pa, self.Pe)

    def distance2point(self, point):
        """
        Returns the distance between a line and a given point
        @param point: The Point which shall be checked
        @return: returns the distance to the Line
        """
        try:
            AE = self.Pa.distance(self.Pe)
            AP = self.Pa.distance(point)
            EP = self.Pe.distance(point)
            AEPA = (AE + AP + EP) / 2
            return abs(2 * sqrt(abs(AEPA * (AEPA - AE) * \
                                     (AEPA - AP) * (AEPA - EP))) / AE)
        except:
            return 1e10
            
