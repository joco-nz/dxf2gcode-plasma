# -*- coding: ISO-8859-1 -*-
from point import PointClass, ArcGeo, LineGeo,floor ,ceil
from shape import ShapeClass
from copy import deepcopy 

from math import sin,cos,  atan2, sqrt, pow,pi

#
# based on an article of X.-Z Liu et al. /Computer in Industry 58(2007)
#
# WED 20.4.09

debug_mode=1        
        
class InterSectionPoint:
    def __init__(self):

        self.num=0
        self.P1=PointClass(0.0,0.0)
        self.P2=PointClass(0.0,0.0)
        self.v1=0.0
        self.v2=0.0
        self.arc1=0.0
        self.arc2=0.0
        self.P1_ext_a=0.0
        self.P2_ext_a=0.0
        self.P1_ext_b=0.0
        self.P2_ext_b=0.0
        
        self.ISPtype1a='none'
        self.ISPstatus1a='none'
        self.ISPtype2a='none'
        self.ISPstatus2a='none'
        self.ISPtype1b='none'
        self.ISPstatus1b='none'
        self.ISPtype2b='none'
        self.ISPstatus2b='none'

    def show(self,shape):
        print ('Anzahl der Elemente',len(shape.geos))
        print('Kurventyp', shape.closed)
        for pos in range (len(shape.geos)):
            print(pos,shape.geos[pos].type)
        
        print ('\ntype:        %s' %shape.type)+\
               ('\nnr:          %s' %shape.nr)+\
               ('\nclosed:      %s' %shape.closed)+\
               ('\ncut_cor:     %s' %shape.cut_cor)+\
               ('\ngeos:        %s' %shape.geos)
        return
    def do_compensation(self, shape, radius, dir):

        inshape=self.CorNextInterSect(shape)
        inshape.cut_cor=dir
        #ccshape=self.GenRawCompData(inshape,radius)
        #self.show(ccshape)

        #print ccshape
        #ccshape=self.compsteplines(ccshape)
        #return(ccshape)
        return(inshape)
#--------------------------------------------------------------------------------------------------------------------------------
# adds additional segment if seg n intersects with seg n+1
#--------------------------------------------------------------------------------------------------------------------------------
    def CorNextInterSect(self, shape):
        print('----------------')
        print('postprocessing')
        print('----------------')
        
        inshape=ShapeClass(parent=shape.parent,
                           cut_cor=40,
                           nr=shape.nr,
                           plotoption=1)

        print('closed parent shape')
            
        pos=0;  
        while pos<len(shape.geos):
            npos=pos+1
            if(npos>=len(shape.geos)):
                npos=0
            if(shape.geos[pos].type=="LineGeo" and shape.geos[npos].type=="LineGeo"):
                self.CheckIntersectLineLine(shape.geos[pos], shape.geos[npos])
                inshape.geos.append(LineGeo(shape.geos[pos].Pa,shape.geos[pos].Pe))
                if(self.num>1):
                    print("ERROR Line/Line Intersect with 2 ponts is not possible")
            elif(shape.geos[pos].type=="LineGeo" and shape.geos[npos].type=="ArcGeo"):
                
                self.CheckIntersectLineArc(shape.geos[pos], shape.geos[npos])
                if(self.num>1):
                    
                   
                    v=PointClass(0.0, 0.0)
                    if(self.ISPstatus1a=='between' and self.ISPstatus1b=='between'):
                        if(self.v1>0 and self.v1<1):
                            v=(shape.geos[pos].Pe-shape.geos[pos].Pa)
                            nv=(self.v1+1)/2 
                    elif(self.ISPstatus2a=='between' and self.ISPstatus2b=='between' ):
                        
                        print("found intersect Line Arc, inserting additional Line")
                        if(self.v2>0 and self.v2<1):
                            v=(shape.geos[pos].Pe-shape.geos[pos].Pa)
                            nv=(self.v1+1)/2
                   
                    if((pow(v.x, 2)+pow(v.y, 2))>0):
                    
                        Pen=PointClass(0.0, 0.0)
                        Pen.x=shape.geos[pos].Pa.x+v.x*nv
                        Pen.y=shape.geos[pos].Pa.y+v.y*nv
                        inshape.geos.append(LineGeo(shape.geos[pos].Pa, Pen))
                        inshape.geos[-1].col='Black'
                        inshape.geos.append(LineGeo(Pen, shape.geos[pos].Pe))
                        inshape.geos[-1].col='Red'
                    else:
                       
                        inshape.geos.append(LineGeo(shape.geos[pos].Pa, shape.geos[pos].Pe))
                        inshape.geos[-1].col='Black'
                      
                else:
                    inshape.geos.append(LineGeo(shape.geos[pos].Pa, shape.geos[pos].Pe))
                    inshape.geos[-1].col='Black' 
                 
                    
            elif(shape.geos[pos].type=="ArcGeo" and shape.geos[npos].type=="ArcGeo"):
                self.CheckIntersectArcArc(shape.geos[pos], shape.geos[npos])
               
                delta=0
                if(self.ISPstatus1a=='between' and self.ISPstatus1b=='between' ):
                    print("found intersect Arc  Arc, inserting additional Arc")
                    delta=self.P1_ext_a/shape.geos[pos].ext
                elif(self.ISPstatus2a=='between' and self.ISPstatus2b=='between' ):
                    print("found intersect Arc  Arc, inserting additional Arc")
                    delta=self.P2_ext_a/shape.geos[pos].ext
                
              
                if(delta>0 and delta<1):
                    delta=delta*0.5
                    arc=shape.geos[pos].s_ang+delta*shape.geos[pos].ext
                   
                    Pen=PointClass(0.0, 0.0)
                    Pen.y=shape.geos[pos].r*sin(arc)+shape.geos[pos].O.y
                    Pen.x=shape.geos[pos].r*cos(arc)+shape.geos[pos].O.x
                  
                    inshape.geos.append(ArcGeo(Pa=shape.geos[pos].Pa,Pe=Pen,r=shape.geos[pos].r,s_ang=shape.geos[pos].s_ang, e_ang=arc, dir=shape.geos[pos].ext, O=shape.geos[pos].O))
                    inshape.geos[-1].col='Black'
                    inshape.geos.append(ArcGeo(Pa=Pen,Pe=shape.geos[pos].Pe,r=shape.geos[pos].r,s_ang=arc, e_ang=shape.geos[pos].e_ang, dir=shape.geos[pos].ext, O=shape.geos[pos].O))
                    inshape.geos[-1].col='Red'
                else:
                    inshape.geos.append(ArcGeo(Pa=shape.geos[pos].Pa,Pe=shape.geos[pos].Pe,r=shape.geos[pos].r,s_ang=shape.geos[pos].s_ang, e_ang=shape.geos[pos].e_ang, dir=shape.geos[pos].ext, O=shape.geos[pos].O))
                    inshape.geos[-1].col='Black'
                 
                
            elif(shape.geos[pos].type=="ArcGeo" and shape.geos[npos].type=="LineGeo"):
                
                self.CheckIntersectArcLine(shape.geos[pos], shape.geos[npos])
                delta=0
                if(self.ISPstatus1a=='between' and self.ISPstatus1b=='between' ):
                    print("found intersect Arc  line, inserting additional Arc")
                    delta=self.P1_ext_a/shape.geos[pos].ext
                elif(self.ISPstatus2a=='between' and self.ISPstatus2b=='between' ):
                    print("found intersect Arc  line, inserting additional Arc")
                    delta=self.P2_ext_a/shape.geos[pos].ext
               
                
                
                if(delta>0 and delta<1):
                    #delta=delta*0.5 Correction according Michael
                    delta=(1+delta)/2

                    arc=shape.geos[pos].s_ang+delta*shape.geos[pos].ext
                    Pen=PointClass(0.0, 0.0)
                    Pen.y=shape.geos[pos].r*sin(arc)+shape.geos[pos].O.y
                    Pen.x=shape.geos[pos].r*cos(arc)+shape.geos[pos].O.x
                    inshape.geos.append(ArcGeo(Pa=shape.geos[pos].Pa,Pe=Pen,r=shape.geos[pos].r,s_ang=shape.geos[pos].s_ang, e_ang=arc, dir=shape.geos[pos].ext, O=shape.geos[pos].O))
                    inshape.geos[-1].col='Black'
                    inshape.geos.append(ArcGeo(Pa=Pen,Pe=shape.geos[pos].Pe,r=shape.geos[pos].r,s_ang=arc, e_ang=shape.geos[pos].e_ang, dir=shape.geos[pos].ext, O=shape.geos[pos].O))
                    inshape.geos[-1].col='Red'
                else:
                    inshape.geos.append(ArcGeo(Pa=shape.geos[pos].Pa,Pe=shape.geos[pos].Pe,r=shape.geos[pos].r,s_ang=shape.geos[pos].s_ang, e_ang=shape.geos[pos].e_ang, dir=shape.geos[pos].ext, O=shape.geos[pos].O))
                    inshape.geos[-1].col='Black'
                   
            pos+=1
        
       
        return (inshape)
      
    
#---------------------------------------------------------------------------------------------
# generate raw Compensation data
#---------------------------------------------------------------------------------------------

    def GenRawCompData(self,inshape,radius):
        print('----------------')
        print('generate segments')
        print('----------------')
        ccshape=ShapeClass(parent=inshape.parent,
                           cut_cor=40,
                           nr=inshape.nr,
                           plotoption=inshape.plotoption)
        ccshape.r=radius
        num_elements=len(inshape.geos)
        pos=0   
        pnew=0 
        
        while pos<num_elements:
            
            if(inshape.geos[pos].type=='LineGeo'):
                if(inshape.cut_cor!=41):
                    Pan=inshape.geos[pos].Pa
                    Pen=inshape.geos[pos].Pe
                    Pan.x-=inshape.geos[pos].nva.x*radius
                    Pan.y-=inshape.geos[pos].nva.y*radius
                    Pen.x-=inshape.geos[pos].nve.x*radius
                    Pen.y-=inshape.geos[pos].nve.y*radius
                 
                else:
                    
                    Pan=inshape.geos[pos].Pa
                    Pen=inshape.geos[pos].Pe
                    Pan.x+=inshape.geos[pos].nva.x*radius
                    Pan.y+=inshape.geos[pos].nva.y*radius
                    Pen.x+=inshape.geos[pos].nve.x*radius
                    Pen.y+=inshape.geos[pos].nve.y*radius
                ccshape.geos.append(LineGeo(Pa=Pan, Pe=Pen)) 
                ccshape.geos[-1].col='Green'
              
            elif(inshape.geos[pos].type=='ArcGeo'): 
                o=inshape.geos[pos].O
                s_ang=inshape.geos[pos].s_ang
                e_ang=inshape.geos[pos].e_ang
                if(inshape.cut_cor!=41):
                    if(inshape.geos[pos].ext<0):
                        rn=inshape.geos[pos].r+radius
                        Pan=inshape.geos[pos].Pa
                        Pen=inshape.geos[pos].Pe
                        Pan.y+=sin(s_ang)*radius
                        Pan.x+=cos(s_ang)*radius
                        Pen.y+=sin(e_ang)*radius
                        Pen.x+=cos(e_ang)*radius
                        ext=inshape.geos[pos].ext
                        ccshape.geos.append(ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=ext))
                        ccshape.geos[-1].col='Green'
                      
                    else:
                        r=inshape.geos[pos].r
                        if(r>=radius):
                            rn=inshape.geos[pos].r-radius
                            Pan=inshape.geos[pos].Pa
                            Pen=inshape.geos[pos].Pe
                            Pan.y-=sin(s_ang)*radius
                            Pan.x-=cos(s_ang)*radius
                            Pen.y-=sin(e_ang)*radius
                            Pen.x-=cos(e_ang)*radius
                            ext=inshape.geos[pos].ext
                            ccshape.geos.append(ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=ext, s_ang=s_ang, e_ang=e_ang, O=o))
                            ccshape.geos[-1].col='Green'
                          
                        else:
                            pass
                else:
                    if(inshape.geos[pos].ext>0):
                        rn=inshape.geos[pos].r+radius
                        Pan=inshape.geos[pos].Pa
                        Pen=inshape.geos[pos].Pe
                        Pan.y+=sin(s_ang)*radius
                        Pan.x+=cos(s_ang)*radius
                        Pen.y+=sin(e_ang)*radius
                        Pen.x+=cos(e_ang)*radius
                        ext=inshape.geos[pos].ext
                        ccshape.geos.append(ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=ext, s_ang=s_ang, e_ang=e_ang, O=o))
                        ccshape.geos[-1].col='Green'
                      
                    else:
                        r=inshape.geos[pos].r
                        if(r>=radius):
                            rn=inshape.geos[pos].r-radius
                            Pan=inshape.geos[pos].Pa
                            Pen=inshape.geos[pos].Pe
                            Pan.y-=sin(s_ang)*radius
                            Pan.x-=cos(s_ang)*radius
                            Pen.y-=sin(e_ang)*radius
                            Pen.x-=cos(e_ang)*radius
                            ext=inshape.geos[pos].ext
                            ccshape.geos.append(ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=ext, s_ang=s_ang, e_ang=e_ang, O=o))
                            ccshape.geos[-1].col='Green'
                           
                        else:
                            pass
                
                        
            pos+=1
        return (ccshape)
        
#---------------------------------------------------------------------------------------------
# handle lines Step1
#---------------------------------------------------------------------------------------------

    def compsteplines(self,inshape):
        print('----------------')
        print('combine segments')
        print('----------------')
        
        
        ccshape=ShapeClass()
        
        num_elements=len(inshape.geos)
        pos=0;   
        pnew=0 
     
        while pos<num_elements:
            ccshape.geos.append(inshape.geos[pos])
            pos+=1
        pos=0
        
        ccshape.r=inshape.r
        # # WED hier die Unterscheidung zwischen geschlossenen und nicht geschlossenen Kurven einfügen
        #if inshape.closed==0:
        #num_elements+=1
        #ccshape.geos.append(inshape.geos[0])
      
        while pos<num_elements:    
            npos=pos+1
            if(npos>=num_elements):
                npos=0
            print('#',len(ccshape.geos),pos,npos,num_elements)
            # ------------ line / line --------------
            if(ccshape.geos[pos].type=='LineGeo' and ccshape.geos[npos].type=='LineGeo'):
                self.CheckIntersectLineLine(ccshape.geos[pos],ccshape.geos[npos])
                if(self.num>0):
                    print('Step1:line/line intersect', self.ISPstatus1a, self.ISPstatus1b)
                    if(self.ISPstatus1a=='above' and self.ISPstatus1b=='under'):
                        print('found above/under')
                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1)
                        ccshape.geos[npos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe)
                        ccshape.geos[pos].col='Blue'
                       
                    if(self.ISPstatus1a=='under' and self.ISPstatus1b=='above'):
                        print('found under/above')
                        ccshape.geos[pos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[pos].Pe)
                        ccshape.geos[npos]=LineGeo(Pa=ccshape.geos[npos].Pa, Pe=self.P1)
                        ccshape.geos[pos].col='Blue'
                       
                    if(self.ISPstatus1a=='between' and self.ISPstatus1b=='between'):
                        print('found between/between')
                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1)
                        ccshape.geos[npos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe)
                        ccshape.geos[pos].col='Blue'
                        print('1')
                        
                    if(self.ISPstatus1a=='between' and self.ISPstatus1b=='at_start'):
                        print('found between/at_start')
                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1)
                        ccshape.geos[npos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe)
                        ccshape.geos[pos].col='Blue'
                        
                    if(self.ISPstatus1a=='between' and (self.ISPstatus1b=='above' or self.ISPstatus1b=='under')):
                        print('found between/above')
                        ccshape.geos.insert(npos,LineGeo(Pa=ccshape.geos[pos].Pe, Pe=ccshape.geos[npos].Pa) )
                        ccshape.geos[pos].col='Blue'
                        ccshape.geos[npos].col='Blue'
                        pos+=1
                        num_elements+=1
                    if(self.ISPstatus1b=='between' and (self.ISPstatus1a=='above' or self.ISPstatus1a=='under')):       
                        print('found between/above')
                        ccshape.geos.insert(npos,LineGeo(Pa=ccshape.geos[pos].Pe, Pe=ccshape.geos[npos].Pa) )
                        ccshape.geos[pos].col='Blue'
                        ccshape.geos[npos].col='Blue'
                        pos+=1
                        num_elements+=1
            # ------------- line / arc -------------------           
            elif(ccshape.geos[pos].type=='LineGeo' and ccshape.geos[npos].type=='ArcGeo'):
                self.CheckIntersectLineArc(ccshape.geos[pos],ccshape.geos[npos])
                if self.num==0:
                    print('found LineArc none')
                    Pa=ccshape.geos[pos].Pe
                    Pe=ccshape.geos[npos].Pa
                    r=ccshape.r
                    dir=ccshape.geos[npos]
                    ccshape.geos.insert(npos, ArcGeo(Pa=ccshape.geos[pos].Pe, Pe=ccshape.geos[npos].Pa, r=r, dir=dir))
                    ccshape.geos[pos].col='Blue'
                    ccshape.geos[npos].col='Blue'
                    pos+=1
                    num_elements+=1
                else:
                    print('Step1:line/arc intersect', self.ISPstatus1a, self.ISPstatus1b,self.ISPstatus2a, self.ISPstatus2b)
                    bw=0
                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_start' or self.ISPstatus1a=='at_end') and (self.ISPstatus1b=='between' or self.ISPstatus1b=='at_start' or self.ISPstatus1b=='at_end')):
                        print('found LineArc between/between')
                        bw=1
                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1)
                        ccshape.geos[npos]=ArcGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r, dir=ccshape.geos[npos].ext)
                        ccshape.geos[pos].col='Blue'
                      
                    if(bw==0 and (self.ISPstatus2a=='between' or self.ISPstatus2a=='at_start' or self.ISPstatus2a=='at_end') and (self.ISPstatus2b=='between' or self.ISPstatus2b=='at_start' or self.ISPstatus2b=='at_end')):
                        print('found LineArc between/between')
                        bw=1
                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P2)
                        ccshape.geos[npos]=ArcGeo(Pa=self.P2, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
                        ccshape.geos[pos].col='Blue'
                        
                    if((self.ISPstatus1a=='above') and (self.ISPstatus1b=='under')and (bw==0)):
                        print('found LineArc above/under')
                        bw=1
                        Pa=ccshape.geos[pos].Pa
                        Pe=self.P1
                        ccshape.geos[pos]=LineGeo(Pa=Pa, Pe=Pe)
                        rn=ccshape.geos[npos].r
                        dirn=ccshape.geos[npos].ext
                        Pen=ccshape.geos[npos].Pe
                        Pan=self.P1
                        ccshape.geos[npos]=ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=dirn)
                        ccshape.geos[pos].col='Blue'
                       
                        
                    if((self.ISPstatus2a=='above') and (self.ISPstatus2b=='under')and (bw==0)):
                        print('found LineArc above/under')
                        bw=1
                        Pa=ccshape.geos[pos].Pa
                        Pe=self.P2
                        ccshape.geos[pos]=LineGeo(Pa=Pa, Pe=Pe)
                        rn=ccshape.geos[npos].r
                        dirn=ccshape.geos[npos].ext
                        Pen=ccshape.geos[npos].Pe
                        Pan=self.P2
                        ccshape.geos[npos]=ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=dirn)
                        ccshape.geos[pos].col='Blue'
                        
                    if((self.ISPstatus1a=='above' and self.ISPstatus1b=='between')or (self.ISPstatus2a=='above' and self.ISPstatus2b=='between')and (bw==0)):
                        print('found LineArc above/between')
                        bw=1
                        ccshape.geos[pos]=LineGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1)
                        ccshape.geos[npos]=ArcGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r, dir=ccshape.geos[npos].ext)
                        #ccshape.geos.insert(npos, LineGeo(Pa=ccshape.geos[pos].Pa, Pe=ccshape.geos[npos].Pa))
                        ccshape.geos[pos].col='Blue'
                        ccshape.geos[npos].col='Blue'
                        
                        
                   # if((self.ISPstatus1a=='between' and ( self.ISPstatus1b=='above' or self.ISPstatus1b=='under' ))or (self.ISPstatus2a=='above' and ( self.ISPstatus2b=='above' or self.ISPstatus2b=='under' ))):
                    #    print('found LineArc bw/ab-un')
                    #    ccshape.geos.insert(npos, LineGeo(Pa=ccshape.geos[pos].Pa, Pe=ccshape.geos[npos].Pa))
                    #    ccshape.geos[pos].col='Blue'
                    #    ccshape.geos[npos].col='Blue'
                    #    pos+=1
                    #    num_elements+=1
                        
            
            # ------------- arc / line -------------------           
            elif(ccshape.geos[pos].type=='ArcGeo' and ccshape.geos[npos].type=='LineGeo'):
                self.CheckIntersectArcLine(ccshape.geos[pos],ccshape.geos[npos])
                if self.num==0:
                    print('found Arc/Line none')
                    Pa=ccshape.geos[pos].Pe
                    Pe=ccshape.geos[npos].Pa
                    r=ccshape.r
                    dir=ccshape.geos[pos]
                    ccshape.geos.insert(npos, ArcGeo(Pa=ccshape.geos[pos].Pe, Pe=ccshape.geos[npos].Pa, r=r, dir=dir))
                    ccshape.geos[pos].col='Blue'
                    ccshape.geos[npos].col='Blue'
                    pos+=1
                    num_elements+=1
                else:
                    bw=0
                    print('Step1:arc/line intersect', self.ISPstatus1a, self.ISPstatus1b,self.ISPstatus2a, self.ISPstatus2b)
                    bw=0
                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_start' or self.ISPstatus1a=='at_end') and (self.ISPstatus1b=='between' or self.ISPstatus1b=='at_start' or self.ISPstatus1b=='at_end')and (bw==0)):
                        print('found arc/line between/between')
                        bw=1
                                             
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1, r=ccshape.geos[pos].r,dir=ccshape.geos[pos].ext)
                        ccshape.geos[npos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe)
                        ccshape.geos[pos].col='Blue'
                      
                    if((self.ISPstatus2a=='between' or self.ISPstatus2a=='at_start' or self.ISPstatus2a=='at_end') and (self.ISPstatus2b=='between' or self.ISPstatus2b=='at_start' or self.ISPstatus2b=='at_end')and (bw==0)):
                        print('found arc/line between/between')
                        bw=1                      
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P2, r=ccshape.geos[pos].r,dir=ccshape.geos[pos].ext)
                        ccshape.geos[npos]=LineGeo(Pa=self.P2, Pe=ccshape.geos[npos].Pe)
                        ccshape.geos[pos].col='Blue'
                        
                    if((self.ISPstatus1a=='above') and (self.ISPstatus1b=='under') and (bw==0)):
                        print('found arc/line above/under')
                        bw=1
                        Pen=self.P1
                        rn=ccshape.geos[pos].r
                        dirn=ccshape.geos[pos].ext
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=Pen, r=rn, dir=dirn)
                        ccshape.geos[npos]=LineGeo(Pa=Pen, Pe=ccshape.geos[npos].Pe)
                        ccshape.geos[pos].col='Blue'
                       
                        
                    if((self.ISPstatus2a=='above') and (self.ISPstatus2b=='under')and (bw==0)):
                        print('found arc/line above/under')
                        bw=1
                        Pen=self.P2
                        rn=ccshape.geos[pos].r
                        dirn=ccshape.geos[pos].ext
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=Pen, r=rn, dir=dirn)
                        ccshape.geos[npos]=LineGeo(Pa=Pen, Pe=ccshape.geos[npos].Pe)
                        ccshape.geos[pos].col='Blue'
                        
                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_end') and self.ISPstatus1b=='under'and (bw==0)):
                        print('found arc/line between/under')
                        bw=1
                        
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1, r=ccshape.geos[pos].r, dir=ccshape.geos[pos].ext)
                        ccshape.geos[npos]=LineGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe)
                        ccshape.geos[pos].col='Blue'
                    if((self.ISPstatus2a=='between' or self.ISPstatus1a=='at_end') and self.ISPstatus2b=='under'and (bw==0)):
                        print('found arc/line between/under')
                        bw=1
                        
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P2, r=ccshape.geos[pos].r, dir=ccshape.geos[pos].ext)
                        ccshape.geos[npos]=LineGeo(Pa=self.P2, Pe=ccshape.geos[npos].Pe)
                        ccshape.geos[pos].col='Blue'
                        
                        
                   # if((self.ISPstatus1a=='between' and ( self.ISPstatus1b=='above' or self.ISPstatus1b=='under' ))or (self.ISPstatus2a=='above' and ( self.ISPstatus2b=='above' or self.ISPstatus2b=='under' ))):
                    #    print('found LineArc bw/ab-un')
                    #    ccshape.geos.insert(npos, LineGeo(Pa=ccshape.geos[pos].Pa, Pe=ccshape.geos[npos].Pa))
                    #    ccshape.geos[pos].col='Blue'
                    #    ccshape.geos[npos].col='Blue'
                    #    pos+=1
                    #    num_elements+=1
               # ------------- arc / arc -------------------           
            elif(ccshape.geos[pos].type=='ArcGeo' and ccshape.geos[npos].type=='ArcGeo'):
                self.CheckIntersectArcArc(ccshape.geos[pos],ccshape.geos[npos])
                if self.num==0:
                    print('found Arc/Arc none')
                    Pa=ccshape.geos[pos].Pe
                    Pe=ccshape.geos[npos].Pa
                    r=ccshape.r
                    dir=ccshape.geos[npos]
                    ccshape.geos.insert(npos, ArcGeo(Pa=ccshape.geos[pos].Pe, Pe=ccshape.geos[npos].Pa, r=r, dir=dir))
                    ccshape.geos[pos].col='Blue'
                    ccshape.geos[npos].col='Blue'
                    pos+=1
                    num_elements+=1
                else:
                    bw=0
                    print('Step1:arc/arc intersect', self.ISPstatus1a, self.ISPstatus1b,self.ISPstatus2a, self.ISPstatus2b)
                    bw=0
                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_start' or self.ISPstatus1a=='at_end') and (self.ISPstatus1b=='between' or self.ISPstatus1b=='at_start' or self.ISPstatus1b=='at_end')and (bw==0)):
                        print('found arc/arc between/between')
                        bw=1
                                             
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1, r=ccshape.geos[pos].r,dir=ccshape.geos[pos].ext)
                        ccshape.geos[npos]=ArcGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
                        ccshape.geos[pos].col='Blue'
                      
                    if((self.ISPstatus2a=='between' or self.ISPstatus2a=='at_start' or self.ISPstatus2a=='at_end') and (self.ISPstatus2b=='between' or self.ISPstatus2b=='at_start' or self.ISPstatus2b=='at_end')and (bw==0)):
                        print('found arc/arc between/between')
                        bw=1                      
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P2, r=ccshape.geos[pos].r,dir=ccshape.geos[pos].ext)
                        ccshape.geos[npos]=ArcGeo(Pa=self.P2, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
                        ccshape.geos[pos].col='Blue'
                        
                    if((self.ISPstatus1a=='above') and (self.ISPstatus1b=='under') and (bw==0)):
                        print('found arc/arc above/under')
                        bw=1
                        Pen=self.P1
                        rn=ccshape.geos[pos].r
                        dirn=ccshape.geos[pos].ext
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=Pen, r=rn, dir=dirn)
                        ccshape.geos[npos]=ArcGeo(Pa=Pen, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
                        ccshape.geos[pos].col='Blue'
                       
                        
                    if((self.ISPstatus2a=='above') and (self.ISPstatus2b=='under')and (bw==0)):
                        print('found arc/arc above/under')
                        bw=1
                        Pen=self.P2
                        rn=ccshape.geos[pos].r
                        dirn=ccshape.geos[pos].ext
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=Pen, r=rn, dir=dirn)
                        ccshape.geos[npos]=ArcGeo(Pa=Pen, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
                        ccshape.geos[pos].col='Blue'
                        
                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_end') and self.ISPstatus1b=='under'and (bw==0)):
                        print('found arc/arc between/under')
                        bw=1
                        
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P1, r=ccshape.geos[pos].r, dir=ccshape.geos[pos].ext)
                        ccshape.geos[npos]=ArcGeo(Pa=self.P1, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
                        ccshape.geos[pos].col='Blue'
                    if((self.ISPstatus2a=='between' or self.ISPstatus1a=='at_end') and self.ISPstatus2b=='under'and (bw==0)):
                        print('found arc/arc between/under')
                        bw=1
                        
                        ccshape.geos[pos]=ArcGeo(Pa=ccshape.geos[pos].Pa, Pe=self.P2, r=ccshape.geos[pos].r, dir=ccshape.geos[pos].ext)
                        ccshape.geos[npos]=ArcGeo(Pa=self.P2, Pe=ccshape.geos[npos].Pe, r=ccshape.geos[npos].r,dir=ccshape.geos[npos].ext)
                        ccshape.geos[pos].col='Blue'
                        
                        
                   # if((self.ISPstatus1a=='between' and ( self.ISPstatus1b=='above' or self.ISPstatus1b=='under' ))or (self.ISPstatus2a=='above' and ( self.ISPstatus2b=='above' or self.ISPstatus2b=='under' ))):
                    #    print('found LineArc bw/ab-un')
                    #    ccshape.geos.insert(npos, LineGeo(Pa=ccshape.geos[pos].Pa, Pe=ccshape.geos[npos].Pa))
                    #    ccshape.geos[pos].col='Blue'
                    #    ccshape.geos[npos].col='Blue'
                    #    pos+=1
                    #    num_elements+=1
                                 
            pos+=1
        print('2')
        ccshape.geos[0]=ccshape.geos[npos]
        print('3')
        print(len(ccshape.geos))
        ccshape.geos[0].col='Yellow'
        return (ccshape)
#---------------------------------------------------------------------------------------------
# Check for intersection between 2 Lines
#---------------------------------------------------------------------------------------------

    def CheckIntersectLineLine(self,L1,L2):
       
        self.num=0
        self.ISPtype1='no'
        self.ISPstatus1='no'
        self.ISPtype2='no'
        self.ISPstatus2='no'

        self.P2=PointClass(0.0,0.0)
        self.P1_ext=0.0
        self.P2_ext=0.0
        self.P1_v1=0.0
        self.P2_v2=0.0
        print('check line/line')
        dx1=L1.Pe.x-L1.Pa.x
        dy1=L1.Pe.y-L1.Pa.y
        dx2=L2.Pe.x-L2.Pa.x
        dy2=L2.Pe.y-L2.Pa.y

        dax=L1.Pa.x-L2.Pa.x
        day=L1.Pa.y-L2.Pa.y

        if dx1==0 and dy1==0:
            return
        if dx2==0 and dy2==0:
            return
        
        print dx1
        print dy1
        print dx2
        print dy2
        
        
        if(abs(dx2)>=abs(dy2)):
            n=(day-dax*dy2/dx2)/(dx1*dy2/dx2 -dy1)
            u=(dax+n*dx1)/dx2
            self.P1=PointClass(x=L1.Pa.x+n*dx1,
                               y=L1.Pa.y+n*dy1)
            self.v1=n
            self.v2=u
            
        else:
            print dy1*dx2/dy2 -dx1
           
            n=(dax-day*dx2/dy2)/(dy1*dx2/dy2 -dx1)
            u=(day+n*dy1)/dy2
            self.P1=PointClass(x=L1.Pa.x+n*dx1,
                               y=L1.Pa.y+n*dy1)
            self.v1=n
            self.v2=u
            
        self.num=1
        
        if 0.00001<self.v1 and self.v1<0.9999:
            self.ISPstatus1a='between'             
        elif 0.9999<self.v1 and self.v1<1.00001:
            self.ISPstatus1a='at_end'
        elif -0.00001<self.v1 and self.v1<0.00001:
            self.ISPstatus1a='at_start'    
        elif self.v1>1.00001:
            self.ISPstatus1a='above'
        else:
            self.ISPstatus1a='under'
            
        if 0.00001<self.v2 and self.v2<0.9999:
            self.ISPstatus1b='between'             
        elif 0.9999<self.v2 and self.v2<1.00001:
            self.ISPstatus1b='at_end'
        elif -0.00001<self.v2 and self.v2<0.00001:
            self.ISPstatus1b='at_start'    
        elif self.v2>1.00001:
            self.ISPstatus1b='above'
        else:
            self.ISPstatus1b='under'    
            
            
        
        print ('num,x1,y1,x2,y2',self.num,self.P1.x,self.P1.y,self.P2.x,self.P2.y)
        print ('st1a,st2a,st1b,st2b,v1,v2',self.ISPstatus1a,self.ISPstatus2a,self.ISPstatus1b,self.ISPstatus2b, self.v1,self.v2, )

        return 

#---------------------------------------------------------------------------------------------
# Check for intersection between a line and an arc
#---------------------------------------------------------------------------------------------

    def CheckIntersectLineArc(self,L1,K1):
       
        self.num=0
        self.ISPtype1='no'
        self.ISPstatus1='no'
        self.ISPtype2='no'
        self.ISPstatus2='no'
        self.P1=PointClass(0.0,0.0)
        self.P2=PointClass(0.0,0.0)
        self.P1_ext=0.0
        self.P2_ext=0.0
        self.P1_v1=0.0
        self.P2_v2=0.0
        print('check line/arc')

        y1=L1.Pa.y
        y2=L1.Pe.y
        x1=L1.Pa.x
        x2=L1.Pe.x
        r=K1.r
        x0=K1.O.x
        y0=K1.O.y
        vx=x2-x1
        vy=y2-y1
        a=pow(vx,2)+pow(vy,2)
        b=2*vx*(x1-x0)+2*vy*(y1-y0)
        c=pow(x1-x0,2)+pow(y1-y0,2)-pow(r,2)
        udw=pow(b,2)-4*a*c
       
        if udw<0:
            print('neg Wurzel')
            return

        v1=(-b+sqrt(udw))/(2*a)
        v2=(-b-sqrt(udw))/(2*a)
        
        self.P1.x=x1+v1*vx
        self.P1.y=y1+v1*vy
        self.P2.x=x1+v2*vx
        self.P2.y=y1+v2*vy
       
        if(udw==0):
            self.num=1
        else:
            self.num=2
            
        dist1=L1.Pe.distance(self.P1)
        self.v1=v1
        self.v2=v2
            
      
        i_ext=K1.dif_ang(K1.Pa, self.P1, K1.ext)
        s_ext=K1.dif_ang(K1.Pa, K1.Pe, K1.ext)
        
        self.P1_ext_a=i_ext
        delta= i_ext/s_ext
        print('delta1',delta)
        
        if 0.00001<delta and delta<0.9999:
            self.ISPstatus1b='between'             
        elif 0.9999<delta and delta<1.00001:
            self.ISPstatus1b='at_end'
        elif -0.00001<delta and delta<0.00001:
            self.ISPstatus1b='at_start'    
        elif delta>1.00001:
            self.ISPstatus1b='above'
        else:
            self.ISPstatus1b='under'
        
        i_ext=K1.dif_ang(K1.Pa, self.P2, K1.ext)
        self.P2_ext_a=i_ext
        
        s_ext=K1.dif_ang(K1.Pa, K1.Pe, K1.ext)
        delta= i_ext/s_ext   
        print('delta2',delta)
        
        if 0.00001<delta and delta<0.9999:
            self.ISPstatus2b='between'             
        elif 0.9999<delta and delta<1.00001:
            self.ISPstatus2b='at_end'
        elif -0.00001<delta and delta<0.00001:
            self.ISPstatus2b='at_start'    
        elif delta>1.00001:
            self.ISPstatus2b='above'
        else:
            self.ISPstatus2b='under'
        
        if 0.00001<self.v1 and self.v1<0.9999:
            self.ISPstatus1a='between'             
        elif 0.9999<self.v1 and self.v1<1.00001:
            self.ISPstatus1a='at_end'
        elif -0.00001<self.v1 and self.v1<0.00001:
            self.ISPstatus1a='at_start'    
        elif self.v1>1.00001:
            self.ISPstatus1a='above'
        else:
            self.ISPstatus1a='under'
            
        if 0.00001<self.v2 and self.v2<0.9999:
            self.ISPstatus2a='between'             
        elif 0.9999<self.v2 and self.v2<1.00001:
            self.ISPstatus2a='at_end'
        elif -0.00001<self.v2 and self.v2<0.00001:
            self.ISPstatus2a='at_start'    
        elif self.v2>1.00001:
            self.ISPstatus2a='above'
        else:
            self.ISPstatus2a='under'    
        
       

        print ('num,x1,y1,x2,y2',self.num,self.P1.x,self.P1.y,self.P2.x,self.P2.y)
        print ('st1a,st1b,st2a,st2b,v1,v2,P1_ext,P2_ext',self.ISPstatus1a,self.ISPstatus1b,self.ISPstatus2a,self.ISPstatus2b, self.v1,self.v2,self.P1_ext_a, self.P2_ext_a )

        return 

#---------------------------------------------------------------------------------------------
# Check for intersection between 2 arcs
#---------------------------------------------------------------------------------------------
    def CheckIntersectArcArc(self,K1,K2):
       

        self.num=0;
        self.ISPtype1='no'
        self.ISPstatus1='no'
        self.ISPtype2='no'
        self.ISPstatus2='no'
        self.num=0;
        self.P1=PointClass(0.0,0.0)
        self.P2=PointClass(0.0,0.0)
        self.P1_ext=0.0
        self.P2_ext=0.0
        print('check arc/arc')
        r1 = abs(K1.r);
        r2 = abs(K2.r);
        print('K1.r, K2.r, K1.O.x, K1.O.y, K2.O.x.K2.O.y, K1.Pe.x, K1.Pe.y, K2.Pa.x, K2.Pa.y', K1.r, K2.r, K1.O.x, K1.O.y, K2.O.x, K2.O.y, K1.Pe.x, K1.Pe.y, K2.Pa.x, K2.Pa.y)
        res = sqrt(pow(abs(K2.O.x - K1.O.x),2)+pow(abs(K2.O.y - K1.O.y),2));
      

        if(res <= abs(r1-r2)):
            return 

        if(res > abs(r1 + r2)):
            return 
            
        if((K1.O.x - K2.O.x == 0) and (K1.O.y - K2.O.y == 0)):
            return 

        if(K1.O.x == K2.O.x):
            d1 = (K1.O.x - K2.O.x)/(K2.O.y - K1.O.y)
            d2 = ((pow(r1,2) - pow(r2,2))- (pow(K1.O.y,2) - pow(K2.O.y,2)) - (pow(K1.O.x,2) - pow(K2.O.x,2))  )/(2*K2.O.y - 2*K1.O.y)
            a = pow(d1,2)+1
            b = (2*d1*(d2-K1.O.y))-(2*K1.O.x)
            c = pow((d2-K1.O.y),2) -pow(r1,2) + pow(K1.O.x,2)
          
            self.P1.x = (-b + sqrt(pow(b,2) - 4*a*c) )/(2*a)
            self.P2.x = (-b - sqrt(pow(b,2) - 4*a*c) )/(2*a)
            self.P1.y = self.P1.x * d1 + d2
            self.P2.y = self.P2.x * d1 + d2

        else:
            d1 =(K1.O.y - K2.O.y)/(K2.O.x - K1.O.x)
            d2 =((pow(r1,2) - pow(r2,2))- (pow(K1.O.x,2) - pow(K2.O.x,2)) -  (pow(K1.O.y,2) - pow(K2.O.y,2))  )/(2*K2.O.x - 2*K1.O.x)
            a = pow(d1,2)+1
            b = (2*d1*(d2-K1.O.x))-(2*K1.O.y)
            c = pow((d2-K1.O.x),2)-pow(r1,2) + pow(K1.O.y,2)
           
            self.P1.y = (-b + sqrt(pow(b,2) - 4*a*c) )/(2*a)
            self.P2.y = (-b - sqrt(pow(b,2) - 4*a*c) )/(2*a)
            self.P1.x = self.P1.y * d1 + d2
            self.P2.x = self.P2.y * d1 + d2


        if(self.P1.y == self.P2.y and self.P1.x == self.P2.x):
            self.num=1
        else:
            self.num=2

    
        i_ext=K1.dif_ang(K1.Pa, self.P1, K1.ext)
        self.P1_ext_a=i_ext
        
        s_ext=K1.dif_ang(K1.Pa, K1.Pe, K1.ext)
        delta= i_ext/s_ext   
        print('delta1',delta)
      
        if 0.00001<delta and delta<0.9999:
            self.ISPstatus1a='between'             
        elif 0.9999<delta and delta<1.00001:
            self.ISPstatus1a='at_end'
        elif -0.00001<delta and delta<0.00001:
            self.ISPstatus1a='at_start'    
        elif delta>1.00001:
            self.ISPstatus1a='above'
        else:
            self.ISPstatus1a='under'
        
            

        i_ext=K1.dif_ang(K1.Pa, self.P2, K1.ext)
        self.P2_ext_a=i_ext
       
        s_ext=K1.dif_ang(K1.Pa, K1.Pe, K1.ext)
        delta= i_ext/s_ext   
        print('delta2',delta)
       
        if 0.00001<delta and delta<0.9999:
            self.ISPstatus2a='between'             
        elif 0.9999<delta and delta<1.00001:
            self.ISPstatus2a='at_end'
        elif -0.00001<delta and delta<0.00001:
            self.ISPstatus2a='at_start'    
        elif delta>1.00001:
            self.ISPstatus2a='above'
        else:
            self.ISPstatus2a='under'
        
            
            
        i_ext=K2.dif_ang(K2.Pe, self.P1, -K2.ext)
        self.P1_ext_a=i_ext
        print ('K2.ext', K2.ext)
        s_ext=K2.dif_ang(K2.Pe, K2.Pa, -K2.ext)
        delta= i_ext/s_ext   
        print('*delta1',delta)
      
        if 0.00001<delta and delta<0.9999:
            self.ISPstatus1b='between'             
        elif 0.9999<delta and delta<1.00001:
            self.ISPstatus1b='at_end'
        elif -0.00001<delta and delta<0.00001:
            self.ISPstatus1b='at_start'    
        elif delta>1.00001:
            self.ISPstatus1b='under'
        else:
            self.ISPstatus1b='above'
        
            

        i_ext=K2.dif_ang(K2.Pe, self.P2, -K2.ext)
        self.P2_ext_a=i_ext
        
        s_ext=K2.dif_ang(K2.Pe, K2.Pa, -K2.ext)
        delta= i_ext/s_ext   
        print('*delta2',delta)
       
        if 0.00001<delta and delta<0.9999:
            self.ISPstatus2b='between'             
        elif 0.9999<delta and delta<1.00001:
            self.ISPstatus2b='at_end'
        elif -0.00001<delta and delta<0.00001:
            self.ISPstatus2b='at_start'    
        elif delta>1.00001:
            self.ISPstatus2b='under'
        else:
            self.ISPstatus2b='above'
        
        
        print ('num,x1,y1,x2,y2, K1.ext, K2.ext',self.num,self.P1.x,self.P1.y,self.P2.x,self.P2.y, K1.ext, K2.ext)
        print ('st1a,st1b,st2a,st2b,v1,v2',self.ISPstatus1a,self.ISPstatus1b,self.ISPstatus2a,self.ISPstatus2b, self.v1,self.v2 )

#===============================================================================
#    def CheckIntersectArcArc(self,K1,K2):
#       
# 
#        self.num=0;
#        self.ISPtype1='no'
#        self.ISPstatus1='no'
#        self.ISPtype2='no'
#        self.ISPstatus2='no'
#        self.num=0;
#        self.P1=PointClass(0.0,0.0)
#        self.P2=PointClass(0.0,0.0)
#        self.P1_ext=0.0
#        self.P2_ext=0.0
#        print('check arc/arc')
#        r1 = abs(K1.r);
#        r2 = abs(K2.r);
#        print('K1.r %0.2f, K2.r %0.2f, K1.O.x %0.2f, K1.O.y %0.2f, K2.O.x %0.2f,K2.O.y %0.2f \nK1.Pe.x %0.2f, K1.Pe.y %0.2f, K2.Pa.x %0.2f, K2.Pa.y %0.2f' %( K1.r, K2.r, K1.O.x, K1.O.y, K2.O.x, K2.O.y, K1.Pe.x, K1.Pe.y, K2.Pa.x, K2.Pa.y))
#        res = sqrt(pow(abs(K2.O.x - K1.O.x),2)+pow(abs(K2.O.y - K1.O.y),2));
#      
# 
#        if(res <= abs(r1-r2)):
#            return 
# 
#        if(res > abs(r1 + r2)):
#            return 
#            
#        if((K1.O.x - K2.O.x == 0) and (K1.O.y - K2.O.y == 0)):
#            return 
# 
#        if(K1.O.x == K2.O.x):
#            d1 = (K1.O.x - K2.O.x)/(K2.O.y - K1.O.y)
#            d2 = ((pow(r1,2) - pow(r2,2))- (pow(K1.O.y,2) - pow(K2.O.y,2)) - (pow(K1.O.x,2) - pow(K2.O.x,2))  )/(2*K2.O.y - 2*K1.O.y)
#            a = pow(d1,2)+1
#            b = (2*d1*(d2-K1.O.y))-(2*K1.O.x)
#            c = pow((d2-K1.O.y),2) -pow(r1,2) + pow(K1.O.x,2)
#          
#            self.P1.x = (-b + sqrt(pow(b,2) - 4*a*c) )/(2*a)
#            self.P2.x = (-b - sqrt(pow(b,2) - 4*a*c) )/(2*a)
#            self.P1.y = self.P1.x * d1 + d2
#            self.P2.y = self.P2.x * d1 + d2
# 
#        else:
#            d1 =(K1.O.y - K2.O.y)/(K2.O.x - K1.O.x)
#            d2 =((pow(r1,2) - pow(r2,2))- (pow(K1.O.x,2) - pow(K2.O.x,2)) -  (pow(K1.O.y,2) - pow(K2.O.y,2))  )/(2*K2.O.x - 2*K1.O.x)
#            a = pow(d1,2)+1
#            b = (2*d1*(d2-K1.O.x))-(2*K1.O.y)
#            c = pow((d2-K1.O.x),2)-pow(r1,2) + pow(K1.O.y,2)
#           
#            self.P1.y = (-b + sqrt(pow(b,2) - 4*a*c) )/(2*a)
#            self.P2.y = (-b - sqrt(pow(b,2) - 4*a*c) )/(2*a)
#            self.P1.x = self.P1.y * d1 + d2
#            self.P2.x = self.P2.y * d1 + d2
# 
# 
#        if(self.P1.y == self.P2.y and self.P1.x == self.P2.x):
#            self.num=1
#        else:
#            self.num=2
# 
#    
#        i_ext=K1.dif_ang(K1.Pa, self.P1, K1.ext)
#        self.P1_ext_a=i_ext
#        
#        s_ext=K1.dif_ang(K1.Pa, K1.Pe, K1.ext)
#        delta= i_ext/s_ext   
#        print('delta1',delta)
#      
#        if 0.00001<delta and delta<0.9999:
#            self.ISPstatus1a='between'             
#        elif 0.9999<delta and delta<1.00001:
#            self.ISPstatus1a='at_end'
#        elif -0.00001<delta and delta<0.00001:
#            self.ISPstatus1a='at_start'    
#        elif delta>1.00001:
#            self.ISPstatus1a='above'
#        else:
#            self.ISPstatus1a='under'
#        
#            
# 
#        i_ext=K1.dif_ang(K1.Pa, self.P2, K1.ext)
#        self.P2_ext_a=i_ext
#       
#        s_ext=K1.dif_ang(K1.Pa, K1.Pe, K1.ext)
#        delta= i_ext/s_ext   
#        print('delta2',delta)
#       
#        if 0.00001<delta and delta<0.9999:
#            self.ISPstatus2a='between'             
#        elif 0.9999<delta and delta<1.00001:
#            self.ISPstatus2a='at_end'
#        elif -0.00001<delta and delta<0.00001:
#            self.ISPstatus2a='at_start'    
#        elif delta>1.00001:
#            self.ISPstatus2a='above'
#        else:
#            self.ISPstatus2a='under'
#        
#            
#            
#        i_ext=K2.dif_ang(K2.Pe, self.P1, -K2.ext)
#        self.P1_ext_a=i_ext
#        print ('K2.ext', K2.ext)
#        s_ext=K2.dif_ang(K2.Pe, K2.Pa, -K2.ext)
#        delta= i_ext/s_ext   
#        print('*delta1',delta)
#      
#        if 0.00001<delta and delta<0.9999:
#            self.ISPstatus1b='between'             
#        elif 0.9999<delta and delta<1.00001:
#            self.ISPstatus1b='at_end'
#        elif -0.00001<delta and delta<0.00001:
#            self.ISPstatus1b='at_start'    
#        elif delta>1.00001:
#            self.ISPstatus1b='under'
#        else:
#            self.ISPstatus1b='above'
#        
#            
# 
#        i_ext=K2.dif_ang(K2.Pe, self.P2, -K2.ext)
#        self.P2_ext_a=i_ext
#        
#        s_ext=K2.dif_ang(K2.Pe, K2.Pa, -K2.ext)
#        delta= i_ext/s_ext   
#        print('*delta2',delta)
#       
#        if 0.00001<delta and delta<0.9999:
#            self.ISPstatus2b='between'             
#        elif 0.9999<delta and delta<1.00001:
#            self.ISPstatus2b='at_end'
#        elif -0.00001<delta and delta<0.00001:
#            self.ISPstatus2b='at_start'    
#        elif delta>1.00001:
#            self.ISPstatus2b='under'
#        else:
#            self.ISPstatus2b='above'
#        
#        
#        print ('num %i,x1 %0.2f,y1 %0.2f,x2 %0.2f,y2 %0.2f, K1.ext %0.2f, K2.ext %0.2f' 
#               %(self.num,self.P1.x,self.P1.y,self.P2.x,self.P2.y, K1.ext, K2.ext))
#        print ('st1a,st1b,st2a,st2b,v1,v2',self.ISPstatus1a,self.ISPstatus1b,self.ISPstatus2a,self.ISPstatus2b, self.v1,self.v2 )
#===============================================================================

#---------------------------------------------------------------------------------------------
# Check for intersection between an arc and a line
#---------------------------------------------------------------------------------------------

    def CheckIntersectArcLine(self,K1,L1):
        
        self.num=0
        self.ISPtype1='no'
        self.ISPstatus1='no'
        self.ISPtype2='no'
        self.ISPstatus2='no'
        self.P1=PointClass(0.0,0.0)
        self.P2=PointClass(0.0,0.0)
        self.P1_ext=0.0
        self.P2_ext=0.0
        self.P1_v1=0.0
        self.P2_v2=0.0
        
        print('check arc/line')
        y1=L1.Pa.y
        y2=L1.Pe.y
        x1=L1.Pa.x
        x2=L1.Pe.x
        r=K1.r
        x0=K1.O.x
        y0=K1.O.y
        vx=x2-x1
        vy=y2-y1
        a=pow(vx,2)+pow(vy,2)
        b=2*vx*(x1-x0)+2*vy*(y1-y0)
        c=pow(x1-x0,2)+pow(y1-y0,2)-pow(r,2)
        udw=pow(b,2)-4*a*c
      
        if udw<0:
            print('neg Wurzel')
            return

        v1=(-b+sqrt(udw))/(2*a)
        v2=(-b-sqrt(udw))/(2*a)
        self.P1.x=x1+v1*vx
        self.P1.y=y1+v1*vy
        self.P2.x=x1+v2*vx
        self.P2.y=y1+v2*vy
      
        if(udw==0):
            self.num=1
        else:
            self.num=2
        self.v1=v1
        self.v2=v2

        i_ext=K1.dif_ang(K1.Pa, self.P1, K1.ext)
        self.P1_ext_a=i_ext
       
        s_ext=K1.dif_ang(K1.Pa, K1.Pe, K1.ext)
        delta= i_ext/s_ext   
        print('delta1', delta)
        
        if 0.00001<delta and delta<0.9999:
            self.ISPstatus1a='between'             
        elif 0.9999<delta and delta<1.00001:
            self.ISPstatus1a='at_end'
        elif -0.00001<delta and delta<0.00001:
            self.ISPstatus1a='at_start'    
        elif delta>1.00001:
            self.ISPstatus1a='above'
        else:
            self.ISPstatus1a='under'
        
        i_ext=K1.dif_ang(K1.Pa, self.P2, K1.ext)
        self.P2_ext_a=i_ext
        
        s_ext=K1.dif_ang(K1.Pa, K1.Pe, K1.ext)
        delta= i_ext/s_ext   
        print('delta2',delta)
        
        if 0.00001<delta and delta<0.9999:
            self.ISPstatus2a='between'             
        elif 0.9999<delta and delta<1.00001:
            self.ISPstatus2a='at_end'
        elif -0.00001<delta and delta<0.00001:
            self.ISPstatus2a='at_start'    
        elif delta>1.00001:
            self.ISPstatus2a='above'
        else:
            self.ISPstatus2a='under'    
            
        if 0.00001<self.v1 and self.v1<0.9999:
            self.ISPstatus1b='between'             
        elif 0.9999<self.v1 and self.v1<1.00001:
            self.ISPstatus1b='at_end'
        elif -0.00001<self.v1 and self.v1<0.00001:
            self.ISPstatus1b='at_start'    
        elif self.v1>1.00001:
            self.ISPstatus1b='above'
        else:
            self.ISPstatus1b='under'
            
        if 0.00001<self.v2 and self.v2<0.9999:
            self.ISPstatus2b='between'             
        elif 0.9999<self.v2 and self.v2<1.00001:
            self.ISPstatus2b='at_end'
        elif -0.00001<self.v2 and self.v2<0.00001:
            self.ISPstatus2b='at_start'    
        elif self.v2>1.00001:
            self.ISPstatus2b='above'
        else:
            self.ISPstatus2b='under'    



        print ('num,x1,y1,x2,y2, K1.ext,',self.num,self.P1.x,self.P1.y,self.P2.x,self.P2.y, K1.ext)
        print ('st1a,st1b,st2a,st2b,v1,v2,P1_ext,P2_ext',self.ISPstatus1a,self.ISPstatus1b,self.ISPstatus2a,self.ISPstatus2b, self.v1,self.v2,self.P1_ext_a, self.P2_ext_a )

        return 
    

#---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------



