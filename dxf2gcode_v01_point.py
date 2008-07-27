#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_v01_point
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


from Canvas import Oval, Arc, Line
from math import sqrt, sin, cos, atan2, radians, degrees, pi, floor, ceil

class PointClass:
    def __init__(self,x=0,y=0):
        self.x=x
        self.y=y
    def __str__(self):
        return ('X ->%6.3f  Y ->%6.3f' %(self.x,self.y))
        #return ('CPoints.append(PointClass(x=%6.5f, y=%6.5f))' %(self.x,self.y))
    def __cmp__(self, other) : 
      return (self.x == other.x) and (self.y == other.y)
    def __neg__(self):
        return -1.0*self
    def __add__(self, other): # add to another point
        return PointClass(self.x+other.x, self.y+other.y)
    def __sub__(self, other):
        return self + -other
    def __rmul__(self, other):
        return PointClass(other * self.x,  other * self.y)
    def __mul__(self, other):
        if type(other)==list:
            #Skalieren des Punkts
            return PointClass(x=self.x*other[0],y=self.y*other[1])
        else:
            #Skalarprodukt errechnen
            return self.x*other.x + self.y*other.y

    def unit_vector(self,Pto=None):
        diffVec=Pto-self
        l=diffVec.distance()
        return PointClass(diffVec.x/l,diffVec.y/l)
    def distance(self,other=None):
        if type(other)==type(None):
            other=PointClass(x=0.0,y=0.0)
        return sqrt(pow(self.x-other.x,2)+pow(self.y-other.y,2))
    def norm_angle(self,other=None):
        if type(other)==type(None):
            other=PointClass(x=0.0,y=0.0)
        return atan2(other.y-self.y,other.x-self.x)
    def isintol(self,other,tol):
        return (abs(self.x-other.x)<=tol) & (abs(self.y-other.y)<tol)
    def transform_to_Norm_Coord(self,other,alpha):
        xt=other.x+self.x*cos(alpha)+self.y*sin(alpha)
        yt=other.y+self.x*sin(alpha)+self.y*cos(alpha)
        return PointClass(x=xt,y=yt)
    def get_arc_point(self,ang=0,r=1):
        return PointClass(x=self.x+cos(radians(ang))*r,\
                          y=self.y+sin(radians(ang))*r)

    def Write_GCode(self,sca,p0,postpro):
        point=self*sca+p0
        #return("G0 %s%0.3f %s%0.3f\n" %(axis1,point.x,axis2,point.y))
        return postpro.rap_pos_xy(point)
    
    def triangle_height(self,other1,other2):
        #Die 3 Längen des Dreiecks ausrechnen
        a=self.distance(other1)
        b=other1.distance(other2)
        c=self.distance(other2)
        return sqrt(pow(b,2)-pow((pow(c,2)+pow(b,2)-pow(a,2))/(2*c),2))                
      
class PointsClass:
    #Initialisieren der Klasse
    def __init__(self,point_nr=0, geo_nr=0,Layer_Nr=None,be=[],en=[],be_cp=[],en_cp=[]):
        self.point_nr=point_nr
        self.geo_nr=geo_nr
        self.Layer_Nr=Layer_Nr
        self.be=be
        self.en=en
        self.be_cp=be_cp
        self.en_cp=en_cp
        
    
    #Wie die Klasse ausgegeben wird.
    def __str__(self):
        # how to print the object
        return '\npoint_nr ->'+str(self.point_nr)+'\ngeo_nr ->'+str(self.geo_nr) \
               +'\nLayer_Nr ->'+str(self.Layer_Nr)\
               +'\nbe ->'+str(self.be)+'\nen ->'+str(self.en)\
               +'\nbe_cp ->'+str(self.be_cp)+'\nen_cp ->'+str(self.en_cp)

class ContourClass:
    #Initialisieren der Klasse
    def __init__(self,cont_nr=0,closed=0,order=[],length=0):
        self.cont_nr=cont_nr
        self.closed=closed
        self.order=order
        self.length=length
        

    #Komplettes umdrehen der Kontur
    def reverse(self):
        self.order.reverse()
        for i in range(len(self.order)):
            if self.order[i][1]==0:
                self.order[i][1]=1
            else:
                self.order[i][1]=0
        return

    #Ist die klasse geschlossen wenn ja dann 1 zurück geben
    def is_contour_closed(self):

        #Immer nur die Letzte überprüfen da diese neu ist        
        for j in range(len(self.order)-1):
            if self.order[-1][0]==self.order[j][0]:
                if j==0:
                    self.closed=1
                    return self.closed
                else:
                    self.closed=2
                    return self.closed
        return self.closed


    #Ist die klasse geschlossen wenn ja dann 1 zurück geben
    def remove_other_closed_contour(self):
        for i in range(len(self.order)):
            for j in range(i+1,len(self.order)):
                #print '\ni: '+str(i)+'j: '+str(j)
                if self.order[i][0]==self.order[j][0]:
                   self.order=self.order[0:i]
                   break
        return 
    #Berechnen der Zusammengesetzen Kontur Länge
    def calc_length(self,geos=None):        
        #Falls die beste geschlossen ist und erste Geo == Letze dann entfernen
        if (self.closed==1) & (len(self.order)>1):
            if self.order[0]==self.order[-1]:
                del(self.order[-1])

        self.length=0
        for i in range(len(self.order)):
            self.length+=geos[self.order[i][0]].length
        return


    
    def analyse_and_opt(self,geos=None):
        #Errechnen der Länge
        self.calc_length(geos)
        
        #Optimierung für geschlossene Konturen
        if self.closed==1:
            summe=0
            #Berechnung der Fläch nach Gauß-Elling Positive Wert bedeutet CW
            #negativer Wert bedeutet CCW geschlossenes Polygon
            geo_point_l, dummy=geos[self.order[-1][0]].get_start_end_points(self.order[-1][1])            
            for geo_order_nr in range(len(self.order)):
                geo_point, dummy=geos[self.order[geo_order_nr][0]].get_start_end_points(self.order[geo_order_nr][1])
                summe+=(geo_point_l.x*geo_point.y-geo_point.x*geo_point_l.y)/2
                geo_point_l=geo_point
            if summe>0.0:
                self.reverse()

            #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
            min_point=geo_point_l
            min_point_nr=None
            for geo_order_nr in range(len(self.order)):
                geo_point, dummy=geos[self.order[geo_order_nr][0]].get_start_end_points(self.order[geo_order_nr][1])
                #Geringster Abstand nach unten Unten Links
                if (min_point.x+min_point.y)>=(geo_point.x+geo_point.y):
                    min_point=geo_point
                    min_point_nr=geo_order_nr
            #Kontur so anordnen das neuer Startpunkt am Anfang liegt
            self.set_new_startpoint(min_point_nr)
            
        #Optimierung für offene Konturen
        else:
            geo_spoint, dummy=geos[self.order[0][0]].get_start_end_points(self.order[0][1])
            geo_epoint, dummy=geos[self.order[0][0]].get_start_end_points(not(self.order[0][1]))
            if (geo_spoint.x+geo_spoint.y)>=(geo_epoint.x+geo_epoint.y):
                self.reverse()


    #Neuen Startpunkt an den Anfang stellen
    def set_new_startpoint(self,st_p):
        self.order=self.order[st_p:len(self.order)]+self.order[0:st_p]
        
    #Wie die Klasse ausgegeben wird.
    def __str__(self):
        # how to print the object
        return '\ncont_nr ->'+str(self.cont_nr)+'\nclosed ->'+str(self.closed) \
               +'\norder ->'+str(self.order)+'\nlength ->'+str(self.length)

class ArcGeo:
    def __init__(self,Pa=None,Pe=None,O=None,r=1,s_ang=None,e_ang=None,dir=1):
        self.type="ArcGeo"
        self.Pa=Pa
        self.Pe=Pe
        self.O=O
        self.r=abs(r)

        #Falls nicht übergeben dann Anfangs- und Endwinkel ausrechen            
        if type(s_ang)==type(None):
            s_ang=O.norm_angle(Pa)
        if type(e_ang)==type(None):
            e_ang=O.norm_angle(Pe)

        #Aus dem Vorzeichen von dir den extend ausrechnen
        self.ext=e_ang-s_ang
        if dir>0.0:
            self.ext=self.ext%(-2*pi)
            self.ext-=floor(self.ext/(2*pi))*(2*pi)
        else:
            self.ext=self.ext%(-2*pi)
            self.ext+=ceil(self.ext/(2*pi))*(2*pi)

        #Falls es ein Kreis ist Umfang 2pi einsetzen        
        if self.ext==0.0:
            self.ext=2*pi
                   
        self.s_ang=s_ang
        self.e_ang=e_ang
        self.length=self.r*abs(self.ext)

    def __str__(self):
        return ("\nArcGeo")+\
               ("\nPa : %s; s_ang: %0.5f" %(self.Pa,self.s_ang))+\
               ("\nPe : %s; e_ang: %0.5f" %(self.Pe,self.e_ang))+\
               ("\nO  : %s; r: %0.3f" %(self.O,self.r))+\
               ("\next  : %0.5f; length: %0.5f" %(self.ext,self.length))

    def reverse(self):
        Pa=self.Pa
        Pe=self.Pe
        ext=self.ext
        s_ang=self.e_ang
        e_ang=self.s_ang
        
        self.Pa=Pe
        self.Pe=Pa
        self.ext=ext*-1
        self.s_ang=s_ang
        self.e_ang=e_ang

    def plot2can(self,canvas=None,p0=PointClass(x=0,y=0),sca=[1,1,1],tag=None,col='black'):

        #Das Plotten mit Tkinter hat Probleme für kleine Kreissegmente     
##        xy=p0.x+(self.O.x-abs(self.r))*sca[0],-p0.y-(self.O.y-abs(self.r))*sca[1],\
##            p0.x+(self.O.x+abs(self.r))*sca[0],-p0.y-(self.O.y+abs(self.r))*sca[1]
##
##        hdl=Arc(canvas,xy,start=degrees(self.s_ang),extent=degrees(self.ext),style="arc",\
##            tag=tag)

        x=[]; y=[]; hdl=[]
        #Alle 6 Grad ein Segment => 60 Segmente für einen Kreis !!
        segments=int((abs(degrees(self.ext))//6)+1)
        for i in range(segments+1):
            ang=self.s_ang+i*self.ext/segments
            x.append(p0.x+(self.O.x+cos(ang)*abs(self.r))*sca[0])
            y.append(p0.y+(self.O.y+sin(ang)*abs(self.r))*sca[1])

            if i>=1:
                hdl.append(Line(canvas,x[i-1],-y[i-1],x[i],-y[i],tag=tag,fill=col))       
        return hdl        

    def get_start_end_points(self,direction):
        if not(direction):
            punkt=self.Pa
            angle=degrees(self.s_ang)+90*self.ext/abs(self.ext)
        elif direction:
            punkt=self.Pe
            angle=degrees(self.e_ang)-90*self.ext/abs(self.ext)
        return punkt,angle
    
    def Write_GCode(self,sca,p0,postpro):
        st_point, st_angle=self.get_start_end_points(0)
        IJ=(self.O-st_point)*sca
        
        en_point, en_angle=self.get_start_end_points(1)
        ende=en_point*sca+p0
        
        #Vorsicht geht nicht für Ovale
        if (self.ext>0):
            #string=("G3 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,ende.x,axis2,ende.y,IJ.x,IJ.y))
            string=postpro.lin_pol_arc("ccw",ende,IJ)
        else:
            #string=("G2 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,ende.x,axis2,ende.y,IJ.x,IJ.y))
            string=postpro.lin_pol_arc("cw",ende,IJ)
        return string      
    
class LineGeo:
    def __init__(self,Pa,Pe):
        self.type="LineGeo"
        self.Pa=Pa
        self.Pe=Pe
        self.length=self.Pa.distance(self.Pe)

    def __str__(self):
        return ("\nLineGeo")+\
               ("\nPa : %s" %self.Pa)+\
               ("\nPe : %s" %self.Pe)+\
               ("\nlength: %0.5f" %self.length)        

    def reverse(self):
        Pa=self.Pa
        Pe=self.Pe
        
        self.Pa=Pe
        self.Pe=Pa

    def reverse_copy(self):
        Pa=self.Pe
        Pe=self.Pa
        return LineGeo(Pa=Pa,Pe=Pe)
        
    def plot2can(self,canvas=None,p0=PointClass(x=0,y=0),sca=[1,1,1],tag=None,col='black'):
        anf=p0+self.Pa*sca
        ende=p0+self.Pe*sca
        hdl=Line(canvas,anf.x,-anf.y,ende.x,-ende.y,tag=tag,fill=col)
        return [hdl]

    def get_start_end_points(self,direction):
        if not(direction):
            punkt=self.Pa
            angle=degrees(self.Pa.norm_angle(self.Pe))
        elif direction:
            punkt=self.Pe
            angle=degrees(self.Pe.norm_angle(self.Pa))
        return punkt, angle
    
    def Write_GCode(self,sca,p0,postpro):
        en_point, en_angle=self.get_start_end_points(1)
        ende=en_point*sca+p0
        #return("G1 %s%0.3f %s%0.3f\n" %(axis1,ende.x,axis2,ende.y))
        return postpro.lin_pol_xy(ende)
        
    def distance2point(self,point):
        try:
            AE=self.Pa.distance(self.Pe)
            AP=self.Pa.distance(point)
            EP=self.Pe.distance(point)
            AEPA=(AE+AP+EP)/2
            return abs(2*sqrt(abs(AEPA*(AEPA-AE)*(AEPA-AP)*(AEPA-EP)))/AE)
        except:
            return 1e10
            

class BiarcClass:
    def __init__(self,Pa=[],tan_a=[],Pb=[],tan_b=[],min_r=5e-4):
        min_len=1e-9        #Min Abstand für doppelten Punkt
        min_alpha=1e-4      #Winkel ab welchem Gerade angenommen wird inr rad
        max_r=5e3           #Max Radius ab welchem Gerade angenommen wird (10m)
        min_r=min_r         #Min Radius ab welchem nichts gemacht wird
        
        self.Pa=Pa
        self.tan_a=tan_a
        self.Pb=Pb
        self.tan_b=tan_b
        self.l=0.0
        self.shape=None
        self.geos=[]
        self.k=0.0

        #Errechnen der Winkel, Länge und Shape
        norm_angle,self.l=self.calc_normal(self.Pa,self.Pb)

        alpha,beta,self.teta,self.shape=self.calc_diff_angles(norm_angle,\
                                                              self.tan_a,\
                                                              self.tan_b,\
                                                              min_alpha)
        
        if(self.l<min_len):
            self.shape="Zero"
            pass
        
            
        elif(self.shape=="LineGeo"):
            #Erstellen der Geometrie
            self.shape="LineGeo"
            self.geos.append(LineGeo(self.Pa,self.Pb))
        else:
            #Berechnen der Radien, Mittelpunkte, Zwichenpunkt            
            r1, r2=self.calc_r1_r2(self.l,alpha,beta,self.teta)
            
            if (abs(r1)>max_r)or(abs(r2)>max_r):
                #Erstellen der Geometrie
                self.shape="LineGeo"
                self.geos.append(LineGeo(self.Pa,self.Pb))
                return
            
            elif (abs(r1)<min_r)or(abs(r2)<min_r):
                self.shape="Zero"
                return
          
            O1, O2, k =self.calc_O1_O2_k(r1,r2,self.tan_a,self.teta)
            
            #Berechnen der Start und End- Angles für das drucken
            s_ang1,e_ang1=self.calc_s_e_ang(self.Pa,O1,k)
            s_ang2,e_ang2=self.calc_s_e_ang(k,O2,self.Pb)

            #Berechnen der Richtung und der Extend
            dir_ang1=(tan_a-s_ang1)%(-2*pi)
            dir_ang1-=ceil(dir_ang1/(pi))*(2*pi)

            dir_ang2=(tan_b-e_ang2)%(-2*pi)
            dir_ang2-=ceil(dir_ang2/(pi))*(2*pi)
            
            
            #Erstellen der Geometrien          
            self.geos.append(ArcGeo(Pa=self.Pa,Pe=k,O=O1,r=r1,\
                                    s_ang=s_ang1,e_ang=e_ang1,dir=dir_ang1))
            self.geos.append(ArcGeo(Pa=k,Pe=self.Pb,O=O2,r=r2,\
                                    s_ang=s_ang2,e_ang=e_ang2,dir=dir_ang2)) 

    def calc_O1_O2_k(self,r1,r2,tan_a,teta):
        #print("r1: %0.3f, r2: %0.3f, tan_a: %0.3f, teta: %0.3f" %(r1,r2,tan_a,teta))
        #print("N1: x: %0.3f, y: %0.3f" %(-sin(tan_a), cos(tan_a)))
        #print("V: x: %0.3f, y: %0.3f" %(-sin(teta+tan_a),cos(teta+tan_a)))

        O1=PointClass(x=self.Pa.x-r1*sin(tan_a),\
                      y=self.Pa.y+r1*cos(tan_a))
        k=PointClass(x=self.Pa.x+r1*(-sin(tan_a)+sin(teta+tan_a)),\
                     y=self.Pa.y+r1*(cos(tan_a)-cos(tan_a+teta)))
        O2=PointClass(x=k.x+r2*(-sin(teta+tan_a)),\
                      y=k.y+r2*(cos(teta+tan_a)))
        return O1, O2, k

    def calc_normal(self,Pa,Pb):
        norm_angle=Pa.norm_angle(Pb)
        l=Pa.distance(Pb)
        return norm_angle, l        

    def calc_diff_angles(self,norm_angle,tan_a,tan_b,min_alpha):
        #print("Norm angle: %0.3f, tan_a: %0.3f, tan_b %0.3f" %(norm_angle,tan_a,tan_b))
        alpha=(norm_angle-tan_a)   
        beta=(tan_b-norm_angle)
        alpha,beta= self.limit_angles(alpha,beta)

        if alpha*beta>0.0:
            shape="C-shaped"
            teta=alpha
        elif abs(alpha-beta)<min_alpha:
            shape="LineGeo"
            teta=alpha
        else:
            shape="S-shaped"
            teta=(3*alpha-beta)/2
            
        return alpha, beta, teta, shape    

    def limit_angles(self,alpha,beta):
        #print("limit_angles: alpha: %s, beta: %s" %(alpha,beta))
        if (alpha<-pi):
           alpha += 2*pi
        if (alpha>pi):
           alpha -= 2*pi
        if (beta<-pi):
           beta += 2*pi
        if (beta>pi):
           beta -= 2*pi
        while (alpha-beta)>pi:
            alpha=alpha-2*pi
        while (alpha-beta)<-pi:
            alpha=alpha+2*pi
        #print("   -->>       alpha: %s, beta: %s" %(alpha,beta))         
        return alpha,beta
            
    def calc_r1_r2(self,l,alpha,beta,teta):
        #print("alpha: %s, beta: %s, teta: %s" %(alpha,beta,teta))
        r1=(l/(2*sin((alpha+beta)/2))*sin((beta-alpha+teta)/2)/sin(teta/2))
        r2=(l/(2*sin((alpha+beta)/2))*sin((2*alpha-teta)/2)/sin((alpha+beta-teta)/2))
        return r1, r2
    
    def calc_s_e_ang(self,P1,O,P2):
        s_ang=O.norm_angle(P1)
        e_ang=O.norm_angle(P2)
        return s_ang, e_ang
    
    def get_biarc_fitting_error(self,Pt):
        #Abfrage in welchem Kreissegment der Punkt liegt:
        w1=self.geos[0].O.norm_angle(Pt)
        if (w1>=min([self.geos[0].s_ang,self.geos[0].e_ang]))and\
           (w1<=max([self.geos[0].s_ang,self.geos[0].e_ang])):
            diff=self.geos[0].O.distance(Pt)-abs(self.geos[0].r)
        else:
            diff=self.geos[1].O.distance(Pt)-abs(self.geos[1].r)
        return abs(diff)
            
    def __str__(self):
        s= ("\nBiarc Shape: %s" %(self.shape))+\
           ("\nPa : %s; Tangent: %0.3f" %(self.Pa,self.tan_a))+\
           ("\nPb : %s; Tangent: %0.3f" %(self.Pb,self.tan_b))+\
           ("\nteta: %0.3f, l: %0.3f" %(self.teta,self.l))
        for geo in self.geos:
            s+=str(geo)
        return s
    
     
    