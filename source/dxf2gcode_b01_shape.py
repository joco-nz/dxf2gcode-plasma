#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b01_shape.py
#Programmer: Christian Kohloeffel
#E-mail:     n/A
#
#Copyright 2007-2008 Christian Kohlöffel
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

import sys, os, string, ConfigParser 
from   dxf2gcode_b01_point import PointClass
from math import cos, sin, radians, degrees
from Canvas import Line

class ShapeClass:
    def __init__(self,nr='None',ent_nr='None',ent_cnr='None',closed=0,\
                 p0=PointClass(x=0,y=0),sca=[],cut_cor=40,length=0.0,geos=[],geos_hdls=[]):
        self.nr=nr
        self.ent_nr=ent_nr
        self.ent_cnr=ent_cnr
        self.closed=closed
        self.p0=p0
        self.sca=sca
        self.cut_cor=40
        self.length=length
        self.geos=geos
        self.geos_hdls=geos_hdls
        
    def __str__(self):
        return ('\nnr:          %i' %self.nr)+\
               ('\nent_nr:      %i' %self.ent_nr)+\
               ('\nent_cnr:      %i' %self.ent_cnr)+\
               ('\nclosed:      %i' %self.closed)+\
               ('\np0:          %s' %self.p0)+\
               ('\nsca:         %s' %self.sca)+\
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
            self.geos_hdls+=geo.plot2can(canvas,self.p0,self.sca,self.nr)
            
    def plot_cut_info(self,CanvasClass):
        hdls=[]
        hdls.append(self.plot_start(CanvasClass))
        hdls.append(self.plot_end(CanvasClass))
        if self.cut_cor>40:
            hdls.append(self.plot_cut_cor(CanvasClass))
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
    
    def Write_GCode(self,string,config,axis1,axis2,axis3):

        #Einlaufradius und Versatz 
        start_rad=config.start_rad.get()
        start_ver=start_rad

        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad=config.tool_dia.get()/2
        
        depth=config.Axis3_mill_depth.get()
        max_slice=config.Axis3_slice_depth.get()

        #Scheibchendicke bei Frästiefe auf Frästiefe begrenzen
        if -abs(max_slice)<=depth:
            mom_depth=depth
        else:
            mom_depth=-abs(max_slice)

        #Errechnen des Startpunkts mit und ohne Werkzeug Kompensation        
        st_point, st_angle=self.geos[0].get_start_end_points(0)
        start_cont=(st_point*self.sca)+self.p0
        
        if self.cut_cor==40:              
            #Positionieren des Werkzeugs über dem Anfang und Eintauchen
            string+=("G0 %s%0.3f %s%0.3f\n" %(axis1,start_cont.x,axis2,start_cont.y))
            string+=("G0 %s%0.3f \n" %(axis3,config.Axis3_safe_margin.get()))
            string+=("F%0.0f\n" %config.F_G1_Depth.get())
            string+=("G1 %s%0.3f \n" %(axis3,mom_depth))
            string+=("F%0.0f\n" %config.F_G1_Plane.get())

        #Fräsradiuskorrektur Links        
        elif self.cut_cor==41:

            #Mittelpunkts für Einlaufradius
            Oein=start_cont.get_arc_point(st_angle+90,start_rad+tool_rad)
            #Startpunkts für Einlaufradius
            Pa_ein=Oein.get_arc_point(st_angle+180,start_rad+tool_rad)
            IJ=Oein-Pa_ein
            #Startwerts für Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(st_angle+90,start_ver)
            #Eintauchpunkts
            start_ein=Pg_ein.get_arc_point(st_angle,tool_rad)
            
            #Positionieren des Werkzeugs über dem Anfang und Eintauchen
            string+=("G0 %s%0.3f %s%0.3f\n" %(axis1,start_ein.x,axis2,start_ein.y))
            string+=("G0 %s%0.3f \n" %(axis3,config.Axis3_safe_margin.get()))
            string+=("F%0.0f\n" %config.F_G1_Depth.get())
            string+=("G1 %s%0.3f \n" %(axis3,mom_depth))
            string+=("F%0.0f\n" %config.F_G1_Plane.get())
            string+=("G41 \n")
            string+=("G1 %s%0.3f %s%0.3f\n" %(axis1,Pa_ein.x,axis2,Pa_ein.y))
            string+=("G3 %s%0.3f %s%0.3f I%0.3f J%0.3f \n" %(axis1,start_cont.x,axis2,start_cont.y,IJ.x,IJ.y))
            

         
        #Fräsradiuskorrektur Rechts        
        elif self.cut_cor==42:

            #Mittelpunkt für Einlaufradius
            Oein=start_cont.get_arc_point(st_angle-90,start_rad+tool_rad)
            #Startpunkt für Einlaufradius
            Pa_ein=Oein.get_arc_point(st_angle+180,start_rad+tool_rad)
            IJ=Oein-Pa_ein
            #Startwerts für Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(st_angle-90,start_ver)
            #Eintauchpunkt
            start_ein=Pg_ein.get_arc_point(st_angle,tool_rad)
            
            #Positionieren des Werkzeugs über dem Anfang und Eintauchen
            string+=("G0 %s%0.3f %s%0.3f\n" %(axis1,start_ein.x,axis2,start_ein.y))
            string+=("G0 %s%0.3f \n" %(axis3,config.Axis3_safe_margin.get()))
            string+=("F%0.0f\n" %config.F_G1_Depth.get())
            string+=("G1 %s%0.3f \n" %(axis3,mom_depth))
            string+=("F%0.0f\n" %config.F_G1_Plane.get())
            string+=("G42 \n")
            string+=("G1 %s%0.3f %s%0.3f\n" %(axis1,Pa_ein.x,axis2,Pa_ein.y))
            string+=("G2 %s%0.3f %s%0.3f I%0.3f J%0.3f \n" %(axis1,start_cont.x,axis2,start_cont.y,IJ.x,IJ.y))
            
            
        #Schreiben der Geometrien für den ersten Schnitt
        for geo in self.geos:
            string+=geo.Write_GCode(config,\
                                    self.sca,self.p0,\
                                    axis1,axis2)

        #Zählen der Schleifen
        snr=0
        #Schleifen für die Anzahl der Schnitte
        while mom_depth>depth:
            snr+=1
            mom_depth=mom_depth-abs(max_slice)
            if mom_depth<depth:
                mom_depth=depth                

            #Erneutes Eintauchen
            string+=("F%0.0f\n" %config.F_G1_Depth.get())
            string+=("G1 %s%0.3f \n" %(axis3,mom_depth))
            string+=("F%0.0f\n" %config.F_G1_Plane.get())

            #Falls es keine geschlossene Kontur ist    
            if self.closed==0:
                self.reverse()
                self.switch_cut_cor()
                
                #Falls cut correction eingeschaltet ist diese umdrehen.
                if not(self.cut_cor==40):
                    string+=("G"+str(self.cut_cor)+" \n")
                
            for geo_nr in range(len(self.geos)):
                string+=self.geos[geo_nr].Write_GCode(config,\
                                                      self.sca,self.p0,\
                                                      axis1,axis2)

        #Anfangswert für Direction wieder herstellen falls nötig
        if (snr%2)>0:
            self.reverse()
            self.switch_cut_cor()

        #Fertig und Zurückziehen des Werkzeugs
        string+=("G1 %s%0.3f \n" %(axis3,config.Axis3_safe_margin.get()))
        string+=("G0 %s%0.3f \n" %(axis3,config.Axis3_retract.get()))
        string+=("G40\n")

        return 1, string      
