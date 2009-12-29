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
from bounding_box import BoundingBoxClass
from copy import copy

#Length of the cross.
dl = 0.1
DEBUG = 0

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
        self.BB = []
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
        
        #Aus dem Vorzeichen von direction den extend ausrechnen
        self.ext = self.e_ang - self.s_ang
        if direction > 0.0:
            self.ext = self.ext % (-2 * pi)
            self.ext -= floor(self.ext / (2 * pi)) * (2 * pi)
        else:
            self.ext = self.ext % (-2 * pi)
            self.ext += ceil(self.ext / (2 * pi)) * (2 * pi)

        #Falls es ein Kreis ist Umfang 2pi einsetzen        
        if self.ext == 0.0:
            self.ext = 2 * pi
                   
        
        self.length = self.r * abs(self.ext)

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\nArcGeo") + \
               ("\nPa : %s; s_ang: %0.5f" % (self.Pa, self.s_ang)) + \
               ("\nPe : %s; e_ang: %0.5f" % (self.Pe, self.e_ang)) + \
               ("\nO  : %s; r: %0.3f" % (self.O, self.r)) + \
               ("\nBB : %s" % self.BB) + \
               ("\next  : %0.5f; length: %0.5f" % (self.ext, self.length))

    
    def dif_ang(self, P1, P2, direction):
        """
        Calculated the angle of extend based on the 3 given points. Center Point,
        P1 and P2.
        @param P1: the start point of the arc 
        @param P2: the end point of the arc
        @param direction: the direction of the arc
        @return: Returns the angle between -2* pi and 2 *pi for the arc extend
        """ 
        sa = self.O.norm_angle(P1)
       
        if(sa < 0):
            sa += 2 * pi
        
        ea = self.O.norm_angle(P2)
        if(ea < 0):
            ea += 2 * pi
        
        if(direction > 0):     # GU
            if(sa > ea):
                ang = (2 * pi - sa + ea)
            else:
                ang = (ea - sa)
        else:
            if(ea > sa):
                ang = (sa + 2 * pi - ea)
            else:
                ang = (sa - ea)
        
        return(ang)        
        
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
    
    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        
        Pa = PointClass(x=self.O.x - self.r, y=self.O.y - self.r)
        Pe = PointClass(x=self.O.x + self.r, y=self.O.y + self.r)
        
        #Do the calculation only for arcs have positiv extend => switch angles
        if self.ext >= 0:
            s_ang = self.s_ang
            e_ang = self.e_ang
        elif self.ext < 0:
            s_ang = self.e_ang
            e_ang = self.s_ang
                 
        #If the positive X Axis is crossed
        if not(self.wrap(s_ang, 0) >= self.wrap(e_ang, 1)):
            Pe.x = max(self.Pa.x, self.Pe.x)

        #If the positive Y Axis is crossed 
        if not(self.wrap(s_ang - pi / 2, 0) >= self.wrap(e_ang - pi / 2, 1)):
            Pe.y = max(self.Pa.y, self.Pe.y)

        #If the negative X Axis is crossed
        if not(self.wrap(s_ang - pi, 0) >= self.wrap(e_ang - pi, 1)):
            Pa.x = min(self.Pa.x, self.Pe.x)

        #If the negative Y is crossed 
        if not(self.wrap(s_ang - 1.5 * pi, 0) >= 
                self.wrap(e_ang - 1.5 * pi, 1)):
            Pa.y = min(self.Pa.y, self.Pe.y)
       
        self.BB = BoundingBoxClass(Pa=Pa, Pe=Pe)
        
    def wrap(self, angle, isend=0):
        """
        Wrapes the given angle into a range between 0 and 2pi
        @param angle: The angle to be wraped
        @param isend: If the angle is the end angle or start angle, this makes a
        difference at 0 or 2pi.
        @return: Returns the angle between 0 and 2 *pi
        """ 
        wrap_angle = angle % (2 * pi)
        if isend and wrap_angle == 0.0:
            wrap_angle += 2 * pi
        elif wrap_angle == 2 * pi:
            wrap_angle -= 2 * pi
            
        return wrap_angle
    
    
    def plot2can(self, canvas=None, tag=None, col='black', plotoption=0):
        """
        Plots the geometry of self into the defined canvas. Arcs will be ploted
        as line segments.
        @param canvas: The canvas instance to plot in
        @param tag: the number of the parent shape
        @param col: The color in which the shape shall be ploted
        @param plotoption: Additional option for Debug print use
        @return: Returns the hdl or hdls of the ploted objects.
        """
                        
        x = []; y = []; hdl = []
        #Alle 10 Grad ein Segment => 120 Segmente für einen Kreis !!
        segments = int((abs(degrees(self.ext)) // 2) + 1)
        
        for i in range(segments + 1):
            
            ang = self.s_ang + i * self.ext / segments
            p_cur = PointClass(x=(self.O.x + cos(ang) * abs(self.r)), \
                       y=(self.O.y + sin(ang) * abs(self.r)))
                    
            x.append(p_cur.x)
            y.append(p_cur.y)
            
            if i >= 1:
                hdl.append(Line(canvas, x[i - 1], -y[i - 1], x[i], -y[i], tag=tag, fill=col))       
               
        if plotoption:
            hdl.append(Line(canvas, self.Pa.x - dl, -self.Pa.y - dl,
                            self.Pa.x + dl, -self.Pa.y + dl, tag=tag, fill=col))
            hdl.append(Line(canvas, self.Pa.x + dl, -self.Pa.y - dl,
                            self.Pa.x - dl, -self.Pa.y + dl, tag=tag, fill=col))
            hdl.append(Line(canvas, self.Pe.x - dl, -self.Pe.y - dl,
                            self.Pe.x + dl, -self.Pe.y + dl, tag=tag, fill=col))
            hdl.append(Line(canvas, self.Pe.x + dl, -self.Pe.y - dl,
                            self.Pe.x - dl, -self.Pe.y + dl, tag=tag, fill=col))
         
        if DEBUG:   
            self.BB.plot2can(canvas=canvas, tag=tag, col='red', hdl=hdl)
         
        return hdl  

    def get_start_end_points(self, direction):
        """
        Returns the start/end point and its direction
        @param direction: 0 to return start point and 1 to return end point
        @return: a list of point and angle Returns the hdl or hdls of the ploted objects.
        """
        if not(direction):
            point = self.Pa
            angle = degrees(self.s_ang) + 90 * self.ext / abs(self.ext)
        elif direction:
            point = self.Pe
            angle = degrees(self.e_ang) - 90 * self.ext / abs(self.ext)
        return point, angle
    
   
    def find_inter_points(self, other):
        """
        Find the intersection between 2 geometry elements. Possible is LineGeo
        and ArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """
        if other.type == "LineGeo":
            return other.find_inter_point_l_a(self)
        elif other.type == "ArcGeo":
            return self.find_inter_point_a_a(other)
        else:
            print 'Hab ich noch nicht'
            
    
    def find_inter_point_a_a(self, other):
        """
        Find the intersection between 2 ArcGeo elements. There can be only one
        intersection between 2 lines.
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """
        
        tol=0.01
            
        O_dis = self.O.distance(other.O)
        
        #If self circle is surrounded by the other no intersection
        if(O_dis < abs(self.r - other.r)-tol):
            return [1]

        #If other circle is surrounded by the self no intersection
        if(O_dis < abs(other.r - self.r)-tol):
            return [2]
        
        #If both circles have the same center and radius
        if abs(O_dis) == 0.0 and abs(self.r-other.r) ==0.0:
            return [self.Pa, self.Pe]

        #The following algorithm was found on :
        #http://www.sonoma.edu/users/w/wilsonst/Papers/Geometry/circles/default.htm
        
        root = ((pow(self.r + other.r , 2) - pow(O_dis, 2)) * 
                  (pow(O_dis, 2) - pow(other.r - self.r, 2)))
        
        #If the Line is a tangent the root is 0.0.
        if root<=0.0:
            root=0.0
        else:  
            root=sqrt(root)
        
        xbase = (other.O.x + self.O.x) / 2 + \
        (other.O.x - self.O.x) * \
        (pow(self.r, 2) - pow(other.r, 2)) / (2 * pow(O_dis, 2))
        
        ybase = (other.O.y + self.O.y) / 2 + \
        (other.O.y - self.O.y) * \
        (pow(self.r, 2) - pow(other.r, 2)) / (2 * pow(O_dis, 2))
        
        Pi1 = PointClass(x=xbase + (other.O.y - self.O.y) / \
                          (2 * pow(O_dis, 2)) * root,
                    y=ybase - (other.O.x - self.O.x) / \
                    (2 * pow(O_dis, 2)) * root)

        Pi2 = PointClass(x=xbase - (other.O.y - self.O.y) / \
                         (2 * pow(O_dis, 2)) * root,
                    y=ybase + (other.O.x - self.O.x) / \
                    (2 * pow(O_dis, 2)) * root)
        
        if Pi1.distance(Pi2) == 0.0:
            return [Pi1]
        else:
            return [Pi1, Pi2]

#        if(self.O.x == other.O.x):
#            d1 = (self.O.x - other.O.x)/(other.O.y - self.O.y)
#            d2 = ((pow(self.r,2) - pow(other.r,2))- (pow(self.O.y,2) 
#            - pow(other.O.y,2)) - (pow(self.O.x,2) - pow(other.O.x,2))  )/
#            (2*other.O.y - 2*self.O.y)
#            a = pow(d1,2)+1
#            b = (2*d1*(d2-self.O.y))-(2*self.O.x)
#            c = pow((d2-self.O.y),2) -pow(self.r,2) + pow(self.O.x,2)
#          
#            self.P1.x = (-b + sqrt(pow(b,2) - 4*a*c) )/(2*a)
#            self.P2.x = (-b - sqrt(pow(b,2) - 4*a*c) )/(2*a)
#            self.P1.y = self.P1.x * d1 + d2
#            self.P2.y = self.P2.x * d1 + d2
#
#        else:
#            d1 =(self.O.y - other.O.y)/(other.O.x - self.O.x)
#            d2 =((pow(self.r,2) - pow(other.r,2))- (pow(self.O.x,2) 
#            - pow(other.O.x,2)) -  (pow(self.O.y,2) - pow(other.O.y,2))  )
#            /(2*other.O.x - 2*self.O.x)
#            a = pow(d1,2)+1
#            b = (2*d1*(d2-self.O.x))-(2*self.O.y)
#            c = pow((d2-self.O.x),2)-pow(self.r,2) + pow(self.O.y,2)
#           
#            self.P1.y = (-b + sqrt(pow(b,2) - 4*a*c) )/(2*a)
#            self.P2.y = (-b - sqrt(pow(b,2) - 4*a*c) )/(2*a)
#            self.P1.x = self.P1.y * d1 + d2
#            self.P2.x = self.P2.y * d1 + d2



        #If both solutions are identical then return only one.

    def isTIP(self, point=PointClass, tol=0.01):
        """
        Checks if the point is a Local Self Intersection Point of the ArcGeo
        @param point: The Point which shall be ckecke
        @return: Returns true or false
        """
        
        #The linear tolerance in angle
        atol = tol / 2 / pi / self.r
        pang = self.O.norm_angle(point)
         
        if self.ext >= 0.0:
            return self.angle_between(self.s_ang - atol, self.e_ang + tol, pang)
        else:
            return self.angle_between(self.e_ang - atol, self.s_ang + tol, pang)
    
        
    def split_into_2geos(self, ipoint=PointClass()):
        """
        Splits the given geometry into 2 not self intersection geometries. The
        geometry will be splitted between ipoint and Pe.
        @param ipoint: The Point where the intersection occures
        @return: A list of 2 ArcGeo's will be returned.
        """
       
        #The angle between endpoint and where the intersection occures
        d_e_ang = self.e_ang - self.O.norm_angle(ipoint)
        
        #Correct by 2*pi if the direction is wrong
        if d_e_ang > self.ext:
            d_e_ang -= 2 * pi
            
        #The point where the geo shall be splitted
        spoint = self.O.get_arc_point(ang=degrees(self.e_ang - d_e_ang / 2),
                                      r=self.r)
        
        #Generate the 2 geometries and their bounding boxes.
        Arc1 = ArcGeo(Pa=self.Pa, Pe=spoint, r=self.r,
                       O=self.O, direction=self.ext)
        Arc1.calc_bounding_box()
        Arc2 = ArcGeo(Pa=spoint, Pe=self.Pe, r=self.r,
                       O=self.O, direction=self.ext)
        Arc2.calc_bounding_box()
        
        return [Arc1, Arc2]
    
    def rawoffset(self, radius=10.0, direction=41):
        """
        Returns the Offset Curve defined by radius and offset direction of the 
        geometry self.
        @param radius: The offset of the curve
        @param direction: The direction of offset 41==Left 42==Right
        @return: The offseted geometry
        """  
        
        
        #For Arcs in ccw direction
        if self.ext < 0.0 and direction == 41:
            offr = self.r + radius
        elif self.ext < 0.0 and direction == 42:
            offr = self.r - radius
        elif self.ext >= 0 and direction == 41:
            offr = self.r - radius
        else:
            offr = self.r + radius
            
        #If the radius of the new element is smaller then 0.0 return nothing 
        #and therefore ignor this geom.
        if offr <= 0.0:
            return []
                    
        offPa = self.O.get_arc_point(ang=degrees(self.s_ang), r=offr)
        offPe = self.O.get_arc_point(ang=degrees(self.e_ang), r=offr)
              
        offArc = ArcGeo(Pa=offPa, Pe=offPe, O=self.O, r=offr, direction=self.ext)
        offArc.calc_bounding_box()
        
        return [offArc]
    
    def trim_join(self, other, newPa, orgPe, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end point of the last geometry)
        @return: A list of geos
        """ 
        if other.type == "LineGeo":
            return self.trim_join_al(other, newPa, orgPe, tol)
        else:
            return self.trim_join_aa(other, newPa, orgPe, tol)
            print 'gibts noch nicht'
            #return self.trim_join_la(other, newPa, orgPe, tol)
        
            #print 'Hab ich noch nicht' 
            
    def trim_join_al(self, other, newPa, orgPe, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end point of the last geometry)
        @return: A list of geos
        """ 
        geos = []
        
        points = self.find_inter_points(other)
        
        #Case 1 according to Algorithm 2
        if len(points):
            ipoint = self.Pe.get_nearest_point(points)
            
            
            isTIP1 = self.isTIP(ipoint, tol)
            isTIP2 = other.isTIP(ipoint, tol)
            
            #Case 1 a
            if isTIP1 and isTIP2:
                geos.append(ArcGeo(Pa=newPa, Pe=ipoint, O=self.O,
                                   r=self.r, direction= self.ext))
                
            #Case 1 b
            elif not(isTIP1) and not(isTIP2):
                direction=-other.Pe.get_arc_direction(other.Pa,orgPe)
                r=self.Pe.distance(orgPe)
                
                geos.append(ArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
                geos.append(ArcGeo(Pa=self.Pe,Pe=other.Pa,
                                   O=orgPe,
                                   r=r, direction=direction))
                
            #Case 1 c & d
            else:
                geos.append(ArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
                geos.append(LineGeo(self.Pe, other.Pa))
                
        #Case 2
        else: 
            direction=-other.Pe.get_arc_direction(other.Pa,orgPe)
            
            r=self.Pe.distance(orgPe)
            geos.append(ArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
            geos.append(ArcGeo(Pa=self.Pe,Pe=other.Pa,
                               O=orgPe, direction=direction, 
                               r=r))
            
        return geos
    
    
    def trim_join_aa(self, other, newPa, orgPe, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end point of the last geometry)
        @return: A list of geos
        """ 
        geos = [] 
        points = self.find_inter_points(other)
        
        
        #Case 1 according to Algorithm 2
        if len(points):
            ipoint = self.Pe.get_nearest_point(points)
            
            isTIP1 = self.isTIP(ipoint, tol)
            isTIP2 = other.isTIP(ipoint, tol)
            
            #Case 1 a
            if (isTIP1 and isTIP2) or (not(isTIP1) and not(isTIP2)):
                geos.append(ArcGeo(Pa=newPa, Pe=ipoint, O=self.O,
                                   r=self.r, direction= self.ext))
                                 
            #Case 1 b
            else:
                geos.append(ArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
                geos.append(LineGeo(self.Pe, other.Pa))
                
        #Case 2
        else: 
            direction=self.get_arc_direction(orgPe)
            r=self.Pe.distance(orgPe)
          
            geos.append(ArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
            geos.append(ArcGeo(Pa=self.Pe,Pe=other.Pa,
                               O=orgPe, direction=-direction,
                               r=r))
            
        return geos
    
    def get_arc_direction(self,newO):
        """ 
        Calculate the arc direction given from the Arc and O of the new Arc.
        @param O: The center of the arc
        @return: Returns the direction (+ or - pi/2)
        """ 
        
        a1= self.e_ang - pi/2 * self.ext / abs(self.ext)
        a2=self.Pe.norm_angle(newO)
        direction=a2-a1
        
        if direction>pi:
            direction=direction-2*pi
        elif direction<-pi:
            direction=direction+2*pi
            
        #print ('Die Direction ist: %s' %direction)
        
        return direction
    
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
        self.BB = []
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
               ("\nBB : %s" % self.BB) + \
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
    
    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        Pa = PointClass(x=min(self.Pa.x, self.Pe.x), y=min(self.Pa.y, self.Pe.y))
        Pe = PointClass(x=max(self.Pa.x, self.Pe.x), y=max(self.Pa.y, self.Pe.y))
        
        self.BB = BoundingBoxClass(Pa=Pa, Pe=Pe)
        
    def plot2can(self, canvas=None, tag=None, col='black', plotoption=0):
        """
        Plots the geometry of self into the defined canvas.
        @param canvas: The canvas instance to plot in
        @param tag: the number of the parent shape
        @param col: The color in which the shape shall be ploted
        @param plotoption: Additional option for Debug print use
        @return: Returns the hdl or hdls of the ploted objects.
        """
        
        hdl = []

        hdl.append(Line(canvas, self.Pa.x, -self.Pa.y,
                        self.Pe.x, -self.Pe.y, tag=tag, fill=col))
        
        if plotoption:
            hdl.append(Line(canvas, self.Pa.x - dl, -self.Pa.y - dl,
                            self.Pa.x + dl, -self.Pa.y + dl, tag=tag, fill=col))
            hdl.append(Line(canvas, self.Pa.x + dl, -self.Pa.y - dl,
                            self.Pa.x - dl, -self.Pa.y + dl, tag=tag, fill=col))
            hdl.append(Line(canvas, self.Pe.x - dl, -self.Pe.y - dl,
                            self.Pe.x + dl, -self.Pe.y + dl, tag=tag, fill=col))
            hdl.append(Line(canvas, self.Pe.x + dl, -self.Pe.y - dl,
                            self.Pe.x - dl, -self.Pe.y + dl, tag=tag, fill=col))
         
        if DEBUG:   
            self.BB.plot2can(canvas=canvas, tag=tag, col='red', hdl=hdl)
            
        return hdl

    def get_start_end_points(self, direction):
        """
        Returns the start/end point and its direction
        @param direction: 0 to return start point and 1 to return end point
        @return: a list of point and angle 
        """
        if not(direction):
            punkt = self.Pa
            angle = degrees(self.Pa.norm_angle(self.Pe))
        elif direction:
            punkt = self.Pe
            angle = degrees(self.Pe.norm_angle(self.Pa))
        return punkt, angle
    
    
    def find_inter_points(self, other):
        """
        Find the intersection between 2 geometry elements. Possible is LineGeo
        and ArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """
        if other.type == "LineGeo":
            return self.find_inter_point_l_l(other)
        elif other.type == "ArcGeo":
            return self.find_inter_point_l_a(other)
        else:
            print 'Hab ich noch nicht'
            
    
    def find_inter_point_l_l(self, L2):
        """
        Find the intersection between 2 LineGeo elements. There can be only one
        intersection between 2 lines.
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """

        dx1 = self.Pe.x - self.Pa.x
        dy1 = self.Pe.y - self.Pa.y
        
        dx2 = L2.Pe.x - L2.Pa.x
        dy2 = L2.Pe.y - L2.Pa.y

        dax = self.Pa.x - L2.Pa.x
        day = self.Pa.y - L2.Pa.y

        #Return nothing if one of the lines has zero length
        if (dx1 == 0 and dy1 == 0) or (dx2 == 0 and dy2 == 0):
            return []
        
        #Possibly check needed for parallel lines (Not sure on that)
        if atan2(dy1, dx1) == atan2(dy2, dx2):
            return []
        
        #If to avoid division by zero.
        if(abs(dx2) >= abs(dy2)):
            v1 = (day - dax * dy2 / dx2) / (dx1 * dy2 / dx2 - dy1)
            #v2 = (dax + v1 * dx1) / dx2    
        else:
            v1 = (dax - day * dx2 / dy2) / (dy1 * dx2 / dy2 - dx1)
            #v2 = (day + v1 * dy1) / dy2
            
        return [PointClass(x=self.Pa.x + v1 * dx1,
                          y=self.Pa.y + v1 * dy1)]
    
    def find_inter_point_l_a(self, Arc):
        """
        Find the intersection between 2 LineGeo elements. There can be only one
        intersection between 2 lines.
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """
        Ldx = self.Pe.x - self.Pa.x
        Ldy = self.Pe.y - self.Pa.y
       
        #Mitternachtsformel zum berechnen der Nullpunkte der quadratischen 
        #Gleichung 
        a = pow(Ldx, 2) + pow(Ldy, 2)
        b = 2 * Ldx * (self.Pa.x - Arc.O.x) + 2 * Ldy * (self.Pa.y - Arc.O.y)
        c = pow(self.Pa.x - Arc.O.x, 2) + pow(self.Pa.y - Arc.O.y, 2) - pow(Arc.r, 2)
        root = pow(b, 2) - 4 * a * c
       
        #If the value under the sqrt is negative there is no intersection.
        if root < 0:
            return []

        v1 = (-b + sqrt(root)) / (2 * a)
        v2 = (-b - sqrt(root)) / (2 * a)
        
        Pi1 = PointClass(x=self.Pa.x + v1 * Ldx,
                       y=self.Pa.y + v1 * Ldy)
        
        #If the root is zero only one solution and the line is a tangent.
        if(root == 0):
            return [Pi1] 
            
        Pi2 = PointClass(x=self.Pa.x + v2 * Ldx,
                       y=self.Pa.y + v2 * Ldy)
        
        return [Pi1, Pi2]  
         
    def isTIP(self, point=PointClass, tol=0.0):
        """
        Checks if the point is on the LineGeo, therefore a true intersection
        point.
        @param other: The Point which shall be ckecke
        @return: Returns true or false
        """
        return self.BB.pointisinBB(point=point, tol=tol)
    
    def isPFIP(self, ipoint):
        """
        Checks if the Intersectionpoint is on the Positiv ray of the line.
        Therefore is a positiv false intersection point. Therefore it's just 
        needed to check if the point is nearer to Pe then to Pa
        @param ipoint: The Point which shall be ckecke
        @return: Returns true or false
        """
        return self.Pa.distance(ipoint)>self.Pe.distance(ipoint)
    
    def split_into_2geos(self, ipoint=PointClass()):
        """
        Splits the given geometry into 2 not self intersection geometries. The
        geometry will be splitted between ipoint and Pe.
        @param ipoint: The Point where the intersection occures
        @return: A list of 2 LineGeo's will be returned.
        """
        #The point where the geo shall be splitted
        spoint = PointClass(x=(ipoint.x + self.Pe.x) / 2,
                          y=(ipoint.y + self.Pe.y) / 2)
        
        Li1 = LineGeo(Pa=self.Pa, Pe=spoint)
        Li1.calc_bounding_box()
        Li2 = LineGeo(Pa=spoint, Pe=self.Pe)
        Li2.calc_bounding_box()
        
        return [Li1, Li2]
     
    def rawoffset(self, radius=10.0, direction=41):
        """
        Returns the Offset Curve defined by radius and offset direction of the 
        geometry self.
        @param radius: The offset of the curve
        @param direction: The direction of offset 41==Left 42==Right
        @return: A list of 2 LineGeo's will be returned.
        """   
        Pa, s_angle = self.get_start_end_points(0)
        Pe, e_angle = self.get_start_end_points(1)
        if direction == 41:
            offPa = Pa.get_arc_point(s_angle + 90, radius)
            offPe = Pe.get_arc_point(e_angle - 90, radius)
        elif direction == 42:
            offPa = Pa.get_arc_point(s_angle - 90, radius)
            offPe = Pe.get_arc_point(e_angle + 90, radius)
            
        offLine = LineGeo(Pa=offPa, Pe=offPe)
        offLine.calc_bounding_box()
        
        return [offLine]
    
    def trim_join(self, other, newPa, orgPe, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end point of the last geometry)
        @return: A list of geos
        """ 
        if other.type == "LineGeo":
            return self.trim_join_ll(other, newPa, tol)
        else:
            return self.trim_join_la(other, newPa, orgPe, tol)
        
            #print 'Hab ich noch nicht'
    
      
    def trim_join_ll(self, other, newPa, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end point of the last geometry)
        @return: A list of geos
        """ 
        geos = []
        
        #Find the nearest intersection point
        points = self.find_inter_points(other)
        
        #Problem??
        #if len(points)==0:
        #    return []
        
        #Case 1 according to para 3.2
        if self.Pe.isintol(other.Pa, tol):
            geos.append(LineGeo(newPa, self.Pe))
        #Case 2 according to para 3.2
        else:
            
            ipoint = self.Pe.get_nearest_point(points)
            
            isTIP1 = self.isTIP(ipoint, tol)
            isTIP2 = other.isTIP(ipoint, tol)
            
            #Case 2a according to para 3.2
            if isTIP1 and isTIP2:
                geos.append(LineGeo(newPa, ipoint))
            #Case 2b according to para 3.2
            elif not(isTIP1) and not(isTIP2):
                if self.isPFIP(ipoint):
                    geos.append(LineGeo(newPa, ipoint))
                else:
                    geos.append(LineGeo(newPa, self.Pe))
                    geos.append(LineGeo(self.Pe, other.Pa))
            #Case 2c according to para 3.2
            else:
                geos.append(LineGeo(newPa, self.Pe))
                geos.append(LineGeo(self.Pe, other.Pa))

        return geos
    
    def trim_join_la(self, other, newPa, orgPe, tol):
        """
        Returns a new geometry based on the input parameters and the self 
        geometry
        @param other: The 2nd Line Geometry
        @param Pe: The hdl to the newPa. (Trying to make the startpoint Pa 
        identical to the end point of the last geometry)
        @return: A list of geos
        """ 
        geos = []
        
        points = self.find_inter_points(other)
        
        #Case 1 according to Algorithm 2
        if len(points):
            ipoint = self.Pe.get_nearest_point(points)
            
            isTIP1 = self.isTIP(ipoint, tol)
            isTIP2 = other.isTIP(ipoint, tol)
            
            #Case 1 a
            if isTIP1 and isTIP2:
                geos.append(LineGeo(newPa, ipoint))
                
            #Case 1 b
            elif not(isTIP1) and not(isTIP2):
                direction=newPa.get_arc_direction(self.Pe,orgPe)
                r=self.Pe.distance(orgPe)
                
                geos.append(LineGeo(newPa, self.Pe))
                geos.append(ArcGeo(Pa=self.Pe,Pe=other.Pa,
                                   O=orgPe, direction=direction,
                                   r=r))
                
            #Case 1 c & d
            else:
                geos.append(LineGeo(newPa, self.Pe))
                geos.append(LineGeo(self.Pe, other.Pa))
                
        #Case 2
        else: 
            direction=newPa.get_arc_direction(self.Pe,orgPe)
            
            r=self.Pe.distance(orgPe)
            geos.append(LineGeo(newPa, self.Pe))
            geos.append(ArcGeo(Pa=self.Pe,Pe=other.Pa,
                               O=orgPe, direction=direction, 
                               r=r))
            
        return geos
    
     
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
            
