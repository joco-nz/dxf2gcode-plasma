# -*- coding: cp1252 -*-
from dxf2gcode_b02_point import PointClass, ArcGeo, LineGeo,floor ,ceil
from dxf2gcode_b02_shape import ShapeClass

from math import sin,cos,  atan2, sqrt, pow,pi

#
# based on an article of X.-Z Liu et al. /Computer in Industry 58(2007)
#
# WED 20.4.09
class Polylines:
    def __init__(self):
        self.closed=0
        self.col=[]
        self.geos=[]
        self.cut_cor=30
        self.nr=0
        self.r=0
        
        
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
        self.shapes=Polylines()
        self.newshapes=Polylines()

    def show(self,shapes):
        print ('Anzahl der Elemente',len(shapes.geos))
        print('Kurventyp', shapes.closed)
        for pos in range (len(shapes.geos)):
            print(pos,shapes.geos[pos].type)
        
        return
    def do_compensation(self, shapes, radius):
        pline=Polylines()
        pline=self.CorNextInterSect(shapes)
        pline=self.GenRawCompData(pline,radius)
        return(pline)
#--------------------------------------------------------------------------------------------------------------------------------
# adds additional segment if seg n intersects with seg n+1
#--------------------------------------------------------------------------------------------------------------------------------
    def CorNextInterSect(self, shapes):
     
        num_elements=len(shapes.geos)
        P1=PointClass(1, 1)
        P2=PointClass(2, 2)
        newshape=Polylines()
        
        if num_elements<2:
            return
        newshape.closed=shapes.closed
        if shapes.closed!=0:
            shapes.geos.insert(num_elements+1, shapes.geos[0])
            num_elements+=1
            
        pos=0;  
        
        while pos<num_elements-1:
            if(shapes.geos[pos].type=="LineGeo" and shapes.geos[pos+1].type=="LineGeo"):
                self.CheckIntersectLineLine(shapes.geos[pos], shapes.geos[pos+1])
                newshape.geos.append(LineGeo(shapes.geos[pos].Pa,shapes.geos[pos].Pe))
                if(self.num>1):
                    print("ERROR Line/Line Intersect with 2 ponts is not possible")
            elif(shapes.geos[pos].type=="LineGeo" and shapes.geos[pos+1].type=="ArcGeo"):
                
                self.CheckIntersectLineArc(shapes.geos[pos], shapes.geos[pos+1])
                if(self.num>1):
                    
                    print('1*') 
                    v=PointClass(0.0, 0.0)
                    if(self.ISPstatus1a=='between' and self.ISPstatus1b=='between'):
                        if(self.v1>0 and self.v1<1):
                            v=(shapes.geos[pos].Pe-shapes.geos[pos].Pa)
                            nv=(self.v1+1)/2 
                    elif(self.ISPstatus2a=='between' and self.ISPstatus2b=='between' ):
                        
                        print("found intersect Line Arc, inserting additional Line")
                        if(self.v2>0 and self.v2<1):
                            v=(shapes.geos[pos].Pe-shapes.geos[pos].Pa)
                            nv=(self.v1+1)/2
                    print('2*')
                    if((pow(v.x, 2)+pow(v.y, 2))>0):
                        print('3*') 
                        Pen=PointClass(0.0, 0.0)
                        Pen.x=shapes.geos[pos].Pa.x+v.x*nv
                        Pen.y=shapes.geos[pos].Pa.y+v.y*nv
                        newshape.geos.append(LineGeo(shapes.geos[pos].Pa, Pen))
                        newshape.geos[-1].col='Black'
                        newshape.geos.append(LineGeo(Pen, shapes.geos[pos].Pe))
                        newshape.geos[-1].col='Red'
                    else:
                        print('4*')
                        newshape.geos.append(LineGeo(shapes.geos[pos].Pa, shapes.geos[pos].Pe))
                        newshape.geos[-1].col='Black'
                        print('4+')
                else:
                    newshape.geos.append(LineGeo(shapes.geos[pos].Pa, shapes.geos[pos].Pe))
                    newshape.geos[-1].col='Black' 
                    print('5*')
                    
            elif(shapes.geos[pos].type=="ArcGeo" and shapes.geos[pos+1].type=="ArcGeo"):
                self.CheckIntersectArcArc(shapes.geos[pos], shapes.geos[pos+1])
                print('6*')
                delta=0
                if(self.ISPstatus1a=='between' and self.ISPstatus1b=='between' ):
                    print("found intersect Arc  Arc, inserting additional Arc")
                    delta=self.P1_ext_a/shapes.geos[pos].ext
                elif(self.ISPstatus2a=='between' and self.ISPstatus2b=='between' ):
                    print("found intersect Arc  Arc, inserting additional Arc")
                    delta=self.P2_ext_a/shapes.geos[pos].ext
                
              
                if(delta>0 and delta<1):
                    delta=delta*0.5
                    arc=shapes.geos[pos].s_ang+delta*shapes.geos[pos].ext
                    print('calcu22', +shapes.geos[pos].O.y+shapes.geos[pos].r*sin(arc),shapes.geos[pos].O.x+shapes.geos[pos].r*cos(arc))
                    Pen=PointClass(0.0, 0.0)
                    Pen.y=shapes.geos[pos].r*sin(arc)+shapes.geos[pos].O.y
                    Pen.x=shapes.geos[pos].r*cos(arc)+shapes.geos[pos].O.x
                    print('DELTA', delta, Pen.x, Pen.y)
                    newshape.geos.append(ArcGeo(Pa=shapes.geos[pos].Pa,Pe=Pen,r=shapes.geos[pos].r,s_ang=shapes.geos[pos].s_ang, e_ang=arc, dir=shapes.geos[pos].ext, O=shapes.geos[pos].O))
                    newshape.geos[-1].col='Black'
                    newshape.geos.append(ArcGeo(Pa=Pen,Pe=shapes.geos[pos].Pe,r=shapes.geos[pos].r,s_ang=arc, e_ang=shapes.geos[pos].e_ang, dir=shapes.geos[pos].ext, O=shapes.geos[pos].O))
                    newshape.geos[-1].col='Red'
                else:
                    newshape.geos.append(ArcGeo(Pa=shapes.geos[pos].Pa,Pe=shapes.geos[pos].Pe,r=shapes.geos[pos].r,s_ang=shapes.geos[pos].s_ang, e_ang=shapes.geos[pos].e_ang, dir=shapes.geos[pos].ext, O=shapes.geos[pos].O))
                    newshape.geos[-1].col='Black'
                 
                
            elif(shapes.geos[pos].type=="ArcGeo" and shapes.geos[pos+1].type=="LineGeo"):
                
                self.CheckIntersectArcLine(shapes.geos[pos], shapes.geos[pos+1])
                delta=0
                if(self.ISPstatus1a=='between' and self.ISPstatus1b=='between' ):
                    print("found intersect Arc  line, inserting additional Arc")
                    delta=self.P1_ext_a/shapes.geos[pos].ext
                elif(self.ISPstatus2a=='between' and self.ISPstatus2b=='between' ):
                    print("found intersect Arc  line, inserting additional Arc")
                    delta=self.P2_ext_a/shapes.geos[pos].ext
               
                
                
                if(delta>0 and delta<1):
                    delta=delta*0.5
                    arc=shapes.geos[pos].s_ang+delta*shapes.geos[pos].ext
                    Pen=PointClass(0.0, 0.0)
                    Pen.y=shapes.geos[pos].r*sin(arc)+shapes.geos[pos].O.y
                    Pen.x=shapes.geos[pos].r*cos(arc)+shapes.geos[pos].O.x
                    newshape.geos.append(ArcGeo(Pa=shapes.geos[pos].Pa,Pe=Pen,r=shapes.geos[pos].r,s_ang=shapes.geos[pos].s_ang, e_ang=arc, dir=shapes.geos[pos].ext, O=shapes.geos[pos].O))
                    newshape.geos[-1].col='Black'
                    newshape.geos.append(ArcGeo(Pa=Pen,Pe=shapes.geos[pos].Pe,r=shapes.geos[pos].r,s_ang=arc, e_ang=shapes.geos[pos].e_ang, dir=shapes.geos[pos].ext, O=shapes.geos[pos].O))
                    newshape.geos[-1].col='Red'
                else:
                    newshape.geos.append(ArcGeo(Pa=shapes.geos[pos].Pa,Pe=shapes.geos[pos].Pe,r=shapes.geos[pos].r,s_ang=shapes.geos[pos].s_ang, e_ang=shapes.geos[pos].e_ang, dir=shapes.geos[pos].ext, O=shapes.geos[pos].O))
                    newshape.geos[-1].col='Black'
                   
            pos+=1
        shapes.geos.pop(-1)
       
        return (newshape)
      
    
#---------------------------------------------------------------------------------------------
# generate raw Compensation data
#---------------------------------------------------------------------------------------------

    def GenRawCompData(self,ins,radius):
      
        outs=Polylines()
        outs.r=radius
        num_elements=len(ins.geos)
        pos=0;   
        pnew=0 
        ins.cut_cor=30 ##########################################################
        while pos<num_elements:
            
            if(ins.geos[pos].type=='LineGeo'):
                if(ins.cut_cor!=31):
                    Pan=ins.geos[pos].Pa
                    Pen=ins.geos[pos].Pe
                    Pan.x-=ins.geos[pos].nva.x*radius
                    Pan.y-=ins.geos[pos].nva.y*radius
                    Pen.x-=ins.geos[pos].nve.x*radius
                    Pen.y-=ins.geos[pos].nve.y*radius
                    print('1')
                else:
                    
                    Pan=ins.geos[pos].Pa
                    Pen=ins.geos[pos].Pe
                    Pan.x+=ins.geos[pos].nva.x*radius
                    Pan.y+=ins.geos[pos].nva.y*radius
                    Pen.x+=ins.geos[pos].nve.x*radius
                    Pen.y+=ins.geos[pos].nve.y*radius
                outs.geos.append(LineGeo(Pa=Pan, Pe=Pen)) 
                outs.geos[-1].col='Green'
                print('2')
            elif(ins.geos[pos].type=='ArcGeo'): 
                o=ins.geos[pos].O
                s_ang=ins.geos[pos].s_ang
                e_ang=ins.geos[pos].e_ang
                if(ins.cut_cor!=31):
                    if(ins.geos[pos].ext<0):
                        rn=ins.geos[pos].r+radius
                        Pan=ins.geos[pos].Pa
                        Pen=ins.geos[pos].Pe
                        Pan.y+=sin(s_ang)*radius
                        Pan.x+=cos(s_ang)*radius
                        Pen.y+=sin(e_ang)*radius
                        Pen.x+=cos(e_ang)*radius
                        ext=ins.geos[pos].ext
                        outs.geos.append(ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=ext, s_ang=s_ang, e_ang=e_ang, O=o))
                        outs.geos[-1].col='Green'
                        print('3')
                    else:
                        r=ins.geos[pos].r
                        if(r>=radius):
                            rn=ins.geos[pos].r-radius
                            Pan=ins.geos[pos].Pa
                            Pen=ins.geos[pos].Pe
                            Pan.y-=sin(s_ang)*radius
                            Pan.x-=cos(s_ang)*radius
                            Pen.y-=sin(e_ang)*radius
                            Pen.x-=cos(e_ang)*radius
                            ext=ins.geos[pos].ext
                            outs.geos.append(ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=ext, s_ang=s_ang, e_ang=e_ang, O=o))
                            outs.geos[-1].col='Green'
                            print('4')
                        else:
                            pass
                else:
                    if(ins.geos[pos].ext>0):
                        rn=ins.geos[pos].r+radius
                        Pan=ins.geos[pos].Pa
                        Pen=ins.geos[pos].Pe
                        Pan.y+=sin(s_ang)*radius
                        Pan.x+=cos(s_ang)*radius
                        Pen.y+=sin(e_ang)*radius
                        Pen.x+=cos(e_ang)*radius
                        ext=ins.geos[pos].ext
                        outs.geos.append(ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=ext, s_ang=s_ang, e_ang=e_ang, O=o))
                        outs.geos[-1].col='Green'
                        print('5')
                    else:
                        r=ins.geos[pos].r
                        if(r>=radius):
                            rn=ins.geos[pos].r-radius
                            Pan=ins.geos[pos].Pa
                            Pen=ins.geos[pos].Pe
                            Pan.y-=sin(s_ang)*radius
                            Pan.x-=cos(s_ang)*radius
                            Pen.y-=sin(e_ang)*radius
                            Pen.x-=cos(e_ang)*radius
                            ext=ins.geos[pos].ext
                            outs.geos.append(ArcGeo(Pa=Pan, Pe=Pen, r=rn, dir=ext, s_ang=s_ang, e_ang=e_ang, O=o))
                            outs.geos[-1].col='Green'
                            print('6')
                        else:
                            pass
                
                        
            pos+=1
        return (outs)
        
#---------------------------------------------------------------------------------------------
# handle lines Step1
#---------------------------------------------------------------------------------------------

    def compsteplines(self,ins):
      
        outs=Polylines()
        
        num_elements=len(ins.geos)
        pos=0;   
        pnew=0 
     
        while pos<num_elements:
            outs.geos.append(ins.geos[pos])
            pos+=1
        pos=0
        if ins.closed==0:
            num_elements+=2
            outs.geos.append(ins.geos[0])
            outs.geos.append(ins.geos[1])
        while pos<num_elements-1:    
            if(outs.geos[pos].type=='LineGeo' and outs.geos[pos+1].type=='LineGeo'):
                self.CheckIntersectLineLine(outs.geos[pos],outs.geos[pos+1])
                if(self.num>0):
                    print('Step1:line/line intersect', self.ISPstatus1a, self.ISPstatus1b)
                    if(self.ISPstatus1a=='above' and self.ISPstatus1b=='under'):
                        print('found a/u')
                        outs.geos[pos]=LineGeo(Pa=outs.geos[pos].Pa, Pe=self.P1)
                        outs.geos[pos+1]=LineGeo(Pa=self.P1, Pe=outs.geos[pos+1].Pe)
                        outs.geos[pos].col='Blue'
                       
                    if(self.ISPstatus1a=='under' and self.ISPstatus1b=='above'):
                        print('found a/u')
                        outs.geos[pos]=LineGeo(Pa=self.P1, Pe=outs.geos[pos].Pe)
                        outs.geos[pos+1]=LineGeo(Pa=outs.geos[pos+1].Pa, Pe=self.P1)
                        outs.geos[pos].col='Blue'
                       
                    if(self.ISPstatus1a=='between' and self.ISPstatus1b=='between'):
                        print('found b/b')
                        outs.geos[pos]=LineGeo(Pa=outs.geos[pos].Pa, Pe=self.P1)
                        outs.geos[pos+1]=LineGeo(Pa=self.P1, Pe=outs.geos[pos+1].Pe)
                        outs.geos[pos].col='Blue'
                        
                    if(self.ISPstatus1a=='between' and self.ISPstatus1b=='at_start'):
                        print('found a/u')
                        outs.geos[pos]=LineGeo(Pa=outs.geos[pos].Pa, Pe=self.P1)
                        outs.geos[pos+1]=LineGeo(Pa=self.P1, Pe=outs.geos[pos+1].Pe)
                        outs.geos[pos].col='Blue'
                        
                    if(self.ISPstatus1a=='between' and (self.ISPstatus1b=='above' or self.ISPstatus1b=='under')):
                        print('found a/u')
                        outs.geos.insert(pos+1,LineGeo(Pa=outs.geos[pos].Pe, Pe=outs.geos[pos+1].Pa) )
                        outs.geos[pos].col='Blue'
                        outs.geos[pos+1].col='Blue'
                        pos+=1
                        num_elements+=1
                    if(self.ISPstatus1b=='between' and (self.ISPstatus1a=='above' or self.ISPstatus1a=='under')):       
                        print('found a/u')
                        outs.geos.insert(pos+1,LineGeo(Pa=outs.geos[pos].Pe, Pe=outs.geos[pos+1].Pa) )
                        outs.geos[pos].col='Blue'
                        outs.geos[pos+1].col='Blue'
                        pos+=1
                        num_elements+=1
                       
            if(outs.geos[pos].type=='LineGeo' and outs.geos[pos+1].type=='ArcGeo'):
                self.CheckIntersectLineArc(outs.geos[pos],outs.geos[pos+1])
                if self.num==0:
                    print('found LineArc bw/ab-un')
                    Pa=outs.geos[pos].Pe
                    Pe=outs.geos[pos+1].Pa
                    s_ang=atan2(Pa.y, Pa.y)
                    e_ang=atan2
                    outs.geos.insert(pos+1, ArcGeo(Pa=outs.geos[pos].Pa, Pe=outs.geos[pos+1].Pa))
                    outs.geos[pos].col='Blue'
                    outs.geos[pos+1].col='Blue'
                    pos+=1
                    num_elements+=1
                else:
                    print('Step1:line/arc intersect', self.ISPstatus1a, self.ISPstatus1b,self.ISPstatus2a, self.ISPstatus2b)
                    if((self.ISPstatus1a=='between' or self.ISPstatus1a=='at_start' or self.ISPstatus1a=='at_end') and (self.ISPstatus1b=='between' or self.ISPstatus1b=='at_start' or self.ISPstatus1b=='at_end')):
                        print('found LineArc b/b')
                        
                        outs.geos[pos]=LineGeo(Pa=outs.geos[pos].Pa, Pe=self.P1)
                        outs.geos[pos+1]=ArcGeo(Pa=self.P1, Pe=outs.geos[pos+1].Pe, r=outs.geos[pos+1].r, O=outs.geos[pos+1].O, dir=outs.geos[pos+1].ext)
                        outs.geos[pos].col='Blue'
                      
                    if((self.ISPstatus2a=='between' or self.ISPstatus2a=='at_start' or self.ISPstatus2a=='at_end') and (self.ISPstatus2b=='between' or self.ISPstatus2b=='at_start' or self.ISPstatus2b=='at_end')):
                        print('found LineArc b/b')
                        
                        outs.geos[pos]=LineGeo(Pa=outs.geos[pos].Pa, Pe=self.P2)
                        outs.geos[pos+1]=ArcGeo(Pa=self.P2, Pe=outs.geos[pos+1].Pe, r=outs.geos[pos+1].r, O=outs.geos[pos+1].O, dir=outs.geos[pos+1].ext)
                        outs.geos[pos].col='Blue'
                        
                    if((self.ISPstatus1a=='above') and (self.ISPstatus1b=='under')):
                        print('found LineArc ab/un')
                        outs.geos[pos]=LineGeo(Pa=outs.geos[pos].Pa, Pe=self.P1)
                        outs.geos[pos+1]=ArcGeo(Pa=self.P1, Pe=outs.geos[pos+1].Pe, r=outs.geos[pos+1].r, O=outs.geos[pos+1].O, dir=outs.geos[pos+1].ext)
                        outs.geos[pos].col='Blue'
                        
                    if((self.ISPstatus2a=='above') and (self.ISPstatus2b=='under')):
                        print('found LineArc ab/un')
                        outs.geos[pos]=LineGeo(Pa=outs.geos[pos].Pa, Pe=self.P2)
                        outs.geos[pos+1]=ArcGeo(Pa=self.P2, Pe=outs.geos[pos+1].Pe, r=outs.geos[pos+1].r, O=outs.geos[pos+1].O, dir=outs.geos[pos+1].ext)
                        outs.geos[pos].col='Blue'
                        
                    if((self.ISPstatus1a=='above' and self.ISPstatus1b=='between')or (self.ISPstatus2a=='above' and self.ISPstatus2b=='between')):
                        print('found LineArc ab/bw')
                        outs.geos.insert(pos+1, LineGeo(Pa=outs.geos[pos].Pa, Pe=outs.geos[pos+1].Pa))
                        outs.geos[pos].col='Blue'
                        outs.geos[pos+1].col='Blue'
                        pos+=1
                        num_elements+=1
                        
                    if((self.ISPstatus1a=='between' and ( self.ISPstatus1b=='above' or self.ISPstatus1b=='under' ))or (self.ISPstatus2a=='above' and ( self.ISPstatus2b=='above' or self.ISPstatus2b=='under' ))):
                        print('found LineArc bw/ab-un')
                        outs.geos.insert(pos+1, LineGeo(Pa=outs.geos[pos].Pa, Pe=outs.geos[pos+1].Pa))
                        outs.geos[pos].col='Blue'
                        outs.geos[pos+1].col='Blue'
                        pos+=1
                        num_elements+=1
                        
                    
            pos+=1
        outs.geos[0]=outs.geos[pos]
        return (outs)
#---------------------------------------------------------------------------------------------
# Check for intersection between 2 Lines
#---------------------------------------------------------------------------------------------

    def CheckIntersectLineLine(self,L1,L2):
       
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
        if(abs(dx2)>=abs(dy2)):
            n=(day-dax*dy2/dx2)/(dx1*dy2/dx2 -dy1)
            u=(dax+n*dx1)/dx2
            self.P1.x=L1.Pa.x+n*dx1
            self.P1.y=L1.Pa.y+n*dy1
            self.v1=n
            self.v2=u
            
        else:
           
            n=(dax-day*dx2/dy2)/(dy1*dx2/dy2 -dx1)
            u=(day+n*dy1)/dy2
            self.P1.x=L1.Pa.x+n*dx1
            self.P1.y=L1.Pa.y+n*dy1
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
        self.v1=v1
        self.v2=v2
        
        i_ext=atan2(self.P1.y-K1.O.y,self.P1.x-K1.O.x)-K1.s_ang
        if K1.ext>0:
             i_ext=i_ext%(-2*pi)
             i_ext-=floor(i_ext/(2*pi))*(2*pi)
        else:
            i_ext=i_ext%(-2*pi)
            i_ext+=ceil(i_ext/(2*pi))*(2*pi)
        if(2*pi-abs(i_ext))<0.00001:
            i_ext=0
        self.P1_ext_a=i_ext
        delta= i_ext/K1.ext
        
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
            
        i_ext=atan2(self.P2.y-K1.O.y,self.P2.x-K1.O.x)-K1.s_ang
        if K1.ext>0:
             i_ext=i_ext%(-2*pi)
             i_ext-=floor(i_ext/(2*pi))*(2*pi)
        else:
            i_ext=i_ext%(-2*pi)
            i_ext+=ceil(i_ext/(2*pi))*(2*pi)
        if(2*pi-abs(i_ext))<0.00001:
            i_ext=0
        self.P2_ext_a=i_ext
        delta= i_ext/K1.ext    
            
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
        print ('st1a,st2a,st1b,st2b,v1,v2',self.ISPstatus1a,self.ISPstatus2a,self.ISPstatus1b,self.ISPstatus2b, self.v1,self.v2, )

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

        res = sqrt(pow(abs(K2.O.x - K1.O.x),2)+pow(abs(K2.O.y - K1.O.y),2));
      

        if(res <= abs(r1-r2)):
            return (result)

        if(res > abs(r1 + r2)):
            return (result)
            
        if((K1.O.x - K2.O.x == 0) and (K1.O.y - K2.O.y == 0)):
            return (result)

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
            print('4',a,b,c)
            self.P1.y = (-b + sqrt(pow(b,2) - 4*a*c) )/(2*a)
            self.P2.y = (-b - sqrt(pow(b,2) - 4*a*c) )/(2*a)
            self.P1.x = self.P1.y * d1 + d2
            self.P2.x = self.P2.y * d1 + d2


        if(self.P1.y == self.P2.y and self.P1.x == self.P2.x):
            self.num=1
        else:
            self.num=2

        i_ext=atan2(self.P1.y-K1.O.y,self.P1.x-K1.O.x)-K1.s_ang
        if K1.ext>0:
             i_ext=i_ext%(-2*pi)
             i_ext-=floor(i_ext/(2*pi))*(2*pi)
        else:
            i_ext=i_ext%(-2*pi)
            i_ext+=ceil(i_ext/(2*pi))*(2*pi)
        if(2*pi-abs(i_ext))<0.00001:
            i_ext=0
        self.P1_ext_a=i_ext
        print('calcu', K1.O.y+K1.r*sin(self.P1_ext_a+K1.s_ang),K1.O.x+K1.r*cos(self.P1_ext_a+K1.s_ang))
        delta= i_ext/K1.ext
      
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
        
            

        i_ext=atan2(self.P2.y-K1.O.y,self.P2.x-K1.O.x)-K1.s_ang
        if K1.ext>0:
             i_ext=i_ext%(-2*pi)
             i_ext-=floor(i_ext/(2*pi))*(2*pi)
        else:
            i_ext=i_ext%(-2*pi)
            i_ext+=ceil(i_ext/(2*pi))*(2*pi)
        if(2*pi-abs(i_ext))<0.00001:
            i_ext=0
        self.P2_ext_a=i_ext
        
        delta= i_ext/K1.ext
       
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
        
            
            
        i_ext=atan2(self.P1.y-K2.O.y,self.P1.x-K2.O.x)-K2.s_ang
        if K2.ext>0:
             i_ext=i_ext%(-2*pi)
             i_ext-=floor(i_ext/(2*pi))*(2*pi)
        else:
            i_ext=i_ext%(-2*pi)
            i_ext+=ceil(i_ext/(2*pi))*(2*pi)
        if(2*pi-abs(i_ext))<0.00001:
            i_ext=0
        self.P1_ext_b=i_ext

        delta= i_ext/K2.ext
      
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
        
            

        i_ext=atan2(self.P2.y-K2.O.y,self.P2.x-K2.O.x)-K2.s_ang
        if K2.ext>0:
             i_ext=i_ext%(-2*pi)
             i_ext-=floor(i_ext/(2*pi))*(2*pi)
        else:
            i_ext=i_ext%(-2*pi)
            i_ext+=ceil(i_ext/(2*pi))*(2*pi)
        if(2*pi-abs(i_ext))<0.00001:
            i_ext=0
        self.P2_ext_b=i_ext
        
        delta= i_ext/K2.ext
       
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
        
        
        print ('num,x1,y1,x2,y2, K1.ext, K2.ext',self.num,self.P1.x,self.P1.y,self.P2.x,self.P2.y, K1.ext, K2.ext)
        print ('st1a,st2a,st1b,st2b,v1,v2',self.ISPstatus1a,self.ISPstatus2a,self.ISPstatus1b,self.ISPstatus2b, self.v1,self.v2, )

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
            return(result)

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

        i_ext=atan2(self.P1.y-K1.O.y,self.P1.x-K1.O.x)-K1.s_ang
        if K1.ext>0:
             i_ext=i_ext%(-2*pi)
             i_ext-=floor(i_ext/(2*pi))*(2*pi)
        else:
            i_ext=i_ext%(-2*pi)
            i_ext+=ceil(i_ext/(2*pi))*(2*pi)
        if(2*pi-abs(i_ext))<0.00001:
            i_ext=0
        self.P1_ext_a=i_ext
            
        delta=i_ext/K1.ext
        print('delta,i_ext', delta, i_ext)
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
        
        i_ext=atan2(self.P2.y-K1.O.y,self.P2.x-K1.O.x)-K1.s_ang
        if K1.ext>0:
             i_ext=i_ext%(-2*pi)
             i_ext-=floor(i_ext/(2*pi))*(2*pi)
        else:
            i_ext=i_ext%(-2*pi)
            i_ext+=ceil(i_ext/(2*pi))*(2*pi)
        if(2*pi-abs(i_ext))<0.00001:
            i_ext=0
        self.P2_ext_a=i_ext
        delta=i_ext/K1.ext
        print('delta,i_ext', delta, i_ext)
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
        print ('st1a,st2a,st1b,st2b,v1,v2',self.ISPstatus1a,self.ISPstatus2a,self.ISPstatus1b,self.ISPstatus2b, self.v1,self.v2, )

        return 
    

#---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------

#print ('jetzt geht es los!')
#ISP=InterSectionPoint()#

#O1=PointClass(2.0,0.0)
#Pa1=PointClass(-1,0)
#Pe1=PointClass(5,0)

#O2=PointClass(-2.0,0.0)
#Pa2=PointClass(-5,0)
#Pe2=PointClass(1,0)

#K1=ArcGeo(O=O1,Pa=Pa1,Pe=Pe1,r=3,dir=-1)
#K2=ArcGeo(O=O2,Pa=Pa2,Pe=Pe2,r=3,dir=-1)

#Pa=PointClass(0.0,1.0)
#Pe=PointClass(3.0,1.0)

#L1=LineGeo(Pa=Pa,Pe=Pe)
#ISP.CheckIntersectArcArc(K1,K2)
#ISP.CheckIntersectLineArc(L1,K1)

#print ('jetzt geht es los!')


