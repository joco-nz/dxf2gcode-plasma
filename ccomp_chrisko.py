# -*- coding: ISO-8859-1 -*-
from point import PointClass
from base_geometries import  LineGeo, ArcGeo 
from bounding_box import BoundingBoxClass
from shape import ShapeClass

from copy import deepcopy 
from math import sin, cos, atan2, sqrt, pow, pi, degrees

#
# based on an article of X.-Z Liu et al. /Computer in Industry 58(2007)
#
# WED 20.4.09

DEBUG = 1        
        
class ShapeOffsetClass:
    """ 
    Main Class to do the Cutter Compensation for a shape. It produces the 
    Offset curve defined by radius and direction.
    """
    def __init__(self, tol=0.01):
        """ 
        Standard method to initialize the class
        """ 
        self.tol = 0.01
        self.shape=ShapeClass()
        self.pretshape = ShapeClass()
        self.radius = 10
        self.dir = 42
        
        
    def do_compensation(self, shape=None, radius=10, direction=41):
        """ 
        Does the Cutter Compensation for the given Shape
        @param shape: The shape which shall be used for cutter correction
        @param radius: The offset to be used for correction
        @param direction: The Direction of compensation 41 for left and 42 for right
        """ 
        self.shape = shape
        self.radius = radius
        self.dir = direction
        
        #Pretreatment of the shapes to have no LSIP
        self.pretshape = self.pretreatment()
              
        rawoffshape = self.make_raw_offsett(self.pretshape)
        
        untroffshape = self.make_untrimmed_offset(rawoffshape)

        clippedshapes = self.do_clipping(untroffshape)
        
        return untroffshape
        

    def pretreatment(self):
        """ 
        The pretreatment searches for local self  intersection points (LSIP) 
        According to X.-Z LIu et al./Computers in Industry 58 (2007) 240-254
        
        If Local self intersections exist the Elements will be splitted into new
        elements at their intersection point.
        """ 

        pretshape = ShapeClass(parent=self.shape.parent,
                           cut_cor=40,
                           nr=self.shape.nr,
                           closed=self.shape.closed,
                           plotoption=1,
                           geos=[],
                           geos_hdls=[])
        
        pretshape.BB = self.shape.BB
        
        #Do for all Geometries -1 (if closed for all)
        for geo_nr in range(len(self.shape.geos)+\
                            (self.shape.closed)):
            
            if geo_nr<len(self.shape.geos):
                #New Geometry copied from pevious one:
                geo = self.shape.geos[geo_nr]
                if geo.type == "LineGeo" or geo.type == "CCLineGeo":
                    ccgeo=CCLineGeo(Pa=geo.Pa,Pe=geo.Pe)
                else:
                    ccgeo=CCArcGeo(Pa=geo.Pa,Pe=geo.Pe,
                                   O=geo.O, r=geo.r,
                                   s_ang=geo.s_ang, e_ang=geo.e_ang,
                                   direction=geo.ext)
                pretshape.geos.append(ccgeo)
                
            if geo_nr>=1:
                if not(geo_nr==len(self.shape.geos)):
                    geo1=pretshape.geos[-2]
                    geo2=pretshape.geos[-1]
                else:
                    geo1=pretshape.geos[-1]
                    geo2=pretshape.geos[0]
                
                intersect = geo1.BB.hasintersection(geo2.BB, self.tol)
                    
                if intersect:
                    points = geo1.find_inter_points(geo2, tol=self.tol)
                    #Check if the point is in tolerance with the last point of geo1
                    #If not it is a Local Self Intersecting Point per Definition 2 
                    #and the element has to be seperated into 2 elements. this will
                    #result in a not self intersecting element. 
                               
                    for point in points:
                        #There can be only one Local Self Intersection Point.
                        if geo1.isTIP(point, self.tol):
                            
                            if not(geo_nr==len(self.shape.geos)):
                                pretshape.geos.pop()
                            pretshape.geos.pop()
                            pretshape.geos += geo1.split_into_2geos(point)
                            if not(geo_nr==len(self.shape.geos)):
                                pretshape.geos += [geo2]
                                            
        return pretshape 
        

       
    def make_raw_offsett(self, pretshape):
        """ 
        Generates the raw offset curves of the pretreated shape, which has no
        local self intersections. 
        According to X.-Z LIu et al./Computers in Industry 58 (2007) 240-254
        @param pretshape: The pretreated shape with not LSIP.
        @return: Returns the raw offset shape which is not trimmed or joined.
        """ 
        
        rawoffshape = ShapeClass(parent=self.shape.parent,
                           cut_cor=40,
                           nr=self.shape.nr,
                           closed=self.shape.closed,
                           plotoption=1,
                           geos=[],
                           geos_hdls=[])
        
        rawoffshape.BB = self.shape.BB
        
        for geo in pretshape.geos:
            rawoffshape.geos+=geo.rawoffset(radius=self.radius,
                                            direction=self.dir)
            
        return rawoffshape
   
    def make_untrimmed_offset(self, rawoffshape):
        """ 
        The untrimmed offset shape is generated according to para 3.2. It 
        searches the intersection points and dependent on the type of 
        intersection it used the rules for trimming and joining.
        According to X.-Z LIu et al./Computers in Industry 58 (2007) 240-254
        @param rawoffshape: The untrimmed / unjoined offset shape
        @return: Returns the joined untrimmed offset shape.
        """  
    
        untroffshape = ShapeClass(parent=self.shape.parent,
                           cut_cor=40,
                           nr=self.shape.nr,
                           plotoption=1,
                           closed=self.shape.closed,
                           geos=[],
                           geos_hdls=[])
         
        #Return nothing if there is no geo in shape
        if len(rawoffshape.geos)==0:
            return untroffshape
        
        newPa = deepcopy(rawoffshape.geos[0].Pa)
        
        #Loop for all geometries in the shape
        for geo_nr in range(1, len(rawoffshape.geos)):
            
            geo1 = rawoffshape.geos[geo_nr - 1]
            #If the for loop is at the last geometry the first one is the 2nd
            if len(rawoffshape.geos) <= 1:
                break
            geo2 = rawoffshape.geos[geo_nr]
            
            orgPe=self.pretshape.geos[geo_nr-1].Pe
            #Call the trim join algorithms for the elements.
            untroffshape.geos += geo1.trim_join(geo2, newPa,
                                                 orgPe, -self.tol)
            
            if len(untroffshape.geos):
                newPa = untroffshape.geos[-1].Pe
               
        untroffshape.BB = untroffshape.BB
        
        #Add the last geometry Case 3 according to para 3.2
        if len(rawoffshape.geos)==1:
            untroffshape.geos.append(rawoffshape.geos[0])
            return untroffshape
        if len(untroffshape.geos)==0:
            return untroffshape
        else:
            if not(untroffshape.closed):
                if geo2.type=='CCLineGeo':
                    untroffshape.geos.append(CCLineGeo(newPa,deepcopy(geo2.Pe)))
                else:
                    untroffshape.geos.append(CCArcGeo(Pa=newPa,
                                                      Pe=deepcopy(geo2.Pe),
                                                    O=geo2.O, 
                                                    r=geo2.r,
                                                    direction=geo2.ext))
            else:
                geo1 = rawoffshape.geos[-1]
                geo2 = rawoffshape.geos[0]
                
                orgPe=self.pretshape.geos[-1].Pe
                #Call the trim join algorithms for the elements.
                untroffshape.geos += geo1.trim_join(geo2, newPa, 
                                                    orgPe, -self.tol)
                if geo2.type=='CCLineGeo':
                    untroffshape.geos[0].Pa=untroffshape.geos[-1].Pe
                else:
                    modgeo=untroffshape.geos[0]
                    modgeo.Pa=untroffshape.geos[-1].Pe
                    modgeo.s_ang = modgeo.O.norm_angle(modgeo.Pa)
                    modgeo.get_arc_extend(modgeo.ext)
                
        
        
        return untroffshape
    
    def do_clipping(self, untroffshape):
        
        clippedshape = ShapeClass(parent=self.shape.parent,
                           cut_cor=40,
                           nr=self.shape.nr,
                           closed=self.shape.closed,
                           plotoption=1,
                           geos=[],
                           geos_hdls=[])
        
        #pretshape.BB = self.shape.BB
        
        #Do for all Geometries -1 (if closed for all)
        for geo_nr1 in range(len(untroffshape.geos)):
            for geo_nr2 in range(geo_nr1+1,len(untroffshape.geos)):
                
                geo1=untroffshape.geos[geo_nr1]
                geo2=untroffshape.geos[geo_nr2]
                                             
                intersect = geo1.BB.hasintersection(geo2.BB, self.tol)
                
                if intersect:
                    points = geo1.find_inter_points(geo2)
                    
                    for point in points:
                        
                        
                        if geo1.isTIP(point, self.tol) and \
                         geo2.isTIP(point, self.tol):
                            print geo1
                            print geo2
                            print point
                            print 'ISTIP'
    
          
class CCArcGeo(ArcGeo):
    def __init__(self, Pa=None, Pe=None, O=None, r=1,
                         s_ang=None, e_ang=None, direction=1):
        """
        Standard Method to initialise the CCArcGeo
        """
            
        ArcGeo.__init__(self, Pa=Pa, Pe=Pe, O=O, r=r,
                         s_ang=s_ang, e_ang=e_ang, direction=direction)
        
        self.type = 'CCArcGeo'
        self.col = 'Blue'
        self.calc_bounding_box()
        

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\nCCArcGeo") + \
               ("\nPa : %s; s_ang: %0.5f" % (self.Pa, self.s_ang)) + \
               ("\nPe : %s; e_ang: %0.5f" % (self.Pe, self.e_ang)) + \
               ("\nO  : %s; r: %0.3f" % (self.O, self.r)) + \
               ("\nBB : %s" % self.BB) + \
               ("\next  : %0.5f; length: %0.5f" % (self.ext, self.length))

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

    def find_inter_points(self, other=[], tol=0.01):
        """
        Find the intersection between 2 geometry elements. Possible is CCLineGeo
        and CCArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """
        if other.type == "CCLineGeo":
            return other.find_inter_point_l_a(self)
        elif other.type == "CCArcGeo":
            return self.find_inter_point_a_a(other,tol=tol)
        else:
            print 'Hab ich noch nicht'
            
    
    def find_inter_point_a_a(self, other, tol=0.01):
        """
        Find the intersection between 2 CCArcGeo elements. There can be only one
        intersection between 2 lines.
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """   
        O_dis = self.O.distance(other.O)
        
        #If self circle is surrounded by the other no intersection 
        #EVENTUELL MIT TOL WIEDER????????????????????????????????????????????????
        if(O_dis < abs(self.r - other.r)-tol):
            return []

        #If other circle is surrounded by the self no intersection
        if(O_dis < abs(other.r - self.r)-tol):
            return []
        
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


    def isTIP(self, point=PointClass, tol=0.01):
        """
        Checks if the point is a Local Self Intersection Point of the CCArcGeo
        @param point: The Point which shall be checked
        @return: Returns true or false
        """
        
        if (self.Pa.isintol(point,tol) or self.Pe.isintol(point,tol)):
            if tol>0.0:
                return False
            else:
                return True
            
        else:
            #The linear tolerance in angle
            atol = tol / 2 / pi / self.r
            pang = self.O.norm_angle(point)
             
            if self.ext >= 0.0:
                return self.angle_between(self.s_ang + atol, self.e_ang - tol, pang)
            else:
                return self.angle_between(self.e_ang + atol, self.s_ang - tol, pang)
        
        
    def split_into_2geos(self, ipoint=PointClass()):
        """
        Splits the given geometry into 2 not self intersection geometries. The
        geometry will be splitted between ipoint and Pe.
        @param ipoint: The Point where the intersection occures
        @return: A list of 2 CCArcGeo's will be returned.
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
        Arc1 = CCArcGeo(Pa=self.Pa, Pe=spoint, r=self.r,
                       O=self.O, direction=self.ext)
        Arc1.calc_bounding_box()
        Arc2 = CCArcGeo(Pa=spoint, Pe=self.Pe, r=self.r,
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
              
        offArc = CCArcGeo(Pa=offPa, Pe=offPe, O=self.O, r=offr, direction=self.ext)
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
        if other.type == "CCLineGeo":
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
                geos.append(CCArcGeo(Pa=newPa, Pe=ipoint, O=self.O,
                                   r=self.r, direction= self.ext))
                
            #Case 1 b
            elif not(isTIP1) and not(isTIP2):
                direction=-other.Pe.get_arc_direction(other.Pa,orgPe)
                r=self.Pe.distance(orgPe)
                
                geos.append(CCArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
                geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
                                   O=orgPe,
                                   r=r, direction=direction))
                
            #Case 1 c & d
            else:
                geos.append(CCArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
                geos.append(CCLineGeo(self.Pe, other.Pa))
                
        #Case 2
        else: 
            direction=-other.Pe.get_arc_direction(other.Pa,orgPe)
            
            r=self.Pe.distance(orgPe)
            geos.append(CCArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
            geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
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
        points = self.find_inter_points(other, tol=abs(tol))
        
        
        #Case 1 according to Algorithm 2
        if len(points):
            ipoint = self.Pe.get_nearest_point(points)
            
            isTIP1 = self.isTIP(ipoint, tol)
            isTIP2 = other.isTIP(ipoint, tol)
            
#            print self
#            print other
#            print isTIP1
#            print isTIP2
            
            #Case 1 a
            if (isTIP1 and isTIP2) or (not(isTIP1) and not(isTIP2)):
                
                geos.append(CCArcGeo(Pa=newPa, Pe=ipoint, O=self.O,
                                   r=self.r, direction= self.ext))
                                 
            #Case 1 b
            else:
                geos.append(CCArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
                geos.append(CCLineGeo(self.Pe, other.Pa))
                
        #Case 2
        else: 
            direction=self.get_arc_direction(orgPe)
            r=self.Pe.distance(orgPe)
          
            geos.append(CCArcGeo(Pa=newPa, Pe=self.Pe, O=self.O,
                                   r=self.r, direction= self.ext))
            geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
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
    
class CCLineGeo(LineGeo):
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """ 
    def __init__(self, Pa, Pe):
        """
        Standard Method to initialise the CCLineGeo
        """
        
        LineGeo.__init__(self, Pa=Pa,Pe=Pe)
        
        self.type = "CCLineGeo"
        self.col = 'Black'
        self.calc_bounding_box()
        
    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\nCCLineGeo") + \
               ("\nPa : %s" % self.Pa) + \
               ("\nPe : %s" % self.Pe) + \
               ("\nBB : %s" % self.BB) + \
               ("\nlength: %0.5f" % self.length)   
    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        Pa = PointClass(x=min(self.Pa.x, self.Pe.x), y=min(self.Pa.y, self.Pe.y))
        Pe = PointClass(x=max(self.Pa.x, self.Pe.x), y=max(self.Pa.y, self.Pe.y))
        
        self.BB = BoundingBoxClass(Pa=Pa, Pe=Pe)
        
    def find_inter_points(self, other=[], tol=0.01):
        """
        Find the intersection between 2 geometry elements. Possible is CCLineGeo
        and CCArcGeo
        @param other: the instance of the 2nd geometry element.
        @return: a list of intersection points. 
        """
        if other.type == "CCLineGeo":
            return self.find_inter_point_l_l(other)
        elif other.type == "CCArcGeo":
            return self.find_inter_point_l_a(other)
        else:
            print 'Hab ich noch nicht'
            
    
    def find_inter_point_l_l(self, L2):
        """
        Find the intersection between 2 CCLineGeo elements. There can be only one
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
        try:
            if(abs(dx2) >= abs(dy2)):
                v1 = (day - dax * dy2 / dx2) / (dx1 * dy2 / dx2 - dy1)
                #v2 = (dax + v1 * dx1) / dx2    
            else:
                v1 = (dax - day * dx2 / dy2) / (dy1 * dx2 / dy2 - dx1)
                #v2 = (day + v1 * dy1) / dy2
        except:
            return []
            
        return [PointClass(x=self.Pa.x + v1 * dx1,
                          y=self.Pa.y + v1 * dy1)]
    
    def find_inter_point_l_a(self, Arc):
        """
        Find the intersection between 2 CCLineGeo elements. There can be only one
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
        Checks if the point is on the CCLineGeo, therefore a true intersection
        point.
        @param other: The Point which shall be ckecke
        @return: Returns true or false
        """
        if (self.Pa.isintol(point,tol) or self.Pe.isintol(point,tol)):
            if tol>0.0:
                return False
            else:
                return True
            
        else:
            return self.BB.pointisinBB(point=point, tol=abs(tol))
    
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
        @return: A list of 2 CCLineGeo's will be returned.
        """
        #The point where the geo shall be splitted
        spoint = PointClass(x=(ipoint.x + self.Pe.x) / 2,
                          y=(ipoint.y + self.Pe.y) / 2)
        
        Li1 = CCLineGeo(Pa=self.Pa, Pe=spoint)
        Li1.calc_bounding_box()
        Li2 = CCLineGeo(Pa=spoint, Pe=self.Pe)
        Li2.calc_bounding_box()
        
        return [Li1, Li2]
     
    def rawoffset(self, radius=10.0, direction=41):
        """
        Returns the Offset Curve defined by radius and offset direction of the 
        geometry self.
        @param radius: The offset of the curve
        @param direction: The direction of offset 41==Left 42==Right
        @return: A list of 2 CCLineGeo's will be returned.
        """   
        Pa, s_angle = self.get_start_end_points(0)
        Pe, e_angle = self.get_start_end_points(1)
        if direction == 41:
            offPa = Pa.get_arc_point(s_angle + 90, radius)
            offPe = Pe.get_arc_point(e_angle - 90, radius)
        elif direction == 42:
            offPa = Pa.get_arc_point(s_angle - 90, radius)
            offPe = Pe.get_arc_point(e_angle + 90, radius)
            
        offLine = CCLineGeo(Pa=offPa, Pe=offPe)
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
        if other.type == "CCLineGeo":
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
            geos.append(CCLineGeo(newPa, self.Pe))
        elif len(points)==0:
            return []
        #Case 2 according to para 3.2
        else:
            
            ipoint = self.Pe.get_nearest_point(points)
            
            isTIP1 = self.isTIP(ipoint, tol)
            isTIP2 = other.isTIP(ipoint, tol)
            
            #Case 2a according to para 3.2
            if isTIP1 and isTIP2:
                geos.append(CCLineGeo(newPa, ipoint))
            #Case 2b according to para 3.2
            elif not(isTIP1) and not(isTIP2):
                if self.isPFIP(ipoint):
                    geos.append(CCLineGeo(newPa, ipoint))
                else:
                    geos.append(CCLineGeo(newPa, self.Pe))
                    geos.append(CCLineGeo(self.Pe, other.Pa))
            #Case 2c according to para 3.2
            else:
                geos.append(CCLineGeo(newPa, self.Pe))
                geos.append(CCLineGeo(self.Pe, other.Pa))

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
                geos.append(CCLineGeo(newPa, ipoint))
                
            #Case 1 b
            elif not(isTIP1) and not(isTIP2):
                direction=newPa.get_arc_direction(self.Pe,orgPe)
                r=self.Pe.distance(orgPe)
                
                geos.append(CCLineGeo(newPa, self.Pe))
                geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
                                   O=orgPe, direction=direction,
                                   r=r))
                
            #Case 1 c & d
            else:
                geos.append(CCLineGeo(newPa, self.Pe))
                geos.append(CCLineGeo(self.Pe, other.Pa))
                
        #Case 2
        else: 
            direction=newPa.get_arc_direction(self.Pe,orgPe)
            
            r=self.Pe.distance(orgPe)
            geos.append(CCLineGeo(newPa, self.Pe))
            geos.append(CCArcGeo(Pa=self.Pe,Pe=other.Pa,
                               O=orgPe, direction=direction, 
                               r=r))
            
        return geos
