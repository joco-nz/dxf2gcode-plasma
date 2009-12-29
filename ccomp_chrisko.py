# -*- coding: ISO-8859-1 -*-
from point import PointClass
from base_geometries import  LineGeo, ArcGeo 
from shape import ShapeClass

from copy import deepcopy 
from math import sin, cos, atan2, sqrt, pow, pi

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
                           plotoption=1,
                           geos=[],
                           geos_hdls=[])
        
        pretshape.BB = self.shape.BB
        
        #Loop for all geometries in the shape
        for geo_nr in range(1, len(self.shape.geos)):
            geo1 = self.shape.geos[geo_nr - 1]
            
            #If the for loop is at the last geometry the first one is the 2nd
            if len(self.shape.geos) <= 1:
                break
            
            geo2 = self.shape.geos[geo_nr]
            
            #Check if the Bounding Box of geo1 has an intersection with BB of 
            #geo2
            intersect = geo1.BB.hasintersection(geo2.BB, self.tol)
            
            if intersect:
                points = geo1.find_inter_points(geo2)

                
                #Check if the point is in tolerance with the last point of geo1
                #If not it is a Local Self Intersecting Point per Definition 2 
                #and the element has to be seperated into 2 elements. this will
                #result in a not self intersecting element. 
                
                added = 0
                
                for point in points:
                    print point
                    #There can be only one Local Self Intersection Point.
                    if geo1.isTIP(point, self.tol):
                        pretshape.geos += geo1.split_into_2geos(point)
                        added = 1
                
                if not(added):
                    pretshape.geos.append(geo1)
                    
                        
            else:
                pretshape.geos.append(geo1)
                
                    
        #Add the last geometry
        if len(self.shape.geos) > 1:           
            pretshape.geos.append(geo2)
        else:
            pretshape.geos.append(self.shape.geos[0])
        
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
            untroffshape.geos += geo1.trim_join(geo2, newPa, orgPe, self.tol)
            newPa = untroffshape.geos[-1].Pe
               
        untroffshape.BB = untroffshape.BB
        
        #Add the last geometry Case 3 according to para 3.2
        if len(rawoffshape.geos) > 1:
            if geo2.type=='LineGeo':
                untroffshape.geos.append(LineGeo(newPa,deepcopy(geo2.Pe)))
            else:
                untroffshape.geos.append(ArcGeo(Pa=newPa,Pe=deepcopy(geo2.Pe),
                                                O=geo2.O, 
                                                r=geo2.r,
                                                direction=geo2.ext))
        else:
            untroffshape.geos.append(rawoffshape.geos[0])
        
        return untroffshape
    
    
    
          


