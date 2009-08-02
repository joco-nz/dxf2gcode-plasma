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
from Canvas import Line

class ShapeClass:
    def __init__(self,nr='None',closed=0,
                cut_cor=40,length=0.0,
                parent=None,
                geos=[],geos_hdls=[]):
                
                    
        self.type="Shape"
        self.nr=nr
        self.closed=closed
        self.cut_cor=40
        self.length=length
        self.parent=parent
        self.geos=geos
        self.geos_hdls=geos_hdls

    def __str__(self):
        return ('\ntype:        %s' %self.type)+\
               ('\nnr:          %i' %self.nr)+\
               ('\nclosed:      %i' %self.closed)+\
               ('\ncut_cor:     %s' %self.cut_cor)+\
               ('\nlen(geos):   %i' %len(self.geos))+\
               ('\nlength:      %0.2f' %self.length)+\
               ('\ngeos:        %s' %self.geos)#+\
               #('\ngeos_hdls:   %s' %self.geos_hdls)
               #+\
               #('\nparent: %s' %self.parent)

    def reverse(self):
        self.geos.reverse()
        for geo in self.geos: 
            geo.reverse()

    def switch_cut_cor(self):
        if self.cut_cor==41:
            self.cut_cor=42
        elif self.cut_cor==42:
            self.cut_cor=41

    def get_st_en_points(self,dir=None):
        start, start_ang=self.geos[0].get_start_end_points(0,self.parent)
        ende, end_ang=self.geos[-1].get_start_end_points(1,self.parent)
        
        if dir==None:
            return start,ende
        elif dir==0:
            return start,start_ang
        elif dir==1:
            return ende, end_ang
        

    def plot2can(self,canvas):
        for geo in self.geos:
            self.geos_hdls+=geo.plot2can(canvas,self.parent,self.nr)
            
    def plot_cut_info(self,CanvasClass,config):
        hdls=[]
        hdls.append(self.plot_start(CanvasClass))
        hdls.append(self.plot_end(CanvasClass))
        if self.cut_cor>40:
            hdls.append(self.plot_cut_cor(CanvasClass))
          
            self.make_start_moves(config)
            
            
            #Versatz des Zeichnens durch Position
            P0=PointClass(x=-CanvasClass.dx*CanvasClass.scale,
                        y=-CanvasClass.dy*CanvasClass.scale-CanvasClass.canvas.winfo_height())
                        
            #Korrektur der Skalierung
            sca=[CanvasClass.scale]*3
            
            #BaseEntitie erstellen um auf oberster Ebene zu Fräsen
            BaseEntitie=EntitieContentClass(Nr=-1,Name='BaseEntitie',
                                        parent=None,
                                        children=[],
                                        p0=P0,
                                        pb=PointClass(x=0.0,y=0.0),
                                        sca=sca,
                                        rot=0.0)
            
            
            hdls+=self.st_move[1].plot2can(CanvasClass.canvas,BaseEntitie,tag=self.nr,col='SteelBlue3')
            hdls+=self.st_move[2].plot2can(CanvasClass.canvas,BaseEntitie,tag=self.nr,col='SteelBlue3')
        return hdls
            
    def plot_start(self,Canvas=None,length=20):
        #st_point, st_angle=self.geos[0].get_start_end_points(0,parent)
                
        start,start_ang=self.get_st_en_points(0)

        x_ca,y_ca=Canvas.get_can_coordinates(start.x,start.y)

        dx=cos(radians(start_ang))*length
        dy=sin(radians(start_ang))*length

        hdl=Line(Canvas.canvas,x_ca,-y_ca,x_ca+dx,-y_ca-dy,fill='SteelBlue3',arrow='last')
        return hdl
    
    
    #Funktion zum drucken der zu fräsenden Kontur mit den Richtungspfeilen usw.
    def plot_cut_cor(self,Canvas=None,length=20):
        start,start_ang=self.get_st_en_points(0)

        #BaseEntitie erstellen um auf oberster Ebene zu Fräsen
        BaseEntitie=EntitieContentClass(Nr=-1,Name='BaseEntitie',
                                        parent=None,
                                        children=[],
                                        p0=PointClass(x=0.0,y=0.0),
                                        pb=PointClass(x=0.0,y=0.0),
                                        sca=[1,1,1],
                                        rot=0.0)


        x_ca,y_ca=Canvas.get_can_coordinates(start.x,start.y)
        
        if self.cut_cor==41:
            start_ang=start_ang+90
        else:
            start_ang=start_ang-90
            
        dx=cos(radians(start_ang))*length
        dy=sin(radians(start_ang))*length

        hdl=Line(Canvas.canvas,x_ca,-y_ca,x_ca+dx,-y_ca-dy,fill='SteelBlue3',arrow='last')
        return hdl
            
    def plot_end(self,Canvas=None,length=20):
        ende,en_angle=self.get_st_en_points(1)
      
        dx=cos(radians(en_angle))*length
        dy=sin(radians(en_angle))*length

        x_ca,y_ca=Canvas.get_can_coordinates(ende.x,ende.y)

        hdl=Line(Canvas.canvas,x_ca,-y_ca,x_ca+dx,-y_ca-dy,fill='PaleGreen2',arrow='first')
        return hdl

    def make_start_moves(self,config):
        self.st_move=[]

        #Einlaufradius und Versatz 
        start_rad=config.start_rad.get()
        start_ver=start_rad

        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad=config.tool_dia.get()/2
    
        #Errechnen des Startpunkts mit und ohne Werkzeug Kompensation        
        start,start_ang=self.get_st_en_points(0)
      
        if self.cut_cor==40:              
            self.st_move.append(start)

        #Fräsradiuskorrektur Links        
        elif self.cut_cor==41:
            #Mittelpunkts für Einlaufradius
            Oein=start.get_arc_point(start_ang+90,start_rad+tool_rad)
            #Startpunkts für Einlaufradius
            Pa_ein=Oein.get_arc_point(start_ang+180,start_rad+tool_rad)
            #Startwerts für Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(start_ang+90,start_ver)
            
            #Eintauchpunkt errechnete Korrektur
            start_ein=Pg_ein.get_arc_point(start_ang,tool_rad)
            self.st_move.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line=LineGeo(Pg_ein,Pa_ein)
            self.st_move.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad=ArcGeo(Pa=Pa_ein,Pe=start,O=Oein,r=start_rad+tool_rad,dir=1)
            self.st_move.append(start_rad)
            
        #Fräsradiuskorrektur Rechts        
        elif self.cut_cor==42:

            #Mittelpunkt für Einlaufradius
            Oein=start.get_arc_point(start_ang-90,start_rad+tool_rad)
            #Startpunkt für Einlaufradius
            Pa_ein=Oein.get_arc_point(start_ang+180,start_rad+tool_rad)
            #IJ=Oein-Pa_ein
            #Startwerts für Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(start_ang-90,start_ver)
            
            #Eintauchpunkts errechnete Korrektur
            start_ein=Pg_ein.get_arc_point(start_ang,tool_rad)
            self.st_move.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line=LineGeo(Pg_ein,Pa_ein)
            self.st_move.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad=ArcGeo(Pa=Pa_ein,Pe=start,O=Oein,r=start_rad+tool_rad,dir=0)
            self.st_move.append(start_rad)
    
    def Write_GCode(self,config,postpro):

        #Erneutes erstellen der Einlaufgeometrien
        self.make_start_moves(config)
        
        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad=config.tool_dia.get()/2

        #BaseEntitie erstellen um auf oberster Ebene zu Fräsen
        BaseEntitie=EntitieContentClass(Nr=-1,Name='BaseEntitie',
                                        parent=None,
                                        children=[],
                                        p0=PointClass(x=0.0,y=0.0),
                                        pb=PointClass(x=0.0,y=0.0),
                                        sca=[1,1,1],
                                        rot=0.0)
        


        depth=config.axis3_mill_depth.get()
        max_slice=config.axis3_slice_depth.get()
        
        #Wenn Output Format DXF dann nur einmal Fräsen
        if postpro.output_type=='dxf':
            depth=max_slice

        #Scheibchendicke bei Frästiefe auf Frästiefe begrenzen
        if -abs(max_slice)<=depth:
            mom_depth=depth
        else:
            mom_depth=-abs(max_slice)


        #Positionieren des Werkzeugs über dem Anfang und Eintauchen
        self.st_move[0].Write_GCode(parent=BaseEntitie,postpro=postpro)
        
        postpro.rap_pos_z(config.axis3_safe_margin.get())
        postpro.chg_feed_rate(config.F_G1_Depth.get())
        postpro.lin_pol_z(mom_depth)
        postpro.chg_feed_rate(config.F_G1_Plane.get())

        #Wenn G41 oder G42 an ist Fräsradiuskorrektur        
        if self.cut_cor!=40:
            
            #Errechnen des Startpunkts ohne Werkzeug Kompensation
            #und einschalten der Kompensation     
            start,start_ang=self.get_st_en_points(0)
            postpro.set_cut_cor(self.cut_cor,start)
            
            self.st_move[1].Write_GCode(parent=BaseEntitie,postpro=postpro)
            self.st_move[2].Write_GCode(parent=BaseEntitie,postpro=postpro)

        #Schreiben der Geometrien für den ersten Schnitt
        for geo in self.geos:
            geo.Write_GCode(self.parent,postpro)

        #Ausschalten der Fräsradiuskorrektur
        if (not(self.cut_cor==40))&(postpro.cancel_cc_for_depth==1):
            ende,en_angle=self.get_st_en_points(1)
            if self.cut_cor==41:
                pos_cut_out=ende.get_arc_point(en_angle-90,tool_rad)
            elif self.cut_cor==42:
                pos_cut_out=ende.get_arc_point(en_angle+90,tool_rad)         
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
                postpro.set_cut_cor(self.cut_cor,start)
                
            for geo_nr in range(len(self.geos)):
                self.geos[geo_nr].Write_GCode(self.parent,postpro)

            #Errechnen des Konturwerte mit Fräsradiuskorrektur und ohne
            ende,en_angle=self.get_st_en_points(1)
            if self.cut_cor==41:
                pos_cut_out=ende.get_arc_point(en_angle-90,tool_rad)
            elif self.cut_cor==42:
                pos_cut_out=ende.get_arc_point(en_angle+90,tool_rad)

            #Ausschalten der Fräsradiuskorrektur falls benötigt          
            if (not(self.cut_cor==40))&(postpro.cancel_cc_for_depth==1):         
                postpro.deactivate_cut_cor(pos_cut_out)
     
        #Anfangswert für Direction wieder herstellen falls nötig
        if (snr%2)>0:
            self.reverse()
            self.switch_cut_cor()

        #Fertig und Zurückziehen des Werkzeugs
        postpro.lin_pol_z(config.axis3_safe_margin.get())
        postpro.rap_pos_z(config.axis3_retract.get())

        #Falls Fräsradius Korrektur noch nicht ausgeschaltet ist ausschalten.
        if (not(self.cut_cor==40))&(not(postpro.cancel_cc_for_depth)):
            #Errechnen des Konturwerte mit Fräsradiuskorrektur und ohne
            ende,en_angle=self.get_st_en_points(1)
            postpro.deactivate_cut_cor(ende)        

        return 1    
    
class EntitieContentClass:
    def __init__(self,type="Entitie",Nr=None,Name='',parent=None,children=[],
                p0=PointClass(x=0.0,y=0.0),pb=PointClass(x=0.0,y=0.0),sca=[1,1,1],rot=0.0):
                    
        self.type=type
        self.Nr=Nr
        self.Name=Name
        self.children=children
        self.p0=p0
        self.pb=pb
        self.sca=sca
        self.rot=rot
        self.parent=parent

    def __cmp__(self, other):
         return cmp(self.EntNr, other.EntNr)        
        
    def __str__(self):
        return ('\ntype:        %s' %self.type) +\
               ('\nNr :      %i' %self.Nr) +\
               ('\nName:     %s' %self.Name)+\
               ('\np0:          %s' %self.p0)+\
               ('\npb:          %s' %self.pb)+\
               ('\nsca:         %s' %self.sca)+\
               ('\nrot:         %s' %self.rot)+\
               ('\nchildren:    %s' %self.children)
            
    #Hinzufuegen der Kontur zu den Entities
    def addchild(self,child):
        self.children.append(child)
        
