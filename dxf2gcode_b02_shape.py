#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_shape.py
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
#
#Main Class Shape

#import sys, os, string, ConfigParser 
from dxf2gcode_b02_point import PointClass, LineGeo, ArcGeo
from math import cos, sin, radians, degrees

class ShapeClass:
    def __init__(self,nr='None',ent_nr='None',ent_cnr='None',closed=0,\
                 p0=PointClass(x=0.0,y=0.0),pb=PointClass(x=0.0,y=0.0),sca=[],rot=0.0,cut_cor=40,length=0.0,geos=[],geos_hdls=[]):
        self.nr=nr
        self.ent_nr=ent_nr
        self.ent_cnr=ent_cnr
        self.closed=closed
        self.p0=p0
        self.pb=pb
        self.sca=sca
        self.rot=rot
        self.cut_cor=40
        self.length=length
        self.geos=geos
        self.geos_hdls=geos_hdls
        print self
        
    def __str__(self):
        return ('\nnr:          %i' %self.nr)+\
               ('\nent_nr:      %i' %self.ent_nr)+\
               ('\nent_cnr:      %i' %self.ent_cnr)+\
               ('\nclosed:      %i' %self.closed)+\
               ('\np0:          %s' %self.p0)+\
               ('\npb:          %s' %self.pb)+\
               ('\nsca:         %s' %self.sca)+\
               ('\nrot:         %s' %self.rot)+\
               ('\ncut_cor:     %s' %self.cut_cor)+\
               ('\nlen(geos):   %i' %len(self.geos))+\
               ('\nlength:      %0.2f' %self.length)+\
               ('\ngeos:        %s' %self.geos)
    

    def reverse(self):
        self.geos.reverse()
        for geo in self.geos: 
            geo.reverse()

    def switch_cut_cor(self):
        if self.cut_cor==41:
            self.cut_cor=42
        elif self.cut_cor==42:
            self.cut_cor=41

    def get_st_en_points(self):
        st_point, st_angle=self.geos[0].get_start_end_points(0)
        start=(st_point*self.sca)+self.p0
        
        en_point, en_angle=self.geos[-1].get_start_end_points(1)
        ende=en_point*self.sca+self.p0
        return [start,ende]

    def plot2can(self,canvas):
        for geo in self.geos:
            self.geos_hdls+=geo.plot2can(canvas,self.p0,self.pb,self.sca,self.rot,self.nr)
            
    def plot_cut_info(self,CanvasClass,config):
        hdls=[]
        hdls.append(self.plot_start(CanvasClass))
        hdls.append(self.plot_end(CanvasClass))
        if self.cut_cor>40:
            hdls.append(self.plot_cut_cor(CanvasClass))

            #Versatz des Zeichnens durch Position
            P0=PointClass(x=-CanvasClass.dx*CanvasClass.scale,\
                          y=-CanvasClass.dy*CanvasClass.scale-CanvasClass.canvas.winfo_height())
            
            #Korrektur der Skalierung
            sca=[CanvasClass.scale]*3
            
            self.make_start_moves(config)
            hdls+=self.st_move[1].plot2can(CanvasClass.canvas,P0,sca,tag=self.nr,col='SteelBlue3')
            hdls+=self.st_move[2].plot2can(CanvasClass.canvas,P0,sca,tag=self.nr,col='SteelBlue3')
        return hdls
            
    def plot_start(self,CanvasClass):
        st_point, st_angle=self.geos[0].get_start_end_points(0)
        start=(st_point*self.sca)+self.p0
        
        x_ca,y_ca=CanvasClass.get_can_coordinates(start.x,start.y)
        length=20
        dx=cos(radians(st_angle))*length
        dy=sin(radians(st_angle))*length

        hdl=Line(CanvasClass.canvas,x_ca,-y_ca,x_ca+dx,-y_ca-dy,fill='SteelBlue3',arrow='last')
        return hdl

    def plot_cut_cor(self,CanvasClass):
        st_point, st_angle=self.geos[0].get_start_end_points(0)
        start=(st_point*self.sca)+self.p0
        x_ca,y_ca=CanvasClass.get_can_coordinates(start.x,start.y)
        length=20
        
        if self.cut_cor==41:
            st_angle=st_angle+90
        else:
            st_angle=st_angle-90
            
        dx=cos(radians(st_angle))*length
        dy=sin(radians(st_angle))*length

        hdl=Line(CanvasClass.canvas,x_ca,-y_ca,x_ca+dx,-y_ca-dy,fill='SteelBlue3',arrow='last')
        return hdl

    def plot_end(self,CanvasClass):
        en_point, en_angle=self.geos[-1].get_start_end_points(1)
        ende=(en_point*self.sca)+self.p0
        
        x_ca,y_ca=CanvasClass.get_can_coordinates(ende.x,ende.y)
        length=20
        dx=cos(radians(en_angle))*length
        dy=sin(radians(en_angle))*length

        hdl=Line(CanvasClass.canvas,x_ca,-y_ca,x_ca+dx,-y_ca-dy,fill='PaleGreen2',arrow='first')
        return hdl

    def make_start_moves(self,config):
        self.st_move=[]

        #Einlaufradius und Versatz 
        start_rad=config.start_rad.get()
        start_ver=start_rad

        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad=config.tool_dia.get()/2
    
        #Errechnen des Startpunkts mit und ohne Werkzeug Kompensation        
        st_point, st_angle=self.geos[0].get_start_end_points(0)
        start_cont=(st_point*self.sca)+self.p0
      
        if self.cut_cor==40:              
            self.st_move.append(start_cont)

        #Fräsradiuskorrektur Links        
        elif self.cut_cor==41:
            #Mittelpunkts für Einlaufradius
            Oein=start_cont.get_arc_point(st_angle+90,start_rad+tool_rad)
            #Startpunkts für Einlaufradius
            Pa_ein=Oein.get_arc_point(st_angle+180,start_rad+tool_rad)
            #Startwerts für Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(st_angle+90,start_ver)
            
            #Eintauchpunkts errechnete Korrektur
            start_ein=Pg_ein.get_arc_point(st_angle,tool_rad)
            self.st_move.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line=LineGeo(Pg_ein,Pa_ein)
            self.st_move.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad=ArcGeo(Pa=Pa_ein,Pe=start_cont,O=Oein,r=start_rad+tool_rad,dir=1)
            self.st_move.append(start_rad)
            
        #Fräsradiuskorrektur Rechts        
        elif self.cut_cor==42:

            #Mittelpunkt für Einlaufradius
            Oein=start_cont.get_arc_point(st_angle-90,start_rad+tool_rad)
            #Startpunkt für Einlaufradius
            Pa_ein=Oein.get_arc_point(st_angle+180,start_rad+tool_rad)
            IJ=Oein-Pa_ein
            #Startwerts für Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(st_angle-90,start_ver)
            
            #Eintauchpunkts errechnete Korrektur
            start_ein=Pg_ein.get_arc_point(st_angle,tool_rad)
            self.st_move.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line=LineGeo(Pg_ein,Pa_ein)
            self.st_move.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad=ArcGeo(Pa=Pa_ein,Pe=start_cont,O=Oein,r=start_rad+tool_rad,dir=0)
            self.st_move.append(start_rad)
    
    def Write_GCode(self,config,postpro):

        #Erneutes erstellen der Einlaufgeometrien
        self.make_start_moves(config)
        
        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad=config.tool_dia.get()/2
        
        depth=config.axis3_mill_depth.get()
        max_slice=config.axis3_slice_depth.get()

        #Scheibchendicke bei Frästiefe auf Frästiefe begrenzen
        if -abs(max_slice)<=depth:
            mom_depth=depth
        else:
            mom_depth=-abs(max_slice)


        #Positionieren des Werkzeugs über dem Anfang und Eintauchen
        self.st_move[0].Write_GCode([1,1,1],\
                                    PointClass(x=0,y=0),\
                                    0.0,\
                                    postpro)
        
        postpro.rap_pos_z(config.axis3_safe_margin.get())
        postpro.chg_feed_rate(config.F_G1_Depth.get())
        postpro.lin_pol_z(mom_depth)
        postpro.chg_feed_rate(config.F_G1_Plane.get())

        #Wenn G41 oder G42 an ist Fräsradiuskorrektur        
        if self.cut_cor!=40:
            
            #Errechnen des Startpunkts ohne Werkzeug Kompensation
            #und einschalten der Kompensation     
            start_cor, st_angle=self.st_move[1].get_start_end_points(0)
            postpro.set_cut_cor(self.cut_cor,start_cor)
            
            self.st_move[1].Write_GCode([1,1,1],\
                                        PointClass(x=0,y=0),\
                                        0.0,\
                                        postpro)
            
            self.st_move[2].Write_GCode([1,1,1],\
                                        PointClass(x=0,y=0),\
                                        0.0,\
                                        postpro)

        #Schreiben der Geometrien für den ersten Schnitt
        for geo in self.geos:
            geo.Write_GCode(self.sca,self.p0,self.rot,postpro)

        #Ausschalten der Fräsradiuskorrektur
        if (not(self.cut_cor==40))&(postpro.cancel_cc_for_depth==1):
            en_point, en_angle=self.geos[-1].get_start_end_points(-1)
            end_cont=(en_point*self.sca)+self.p0
            if self.cut_cor==41:
                pos_cut_out=end_cont.get_arc_point(en_angle-90,tool_rad)
            elif self.cut_cor==42:
                pos_cut_out=end_cont.get_arc_point(en_angle+90,tool_rad)         
            postpro.deactivate_cut_cor(pos_cut_out)            

        #Zählen der Schleifen
        snr=0
        #Schleifen für die Anzahl der Schnitte
        while mom_depth>depth:
            snr+=1
            mom_depth=mom_depth-abs(max_slice)
            if mom_depth<depth:
                mom_depth=depth                

            #Erneutes Eintauchen
            postpro.chg_feed_rate(config.F_G1_Depth.get())
            postpro.lin_pol_z(mom_depth)
            postpro.chg_feed_rate(config.F_G1_Plane.get())

            #Falls es keine geschlossene Kontur ist    
            if self.closed==0:
                self.reverse()
                self.switch_cut_cor()
                
            #Falls cut correction eingeschaltet ist diese einschalten.
            if ((not(self.cut_cor==40))&(self.closed==0))or(postpro.cancel_cc_for_depth==1):
                #Errechnen des Startpunkts ohne Werkzeug Kompensation
                #und einschalten der Kompensation     
                st_point, st_angle=self.geos[0].get_start_end_points(0)
                start_cor=(st_point*self.sca)+self.p0
                postpro.set_cut_cor(self.cut_cor,start_cor)
                
            for geo_nr in range(len(self.geos)):
                self.geos[geo_nr].Write_GCode(self.sca,self.p0,self.rot,postpro)

            #Errechnen des Konturwerte mit Fräsradiuskorrektur und ohne
            en_point, en_angle=self.geos[-1].get_start_end_points(-1)
            en_point=(en_point*self.sca)+self.p0
            if self.cut_cor==41:
                en_point=en_point.get_arc_point(en_angle-90,tool_rad)
            elif self.cut_cor==42:
                en_point=en_point.get_arc_point(en_angle+90,tool_rad)

            #Ausschalten der Fräsradiuskorrektur falls benötigt          
            if (not(self.cut_cor==40))&(postpro.cancel_cc_for_depth==1):         
                postpro.deactivate_cut_cor(en_point)
     
        #Anfangswert für Direction wieder herstellen falls nötig
        if (snr%2)>0:
            self.reverse()
            self.switch_cut_cor()

        #Fertig und Zurückziehen des Werkzeugs
        postpro.lin_pol_z(config.axis3_safe_margin.get())
        postpro.rap_pos_z(config.axis3_retract.get())

        #Falls Fräsradius Korrektur noch nicht ausgeschaltet ist ausschalten.
        if (not(self.cut_cor==40))&(not(postpro.cancel_cc_for_depth)):
            postpro.deactivate_cut_cor(en_point)        

        return 1      
