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
        self.pretshape = ShapeClass()
        self.radius = 10
        self.dir = 41
        
        
    def do_compensation(self, shape=None, radius=2, direction=41):
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
        pretshape = self.pretreatment()
              
        rawoffshape = self.make_raw_offsett(pretshape)
        
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
            rawoffshape.geos.append(geo.rawoffset(radius=self.radius,
                                                  direction=self.dir))
            
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
        
        newPa = deepcopy(rawoffshape.geos[0].Pa)
        
        #Loop for all geometries in the shape
        for geo_nr in range(1, len(rawoffshape.geos)):
            
            geo1 = rawoffshape.geos[geo_nr - 1]
            #If the for loop is at the last geometry the first one is the 2nd
            if len(rawoffshape.geos) <= 1:
                break
            geo2 = rawoffshape.geos[geo_nr]
            
            #Call the trim join algorithems for the elements.
            untroffshape.geos += geo1.trim_join(geo2, newPa, self.tol)
            newPa = untroffshape.geos[-1].Pe
               
        untroffshape.BB = untroffshape.BB
        
        #Add the last geometry Case 3 according to para 3.2
        if len(self.shape.geos) > 1:
            if geo2.type=='LineGeo':
                untroffshape.geos.append(LineGeo(newPa,deepcopy(geo2.Pe)))
            else:
                print 'hab ich noch nicht'
        else:
            untroffshape.geos.append(self.shape.geos[0])
        
        return untroffshape
    
    
    
             

#    def compsteplines(self,inshape):
#        print('----------------')
#        print('combine segments')
#        print('----------------')
#        
#        
#        ccshape=ShapeClass()
#        
#        num_elements=len(inshape.geos)
#        pos=0;   
#        pnew=0 
#     
#        while pos<num_elements:
#            ccshape.geos.append(inshape.geos[pos])
#            pos+=1
#        pos=0
#        
#        ccshape.r=inshape.r
#        # # WED hier die Unterscheidung zwischen geschlossenen und nicht geschlossenen Kurven einfügen
#        #if inshape.closed==0:
#        #num_elements+=1
#        #ccshape.geos.append(inshape.geos[0])
#      
#        while pos<num_elements:    
#            npos=pos+1
#            if(npos>=num_elements):
#                npos=0
#            print('#',len(ccshape.geos),pos,npos,num_elements)
#            # ------------ line / line --------------
#            if(ccshape.geos[pos].type=='LineGeo' and ccshape.geos[npos].type=='LineGeo'):
#                self.CheckIntersectLineLine(ccshape.geos[pos],ccshape.geos[npos])
#                if(self.num>0):
#                    print('Step1:line/line intersect', self.ISPstatus1a, self.ISPstatus1b)
#                    if(self.ISPstatus1a=='above' and self.ISPstatus1b=='under'):
#                        print('found above/under')
#                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1)
#                        ccshape.geos[npos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe)
#                        ccshape.geos[pos].col='Blue'
#                       
#                    if(self.ISPstatus1a=='under' and self.ISPstatus1b=='above'):
#                        print('found under/above')
#                        ccshape.geos[pos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[pos].Pe)
#                        ccshape.geos[npos]=LineGeo(Pa=ccshape.geos[npos].Pa, Pe=self.P1)
#                        ccshape.geos[pos].col='Blue'
#                       
#                    if(self.ISPstatus1a=='between' and self.ISPstatus1b=='between'):
#                        print('found between/between')
#                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1)
#                        ccshape.geos[npos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe)
#                        ccshape.geos[pos].col='Blue'
#                        print('1')
#                        
#                    if(self.ISPstatus1a=='between' and self.ISPstatus1b=='at_start'):
#                        print('found between/at_start')
#                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1)
#                        ccshape.geos[npos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe)
#                        ccshape.geos[pos].col='Blue'
#                        
#                    if(self.ISPstatus1a=='between' and (self.ISPstatus1b=='above' or self.ISPstatus1b=='under')):
#                        print('found between/above')
#                        ccshape.geos.insert(npos,LineGeo(Pa=ccshape.geos[pos].Pe, Pe=ccshape.geos[npos].Pa) )
#                        ccshape.geos[pos].col='Blue'
#                        ccshape.geos[npos].col='Blue'
#                        pos+=1
#                        num_elements+=1
#                    if(self.ISPstatus1b=='between' and (self.ISPstatus1a=='above' or self.ISPstatus1a=='under')):       
#                        print('found between/above')
#                        ccshape.geos.insert(npos,LineGeo(Pa=ccshape.geos[pos].Pe, Pe=ccshape.geos[npos].Pa) )
#                        ccshape.geos[pos].col='Blue'
#                        ccshape.geos[npos].col='Blue'
#                        pos+=1
#                        num_elements+=1
#            # ------------- line / arc -------------------           
#            elif(ccshape.geos[pos].type=='LineGeo' and ccshape.geos[npos].type=='ArcGeo'):
#                self.CheckIntersectLineArc(ccshape.geos[pos],ccshape.geos[npos])
#                if self.num==0:
#                    print('found LineArc none')
#                    Pa=ccshape.geos[pos].Pe
#                    Pe=ccshape.geos[npos].Pa
#                    r=ccshape.r
#                    dir=ccshape.geos[npos]
#                    ccshape.geos.insert(npos, ArcGeo(Pa=ccshape.geos[pos].Pe, Pe=ccshape.geos[npos].Pa, r=r, dir=dir))
#                    ccshape.geos[pos].col='Blue'
#                    ccshape.geos[npos].col='Blue'
#                    pos+=1
#                    num_elements+=1
#                else:
#                    print('Step1:line/arc intersect', self.ISPstatus1a, self.ISPstatus1b,self.ISPstatus2a, self.ISPstatus2b)
#                    bw=0
#                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_start' or self.ISPstatus1a=='at_end') and (self.ISPstatus1b=='between' or self.ISPstatus1b=='at_start' or self.ISPstatus1b=='at_end')):
#                        print('found LineArc between/between')
#                        bw=1
#                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1)
#                        ccshape.geos[npos]=ArcGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r, dir=ccshape.geos[npos].ext)
#                        ccshape.geos[pos].col='Blue'
#                      
#                    if(bw==0 and (self.ISPstatus2a=='between' or self.ISPstatus2a=='at_start' or self.ISPstatus2a=='at_end') and (self.ISPstatus2b=='between' or self.ISPstatus2b=='at_start' or self.ISPstatus2b=='at_end')):
#                        print('found LineArc between/between')
#                        bw=1
#                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P2)
#                        ccshape.geos[npos]=ArcGeo(Pa=self.P2, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
#                        ccshape.geos[pos].col='Blue'
#                        
#                    if((self.ISPstatus1a=='above') and (self.ISPstatus1b=='under')and (bw==0)):
#                        print('found LineArc above/under')
#                        bw=1
#                        Pa=ccshape.geos[pos].Pa
#                        Pe=self.P1
#                        ccshape.geos[pos]=LineGeo(Pa=Pa, Pe=Pe)
#                        rn=ccshape.geos[npos].r
#                        dirn=ccshape.geos[npos].ext
#                        Pen=ccshape.geos[npos].Pe
#                        Pan=self.P1
#                        ccshape.geos[npos]=ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=dirn)
#                        ccshape.geos[pos].col='Blue'
#                       
#                        
#                    if((self.ISPstatus2a=='above') and (self.ISPstatus2b=='under')and (bw==0)):
#                        print('found LineArc above/under')
#                        bw=1
#                        Pa=ccshape.geos[pos].Pa
#                        Pe=self.P2
#                        ccshape.geos[pos]=LineGeo(Pa=Pa, Pe=Pe)
#                        rn=ccshape.geos[npos].r
#                        dirn=ccshape.geos[npos].ext
#                        Pen=ccshape.geos[npos].Pe
#                        Pan=self.P2
#                        ccshape.geos[npos]=ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=dirn)
#                        ccshape.geos[pos].col='Blue'
#                        
#                    if((self.ISPstatus1a=='above' and self.ISPstatus1b=='between')or (self.ISPstatus2a=='above' and self.ISPstatus2b=='between')and (bw==0)):
#                        print('found LineArc above/between')
#                        bw=1
#                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1)
#                        ccshape.geos[npos]=ArcGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r, dir=ccshape.geos[npos].ext)
#                        #ccshape.geos.insert(npos, LineGeo(Pa=ccshape.geos[pos].Pa, Pe=ccshape.geos[npos].Pa))
#                        ccshape.geos[pos].col='Blue'
#                        ccshape.geos[npos].col='Blue'
#                        
#                        
#                   # if((self.ISPstatus1a=='between' and ( self.ISPstatus1b=='above' or self.ISPstatus1b=='under' ))or (self.ISPstatus2a=='above' and ( self.ISPstatus2b=='above' or self.ISPstatus2b=='under' ))):
#                    #    print('found LineArc bw/ab-un')
#                    #    ccshape.geos.insert(npos, LineGeo(Pa=ccshape.geos[pos].Pa, Pe=ccshape.geos[npos].Pa))
#                    #    ccshape.geos[pos].col='Blue'
#                    #    ccshape.geos[npos].col='Blue'
#                    #    pos+=1
#                    #    num_elements+=1
#                        
#            
#            # ------------- arc / line -------------------           
#            elif(ccshape.geos[pos].type=='ArcGeo' and ccshape.geos[npos].type=='LineGeo'):
#                self.CheckIntersectArcLine(ccshape.geos[pos],ccshape.geos[npos])
#                if self.num==0:
#                    print('found Arc/Line none')
#                    Pa=ccshape.geos[pos].Pe
#                    Pe=ccshape.geos[npos].Pa
#                    r=ccshape.r
#                    dir=ccshape.geos[pos]
#                    ccshape.geos.insert(npos, ArcGeo(Pa=ccshape.geos[pos].Pe, Pe=ccshape.geos[npos].Pa, r=r, dir=dir))
#                    ccshape.geos[pos].col='Blue'
#                    ccshape.geos[npos].col='Blue'
#                    pos+=1
#                    num_elements+=1
#                else:
#                    bw=0
#                    print('Step1:arc/line intersect', self.ISPstatus1a, self.ISPstatus1b,self.ISPstatus2a, self.ISPstatus2b)
#                    bw=0
#                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_start' or self.ISPstatus1a=='at_end') and (self.ISPstatus1b=='between' or self.ISPstatus1b=='at_start' or self.ISPstatus1b=='at_end')and (bw==0)):
#                        print('found arc/line between/between')
#                        bw=1
#                                             
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1, r=ccshape.geos[pos].r,dir=ccshape.geos[pos].ext)
#                        ccshape.geos[npos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe)
#                        ccshape.geos[pos].col='Blue'
#                      
#                    if((self.ISPstatus2a=='between' or self.ISPstatus2a=='at_start' or self.ISPstatus2a=='at_end') and (self.ISPstatus2b=='between' or self.ISPstatus2b=='at_start' or self.ISPstatus2b=='at_end')and (bw==0)):
#                        print('found arc/line between/between')
#                        bw=1                      
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P2, r=ccshape.geos[pos].r,dir=ccshape.geos[pos].ext)
#                        ccshape.geos[npos]=LineGeo(Pa=self.P2, Pe=ccshape.geos[npos].Pe)
#                        ccshape.geos[pos].col='Blue'
#                        
#                    if((self.ISPstatus1a=='above') and (self.ISPstatus1b=='under') and (bw==0)):
#                        print('found arc/line above/under')
#                        bw=1
#                        Pen=self.P1
#                        rn=ccshape.geos[pos].r
#                        dirn=ccshape.geos[pos].ext
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=Pen, r=rn, dir=dirn)
#                        ccshape.geos[npos]=LineGeo(Pa=Pen, Pe=ccshape.geos[npos].Pe)
#                        ccshape.geos[pos].col='Blue'
#                       
#                        
#                    if((self.ISPstatus2a=='above') and (self.ISPstatus2b=='under')and (bw==0)):
#                        print('found arc/line above/under')
#                        bw=1
#                        Pen=self.P2
#                        rn=ccshape.geos[pos].r
#                        dirn=ccshape.geos[pos].ext
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=Pen, r=rn, dir=dirn)
#                        ccshape.geos[npos]=LineGeo(Pa=Pen, Pe=ccshape.geos[npos].Pe)
#                        ccshape.geos[pos].col='Blue'
#                        
#                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_end') and self.ISPstatus1b=='under'and (bw==0)):
#                        print('found arc/line between/under')
#                        bw=1
#                        
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1, r=ccshape.geos[pos].r, dir=ccshape.geos[pos].ext)
#                        ccshape.geos[npos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe)
#                        ccshape.geos[pos].col='Blue'
#                    if((self.ISPstatus2a=='between' or self.ISPstatus1a=='at_end') and self.ISPstatus2b=='under'and (bw==0)):
#                        print('found arc/line between/under')
#                        bw=1
#                        
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P2, r=ccshape.geos[pos].r, dir=ccshape.geos[pos].ext)
#                        ccshape.geos[npos]=LineGeo(Pa=self.P2, Pe=ccshape.geos[npos].Pe)
#                        ccshape.geos[pos].col='Blue'
#                        
#                        
#                   # if((self.ISPstatus1a=='between' and ( self.ISPstatus1b=='above' or self.ISPstatus1b=='under' ))or (self.ISPstatus2a=='above' and ( self.ISPstatus2b=='above' or self.ISPstatus2b=='under' ))):
#                    #    print('found LineArc bw/ab-un')
#                    #    ccshape.geos.insert(npos, LineGeo(Pa=ccshape.geos[pos].Pa, Pe=ccshape.geos[npos].Pa))
#                    #    ccshape.geos[pos].col='Blue'
#                    #    ccshape.geos[npos].col='Blue'
#                    #    pos+=1
#                    #    num_elements+=1
#               # ------------- arc / arc -------------------           
#            elif(ccshape.geos[pos].type=='ArcGeo' and ccshape.geos[npos].type=='ArcGeo'):
#                self.CheckIntersectArcArc(ccshape.geos[pos],ccshape.geos[npos])
#                if self.num==0:
#                    print('found Arc/Arc none')
#                    Pa=ccshape.geos[pos].Pe
#                    Pe=ccshape.geos[npos].Pa
#                    r=ccshape.r
#                    dir=ccshape.geos[npos]
#                    ccshape.geos.insert(npos, ArcGeo(Pa=ccshape.geos[pos].Pe, Pe=ccshape.geos[npos].Pa, r=r, dir=dir))
#                    ccshape.geos[pos].col='Blue'
#                    ccshape.geos[npos].col='Blue'
#                    pos+=1
#                    num_elements+=1
#                else:
#                    bw=0
#                    print('Step1:arc/arc intersect', self.ISPstatus1a, self.ISPstatus1b,self.ISPstatus2a, self.ISPstatus2b)
#                    bw=0
#                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_start' or self.ISPstatus1a=='at_end') and (self.ISPstatus1b=='between' or self.ISPstatus1b=='at_start' or self.ISPstatus1b=='at_end')and (bw==0)):
#                        print('found arc/arc between/between')
#                        bw=1
#                                             
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1, r=ccshape.geos[pos].r,dir=ccshape.geos[pos].ext)
#                        ccshape.geos[npos]=ArcGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
#                        ccshape.geos[pos].col='Blue'
#                      
#                    if((self.ISPstatus2a=='between' or self.ISPstatus2a=='at_start' or self.ISPstatus2a=='at_end') and (self.ISPstatus2b=='between' or self.ISPstatus2b=='at_start' or self.ISPstatus2b=='at_end')and (bw==0)):
#                        print('found arc/arc between/between')
#                        bw=1                      
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P2, r=ccshape.geos[pos].r,dir=ccshape.geos[pos].ext)
#                        ccshape.geos[npos]=ArcGeo(Pa=self.P2, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
#                        ccshape.geos[pos].col='Blue'
#                        
#                    if((self.ISPstatus1a=='above') and (self.ISPstatus1b=='under') and (bw==0)):
#                        print('found arc/arc above/under')
#                        bw=1
#                        Pen=self.P1
#                        rn=ccshape.geos[pos].r
#                        dirn=ccshape.geos[pos].ext
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=Pen, r=rn, dir=dirn)
#                        ccshape.geos[npos]=ArcGeo(Pa=Pen, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
#                        ccshape.geos[pos].col='Blue'
#                       
#                        
#                    if((self.ISPstatus2a=='above') and (self.ISPstatus2b=='under')and (bw==0)):
#                        print('found arc/arc above/under')
#                        bw=1
#                        Pen=self.P2
#                        rn=ccshape.geos[pos].r
#                        dirn=ccshape.geos[pos].ext
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=Pen, r=rn, dir=dirn)
#                        ccshape.geos[npos]=ArcGeo(Pa=Pen, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
#                        ccshape.geos[pos].col='Blue'
#                        
#                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_end') and self.ISPstatus1b=='under'and (bw==0)):
#                        print('found arc/arc between/under')
#                        bw=1
#                        
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1, r=ccshape.geos[pos].r, dir=ccshape.geos[pos].ext)
#                        ccshape.geos[npos]=ArcGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
#                        ccshape.geos[pos].col='Blue'
#                    if((self.ISPstatus2a=='between' or self.ISPstatus1a=='at_end') and self.ISPstatus2b=='under'and (bw==0)):
#                        print('found arc/arc between/under')
#                        bw=1
#                        
#                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P2, r=ccshape.geos[pos].r, dir=ccshape.geos[pos].ext)
#                        ccshape.geos[npos]=ArcGeo(Pa=self.P2, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
#                        ccshape.geos[pos].col='Blue'
#                        
#                        
#                   # if((self.ISPstatus1a=='between' and ( self.ISPstatus1b=='above' or self.ISPstatus1b=='under' ))or (self.ISPstatus2a=='above' and ( self.ISPstatus2b=='above' or self.ISPstatus2b=='under' ))):
#                    #    print('found LineArc bw/ab-un')
#                    #    ccshape.geos.insert(npos, LineGeo(Pa=ccshape.geos[pos].Pa, Pe=ccshape.geos[npos].Pa))
#                    #    ccshape.geos[pos].col='Blue'
#                    #    ccshape.geos[npos].col='Blue'
#                    #    pos+=1
#                    #    num_elements+=1
#                                 
#            pos+=1
#        print('2')
#        ccshape.geos[0]=ccshape.geos[npos]
#        print('3')
#        print(len(ccshape.geos))
#        ccshape.geos[0].col='Yellow'
#        return (ccshape)

#
